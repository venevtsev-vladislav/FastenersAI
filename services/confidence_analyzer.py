"""
Сервис для анализа уверенности бота в результатах поиска
"""

import logging
from typing import Dict, List
from services.openai_service import OpenAIService

logger = logging.getLogger(__name__)

class ConfidenceAnalyzer:
    """Анализатор уверенности бота в результатах поиска"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
    
    async def analyze_confidence(self, user_query: str, search_results: List[Dict]) -> List[Dict]:
        """Анализирует уверенность бота в каждом результате"""
        try:
            if not search_results:
                return []
            
            # Анализируем каждый результат через GPT
            analyzed_results = []
            
            for i, result in enumerate(search_results):  # Анализируем все результаты
                confidence_score = await self._analyze_single_result(user_query, result, i + 1)
                
                # Добавляем оценку уверенности к результату
                result_with_confidence = result.copy()
                result_with_confidence['confidence_score'] = confidence_score
                analyzed_results.append(result_with_confidence)
            
            # Сортируем по уверенности
            analyzed_results.sort(key=lambda x: x['confidence_score'], reverse=True)
            
            logger.info(f"Проанализирована уверенность для {len(analyzed_results)} результатов")
            return analyzed_results
            
        except Exception as e:
            logger.error(f"Ошибка при анализе уверенности: {e}")
            # Возвращаем результаты с базовой оценкой уверенности
            return self._fallback_confidence_analysis(user_query, search_results)
    
    async def _analyze_single_result(self, user_query: str, result: Dict, position: int) -> int:
        """Анализирует уверенность в одном результате через GPT"""
        try:
            name = result.get('name', '')
            sku = result.get('sku', '')
            
            # Формируем промпт для GPT
            system_prompt = """
Ты - эксперт по анализу соответствия результатов поиска запросам пользователей.
Оцени, насколько точно найденная деталь соответствует запросу пользователя.

Оцени по шкале от 0 до 100, где:
- 100% - идеальное совпадение
- 80-99% - очень хорошее совпадение
- 60-79% - хорошее совпадение
- 40-59% - среднее совпадение
- 20-39% - слабое совпадение
- 0-19% - очень слабое совпадение

Учитывай:
- Точность названия
- Соответствие характеристик
- Релевантность типа детали
- Позицию в результатах поиска

Верни только число от 0 до 100, без дополнительного текста.
"""
            
            user_prompt = f"""
Запрос пользователя: "{user_query}"

Найденная деталь:
- Название: {name}
- SKU: {sku}
- Позиция в результатах: {position}

Оцени уверенность в процентах (0-100):
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=10
            )
            
            # Извлекаем ответ
            confidence_text = response.choices[0].message.content.strip()
            
            # Парсим число
            try:
                confidence = int(confidence_text.replace('%', ''))
                confidence = max(0, min(100, confidence))  # Ограничиваем диапазон
                return confidence
            except ValueError:
                # Если не удалось распарсить, используем fallback
                return self._calculate_fallback_confidence(user_query, result, position)
                
        except Exception as e:
            logger.error(f"Ошибка при GPT анализе уверенности: {e}")
            return self._calculate_fallback_confidence(user_query, result, position)
    
    def _calculate_fallback_confidence(self, user_query: str, result: Dict, position: int) -> int:
        """Fallback расчет уверенности без GPT"""
        try:
            # Базовый балл на основе позиции
            position_score = max(0, 100 - (position - 1) * 8)
            
            # Анализ совпадения названия
            name = result.get('name', '').lower()
            query = user_query.lower()
            
            # Подсчет совпадающих слов
            query_words = [word for word in query.split() if len(word) > 2]
            name_words = name.split()
            
            matching_words = 0
            for q_word in query_words:
                for n_word in name_words:
                    if q_word in n_word or n_word in q_word:
                        matching_words += 1
                        break
            
            # Балл за совпадение слов
            word_match_score = min(30, (matching_words / len(query_words)) * 30) if query_words else 0
            
            # Балл за точность совпадения
            if query in name:
                exact_match_score = 40
            elif any(word in name for word in query_words):
                exact_match_score = 20
            else:
                exact_match_score = 0
            
            # Итоговый балл
            total_confidence = min(100, position_score + word_match_score + exact_match_score)
            
            return int(total_confidence)
            
        except Exception as e:
            logger.error(f"Ошибка в fallback расчете уверенности: {e}")
            return max(0, 100 - (position - 1) * 8)
    
    def _fallback_confidence_analysis(self, user_query: str, search_results: List[Dict]) -> List[Dict]:
        """Fallback анализ уверенности без GPT"""
        analyzed_results = []
        
        for i, result in enumerate(search_results):
            confidence_score = self._calculate_fallback_confidence(user_query, result, i + 1)
            
            result_with_confidence = result.copy()
            result_with_confidence['confidence_score'] = confidence_score
            analyzed_results.append(result_with_confidence)
        
        # Сортируем по уверенности
        analyzed_results.sort(key=lambda x: x['confidence_score'], reverse=True)
        
        return analyzed_results
