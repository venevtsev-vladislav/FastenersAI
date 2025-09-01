"""
Обновленный обработчик сообщений для Telegram бота
Использует новый модульный pipeline
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes
from pipeline.message_processor import MessagePipeline
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
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        try:
            # Используем новый модульный pipeline
            pipeline = MessagePipeline(bot=update.get_bot())
            result = await pipeline.process_message(update.message, context)
            
            if not result:
                await processing_msg.edit_text("❌ Не удалось обработать сообщение. Попробуйте еще раз.")
                return
            
            # Отправляем Excel файл
            await processing_msg.edit_text("📊 Создаю Excel файл с результатами...")
            
            # Создаем подпись для файла
            import datetime
            current_time = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
            
            # Определяем тип запроса
            if result.get('is_multiple_order'):
                request_type = "📋 Множественный заказ"
                request_summary = f"{len(result.get('results', []))} позиций"
            else:
                request_type = "💬 Текстовый запрос"
                request_summary = result['query'][:50] + "..." if len(result['query']) > 50 else result['query']
            
            caption = f"{request_type}\n{request_summary}\n✅ Найдено: {result['total_results']} позиций\n📅 {current_time}"
            
            # Отправляем файл
            with open(result['excel_file'], 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=f"результаты_поиска_{user.id}.xlsx",
                    caption=caption
                )
            
            # Отправляем вопросы для уточнения, если есть
            if result.get('clarification_questions'):
                questions_text = "❓ Вопросы для уточнения:\n" + "\n".join([f"• {q}" for q in result['clarification_questions']])
                await update.message.reply_text(questions_text)
            
            await processing_msg.delete()
            logger.info(f"Успешно обработан запрос пользователя {user.id}")
            
        except Exception as e:
            error = handle_service_error(e, "message_processing")
            logger.error(f"Ошибка при обработке сообщения: {error}")
            
            await processing_msg.edit_text("❌ Произошла ошибка при обработке. Попробуйте еще раз или обратитесь к администратору.")
            
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

