"""
Модульный процессор сообщений для Telegram бота
Реализует BPMN pipeline: validation → normalize → search → rank → export
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from telegram import Bot, Message
from telegram.ext import ContextTypes

from shared.logging import get_logger, set_correlation_id, log_user_request
from shared.errors import MessageProcessingError, handle_service_error
from core.services.ranking import RankingService
from services.message_processor import MessageProcessor
from services.excel_generator import ExcelGenerator
from database.supabase_client import save_user_request, search_parts

logger = get_logger(__name__)


class MessagePipeline:
    """Pipeline для обработки сообщений согласно BPMN"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.ranking_service = RankingService()
        self.message_processor = MessageProcessor(bot=bot)
        self.excel_generator = ExcelGenerator()
    
    async def process_message(self, message: Message, context: ContextTypes.DEFAULT_TYPE) -> Dict[str, Any]:
        """Основной метод обработки сообщения"""
        # Устанавливаем correlation ID для логирования
        correlation_id = set_correlation_id()
        
        try:
            user = message.from_user
            chat_id = message.chat.id
            
            log_user_request(logger, user.id, chat_id, "message", f"Начало обработки: {message.text[:50]}...")
            
            # Этап 1: Валидация и парсинг
            parsed_result = await self._validate_and_parse(message)
            if not parsed_result:
                raise MessageProcessingError("Не удалось обработать сообщение")
            
            # Сохраняем запрос в БД
            await self._save_request(user.id, chat_id, parsed_result)
            
            # Этап 2: Нормализация через ИИ агента
            normalized_result = await self._normalize_with_ai(parsed_result)
            
            # Этап 3: Поиск в базе данных
            search_results = await self._search_database(normalized_result)
            
            # Этап 4: Ранжирование результатов
            ranked_results = await self._rank_results(search_results, normalized_result)
            
            # Этап 5: Подготовка контейнера данных
            data_container = await self._prepare_data_container(ranked_results, normalized_result)
            
            # Этап 6: Валидация релевантности
            validation_result = await self._validate_relevance(data_container)
            
            # Этап 7: Сборка Excel
            excel_file = await self._generate_excel(data_container)
            
            # Этап 8: Разделение по вероятности и генерация вопросов
            final_result = await self._finalize_results(data_container, excel_file, validation_result)
            
            log_user_request(logger, user.id, chat_id, "success", f"Обработка завершена: {len(ranked_results)} результатов")
            
            return final_result
            
        except Exception as e:
            error = handle_service_error(e, "message_processing")
            log_user_request(logger, message.from_user.id, message.chat.id, "error", f"Ошибка обработки сообщения: {e}")
            raise error
    
    async def _validate_and_parse(self, message: Message) -> Optional[Dict[str, Any]]:
        """Этап 1: Валидация и парсинг сообщения"""
        try:
            result = await self.message_processor.process_message(message)
            if not result:
                logger.warning("MessageProcessor не вернул результат")
                return None
            
            logger.info(f"Сообщение обработано: тип={result.get('type')}, intent={result.get('user_intent')}")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка при валидации и парсинге: {e}")
            raise MessageProcessingError(f"Ошибка парсинга: {e}")
    
    async def _save_request(self, user_id: int, chat_id: int, parsed_result: Dict[str, Any]) -> None:
        """Сохраняет запрос пользователя в БД"""
        try:
            await save_user_request(
                user_id=user_id,
                chat_id=chat_id,
                request_type=parsed_result.get('type', 'unknown'),
                original_content=parsed_result.get('original_content', ''),
                processed_text=parsed_result.get('processed_text', ''),
                user_intent=parsed_result.get('user_intent', {})
            )
            logger.info(f"Запрос пользователя {user_id} сохранен в БД")
            
        except Exception as e:
            logger.warning(f"Не удалось сохранить запрос в БД: {e}")
            # Не прерываем выполнение, если не удалось сохранить
    
    async def _normalize_with_ai(self, parsed_result: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 2: Нормализация через ИИ агента"""
        # Если у нас уже есть user_intent от GPT, используем его
        if parsed_result.get('user_intent'):
            logger.info("Используем существующий user_intent от GPT")
            return parsed_result
        
        # Иначе используем fallback сервис
        try:
            from services.query_fallback_service import QueryFallbackService
            fallback_service = QueryFallbackService()
            
            fallback_result = await fallback_service.process_failed_query(
                original_query=parsed_result['processed_text'],
                search_results=[]
            )
            
            if fallback_result.get('can_normalize'):
                normalized_query = fallback_result['normalized_query']
                logger.info(f"Fallback сервис нормализовал запрос: {normalized_query}")
                
                # Обновляем результат
                parsed_result['processed_text'] = normalized_query
                parsed_result['is_normalized'] = True
                parsed_result['normalized_query'] = normalized_query
            
            return parsed_result
            
        except Exception as e:
            logger.warning(f"Fallback сервис недоступен: {e}")
            return parsed_result
    
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
                search_results = await search_parts(query, user_intent)
                logger.info(f"Поиск вернул {len(search_results)} результатов")
                return search_results
                
        except Exception as e:
            logger.error(f"Ошибка при поиске в БД: {e}")
            raise MessageProcessingError(f"Ошибка поиска: {e}")
    
    async def _handle_multiple_order_search(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обрабатывает поиск для множественного заказа"""
        all_results = []
        position_results = {}
        
        for i, item in enumerate(items):
            # Создаем упрощенный запрос для поиска
            search_query_parts = []
            if item.get('type'):
                search_query_parts.append(item['type'])
            if item.get('diameter'):
                diameter = item['diameter'].replace(' мм', '')
                search_query_parts.append(diameter)
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
            
            # Ищем деталь
            item_results = await search_parts(item_query, item)
            
            if item_results:
                # Добавляем информацию о заказе
                for item_result in item_results:
                    item_result.update({
                        'requested_quantity': item.get('quantity', 1),
                        'order_position': i + 1,
                        'search_query': item_query,
                        'full_query': full_item_query,
                        'original_position': i + 1
                    })
                position_results[i + 1] = item_results
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
                    'match_reason': 'Результаты не найдены'
                }
                position_results[i + 1] = [fallback_result]
        
        # Собираем результаты в правильном порядке позиций
        for position in sorted(position_results.keys()):
            all_results.extend(position_results[position])
        
        logger.info(f"Множественный поиск вернул {len(all_results)} результатов")
        return all_results
    
    async def _rank_results(self, search_results: List[Dict[str, Any]], normalized_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Этап 4: Ранжирование результатов"""
        if not search_results:
            return search_results
        
        try:
            query = normalized_result['processed_text']
            user_intent = normalized_result.get('user_intent', {})
            
            # Используем единый сервис ранжирования
            ranked_results = self.ranking_service.rank_results(search_results, query, user_intent)
            
            logger.info(f"Результаты ранжированы: {len(ranked_results)} позиций")
            return ranked_results
            
        except Exception as e:
            logger.error(f"Ошибка при ранжировании: {e}")
            # Возвращаем исходные результаты без ранжирования
            return search_results
    
    async def _prepare_data_container(self, ranked_results: List[Dict[str, Any]], normalized_result: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 5: Подготовка контейнера данных"""
        return {
            'results': ranked_results,
            'query': normalized_result['processed_text'],
            'user_intent': normalized_result.get('user_intent', {}),
            'is_multiple_order': normalized_result.get('user_intent', {}).get('is_multiple_order', False),
            'metadata': {
                'total_results': len(ranked_results),
                'processing_timestamp': normalized_result.get('timestamp'),
                'is_normalized': normalized_result.get('is_normalized', False)
            }
        }
    
    async def _validate_relevance(self, data_container: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 6: Валидация релевантности"""
        # Временно отключаем циклическую валидацию
        validation_result = {
            "status": "APPROVED",
            "message": "Валидация отключена",
            "confidence": 0.9
        }
        
        # Добавляем статус к результатам
        for result in data_container['results']:
            result['validation_status'] = 'APPROVED'
        
        logger.info("Валидация релевантности завершена")
        return validation_result
    
    async def _generate_excel(self, data_container: Dict[str, Any]) -> str:
        """Этап 7: Генерация Excel файла"""
        try:
            excel_file = await self.excel_generator.generate_excel(
                search_results=data_container['results'],
                user_request=data_container['query']
            )
            
            logger.info(f"Excel файл создан: {excel_file}")
            return excel_file
            
        except Exception as e:
            logger.error(f"Ошибка при генерации Excel: {e}")
            raise MessageProcessingError(f"Ошибка генерации Excel: {e}")
    
    async def _finalize_results(self, data_container: Dict[str, Any], excel_file: str, validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """Этап 8: Финальная обработка результатов"""
        validation_status = validation_result.get('status', 'UNKNOWN')
        
        # Фильтруем результаты по уверенности
        filtered_results = self._filter_results_by_confidence(data_container['results'])
        
        # Генерируем вопросы для низкой вероятности
        questions = self._generate_clarification_questions(filtered_results)
        
        final_result = {
            'excel_file': excel_file,
            'results': filtered_results,
            'validation_status': validation_status,
            'clarification_questions': questions,
            'total_results': len(filtered_results),
            'query': data_container['query'],
            'is_multiple_order': data_container['is_multiple_order']
        }
        
        logger.info(f"Финальная обработка завершена: {len(filtered_results)} результатов, статус: {validation_status}")
        return final_result
    
    def _filter_results_by_confidence(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Фильтрует результаты по уверенности"""
        if not results:
            return []
        
        # Сортируем по уверенности (убывание)
        sorted_results = sorted(results, key=lambda x: x.get('confidence_score', 0), reverse=True)
        
        # Проверяем максимальную уверенность
        max_confidence = sorted_results[0].get('confidence_score', 0)
        
        if max_confidence >= 100:
            # Есть 100% - показываем только их (максимум 3)
            filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 100]
            return filtered[:3]
        
        elif max_confidence >= 90:
            # Есть 90%+ - показываем только их (максимум 5)
            filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 90]
            return filtered[:5]
        
        elif max_confidence >= 70:
            # Есть 70%+ - показываем только их (максимум 10)
            filtered = [r for r in sorted_results if r.get('confidence_score', 0) >= 70]
            return filtered[:10]
        
        else:
            # Все ниже 70% - показываем топ-5
            return sorted_results[:5]
    
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
