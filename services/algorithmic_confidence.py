"""
Алгоритмический анализатор уверенности для результатов поиска
Заменяет GPT анализ на математические алгоритмы
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class AlgorithmicConfidenceAnalyzer:
    """Алгоритмический анализатор уверенности без GPT"""
    
    def __init__(self):
        # Веса для разных типов совпадений
        self.weights = {
            'type_match': 0.4,        # Совпадение типа детали
            'diameter_match': 0.3,    # Совпадение диаметра
            'length_match': 0.2,      # Совпадение длины
            'standard_match': 0.1,    # Совпадение стандарта
            'material_match': 0.1,    # Совпадение материала
            'coating_match': 0.1,     # Совпадение покрытия
            'grade_match': 0.1,       # Совпадение класса прочности
        }
    
    def analyze_confidence(self, user_query: str, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Анализирует уверенность в результатах поиска алгоритмически
        
        Args:
            user_query: Исходный запрос пользователя
            search_results: Результаты поиска из базы
            
        Returns:
            List[Dict]: Результаты с добавленными confidence_score и match_reason
        """
        logger.info(f"🔍 AlgorithmicConfidence: Анализирую {len(search_results)} результатов")
        
        # Если нет результатов, возвращаем как есть
        if not search_results:
            return search_results
        
        # Проверяем, является ли это множественным заказом
        is_multiple_order = any(result.get('order_position') for result in search_results)
        
        # Анализируем каждый результат
        for result in search_results:
            confidence_score = self.calculate_confidence(result, user_query)
            match_reason = self.get_match_reason(result, user_query)
            
            result['confidence_score'] = confidence_score
            result['match_reason'] = match_reason
        
        # Для множественных заказов НЕ пересортировываем по уверенности
        # Сохраняем порядок позиций из заказа пользователя
        if not is_multiple_order:
            # Сортируем по уверенности только для одиночных запросов
            search_results.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
            logger.info(f"🔍 AlgorithmicConfidence: Одиночный запрос - сортирую по уверенности")
        else:
            logger.info(f"🔍 AlgorithmicConfidence: Множественный заказ - сохраняю порядок позиций")
        
        logger.info(f"🔍 AlgorithmicConfidence: Анализ завершен, топ-3 по уверенности:")
        for i, result in enumerate(search_results[:3]):
            logger.info(f"   {i+1}. SKU: {result.get('sku')}, Уверенность: {result.get('confidence_score', 0):.2f}, Причина: {result.get('match_reason')}")
        
        return search_results
    
    def calculate_confidence(self, search_result: Dict[str, Any], user_query: str) -> float:
        """
        Вычисляет уверенность в результате поиска
        
        Args:
            search_result: Результат поиска из базы
            user_query: Исходный запрос пользователя
            
        Returns:
            float: Оценка уверенности от 0.0 до 1.0
        """
        score = 0.0
        
        # Базовый балл за то, что что-то нашли
        score += 0.1
        
        # Совпадение типа детали
        if self._match_type(search_result, user_query):
            score += self.weights['type_match']
        
        # Совпадение диаметра
        if self._match_diameter(search_result, user_query):
            score += self.weights['diameter_match']
        
        # Совпадение длины
        if self._match_length(search_result, user_query):
            score += self.weights['length_match']
        
        # Совпадение стандарта
        if self._match_standard(search_result, user_query):
            score += self.weights['standard_match']
        
        # Совпадение материала
        if self._match_material(search_result, user_query):
            score += self.weights['material_match']
        
        # Совпадение покрытия
        if self._match_coating(search_result, user_query):
            score += self.weights['coating_match']
        
        # Совпадение класса прочности
        if self._match_grade(search_result, user_query):
            score += self.weights['grade_match']
        
        # Ограничиваем максимальным значением 1.0
        return min(score, 1.0)
    
    def _match_type(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение типа детали"""
        result_type = search_result.get('type', '').lower()
        query_lower = user_query.lower()
        
        type_keywords = ['винт', 'гайка', 'шайба', 'болт', 'саморез', 'шуруп', 'анкер', 'дюбель']
        
        for keyword in type_keywords:
            if keyword in query_lower and keyword in result_type:
                return True
        
        return False
    
    def _match_diameter(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение диаметра"""
        result_diameter = search_result.get('diameter', '').lower()
        query_lower = user_query.lower()
        
        # Ищем M6, M8, 6 мм, 8 мм в запросе
        diameter_patterns = [
            r'[мm]\d+',           # M6, M8
            r'\d+\s*мм',          # 6 мм, 8 мм
            r'\d+\s*см',          # 6 см, 8 см
        ]
        
        import re
        for pattern in diameter_patterns:
            query_match = re.search(pattern, query_lower)
            if query_match:
                query_diameter = query_match.group(0)
                # Проверяем совпадение
                if query_diameter in result_diameter or result_diameter in query_diameter:
                    return True
        
        return False
    
    def _match_length(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение длины"""
        result_length = search_result.get('length', '').lower()
        query_lower = user_query.lower()
        
        # Ищем размеры в запросе
        length_patterns = [
            r'\d+\s*мм',          # 20 мм, 30 мм
            r'\d+\s*см',          # 2 см, 3 см
            r'\d+\s*дюйм',        # 1 дюйм
        ]
        
        import re
        for pattern in length_patterns:
            query_match = re.search(pattern, query_lower)
            if query_match:
                query_length = query_match.group(0)
                # Проверяем совпадение
                if query_length in result_length or result_length in query_length:
                    return True
        
        return False
    
    def _match_standard(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение стандарта"""
        result_name = search_result.get('name', '').lower()
        query_lower = user_query.lower()
        
        # Ищем стандарты в запросе
        standard_patterns = [
            r'din\s+\d+',         # DIN 965, DIN 985
            r'iso\s+\d+',         # ISO 7380
            r'гост\s+\d+',        # ГОСТ 7798
        ]
        
        import re
        for pattern in standard_patterns:
            query_match = re.search(pattern, query_lower)
            if query_match:
                query_standard = query_match.group(0)
                # Проверяем совпадение в названии
                if query_standard in result_name:
                    return True
        
        return False
    
    def _match_material(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение материала"""
        result_name = search_result.get('name', '').lower()
        query_lower = user_query.lower()
        
        materials = ['сталь', 'нержавеющая', 'латунь', 'алюминий', 'пластик', 'металл']
        
        for material in materials:
            if material in query_lower and material in result_name:
                return True
        
        return False
    
    def _match_coating(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение покрытия"""
        result_name = search_result.get('name', '').lower()
        query_lower = user_query.lower()
        
        coatings = ['цинк', 'оцинкованный', 'хромированный', 'крашеный', 'железо']
        
        for coating in coatings:
            if coating in query_lower and coating in result_name:
                return True
        
        return False
    
    def _match_grade(self, search_result: Dict[str, Any], user_query: str) -> bool:
        """Проверяет совпадение класса прочности"""
        result_name = search_result.get('name', '').lower()
        query_lower = user_query.lower()
        
        # Ищем классы прочности в запросе
        grade_patterns = [
            r'[aа]\d+',           # A2, A4
            r'\d+\.\d+',          # 8.8, 10.9
        ]
        
        import re
        for pattern in grade_patterns:
            query_match = re.search(pattern, query_lower)
            if query_match:
                query_grade = query_match.group(0)
                # Проверяем совпадение в названии
                if query_grade in result_name:
                    return True
        
        return False
    
    def get_match_reason(self, search_result: Dict[str, Any], user_query: str) -> str:
        """
        Определяет причину совпадения
        
        Args:
            search_result: Результат поиска
            user_query: Исходный запрос
            
        Returns:
            str: Причина совпадения
        """
        # Проверяем по приоритету
        if self._match_type(search_result, user_query) and self._match_diameter(search_result, user_query):
            return 'Точное совпадение типа и диаметра'
        elif self._match_type(search_result, user_query):
            return 'Совпадение типа детали'
        elif self._match_diameter(search_result, user_query):
            return 'Совпадение диаметра'
        elif self._match_standard(search_result, user_query):
            return 'Совпадение стандарта'
        elif self._match_material(search_result, user_query):
            return 'Совпадение материала'
        else:
            return 'Частичное совпадение по названию'
