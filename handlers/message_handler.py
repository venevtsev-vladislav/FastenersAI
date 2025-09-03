"""
Обновленный обработчик сообщений для Telegram бота
Использует новый модульный pipeline
"""

import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from pipeline.message_processor import MessagePipeline
from services.media_processor import MediaProcessor
from services.file_processor import FileProcessor
from services.file_queue import file_queue
from shared.logging import get_logger, set_correlation_id
from shared.errors import MessageProcessingError, handle_service_error

logger = get_logger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех типов сообщений"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        # Устанавливаем correlation ID для логирования
        correlation_id = set_correlation_id()
        
        logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
        
        # Проверяем тип сообщения
        message = update.message
        
        # Обрабатываем голосовые сообщения как текстовые (после распознавания речи)
        if message.voice:
            await _handle_voice_as_text(update, context)
            return
        
        # Обрабатываем другие медиа файлы
        if message.photo or message.document:
            await _handle_multiple_files(update, context)
            return
        
        # Обрабатываем как текстовое сообщение
        await _handle_text_message(update, context)
            
    except Exception as e:
        logger.error(f"Критическая ошибка в обработчике сообщений: {e}")
        try:
            await update.message.reply_text("❌ Произошла критическая ошибка. Обратитесь к администратору.")
        except:
            pass


def _filter_results_by_confidence(results):
    """
    Фильтрует результаты по уверенности:
    - Если есть 100% → показываем только их (максимум 3)
    - Если нет 100%, но есть 90%+ → показываем только их (максимум 5)
    - Если нет 90%, но есть 70%+ → показываем только их (максимум 10)
    - Если все ниже 70% → показываем топ-5
    """
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


async def _handle_voice_as_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает голосовое сообщение как текстовое (после распознавания речи)"""
    try:
        message = update.message
        user = update.effective_user
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply_text("🎤 Распознаю речь...")
        
        # Создаем процессор медиа
        media_processor = MediaProcessor()
        
        try:
            # Обрабатываем голосовое сообщение
            media_result = await media_processor.process_media_message(message, context)
            
            if not media_result or media_result.get('error'):
                await processing_msg.edit_text("❌ Не удалось обработать голосовое сообщение.")
                return
            
            # TODO: Здесь будет Speech-to-Text
            # Пока используем заглушку
            transcribed_text = "Анкер забиваемый М6"  # Заглушка для тестирования
            
            await processing_msg.edit_text(f"🎤 Распознано: '{transcribed_text}'\n\n🔄 Обрабатываю как текстовый запрос...")
            
            # Создаем фиктивное текстовое сообщение
            message.text = transcribed_text
            
            # Обрабатываем как обычный текстовый запрос
            await _handle_text_message(update, context, processing_msg)
            
        finally:
            # Очищаем временные файлы
            media_processor.cleanup_temp_files()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")
        except:
            pass


async def _handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE, processing_msg=None):
    """Обрабатывает текстовое сообщение"""
    try:
        if not processing_msg:
            processing_msg = await update.message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        # Этап 1: Анализ запроса
        await processing_msg.edit_text("🧠 Анализирую ваш запрос через ИИ...")
        
        # Логируем начало обработки ИИ
        logger.info(f"🤖 Начинаем ИИ анализ для пользователя {update.effective_user.id}: '{update.message.text[:100]}...'")
        
        # Используем новый модульный pipeline
        pipeline = MessagePipeline(bot=update.get_bot())
        result = await pipeline.process_message(update.message, context)
        
        # Логируем результат ИИ анализа
        if result:
            logger.info(f"✅ ИИ анализ успешен для пользователя {update.effective_user.id}: найдено {result.get('total_results', 0)} результатов")
        else:
            logger.error(f"❌ ИИ анализ не удался для пользователя {update.effective_user.id}")
        
        if not result:
            await processing_msg.edit_text("❌ Не удалось обработать сообщение. Попробуйте еще раз.")
            return
        
        # Этап 2: Поиск в базе данных
        await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
        
        # Небольшая задержка для показа этапа
        import asyncio
        await asyncio.sleep(0.5)
        
        # Этап 3: Создание Excel
        await processing_msg.edit_text("📊 Создаю Excel файл с результатами...")
        
        # Создаем подпись для файла
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        # Определяем тип запроса
        if result.get('is_multiple_order'):
            request_type = "📋 Множественный заказ"
            request_summary = f"{len(result.get('results', []))} позиций"
        else:
            request_type = "💬 Текстовый запрос"
            request_summary = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
        
        # Создаем сводную информацию
        summary = result.get('summary', {})
        user = update.effective_user
        
        # Формируем информативное сообщение
        summary_text = f"""📋 **Сводная информация по запросу**

📊 **В запросе:** {summary.get('total_requested', 0)} позиций
✅ **Найдено:** {summary.get('total_found', 0)} позиций
❌ **Не найдено:** {summary.get('total_not_found', 0)} позиций
📈 **Средняя вероятность совпадения:** {summary.get('avg_probability', 0)}%

