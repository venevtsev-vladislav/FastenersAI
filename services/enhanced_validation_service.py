"""
Улучшенный сервис валидации результатов поиска с помощью ИИ
Делает повторный поиск с улучшенными запросами и формирует точные вопросы
"""

import logging
import json
from typing import List, Dict, Any, Tuple
from services.openai_service import OpenAIService
from database.supabase_client import search_parts

logger = logging.getLogger(__name__)

class EnhancedValidationService:
    """Улучшенный сервис валидации с повторным поиском"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        from services.validation_prompts import ENHANCED_VALIDATION_PROMPT
        self.validation_prompt = ENHANCED_VALIDATION_PROMPT
    
    async def enhanced_validate_and_refine(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Валидирует результаты и делает повторный поиск с улучшениями
        
        Args:
            original_request: Исходный запрос пользователя
            search_results: Результаты поиска
            
        Returns:
            Dict: Результат валидации с улучшенными результатами
        """
        try:
            logger.info("🔍 Начинаю улучшенную валидацию с повторным поиском")
            
            # 1. Анализируем текущие результаты
            validation_data = self._prepare_validation_data(original_request, search_results)
            initial_validation = await self._analyze_with_ai(validation_data)
            
            logger.info(f"📊 Первичная валидация: {initial_validation.get('status')}")
            
            # 2. Если нужна доработка, генерируем улучшенные запросы
            if initial_validation.get('status') in ['NEEDS_REFINEMENT', 'NEEDS_CLARIFICATION']:
                logger.info("🔄 Генерирую улучшенные поисковые запросы...")
                
                improved_queries = await self._generate_improved_queries(
                    original_request, search_results, initial_validation
                )
                
                # 3. Делаем повторный поиск с улучшенными запросами
                if improved_queries:
                    logger.info("🔍 Выполняю повторный поиск с улучшенными запросами...")
                    refined_results = await self._refined_search(improved_queries, search_results)
                    
                    # 4. Объединяем и анализируем финальные результаты
                    final_results = self._merge_results(search_results, refined_results)
                    final_validation = await self._analyze_with_ai(
                        self._prepare_validation_data(original_request, final_results)
                    )
                    
                    return {
                        **final_validation,
                        'improved_queries': improved_queries,
                        'refined_results': refined_results,
                        'final_results': final_results,
                        'has_improvements': True
                    }
            
            # Если доработка не нужна, возвращаем исходный результат
            return {
                **initial_validation,
                'has_improvements': False
            }
            
        except Exception as e:
            logger.error(f"❌ Ошибка при улучшенной валидации: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка улучшенной валидации: {str(e)}",
                "issues": [],
                "confidence": 0.0,
                "has_improvements": False
            }
    
    async def _generate_improved_queries(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]], 
        validation: Dict[str, Any]
    ) -> Dict[int, List[str]]:
        """Генерирует улучшенные поисковые запросы для проблемных позиций"""
        try:
            # Формируем запрос для ИИ
            improvement_prompt = f"""
Проанализируй проблемы с поиском и предложи улучшенные запросы для Supabase.

ИСХОДНЫЙ ЗАПРОС: {original_request}

ПРОБЛЕМЫ ВАЛИДАЦИИ: {validation.get('message', '')}

ТВОЯ ЗАДАЧА:
1. Определи, какие позиции требуют улучшения
2. Предложи 2-3 альтернативных поисковых запроса для каждой проблемной позиции
3. Учитывай синонимы, альтернативные названия, возможные ошибки в написании

ФОРМАТ ОТВЕТА:
{{
    "improvements": [
        {{
            "position": 1,
            "original_query": "винт DIN 603 6 мм 40 мм",
            "improved_queries": [
                "болт DIN603 6x40 цинк",
                "винт мебельный 6мм 40мм",
                "DIN603 M6 40 цинк"
            ],
            "reason": "Возможно, в каталоге используется другое название или формат"
        }}
    ]
}}

Будь конкретным и предлагай реальные альтернативы!
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по поиску крепежных деталей. Помогаешь улучшить поисковые запросы."},
                    {"role": "user", "content": improvement_prompt}
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
            # Парсим JSON ответ
            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)
                    return {item['position']: item['improved_queries'] for item in result.get('improvements', [])}
                else:
                    logger.warning("Не удалось найти JSON в ответе ИИ")
                    return {}
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON ответ: {e}")
                return {}
                
        except Exception as e:
            logger.error(f"Ошибка при генерации улучшенных запросов: {e}")
            return {}
    
    async def _refined_search(
        self, 
        improved_queries: Dict[int, List[str]], 
        original_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Выполняет повторный поиск с улучшенными запросами"""
        refined_results = []
        
        for position, queries in improved_queries.items():
            logger.info(f"🔍 Повторный поиск для позиции {position}: {queries}")
            
            for query in queries:
                try:
                    # Ищем деталь с улучшенным запросом
                    results = await search_parts(query=query, user_intent={})
                    
                    if results:
                        # Добавляем информацию о позиции и улучшенном запросе
                        for result in results:
                            result['order_position'] = position
                            result['improved_query'] = query
                            result['is_refined_search'] = True
                            result['search_query'] = query
                            result['full_query'] = f"Улучшенный поиск: {query}"
                        
                        refined_results.extend(results)
                        logger.info(f"✅ Найдено {len(results)} результатов для '{query}'")
                        break  # Если нашли, переходим к следующей позиции
                        
                except Exception as e:
                    logger.warning(f"Ошибка при поиске '{query}': {e}")
                    continue
        
        return refined_results
    
    def _merge_results(
        self, 
        original_results: List[Dict[str, Any]], 
        refined_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Объединяет исходные и улучшенные результаты"""
        # Группируем по позициям
        position_results = {}
        
        # Добавляем исходные результаты
        for result in original_results:
            position = result.get('order_position', 0)
            if position not in position_results:
                position_results[position] = []
            position_results[position].append(result)
        
        # Добавляем улучшенные результаты
        for result in refined_results:
            position = result.get('order_position', 0)
            if position not in position_results:
                position_results[position] = []
            position_results[position].append(result)
        
        # Собираем в правильном порядке
        merged_results = []
        for position in sorted(position_results.keys()):
            merged_results.extend(position_results[position])
        
        return merged_results
    
    def _prepare_validation_data(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]]
    ) -> str:
        """Подготавливает данные для валидации"""
        
        # Группируем результаты по позициям
        positions_data = {}
        for result in search_results:
            position = result.get('order_position', 0)
            if position not in positions_data:
                positions_data[position] = {
                    'search_query': result.get('full_query', ''),
                    'found_items': []
                }
            
            if result.get('sku') != 'НЕ НАЙДЕНО':
                item_info = {
                    'sku': result.get('sku', ''),
                    'name': result.get('name', ''),
                    'type': result.get('type', ''),
                    'confidence': result.get('confidence_score', 0)
                }
                
                # Добавляем информацию об улучшенном поиске
                if result.get('is_refined_search'):
                    item_info['improved_query'] = result.get('improved_query', '')
                    item_info['is_refined'] = True
                
                positions_data[position]['found_items'].append(item_info)
        
        # Формируем текст для анализа
        analysis_text = f"""
ИСХОДНЫЙ ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{original_request}

АНАЛИЗ ПОЗИЦИЙ:
"""
        
        for position in sorted(positions_data.keys()):
            pos_data = positions_data[position]
            analysis_text += f"""
ПОЗИЦИЯ {position}:
Поисковый запрос: {pos_data['search_query']}
Найдено товаров: {len(pos_data['found_items'])}
"""
            
            if pos_data['found_items']:
                for item in pos_data['found_items']:
                    if item.get('is_refined'):
                        analysis_text += f"  - {item['name']} (SKU: {item['sku']}, улучшенный поиск: {item.get('improved_query', '')})\n"
                    else:
                        analysis_text += f"  - {item['name']} (SKU: {item['sku']}, уверенность: {item['confidence']:.2f})\n"
            else:
                analysis_text += "  - ТОВАР НЕ НАЙДЕН\n"
        
        return analysis_text
    
    async def _analyze_with_ai(self, validation_data: str) -> Dict[str, Any]:
        """Анализирует данные с помощью ИИ"""
        try:
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": self.validation_prompt},
                    {"role": "user", "content": f"ДАННЫЕ ДЛЯ АНАЛИЗА:\n{validation_data}"}
                ],
                temperature=0.1,
                max_tokens=1000
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = ai_response[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    result = self._parse_text_response(ai_response)
                
                return result
                
            except json.JSONDecodeError as e:
                logger.warning(f"Не удалось распарсить JSON ответ: {e}")
                return self._parse_text_response(ai_response)
                
        except Exception as e:
            logger.error(f"Ошибка при анализе с ИИ: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка анализа ИИ: {str(e)}",
                "issues": [],
                "confidence": 0.0
            }
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Парсит текстовый ответ ИИ"""
        response_lower = response.lower()
        
        if "approved" in response_lower or "одобрено" in response_lower:
            status = "APPROVED"
        elif "refinement" in response_lower or "доработка" in response_lower:
            status = "NEEDS_REFINEMENT"
        else:
            status = "NEEDS_CLARIFICATION"
        
        return {
            "status": status,
            "message": response,
            "issues": [],
            "confidence": 0.7 if status == "APPROVED" else 0.5
        }
    
    def generate_clarification_questions(self, validation_result: Dict[str, Any]) -> List[str]:
        """Генерирует точные вопросы для уточнения на основе валидации"""
        questions = []
        
        if validation_result.get('status') == 'NEEDS_CLARIFICATION':
            questions.append("Какие именно характеристики деталей наиболее важны для вас?")
            questions.append("Можете уточнить стандарты (DIN, ISO) если они критичны?")
            questions.append("Есть ли предпочтения по материалу или покрытию?")
        
        elif validation_result.get('status') == 'NEEDS_REFINEMENT':
            if validation_result.get('has_improvements'):
                questions.append("Мы нашли альтернативные варианты. Подходят ли они?")
                questions.append("Нужно ли искать товары с другими параметрами?")
            else:
                questions.append("Какие параметры можно изменить для поиска аналогов?")
                questions.append("Есть ли альтернативные названия для этих деталей?")
        
        return questions
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Формирует краткое резюме валидации для пользователя"""
        status = validation_result.get('status', 'UNKNOWN')
        message = validation_result.get('message', '')
        
        if status == "APPROVED":
            return f"✅ Валидация пройдена успешно!\n\n{message}"
        
        elif status == "NEEDS_REFINEMENT":
            if validation_result.get('has_improvements'):
                return f"⚠️ Требуется доработка заказа (с улучшениями)\n\n{message}"
            else:
                return f"⚠️ Требуется доработка заказа\n\n{message}"
        
        elif status == "NEEDS_CLARIFICATION":
            return f"❓ Нужны уточнения\n\n{message}"
        
        else:
            return f"❌ Ошибка валидации\n\n{message}"
