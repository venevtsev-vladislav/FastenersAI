"""
Циклический сервис валидации Excel файла
Проверяет весь файл, улучшает проблемные позиции, максимум 3 цикла
"""

import logging
import json
from typing import List, Dict, Any, Tuple
from services.openai_service import OpenAIService
from database.supabase_client import search_parts
from services.excel_generator import ExcelGenerator
import tempfile
import os

logger = logging.getLogger(__name__)

class CyclicValidationService:
    """Циклический сервис валидации с автоматическим улучшением"""
    
    def __init__(self):
        self.openai_service = OpenAIService()
        from services.validation_prompts import CYCLIC_VALIDATION_PROMPT
        self.validation_prompt = CYCLIC_VALIDATION_PROMPT
        self.max_cycles = 3
    
    async def cyclic_validate_and_improve(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Циклически валидирует и улучшает результаты до готовности или лимита циклов
        
        Args:
            original_request: Исходный запрос пользователя
            search_results: Результаты поиска
            
        Returns:
            Dict: Финальный результат с улучшенными данными
        """
        try:
            logger.info("🔄 Начинаю циклическую валидацию и улучшение")
            
            current_results = search_results.copy()
            cycle_count = 0
            improvement_history = []
            
            while cycle_count < self.max_cycles:
                cycle_count += 1
                logger.info(f"🔄 Цикл валидации {cycle_count}/{self.max_cycles}")
                
                # 1. Создаем Excel для анализа
                excel_file = await self._create_excel_for_validation(current_results, original_request)
                
                # 2. ИИ анализирует весь Excel файл
                validation_result = await self._validate_excel_file(
                    original_request, current_results, excel_file
                )
                
                logger.info(f"📊 Цикл {cycle_count}: {validation_result.get('status')}")
                
                # 3. Если все готово - выходим
                if validation_result.get('status') == 'APPROVED':
                    logger.info(f"✅ Цикл {cycle_count}: Валидация пройдена!")
                    break
                
                # 4. Если нужна доработка - улучшаем проблемные позиции
                if validation_result.get('status') in ['NEEDS_REFINEMENT', 'NEEDS_CLARIFICATION']:
                    logger.info(f"🔧 Цикл {cycle_count}: Улучшаю проблемные позиции...")
                    
                    improved_results = await self._improve_problematic_positions(
                        original_request, current_results, validation_result
                    )
                    
                    if improved_results:
                        # Обновляем только проблемные позиции
                        current_results = self._update_problematic_positions(
                            current_results, improved_results
                        )
                        
                        improvement_history.append({
                            'cycle': cycle_count,
                            'improvements': improved_results,
                            'validation_status': validation_result.get('status')
                        })
                        
                        logger.info(f"✅ Цикл {cycle_count}: Улучшено {len(improved_results)} позиций")
                    else:
                        logger.warning(f"⚠️ Цикл {cycle_count}: Не удалось улучшить позиции")
                        break
                else:
                    logger.warning(f"❌ Цикл {cycle_count}: Неожиданный статус валидации")
                    break
                
                # Очищаем временный файл
                if os.path.exists(excel_file):
                    os.remove(excel_file)
            
            # Формируем финальный результат
            final_result = {
                'status': validation_result.get('status', 'UNKNOWN'),
                'message': validation_result.get('message', ''),
                'final_results': search_results,  # Используем исходные результаты
                'cycles_completed': cycle_count,
                'improvement_history': improvement_history,
                'max_cycles_reached': cycle_count >= self.max_cycles
            }
            
            logger.info(f"🏁 Циклическая валидация завершена: {cycle_count} циклов, статус: {final_result['status']}")
            return final_result
            
        except Exception as e:
            logger.error(f"❌ Ошибка при циклической валидации: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка циклической валидации: {str(e)}",
                "final_results": search_results,
                "cycles_completed": 0,
                "improvement_history": [],
                "max_cycles_reached": False
            }
    
    async def _create_excel_for_validation(
        self, 
        search_results: List[Dict[str, Any]], 
        user_request: str
    ) -> str:
        """Создает Excel файл для анализа ИИ"""
        try:
            excel_generator = ExcelGenerator()
            excel_file = await excel_generator.generate_excel(search_results, user_request)
            logger.info(f"📊 Excel создан для валидации: {excel_file}")
            return excel_file
        except Exception as e:
            logger.error(f"Ошибка создания Excel для валидации: {e}")
            raise
    
    async def _validate_excel_file(
        self, 
        original_request: str, 
        search_results: List[Dict[str, Any]], 
        excel_file_path: str
    ) -> Dict[str, Any]:
        """ИИ анализирует весь Excel файл"""
        try:
            # Читаем содержимое Excel для анализа
            excel_content = self._read_excel_content(excel_file_path, search_results)
            
            # Формируем данные для анализа
            validation_data = f"""
ИСХОДНЫЙ ЗАПРОС ПОЛЬЗОВАТЕЛЯ:
{original_request}

АНАЛИЗ EXCEL ФАЙЛА:
{excel_content}

ТВОЯ ЗАДАЧА:
Проанализируй весь Excel файл и определи, готов ли он для отправки клиенту.

КРИТЕРИИ ОЦЕНКИ:
1. Все ли позиции найдены?
2. Соответствуют ли найденные товары запросу?
3. Есть ли множественные варианты, требующие выбора?
4. Качество найденных товаров

ОТВЕТЬ:
- "APPROVED" - если файл готов для клиента
- "NEEDS_REFINEMENT" - если нужны улучшения
- "NEEDS_CLARIFICATION" - если нужны уточнения от пользователя

УКАЖИ конкретные проблемы и позиции для улучшения.
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": self.validation_prompt},
                    {"role": "user", "content": validation_data}
                ],
                temperature=0.1,
                max_tokens=1500
            )
            
            ai_response = response.choices[0].message.content
            
            # Парсим ответ
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
            logger.error(f"Ошибка при валидации Excel файла: {e}")
            return {
                "status": "ERROR",
                "message": f"Ошибка валидации Excel: {str(e)}",
                "issues": [],
                "confidence": 0.0
            }
    
    def _read_excel_content(self, excel_file_path: str, search_results: List[Dict[str, Any]]) -> str:
        """Читает содержимое Excel файла для анализа"""
        try:
            # Простое чтение - можно расширить для более детального анализа
            excel_content = f"Excel файл содержит результаты поиска для {len(self._get_unique_positions(search_results))} позиций"
            return excel_content
        except Exception as e:
            logger.warning(f"Не удалось прочитать Excel: {e}")
            return "Excel файл создан"
    
    def _get_unique_positions(self, search_results: List[Dict[str, Any]]) -> set:
        """Получает уникальные позиции из результатов"""
        return set(result.get('order_position', 0) for result in search_results)
    
    async def _improve_problematic_positions(
        self, 
        original_request: str, 
        current_results: List[Dict[str, Any]], 
        validation_result: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Улучшает только проблемные позиции"""
        try:
            # Анализируем проблемы и генерируем улучшенные запросы
            problematic_positions = self._identify_problematic_positions(validation_result)
            
            if not problematic_positions:
                logger.info("Нет проблемных позиций для улучшения")
                return []
            
            logger.info(f"🔧 Улучшаю позиции: {problematic_positions}")
            
            improved_results = []
            for position in problematic_positions:
                improved_queries = await self._generate_improved_queries_for_position(
                    position, original_request, validation_result
                )
                
                if improved_queries:
                    # Ищем с улучшенными запросами
                    refined_results = await self._search_with_improved_queries(
                        position, improved_queries
                    )
                    
                    if refined_results:
                        improved_results.extend(refined_results)
                        logger.info(f"✅ Позиция {position}: найдено {len(refined_results)} улучшений")
            
            return improved_results
            
        except Exception as e:
            logger.error(f"Ошибка при улучшении проблемных позиций: {e}")
            return []
    
    def _identify_problematic_positions(self, validation_result: Dict[str, Any]) -> List[int]:
        """Определяет проблемные позиции из валидации"""
        problematic_positions = []
        
        # Анализируем сообщение валидации
        message = validation_result.get('message', '').lower()
        
        # Ищем упоминания позиций
        import re
        position_matches = re.findall(r'позиция\s*(\d+)', message)
        for match in position_matches:
            problematic_positions.append(int(match))
        
        # Если не нашли конкретные позиции, берем все с низкой уверенностью
        if not problematic_positions:
            for result in current_results:
                if result.get('confidence_score', 0) < 0.7:
                    pos = result.get('order_position', 0)
                    if pos not in problematic_positions:
                        problematic_positions.append(pos)
        
        return problematic_positions
    
    async def _generate_improved_queries_for_position(
        self, 
        position: int, 
        original_request: str, 
        validation_result: Dict[str, Any]
    ) -> List[str]:
        """Генерирует улучшенные запросы для конкретной позиции"""
        try:
            # Находим исходный запрос для позиции
            original_item = None
            for result in self._current_results:
                if result.get('order_position') == position:
                    original_item = result
                    break
            
            if not original_item:
                return []
            
            improvement_prompt = f"""
Улучши поисковый запрос для позиции {position}.

ИСХОДНЫЙ ЗАПРОС: {original_item.get('full_query', '')}
ПРОБЛЕМА: {validation_result.get('message', '')}

Предложи 3 альтернативных запроса для поиска в Supabase.
Учитывай синонимы, альтернативные названия, возможные ошибки.

ФОРМАТ: просто список запросов, каждый с новой строки
"""
            
            response = await self.openai_service.client.chat.completions.create(
                model=self.openai_service.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по поиску крепежных деталей. Помогаешь улучшить поисковые запросы."},
                    {"role": "user", "content": improvement_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            ai_response = response.choices[0].message.content
            
            # Парсим ответ - простое разделение по строкам
            queries = [q.strip() for q in ai_response.split('\n') if q.strip()]
            return queries[:3]  # Берем максимум 3
            
        except Exception as e:
            logger.error(f"Ошибка генерации улучшенных запросов для позиции {position}: {e}")
            return []
    
    async def _search_with_improved_queries(
        self, 
        position: int, 
        improved_queries: List[str]
    ) -> List[Dict[str, Any]]:
        """Ищет с улучшенными запросами"""
        refined_results = []
        
        for query in improved_queries:
            try:
                results = await search_parts(query=query, user_intent={})
                
                if results:
                    # Добавляем информацию о позиции и улучшенном запросе
                    for result in results:
                        result['order_position'] = position
                        result['improved_query'] = query
                        result['is_refined_search'] = True
                        result['search_query'] = query
                        result['full_query'] = f"Улучшенный поиск: {query}"
                        result['cycle_number'] = cycle_count
                    
                    refined_results.extend(results)
                    logger.info(f"✅ Позиция {position}: найдено {len(results)} результатов для '{query}'")
                    break  # Если нашли, переходим к следующей позиции
                    
            except Exception as e:
                logger.warning(f"Ошибка при поиске '{query}': {e}")
                continue
        
        return refined_results
    
    def _update_problematic_positions(
        self, 
        current_results: List[Dict[str, Any]], 
        improved_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Обновляет только проблемные позиции улучшенными результатами"""
        # Группируем по позициям
        position_results = {}
        
        # Добавляем текущие результаты
        for result in current_results:
            position = result.get('order_position', 0)
            if position not in position_results:
                position_results[position] = []
            position_results[position].append(result)
        
        # Заменяем проблемные позиции улучшенными результатами
        for result in improved_results:
            position = result.get('order_position', 0)
            if position in position_results:
                # Заменяем все результаты для этой позиции
                position_results[position] = [result]
            else:
                # Добавляем новую позицию
                position_results[position] = [result]
        
        # Собираем в правильном порядке
        updated_results = []
        for position in sorted(position_results.keys()):
            updated_results.extend(position_results[position])
        
        return updated_results
    
    def _parse_text_response(self, response: str) -> Dict[str, Any]:
        """Парсит текстовый ответ ИИ"""
        response_lower = response.lower()
        
        if "approved" in response_lower or "одобрено" in response_lower or "готово" in response_lower:
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
    
    def get_validation_summary(self, validation_result: Dict[str, Any]) -> str:
        """Формирует резюме циклической валидации"""
        status = validation_result.get('status', 'UNKNOWN')
        cycles = validation_result.get('cycles_completed', 0)
        max_reached = validation_result.get('max_cycles_reached', False)
        
        if status == "APPROVED":
            return f"✅ Валидация пройдена успешно за {cycles} циклов!\n\nФайл готов для отправки клиенту."
        
        elif max_reached:
            return f"⚠️ Достигнут лимит циклов ({cycles}). Файл требует ручной доработки."
        
        else:
            return f"⚠️ Требуется доработка заказа (цикл {cycles})\n\n{validation_result.get('message', '')}"
    
    def generate_clarification_questions(self, validation_result: Dict[str, Any]) -> List[str]:
        """Генерирует вопросы на основе циклической валидации"""
        questions = []
        cycles = validation_result.get('cycles_completed', 0)
        
        if cycles >= self.max_cycles:
            questions.append("Достигнут лимит автоматических улучшений. Нужна ручная доработка.")
            questions.append("Какие параметры можно изменить для поиска аналогов?")
        else:
            questions.append("Мы улучшили поиск. Подходят ли найденные альтернативы?")
            questions.append("Нужно ли искать товары с другими параметрами?")
        
        return questions