📅 **Время обработки:** {current_time}"""
        
        # Отправляем файл
        with open(result['excel_file'], 'rb') as f:
            await update.message.reply_document(
                document=f,
                filename=f"результаты_поиска_{user.id}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                caption=summary_text,
                parse_mode='Markdown'
            )
        
        # Отправляем кнопки для оценки работы бота
        keyboard = [
            [
                InlineKeyboardButton("✅ Да, справился", callback_data=f"rating_good_{user.id}"),
                InlineKeyboardButton("❌ Нет, не справился", callback_data=f"rating_bad_{user.id}")
            ],
            [
                InlineKeyboardButton("⚠️ Не совсем", callback_data=f"rating_partial_{user.id}"),
                InlineKeyboardButton("❓ Не знаю", callback_data=f"rating_unknown_{user.id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "🤖 **Оцените работу бота:**\n\nСправился ли бот с вашим запросом?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
        await processing_msg.delete()
        logger.info(f"Успешно обработан запрос пользователя {update.effective_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")
        if processing_msg:
            await processing_msg.edit_text("❌ Произошла ошибка при обработке. Попробуйте еще раз или обратитесь к администратору.")


async def _handle_media_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает медиа сообщения (фото, голос, документы)"""
    try:
        message = update.message
        user = update.effective_user
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply_text("🔄 Обрабатываю медиа файл...")
        
        # Определяем тип медиа и обновляем статус
        if message.photo:
            await processing_msg.edit_text("📸 Скачиваю и анализирую фотографию...")
        elif message.voice:
            await processing_msg.edit_text("🎤 Скачиваю и анализирую голосовое сообщение...")
        elif message.document:
            await processing_msg.edit_text("📄 Скачиваю и анализирую документ...")
        
        # Создаем процессор медиа
        media_processor = MediaProcessor()
        
        try:
            # Обрабатываем медиа файл
            media_result = await media_processor.process_media_message(message, context)
            
            if not media_result:
                await processing_msg.edit_text("❌ Не удалось обработать медиа файл.")
                return
            
            # Проверяем на ошибки
            if media_result.get('error'):
                await processing_msg.edit_text(f"❌ {media_result['error']}")
                return
            
            # Обрабатываем в зависимости от типа
            if media_result['type'] == 'photo':
                await _handle_photo_result(update, context, media_result, processing_msg)
            elif media_result['type'] == 'voice':
                await _handle_voice_result(update, context, media_result, processing_msg)
            elif media_result['type'] == 'document':
                await _handle_document_result(update, context, media_result, processing_msg)
            
        finally:
            # Очищаем временные файлы
            media_processor.cleanup_temp_files()
            
    except Exception as e:
        logger.error(f"Ошибка при обработке медиа сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке медиа файла.")
        except:
            pass


async def _handle_photo_result(update: Update, context: ContextTypes.DEFAULT_TYPE, media_result: dict, processing_msg):
    """Обрабатывает результат обработки фото"""
    try:
        await processing_msg.edit_text("📸 Фото получено! В будущем здесь будет OCR для извлечения текста.")
        
        # TODO: Добавить OCR для извлечения текста из изображения
        # Пока просто подтверждаем получение
        
    except Exception as e:
        logger.error(f"Ошибка при обработке результата фото: {e}")

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки оценки работы бота"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем тип оценки и ID пользователя
    callback_data = query.data
    if callback_data.startswith("rating_"):
        rating_type = callback_data.split("_")[1]  # good, bad, partial, unknown
        user_id = callback_data.split("_")[2]
        
        # Логируем оценку
        logger.info(f"Пользователь {user_id} оценил работу бота: {rating_type}")
        
        # Отвечаем пользователю
        rating_messages = {
            "good": "✅ Спасибо за положительную оценку!",
            "bad": "❌ Спасибо за обратную связь. Мы работаем над улучшением.",
            "partial": "⚠️ Понятно, есть над чем поработать.",
            "unknown": "❓ Спасибо за использование бота!"
        }
        
        await query.edit_message_text(
            rating_messages.get(rating_type, "Спасибо за оценку!"),
            reply_markup=None
        )

async def _handle_voice_result(update: Update, context: ContextTypes.DEFAULT_TYPE, media_result: dict, processing_msg):
    """Обрабатывает результат обработки голосового сообщения"""
    try:
        await processing_msg.edit_text("🎤 Голосовое сообщение получено! В будущем здесь будет распознавание речи.")
        
        # TODO: Добавить Speech-to-Text для распознавания речи
        # Пока просто подтверждаем получение
        
    except Exception as e:
        logger.error(f"Ошибка при обработке результата голосового сообщения: {e}")


