"""
Система очереди для обработки множественных файлов
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from telegram import Message
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

@dataclass
class FileQueueItem:
    """Элемент очереди файлов"""
    user_id: int
    chat_id: int
    messages: List[Message]
    created_at: datetime
    last_updated: datetime
    status: str = 'pending'  # pending, processing, completed, failed
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class FileQueue:
    """Очередь для обработки множественных файлов"""
    
    def __init__(self):
        self.queue: Dict[int, FileQueueItem] = {}  # user_id -> FileQueueItem
        self.processing_timeout = timedelta(minutes=5)  # Таймаут обработки
        self.cleanup_interval = timedelta(minutes=10)  # Интервал очистки
        self.file_grouping_timeout = timedelta(seconds=10)  # Время ожидания дополнительных файлов
        self._cleanup_task = None
    
    async def add_files(self, user_id: int, chat_id: int, messages: List[Message]) -> str:
        """Добавляет файлы в очередь"""
        try:
            current_time = datetime.now()
            
            # Проверяем, есть ли уже очередь для этого пользователя
            if user_id in self.queue:
                existing_item = self.queue[user_id]
                
                # Если очередь в процессе обработки, не добавляем файлы
                if existing_item.status == 'processing':
                    return "Ваши файлы уже обрабатываются. Дождитесь завершения."
                
                # Если очередь завершена или провалена, создаем новую
                if existing_item.status in ['completed', 'failed']:
                    del self.queue[user_id]
                else:
                    # Проверяем, не прошло ли слишком много времени с последнего обновления
                    if current_time - existing_item.last_updated <= self.file_grouping_timeout:
                        # Добавляем к существующей очереди
                        existing_item.messages.extend(messages)
                        existing_item.last_updated = current_time
                        logger.info(f"Добавлено {len(messages)} файлов к существующей очереди пользователя {user_id}. Всего: {len(existing_item.messages)}")
                        return f"Добавлено {len(messages)} файлов к очереди. Всего в очереди: {len(existing_item.messages)} файлов"
                    else:
                        # Слишком много времени прошло, создаем новую очередь
                        del self.queue[user_id]
            
            # Создаем новую очередь
            queue_item = FileQueueItem(
                user_id=user_id,
                chat_id=chat_id,
                messages=messages,
                created_at=current_time,
                last_updated=current_time
            )
            
            self.queue[user_id] = queue_item
            logger.info(f"Создана новая очередь для пользователя {user_id} с {len(messages)} файлами")
            
            return f"Создана очередь из {len(messages)} файлов. Обработка начнется автоматически."
            
        except Exception as e:
            logger.error(f"Ошибка при добавлении файлов в очередь: {e}")
            return f"Ошибка при создании очереди: {str(e)}"
    
    async def _auto_process_queue(self, user_id: int, context: ContextTypes.DEFAULT_TYPE):
        """Автоматически обрабатывает очередь с задержкой"""
        try:
            # Ждем время группировки файлов
            await asyncio.sleep(self.file_grouping_timeout.total_seconds())
            
            # Проверяем, что очередь все еще существует и не обрабатывается
            if user_id in self.queue:
                queue_item = self.queue[user_id]
                if queue_item.status == 'pending':
                    logger.info(f"Автоматически запускаем обработку очереди для пользователя {user_id}")
                    await self.process_queue(user_id, context)
                    
        except Exception as e:
            logger.error(f"Ошибка при автоматической обработке очереди: {e}")
    
    async def _send_result_to_user(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, result: Dict[str, Any]):
        """Отправляет результат обработки пользователю"""
        try:
            if not result:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Не удалось обработать файлы."
                )
                return
            
            total_files = result.get('total_files', 0)
            processed_files = result.get('processed_files', 0)
            failed_files = result.get('failed_files', 0)
            
            # Отправляем одно сообщение о получении файлов
            await context.bot.send_message(
                chat_id=user_id,
                text=f"✅ Получено {total_files} файлов, начинаю обработку..."
            )
            
        except Exception as e:
            logger.error(f"Ошибка при отправке результата пользователю: {e}")
    
    async def _send_excel_result(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, file_result: dict, file_number: int):
        """Отправляет результат Excel файла пользователю"""
        try:
            file_name = file_result.get('file_name', f'Файл {file_number}')
            parsed_content = file_result.get('parsed_content')
            
            if not parsed_content:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📊 Файл {file_number}: {file_name} - Excel файл получен, но не удалось распарсить"
                )
                return
            
            # Создаем сводную информацию по Excel файлу
            sheets_info = []
            for sheet_name, sheet_data in parsed_content.get('sheets', {}).items():
                rows, cols = sheet_data.get('shape', (0, 0))
                sheets_info.append(f"• **{sheet_name}:** {rows} строк, {cols} столбцов")
            
            excel_summary = f"""📊 **Файл {file_number}:** {file_name}

