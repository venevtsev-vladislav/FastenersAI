"""
Единый сервис ранжирования результатов поиска
Объединяет логику из Python и Deno Edge Function
"""

import logging
import re
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
from shared.logging import get_logger

logger = get_logger(__name__)


@dataclass
class MatchAnalysis:
    """Анализ совпадений для результата поиска"""
    type_match: bool
    standard_match: bool
    size_match: bool
    coating_match: bool
    matched_tokens: List[str]
    explanation: List[str]


@dataclass
class RankingTokens:
    """Токены для ранжирования"""
    type_tok: str | None
    std_toks: List[str]
    mxl_toks: List[str]
    coat_toks: List[str]


class RankingService:
    """Сервис ранжирования результатов поиска"""
    
    def __init__(self):
        # Веса для разных типов совпадений
        self.weights = {
            'type': 25,        # 25% за тип детали
            'standard': 40,    # 40% за стандарт DIN
            'size': 30,        # 30% за точные размеры
            'coating': 15      # 15% за покрытие
        }
        
        # Бонусы за комбинации
        self.combination_bonuses = {
            'standard_size': 15,      # Стандарт + размеры
            'type_size': 10,          # Тип + размеры
            'full_match': 20          # Полное совпадение
        }
    
    def normalize_string(self, text: str) -> str:
        """Нормализует строку для сравнения"""
        if not text:
            return ""
        
        return text.lower().strip() \
            .replace('×', 'x') \
            .replace('х', 'x') \
            .replace(' ', '') \
            .replace('din', 'din') \
            .replace('оцинк', 'цинк')
    
    def canonicalize_diameter(self, diameter: str) -> str:
        """Канонизирует диаметр"""
        if not diameter:
            return ""
        
        return diameter.replace(' мм', '').upper().replace('М', 'M')
    
    def canonicalize_length(self, length: str) -> str:
        """Канонизирует длину"""
        if not length:
            return ""
        
        return length.replace(' мм', '')
    
    def generate_mxl_variants(self, diameter: str, length: str) -> List[str]:
        """Генерирует варианты размеров MxL"""
        D = self.canonicalize_diameter(diameter)
        L = self.canonicalize_length(length)
        
        if not D or not L:
            return []
        
        # Специальная обработка для уголков (формат 50x50x40)
        if 'x' in D and not D.startswith('M'):
            # Это уголок, возвращаем как есть
            xs = ["x", "х", "×"]
            variants = []
            for X in xs:
                variants.extend([
                    D.replace('x', X),
                    D.replace('х', X),
                    D.replace('×', X)
                ])
            return list(set(variants))
        
        # Обычная обработка для болтов/винтов
        d_lat = D
        d_cyr = D.replace('M', 'М')
        xs = ["x", "х", "×", "-"]
        variants = []
        
        for X in xs:
            variants.extend([
                f"{d_lat}{X}{L}",
                f"{d_lat} {X} {L}",
                f"{d_cyr}{X}{L}",
                f"{d_cyr} {X} {L}"
            ])
        
        variants.extend([f"{d_lat}{L}", f"{d_cyr}{L}"])
        
        # Дополнительно: если диаметр десятичный, генерируем варианты
        decimal_match = re.match(r'^(\d+)[\.,](\d+)$', D)
        if decimal_match:
            fractional = decimal_match.group(2)
            alt_tokens = [
                f"{fractional}x{L}",
                f"{fractional} x {L}",
                f"{fractional}х{L}",
                f"{fractional} х {L}",
                f"{fractional}×{L}",
                f"{fractional} × {L}"
            ]
            variants.extend(alt_tokens)
        
        return list(set(variants))
    
    def extract_tokens(self, query: str, user_intent: Dict[str, Any]) -> RankingTokens:
        """Извлекает токены для ранжирования из запроса и намерения пользователя"""
        type_tok = user_intent.get('type')
        std_toks = []
        mxl_toks = []
        coat_toks = []
        
        # Стандарты
        if user_intent.get('standard'):
            std_toks.append(user_intent['standard'])
        
        # Размеры
        diameter = user_intent.get('diameter')
        length = user_intent.get('length')
        if diameter and length:
            mxl_variants = self.generate_mxl_variants(diameter, length)
            mxl_toks.extend(mxl_variants)
        
        # Покрытия
        if user_intent.get('coating'):
            coat_toks.append(user_intent['coating'])
        
        # Дополнительные токены из запроса
        query_lower = query.lower()
        if 'din' in query_lower:
            din_match = re.search(r'din\s*(\d+)', query_lower)
            if din_match:
                std_toks.append(f"DIN{din_match.group(1)}")
        
        return RankingTokens(
            type_tok=type_tok,
            std_toks=list(set(std_toks)),
            mxl_toks=list(set(mxl_toks)),
            coat_toks=list(set(coat_toks))
        )
    
    def analyze_matches(self, name: str, tokens: RankingTokens) -> MatchAnalysis:
        """Анализирует совпадения названия с токенами"""
        normalized_name = self.normalize_string(name)
        
        analysis = MatchAnalysis(
            type_match=False,
            standard_match=False,
            size_match=False,
            coating_match=False,
            matched_tokens=[],
            explanation=[]
        )
        
        logger.debug(f"Анализируем '{name}' с токенами: {tokens}")
        
        # Проверяем совпадение типа
        if tokens.type_tok and self.normalize_string(tokens.type_tok) in normalized_name:
            analysis.type_match = True
            analysis.matched_tokens.append(tokens.type_tok)
            analysis.explanation.append(f"✅ Совпадение типа: '{tokens.type_tok}'")
        
        # Проверяем совпадение стандарта
        matched_standards = [
            std for std in tokens.std_toks 
            if self.normalize_string(std) in normalized_name
        ]
        if matched_standards:
            analysis.standard_match = True
            analysis.matched_tokens.extend(matched_standards)
            analysis.explanation.append(f"✅ Совпадение стандарта: {', '.join(matched_standards)}")
        
        # Проверяем совпадение размеров
        matched_sizes = [
            size for size in tokens.mxl_toks 
            if self.normalize_string(size) in normalized_name
        ]
        if matched_sizes:
            analysis.size_match = True
            analysis.matched_tokens.extend(matched_sizes)
            analysis.explanation.append(f"✅ Совпадение размеров: {', '.join(matched_sizes)}")
        
        # Проверяем совпадение покрытия
        matched_coatings = [
            coat for coat in tokens.coat_toks 
            if self.normalize_string(coat) in normalized_name
        ]
        if matched_coatings:
            analysis.coating_match = True
            analysis.matched_tokens.extend(matched_coatings)
            analysis.explanation.append(f"✅ Совпадение покрытия: {', '.join(matched_coatings)}")
        
        return analysis
    
    def calculate_probability(self, analysis: MatchAnalysis) -> Tuple[int, str]:
        """Вычисляет вероятность совпадения"""
        total_score = 0
        explanation = analysis.explanation.copy()
        
        # Базовые очки за каждый тип совпадения
        if analysis.type_match:
            total_score += self.weights['type']
            explanation.append(f"📊 Вклад типа: +{self.weights['type']}%")
        
        if analysis.standard_match:
            total_score += self.weights['standard']
            explanation.append(f"📊 Вклад стандарта: +{self.weights['standard']}%")
        
        if analysis.size_match:
            total_score += self.weights['size']
            explanation.append(f"📊 Вклад размеров: +{self.weights['size']}%")
        
        if analysis.coating_match:
            total_score += self.weights['coating']
            explanation.append(f"📊 Вклад покрытия: +{self.weights['coating']}%")
        
        # Бонусы за комбинации
        if analysis.standard_match and analysis.size_match:
            bonus = self.combination_bonuses['standard_size']
            total_score += bonus
            explanation.append(f"🎯 Бонус за стандарт + размеры: +{bonus}%")
        
        if analysis.type_match and analysis.size_match:
            bonus = self.combination_bonuses['type_size']
            total_score += bonus
            explanation.append(f"🎯 Бонус за тип + размеры: +{bonus}%")
        
        if analysis.type_match and analysis.standard_match and analysis.size_match:
            bonus = self.combination_bonuses['full_match']
            total_score += bonus
            explanation.append(f"🎯 Бонус за полное совпадение: +{bonus}%")
        
        # Ограничения согласно требованиям
        if analysis.standard_match and analysis.size_match:
            # Если совпали и стандарт, и размеры, вероятность должна быть не меньше 80%
            total_score = max(total_score, 80)
            if total_score > 80:
                explanation.append("🔒 Минимальная вероятность для стандарт+размеры: 80%")
        
        elif analysis.type_match and not analysis.size_match and not analysis.standard_match:
            # Если совпал только тип без размеров и стандарта — не более 40%
            total_score = min(total_score, 40)
            explanation.append("🔒 Максимальная вероятность для только типа: 40%")
        
        elif analysis.coating_match and not analysis.type_match and not analysis.size_match and not analysis.standard_match:
            # Если совпало только покрытие — не более 20%
            total_score = min(total_score, 20)
            explanation.append("🔒 Максимальная вероятность для только покрытия: 20%")
        
        # Нормализация в диапазон 0-100%
        probability = max(0, min(100, round(total_score)))
        explanation.append(f"📈 Итоговая вероятность: {probability}%")
        
        return probability, '\n'.join(explanation)
    
    def get_match_reason(self, name: str, tokens: RankingTokens) -> str:
        """Определяет причину совпадения"""
        normalized_name = self.normalize_string(name)
        
        if tokens.type_tok and self.normalize_string(tokens.type_tok) in normalized_name and \
           any(self.normalize_string(t) in normalized_name for t in tokens.mxl_toks):
            return 'Точное совпадение типа и размеров'
        
        if tokens.type_tok and self.normalize_string(tokens.type_tok) in normalized_name:
            return 'Совпадение типа детали'
        
        if any(self.normalize_string(t) in normalized_name for t in tokens.std_toks):
            return 'Совпадение стандарта'
        
        if any(self.normalize_string(t) in normalized_name for t in tokens.mxl_toks):
            return 'Совпадение размеров'
        
        if any(self.normalize_string(t) in normalized_name for t in tokens.coat_toks):
            return 'Совпадение покрытия'
        
        return 'Частичное совпадение по названию'
    
    def rank_results(self, results: List[Dict[str, Any]], query: str, user_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Ранжирует результаты поиска"""
        if not results:
            return results
        
        logger.info(f"Ранжирую {len(results)} результатов для запроса: {query}")
        
        # Извлекаем токены для ранжирования
        tokens = self.extract_tokens(query, user_intent)
        
        # Анализируем каждый результат
        for result in results:
            analysis = self.analyze_matches(result.get('name', ''), tokens)
            probability, explanation = self.calculate_probability(analysis)
            
            # Добавляем поля ранжирования
            result.update({
                'relevance_score': probability,
                'probability_percent': probability,
                'confidence_score': probability / 100.0,  # Для совместимости
                'match_reason': self.get_match_reason(result.get('name', ''), tokens),
                'explanation': explanation,
                'matched_tokens': analysis.matched_tokens,
                'search_query': query,
                'full_query': query
            })
        
        # Сортируем по вероятности (убывание)
        results.sort(key=lambda x: x.get('probability_percent', 0), reverse=True)
        
        logger.info(f"Ранжирование завершено. Топ-3:")
        for i, result in enumerate(results[:3]):
            logger.info(f"  {i+1}. {result.get('sku', 'N/A')}: {result.get('probability_percent', 0)}% - {result.get('match_reason', 'N/A')}")
        
        return results