async def _handle_document_result(update: Update, context: ContextTypes.DEFAULT_TYPE, media_result: dict, processing_msg):
    """Обрабатывает результат обработки документа"""
    try:
        file_name = media_result.get('file_name', 'документ')
        file_size = media_result.get('file_size', 0)
        file_extension = media_result.get('file_extension', '')
        
        await processing_msg.edit_text(f"📄 Документ '{file_name}' получен! В будущем здесь будет парсинг содержимого.")
        
        # TODO: Добавить парсинг Excel/PDF файлов
        # Пока просто подтверждаем получение
        
    except Exception as e:
        logger.error(f"Ошибка при обработке результата документа: {e}")

async def _handle_multiple_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает множественные файлы через очередь"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        message = update.message
        
        # Получаем все файлы из сообщения
        files = []
        if message.photo:
            files.append(message)
        if message.document:
            files.append(message)
        
        if not files:
            await message.reply_text("❌ Не найдено файлов для обработки.")
            return
        
        # Добавляем файлы в очередь
        status_msg = await message.reply_text("🔄 Добавляю файлы в очередь обработки...")
        
        queue_status = await file_queue.add_files(user.id, chat_id, files)
        await status_msg.edit_text(f"✅ {queue_status}")
        
        # Запускаем автоматическую обработку с задержкой
        asyncio.create_task(_auto_process_files(user.id, context))
            
    except Exception as e:
        logger.error(f"Ошибка в _handle_multiple_files: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке файлов.")
        except:
            pass

async def _handle_multiple_files_result(update: Update, context: ContextTypes.DEFAULT_TYPE, result: dict, processing_msg):
    """Обрабатывает результат множественных файлов"""
    try:
        total_files = result.get('total_files', 0)
        processed_files = result.get('processed_files', 0)
        failed_files = result.get('failed_files', 0)
        
        # Создаем сводную информацию
        summary_text = f"""📋 **Результат обработки файлов**

📊 **Всего файлов:** {total_files}
✅ **Успешно обработано:** {processed_files}
❌ **Ошибок:** {failed_files}

📅 **Время обработки:** {datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        await processing_msg.edit_text(summary_text)
        
        # Обрабатываем каждый файл отдельно
        for i, file_result in enumerate(result.get('results', []), 1):
            if file_result.get('type') == 'error':
                await update.message.reply_text(f"❌ **Файл {i}:** {file_result.get('error', 'Неизвестная ошибка')}")
            else:
                file_type = file_result.get('type', 'unknown')
                file_name = file_result.get('file_name', f'Файл {i}')
                
                if file_type == 'document':
                    file_extension = file_result.get('file_extension', '')
                    if file_extension in ['.xlsx', '.xls']:
                        await _handle_excel_result(update, context, file_result, i)
                    elif file_extension == '.pdf':
                        await update.message.reply_text(f"📄 **Файл {i}:** {file_name} - PDF файл получен (парсинг в разработке)")
                    else:
                        await update.message.reply_text(f"📄 **Файл {i}:** {file_name} - файл получен")
                elif file_type == 'photo':
                    await update.message.reply_text(f"📸 **Файл {i}:** Фотография получена (OCR в разработке)")
        
        # Очищаем очередь
        await file_queue.clear_queue(update.effective_user.id)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке результата множественных файлов: {e}")
        try:
            await processing_msg.edit_text("❌ Ошибка при обработке результатов.")
        except:
            pass

async def _handle_excel_result(update: Update, context: ContextTypes.DEFAULT_TYPE, file_result: dict, file_number: int):
    """Обрабатывает результат Excel файла"""
    try:
        file_name = file_result.get('file_name', f'Файл {file_number}')
        parsed_content = file_result.get('parsed_content')
        
        if not parsed_content:
            await update.message.reply_text(f"📊 **Файл {file_number}:** {file_name} - Excel файл получен, но не удалось распарсить")
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
        
        await update.message.reply_text(excel_summary)
        
        # TODO: Здесь можно добавить обработку данных Excel через pipeline
        # Например, извлечение списка крепежных изделий и поиск по ним
        
    except Exception as e:
        logger.error(f"Ошибка при обработке Excel результата: {e}")
        try:
            await update.message.reply_text(f"❌ Ошибка при обработке Excel файла {file_number}")
        except:
            pass

async def _auto_process_files(user_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Автоматически обрабатывает файлы с задержкой"""
    try:
        # Ждем 10 секунд для группировки файлов
        await asyncio.sleep(10)
        
        # Проверяем, что очередь все еще существует и не обрабатывается
        if user_id in file_queue.queue:
            queue_item = file_queue.queue[user_id]
            if queue_item.status == 'pending':
                logger.info(f"Автоматически запускаем обработку очереди для пользователя {user_id}")
                result = await file_queue.process_queue(user_id, context)
                
                if result:
                    # Результат уже отправлен в process_queue
                    logger.info(f"Обработка завершена для пользователя {user_id}")
                else:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="❌ Не удалось обработать файлы."
                    )
                    
    except Exception as e:
        logger.error(f"Ошибка при автоматической обработке файлов: {e}")
        try:
            await context.bot.send_message(
                chat_id=user_id,
                text="❌ Произошла ошибка при обработке файлов."
            )
        except:
            pass