📋 **Листы в файле:**
{chr(10).join(sheets_info)}

📈 **Всего листов:** {parsed_content.get('total_sheets', 0)}"""
            
            await context.bot.send_message(
                chat_id=user_id,
                text=excel_summary
            )
            
        except Exception as e:
            logger.error(f"Ошибка при отправке Excel результата: {e}")
    
    async def _process_files_with_search(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, result: Dict[str, Any]):
        """Интегрирует файлы с поиском крепежных изделий"""
        try:
            # Ищем файлы для обработки (Excel и PDF)
            processable_files = []
            for file_result in result.get('results', []):
                if (file_result.get('type') == 'document' and 
                    file_result.get('file_extension') in ['.xlsx', '.xls', '.pdf']):
                    processable_files.append(file_result)
            
            if not processable_files:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="❌ Не найдено файлов для обработки (поддерживаются Excel и PDF)"
                )
                return
            
            # Объединяем все данные из всех файлов
            await self._process_all_files_together(user_id, context, processable_files)
                
        except Exception as e:
            logger.error(f"Ошибка при интеграции файлов с поиском: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка при обработке файлов: {str(e)}"
            )
    
    async def _process_all_files_together(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, files: list):
        """Обрабатывает все файлы вместе и отправляет в GPT"""
        try:
            # Объединяем данные из всех файлов
            all_data = []
            file_names = []
            
            for file in files:
                file_name = file.get('file_name', 'Файл')
                file_extension = file.get('file_extension', '')
                file_names.append(file_name)
                
                if file_extension in ['.xlsx', '.xls']:
                    # Обрабатываем Excel файлы
                    parsed_content = file.get('parsed_content', {})
                    if parsed_content:
                        # Извлекаем данные из всех листов
                        for sheet_name, sheet_data in parsed_content.get('sheets', {}).items():
                            data = sheet_data.get('data', [])
                            for row in data:
                                # Ищем строки, которые могут содержать крепежные изделия
                                row_text = ' '.join([str(v) for v in row.values() if v])
                                if any(keyword in row_text.lower() for keyword in ['болт', 'винт', 'саморез', 'анкер', 'гайка', 'шайба', 'шпилька', 'хомут', 'зажим', 'креп', 'метиз', 'издел']):
                                    all_data.append({
                                        'file': file_name,
                                        'sheet': sheet_name,
                                        'data': row,
                                        'text': row_text
                                    })
                
                elif file_extension == '.pdf':
                    # Для PDF файлов пока отправляем весь файл на анализ
                    all_data.append({
                        'file': file_name,
                        'sheet': 'PDF',
                        'data': {},
                        'text': f"PDF файл {file_name} - требуется анализ содержимого"
                    })
            
            if not all_data:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"📊 В файлах {', '.join(file_names)} не найдено данных для анализа"
                )
                return
            
            # Отправляем все данные в GPT для анализа
            await self._send_all_data_to_gpt(user_id, context, file_names, all_data)
            
        except Exception as e:
            logger.error(f"Ошибка при обработке всех файлов: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка при обработке файлов: {str(e)}"
            )
    
    async def _send_all_data_to_gpt(self, user_id: int, context: ContextTypes.DEFAULT_TYPE, file_names: list, all_data: list):
        """Отправляет все данные в GPT для анализа и поиска"""
        try:
            # Создаем текст для анализа
            analysis_text = f"Проанализируй следующие данные из файлов {', '.join(file_names)} и найди крепежные изделия (болты, винты, саморезы, анкеры, гайки, шайбы, шпильки, хомуты, зажимы и другие метизы):\n\n"
            
            for i, item in enumerate(all_data[:20], 1):  # Берем первые 20 строк
                analysis_text += f"{i}. Файл '{item['file']}', Лист '{item['sheet']}': {item['text']}\n"
            
            if len(all_data) > 20:
                analysis_text += f"\n... и еще {len(all_data) - 20} строк из всех файлов\n"
            
            analysis_text += f"\nВажно: Обрати внимание на все типы крепежных изделий, включая хомуты, зажимы и другие метизы. Извлеки точные параметры каждого изделия."
            
            # Логируем что отправляем в GPT
            logger.info(f"Отправляем в GPT для анализа: {len(all_data)} строк из файлов {file_names}")
            logger.info(f"Текст для анализа: {analysis_text[:200]}...")
            
            # Отправляем в GPT через MessagePipeline
            from pipeline.message_processor import MessagePipeline
            
            # Создаем фиктивное сообщение для pipeline
            class FakeMessage:
                def __init__(self, text, user_id):
                    self.text = text
                    self.voice = None
                    self.photo = None
                    self.document = None
                    self.from_user = type('User', (), {'id': user_id})()
                    self.chat = type('Chat', (), {'id': user_id})()
            
            fake_message = FakeMessage(analysis_text, user_id)
            
            # Создаем pipeline и обрабатываем
            pipeline = MessagePipeline(bot=context.bot)
            result = await pipeline.process_message(fake_message, context)
            
            if result and result.get('excel_file'):
                # Отправляем результат пользователю
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🔍 Найдены крепежные изделия в файлах {', '.join(file_names)}! Обрабатываю через GPT..."
                )
                
                # Отправляем Excel файл с результатами
                with open(result['excel_file'], 'rb') as f:
                    await context.bot.send_document(
                        chat_id=user_id,
                        document=f,
                        filename=f"результаты_поиска_все_файлы_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                        caption=f"📊 Результаты поиска крепежных изделий из всех файлов"
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ Не удалось найти крепежные изделия в файлах {', '.join(file_names)}"
                )
                
        except Exception as e:
            logger.error(f"Ошибка при отправке в GPT: {e}")
            await context.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ошибка при анализе файлов: {str(e)}"
            )
    
    async def process_queue(self, user_id: int, context: ContextTypes.DEFAULT_TYPE) -> Optional[Dict[str, Any]]:
        """Обрабатывает очередь файлов для пользователя"""
        try:
            if user_id not in self.queue:
                logger.warning(f"Очередь для пользователя {user_id} не найдена")
                return None
            
            queue_item = self.queue[user_id]
            
            if queue_item.status != 'pending':
                logger.warning(f"Очередь для пользователя {user_id} уже обрабатывается или завершена")
                return None
            
            # Помечаем как обрабатываемую
            queue_item.status = 'processing'
            
            try:
                # Импортируем FileProcessor
                from services.file_processor import FileProcessor
                file_processor = FileProcessor()
                
                # Обрабатываем файлы
                results = await file_processor.process_multiple_files(queue_item.messages, context)
                
                # Создаем итоговый результат
                queue_item.result = {
                    'type': 'multiple_files',
                    'total_files': len(queue_item.messages),
                    'processed_files': len([r for r in results if r.get('type') != 'error']),
                    'failed_files': len([r for r in results if r.get('type') == 'error']),
                    'results': results,
                    'processed_at': datetime.now().isoformat()
                }
                
                queue_item.status = 'completed'
                logger.info(f"Очередь для пользователя {user_id} успешно обработана")
                
                # Отправляем результат пользователю
                await self._send_result_to_user(user_id, context, queue_item.result)
                
                # Интегрируем с поиском крепежных изделий
                await self._process_files_with_search(user_id, context, queue_item.result)
                
                return queue_item.result
                
            except Exception as e:
                queue_item.status = 'failed'
                queue_item.error = str(e)
                logger.error(f"Ошибка при обработке очереди для пользователя {user_id}: {e}")
                return None
                
            finally:
                # Очищаем временные файлы
                try:
                    file_processor.cleanup_temp_files()
                except:
                    pass
                
        except Exception as e:
            logger.error(f"Критическая ошибка при обработке очереди: {e}")
            return None
    
    async def get_queue_status(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получает статус очереди для пользователя"""
        try:
            if user_id not in self.queue:
                return None
            
            queue_item = self.queue[user_id]
            
            return {
                'user_id': user_id,
                'status': queue_item.status,
                'total_files': len(queue_item.messages),
                'created_at': queue_item.created_at.isoformat(),
                'error': queue_item.error
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении статуса очереди: {e}")
            return None
    
    async def clear_queue(self, user_id: int) -> bool:
        """Очищает очередь для пользователя"""
        try:
            if user_id in self.queue:
                del self.queue[user_id]
                logger.info(f"Очередь для пользователя {user_id} очищена")
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при очистке очереди: {e}")
            return False
    
    async def cleanup_expired_queues(self):
        """Очищает просроченные очереди"""
        try:
            current_time = datetime.now()
            expired_users = []
            
            for user_id, queue_item in self.queue.items():
                if current_time - queue_item.created_at > self.processing_timeout:
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del self.queue[user_id]
                logger.info(f"Очищена просроченная очередь для пользователя {user_id}")
            
            if expired_users:
                logger.info(f"Очищено {len(expired_users)} просроченных очередей")
                
        except Exception as e:
            logger.error(f"Ошибка при очистке просроченных очередей: {e}")
    
    async def start_cleanup_task(self):
        """Запускает задачу очистки"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def _cleanup_loop(self):
        """Цикл очистки"""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self.cleanup_expired_queues()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Ошибка в цикле очистки: {e}")
    
    def stop_cleanup_task(self):
        """Останавливает задачу очистки"""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()

# Глобальный экземпляр очереди
file_queue = FileQueue()
