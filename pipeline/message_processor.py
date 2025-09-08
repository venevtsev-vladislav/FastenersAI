"""
Модульный процессор сообщений для Telegram бота
Реализует УПРОЩЕННЫЙ pipeline: parse_normalize → search → rank → excel → finalize
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from telegram import Bot, Message
from telegram.ext import ContextTypes

from shared.logging import get_logger, set_correlation_id, log_user_request
from shared.errors import MessageProcessingError, handle_service_error
# from core.services.ranking import RankingService  # Убрано - ранжирование в Edge Function
from services.message_processor import MessageProcessor
from services.excel_generator import ExcelGenerator
# from database.supabase_client import save_user_request, search_parts  # Заменяем на Edge Function
from config import MIN_PROBABILITY_THRESHOLD

import os
import aiohttp

logger = get_logger(__name__)


class MessagePipeline:
    """Pipeline для обработки сообщений - УПРОЩЕННЫЙ"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        # self.ranking_service = RankingService()  # Убрано - ранжирование в Edge Function
        self.message_processor = MessageProcessor(bot=bot)
        self.excel_generator = ExcelGenerator()
    
    async def process_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Основной метод обработки сообщения - УПРОЩЕННЫЙ"""
        # Устанавливаем correlation ID для логирования
        correlation_id = set_correlation_id()
        
        try:
            user = message.from_user
            chat_id = message.chat.id
            
            log_user_request(logger, user.id, chat_id, "message", f"Начало обработки: {message.text[:50]}...")
            
            # Этап 1: Парсинг и нормализация (объединено)
            normalized_result = await self._parse_and_normalize(message)
            if not normalized_result:
                raise MessageProcessingError("Не удалось обработать сообщение")
            
            # Сохраняем запрос в БД
            # await self._save_request(user.id, chat_id, normalized_result)  # Отложено - не нужен для тестирования
            
            # Этап 2: Поиск в базе данных
            search_results = await self._search_database(normalized_result)
            
            # Этап 3: Ранжирование результатов
            ranked_results = await self._rank_results(search_results, normalized_result)
            
            # Этап 4: Генерация Excel
            excel_file = await self._generate_excel(ranked_results, normalized_result)
            
            # Этап 5: Финальная обработка
            final_result = await self._finalize_results(ranked_results, excel_file, normalized_result)
            
            log_user_request(logger, user.id, chat_id, "success", f"Обработка завершена: {len(ranked_results)} результатов")
            
            return final_result
            
        except Exception as e:
            error = handle_service_error(e, "message_processing")
            log_user_request(logger, message.from_user.id, message.chat.id, "error", f"Ошибка обработки сообщения: {e}")
            raise error
    
    async def _parse_and_normalize(self, message: Message) -> Optional[Dict[str, Any]]:
        """Этап 1: Парсинг и нормализация сообщения (объединено)"""
        try:
            # Обрабатываем сообщение через MessageProcessor
            result = await self.message_processor.process_message(message)
            if not result:
                logger.warning("MessageProcessor не вернул результат")
                return None
            
            logger.info(f"Сообщение обработано: тип={result.get('type')}, intent={result.get('user_intent')}")
            
            # Если у нас уже есть user_intent от GPT, используем его
            if result.get('user_intent'):
                logger.info("Используем существующий user_intent от GPT")
                return result
            
            # Иначе используем fallback сервис для нормализации
            try:
                from services.query_fallback_service import QueryFallbackService
                fallback_service = QueryFallbackService()
                
                fallback_result = await fallback_service.process_failed_query(
                    original_query=result['processed_text'],
                    search_results=[]
                )
                
                if fallback_result.get('can_normalize'):
                    result['user_intent'] = fallback_result['normalized_query']
                    logger.info("Fallback сервис успешно нормализовал запрос")
                
            except Exception as e:
                logger.warning(f"Fallback сервис не сработал: {e}")
            
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге и нормализации: {e}")
            raise MessageProcessingError(f"Ошибка парсинга: {e}")
    
    # async def _save_request(self, user_id: int, chat_id: int, parsed_result: Dict[str, Any]) -> None:
    #     """Сохраняет запрос пользователя в БД - ОТЛОЖЕНО"""
    #     try:
    #         await save_user_request(
    #             user_id=user_id,
    #             chat_id=chat_id,
    #             request_type=parsed_result.get('type', 'unknown'),
    #             original_content=parsed_result.get('original_content', ''),
    #             processed_text=parsed_result.get('processed_text', ''),
    #             user_intent=parsed_result.get('user_intent', {})
    #         )
    #         logger.info(f"Запрос пользователя {user_id} сохранен в БД")
    #         
    #     except Exception as e:
    #         logger.warning(f"Не удалось сохранить запрос в БД: {e}")
    #         # Не прерываем выполнение, если не удалось сохранить
    
# Метод _normalize_with_ai удален - объединен с _parse_and_normalize
    
    async def _search_database(self, normalized_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Этап 3: Поиск в базе данных"""
        try:
            query = normalized_result['processed_text']
            user_intent = normalized_result.get('user_intent', {})
            
            # Проверяем множественный заказ
            if user_intent.get('is_multiple_order') and user_intent.get('items'):
                return await self._handle_multiple_order_search(user_intent['items'])
            else:
                # Обычный поиск для одной позиции
                search_results = await search_parts_direct(query, user_intent)
                logger.info(f"Поиск вернул {len(search_results)} результатов")
                return search_results
                
        except Exception as e:
            logger.error(f"Ошибка при поиске в БД: {e}")
            raise MessageProcessingError(f"Ошибка поиска: {e}")
    
    async def _handle_multiple_order_search(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обрабатывает поиск для множественного заказа"""
        all_results = []
        position_results = {}
        processed_queries = {}  # Кэш для избежания дублирования запросов
        
        for i, item in enumerate(items):
            # Создаем уникальный запрос для поиска (включаем длину для различения)
            search_query_parts = []
            if item.get('type'):
                search_query_parts.append(item['type'])
            if item.get('diameter'):
                diameter = item['diameter'].replace(' мм', '')
                search_query_parts.append(diameter)
            if item.get('length'):
                length = item['length'].replace(' мм', '')
                search_query_parts.append(length)
            if item.get('standard'):
                search_query_parts.append(item['standard'])
            
            item_query = ' '.join(search_query_parts).strip()
            if not item_query:
                item_query = item.get('type', '')
            
            # Полный запрос для отображения в Excel
            full_item_query = ' '.join([
                item.get('type', '') or '',
                item.get('standard', '') or '',
                item.get('diameter', '') or '',
                item.get('length', '') or '',
                item.get('material', '') or '',
                item.get('coating', '') or '',
                item.get('grade', '') or ''
            ]).strip()
            
            logger.info(f"Позиция {i+1}: поиск по '{item_query}'")
            
            # Проверяем, не делали ли мы уже такой запрос
            if item_query in processed_queries:
                logger.info(f"Используем кэшированный результат для '{item_query}'")
                item_results = processed_queries[item_query].copy()
            else:
                # Ищем деталь
                item_results = await search_parts_direct(item_query, item)
                # Сохраняем в кэш
                processed_queries[item_query] = item_results.copy() if item_results else []
            
            if item_results:
                # Добавляем информацию о заказе
                for item_result in item_results:
                    item_result.update({
                        'requested_quantity': item.get('quantity', 1),
                        'order_position': i + 1,
                        'search_query': item_query,
                        'full_query': full_item_query,
                        'original_position': i + 1,
                        # Добавляем данные из user_intent для Excel
                        'diameter': item.get('diameter', ''),
                        'length': item.get('length', ''),
                        'material': item.get('material', ''),
                        'coating': item.get('coating', ''),
                        'confidence': item.get('confidence', 0)
                    })
                
                # Берем ТОЛЬКО 1 результат с максимальной вероятностью для каждой позиции
                best_result = max(item_results, key=lambda x: x.get('probability_percent', 0))
                
                # Рассчитываем умную вероятность совпадения
                smart_probability = self._calculate_smart_probability(best_result, item)
                best_result['smart_probability'] = smart_probability
                
                position_results[i + 1] = [best_result]
            else:
                # Создаем fallback результат для позиции без найденных деталей
                fallback_result = {
                    'sku': 'НЕ НАЙДЕНО',
                    'name': 'Деталь не найдена в каталоге',
                    'type': 'Н/Д',
                    'pack_size': 0,
                    'unit': 'шт',
                    'requested_quantity': item.get('quantity', 1),
                    'order_position': i + 1,
                    'search_query': item_query,
                    'full_query': full_item_query,
                    'original_position': i + 1,
                    'confidence_score': 0,
                    'match_reason': 'Результаты не найдены',
                    # Добавляем данные из user_intent для Excel
                    'diameter': item.get('diameter', ''),
                    'length': item.get('length', ''),
                    'material': item.get('material', ''),
                    'coating': item.get('coating', ''),
                    'confidence': item.get('confidence', 0)
                }
                position_results[i + 1] = [fallback_result]
        
        # Собираем результаты в правильном порядке позиций
        for position in sorted(position_results.keys()):
            all_results.extend(position_results[position])
        
        # Логируем статистику по дублированию
        total_items = len(items)
        unique_queries = len(processed_queries)
        duplicates_saved = total_items - unique_queries
        
        logger.info(f"Множественный поиск вернул {len(all_results)} результатов")
        logger.info(f"Статистика запросов: {total_items} позиций, {unique_queries} уникальных запросов, {duplicates_saved} дублей сэкономлено")
        return all_results
    
    async def _rank_results(self, search_results: List[Dict[str, Any]], normalized_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Этап 4: Ранжирование результатов"""
        if not search_results:
            return search_results
        
        try:
            query = normalized_result['processed_text']
            user_intent = normalized_result.get('user_intent', {})
            
            # Ранжирование происходит в Edge Function, возвращаем как есть
            ranked_results = search_results
            
            # Фильтруем результаты по вероятности (исключаем менее 0.6)
            filtered_results = self._filter_results_by_probability(ranked_results)
            
            logger.info(f"Результаты ранжированы: {len(ranked_results)} позиций")
            logger.info(f"Фильтрация по вероятности: {len(ranked_results)} -> {len(filtered_results)} результатов")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Ошибка при ранжировании: {e}")
            # Возвращаем исходные результаты без ранжирования
            return search_results
    
# Методы _prepare_data_container и _validate_relevance удалены - избыточны
    
    async def _generate_excel(self, ranked_results: List[Dict[str, Any]], normalized_result: Dict[str, Any]) -> str:
        """Этап 4: Генерация Excel файла"""
        try:
            excel_file = await self.excel_generator.generate_excel(
                search_results=ranked_results,
                user_request=normalized_result['processed_text']
            )
            
            logger.info(f"Excel файл создан: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"Ошибка при генерации Excel: {e}")
            raise MessageProcessingError(f"Ошибка генерации Excel: {e}")
    
    async def _finalize_results(self, ranked_results: List[Dict[str, Any]], excel_file: str, normalized_result: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 5: Финальная обработка результатов"""
        # Фильтруем результаты по уверенности
        filtered_results = self._filter_results_by_confidence(ranked_results)
        
        # Вопросы для уточнения убраны - они не несут смысла
        # questions = self._generate_clarification_questions(filtered_results)
        
        # Вычисляем сводную статистику
        total_requested = len(normalized_result.get('user_intent', {}).get('items', []))
        total_found = len([r for r in filtered_results if r.get('sku') != 'НЕ НАЙДЕНО'])
        total_not_found = total_requested - total_found
        
        # Логируем для отладки подсчета
        logger.info(f"Отладка подсчета: всего позиций={total_requested}, найдено={total_found}, не найдено={total_not_found}")
        for i, r in enumerate(filtered_results):
            logger.info(f"Позиция {i+1}: sku='{r.get('sku')}', found_sku='{r.get('found_sku', 'НЕТ')}'")
        
        # Вычисляем среднюю вероятность (используем smart_probability)
        probabilities = [r.get('smart_probability', 0) for r in filtered_results if r.get('smart_probability', 0) > 0]
        avg_probability = sum(probabilities) / len(probabilities) if probabilities else 0
        
        # Логируем для отладки
        logger.info(f"Отладка вероятностей: {len(probabilities)} позиций с вероятностями: {probabilities}")
        logger.info(f"Средняя вероятность: {avg_probability}")
        
        final_result = {
            'excel_file': excel_file,
            'results': filtered_results,
            'validation_status': 'APPROVED',  # Упрощено
            'clarification_questions': [],  # Убраны
            'total_results': len(filtered_results),
            'query': normalized_result['processed_text'],
            'is_multiple_order': normalized_result.get('user_intent', {}).get('is_multiple_order', False),
            # Новая сводная информация
            'summary': {
                'total_requested': total_requested,  # Общее количество позиций в запросе
                'total_found': total_found,  # Количество найденных позиций
                'total_not_found': total_not_found,  # Количество не найденных позиций
                'avg_probability': round(avg_probability, 1)  # Средняя вероятность совпадения найденных позиций
            }
        }
        
        logger.info(f"Финальная обработка завершена: {len(filtered_results)} результатов")
        return final_result
    
    def _filter_results_by_confidence(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Фильтрует результаты по уверенности - ОБНОВЛЕНО: возвращаем все результаты"""
        if not results:
            return []
        
        # Теперь у нас уже только 1 результат на позицию, 
        # поэтому просто возвращаем все результаты без дополнительной фильтрации
        return results
    
    def _generate_clarification_questions(self, results: List[Dict[str, Any]]) -> List[str]:
        """Генерирует вопросы для уточнения для результатов с низкой вероятностью"""
        questions = []
        
        for result in results:
            confidence = result.get('confidence_score', 0)
            if confidence < 0.7:  # < 70%
                if confidence < 0.5:
                    questions.append(f"Это точно то, что вы ищете? Можете уточнить параметры для {result.get('name', 'детали')}?")
                else:
                    questions.append(f"Какие характеристики наиболее важны для {result.get('name', 'детали')}?")
        
        return questions[:3]  # Максимум 3 вопроса

    def _calculate_smart_probability(self, item: Dict[str, Any], user_intent: Dict[str, Any]) -> int:
        """Умный расчет вероятности совпадения на основе параметров GPT и результатов Supabase"""
        try:
            score = 0
            max_score = 100
            
            # 1. Совпадение типа детали (25 баллов)
            if item.get('type') and user_intent.get('type'):
                item_type = str(item['type']).lower()
                intent_type = str(user_intent['type']).lower()
                
                # Точное совпадение
                if item_type == intent_type:
                    score += 25
                # Частичное совпадение
                elif intent_type in item_type or item_type in intent_type:
                    score += 20
                # Словарное совпадение
                elif any(word in item_type for word in intent_type.split()):
                    score += 15
            
            # 2. Совпадение диаметра (20 баллов)
            if item.get('diameter') and user_intent.get('diameter'):
                item_diameter = str(item['diameter']).replace(' мм', '').replace('М', '')
                intent_diameter = str(user_intent['diameter']).replace(' мм', '').replace('М', '')
                
                if item_diameter == intent_diameter:
                    score += 20
            
            # 3. Совпадение длины (15 баллов)
            if item.get('length') and user_intent.get('length'):
                item_length = str(item['length']).replace(' мм', '')
                intent_length = str(user_intent['length']).replace(' мм', '')
                
                if item_length == intent_length:
                    score += 15
            
            # 4. Совпадение покрытия (15 баллов)
            if item.get('coating') and user_intent.get('coating'):
                item_coating = str(item['coating']).lower()
                intent_coating = str(user_intent['coating']).lower()
                
                if item_coating == intent_coating:
                    score += 15
                elif intent_coating in item_coating or item_coating in intent_coating:
                    score += 10
            
            # 5. Совпадение материала (10 баллов)
            if item.get('material') and user_intent.get('material'):
                item_material = str(item['material']).lower()
                intent_material = str(user_intent['material']).lower()
                
                if item_material == intent_material:
                    score += 10
                elif intent_material in item_material or item_material in intent_material:
                    score += 8
            
            # 6. Дополнительные баллы за качество названия (15 баллов)
            name = item.get('name', '').lower()
            search_query = user_intent.get('type', '').lower()
            
            # Подсчет совпадающих слов
            query_words = [word for word in search_query.split() if len(word) > 2]
            name_words = name.split()
            
            matching_words = 0
            for q_word in query_words:
                for n_word in name_words:
                    if q_word in n_word or n_word in q_word:
                        matching_words += 1
                        break
            
            if query_words:
                word_match_score = min(15, (matching_words / len(query_words)) * 15)
                score += word_match_score
            
            return min(int(score), max_score)
            
        except Exception as e:
            logger.error(f"Ошибка при расчете вероятности: {e}")
            return 0

    def _filter_results_by_probability(self, search_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Фильтрует результаты по вероятности (исключает менее 0.3)"""
        if not search_results:
            return []
        
        # Фильтруем результаты с вероятностью >= порога из конфигурации
        filtered_results = []
        for result in search_results:
            # Проверяем smart_probability (вероятность от поиска)
            smart_probability = result.get('smart_probability', 0)
            if smart_probability >= MIN_PROBABILITY_THRESHOLD:
                filtered_results.append(result)
                logger.debug(f"Результат включен: {result.get('sku', 'N/A')} - вероятность {smart_probability}%")
            else:
                logger.debug(f"Результат исключен: {result.get('sku', 'N/A')} - вероятность {smart_probability}% < 30%")
        
        logger.info(f"Фильтрация завершена: {len(search_results)} -> {len(filtered_results)} результатов (вероятность >= {MIN_PROBABILITY_THRESHOLD}%)")
        return filtered_results

async def search_parts_direct(query: str, user_intent: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Прямой вызов Edge Function для поиска деталей"""
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')

        if not supabase_url or not supabase_key:
            logger.error("Не настроены переменные окружения SUPABASE_URL или SUPABASE_KEY")
            return []

        edge_function_url = f"{supabase_url}/functions/v1/fastener-search"

        headers = {
            "Authorization": f"Bearer {supabase_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "search_query": query,
            "user_intent": user_intent
        }

        logger.info(f"Вызываем Edge Function: {edge_function_url}")
        logger.info(f"Payload: {payload}")

        timeout = aiohttp.ClientTimeout(total=30)
        max_retries = 3

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Попытка {attempt}/{max_retries} вызова Edge Function")
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(edge_function_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            results = result.get('results', [])
                            logger.info(f"Edge Function вернул {len(results)} результатов на попытке {attempt}")
                            return results
                        else:
                            error_text = await response.text()
                            logger.warning(f"Попытка {attempt} завершилась ошибкой {response.status}: {error_text}")
            except Exception as e:
                logger.error(f"Попытка {attempt} вызова Edge Function завершилась исключением: {e}")

            if attempt < max_retries:
                delay = 2 ** (attempt - 1)
                logger.info(f"Повтор через {delay} с")
                await asyncio.sleep(delay)

        logger.error("Все попытки вызова Edge Function завершились неудачей")
        return []

    except Exception as e:
        logger.error(f"Ошибка при подготовке вызова Edge Function: {e}")
        return []



