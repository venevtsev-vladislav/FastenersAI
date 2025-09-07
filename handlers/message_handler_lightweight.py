"""
Упрощенный обработчик сообщений для lightweight версии бота
"""

import logging
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упрощенный обработчик всех типов сообщений для lightweight версии"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        message = update.message
        
        logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
        
        # Определяем тип сообщения
        if message.text:
            await _handle_text_message(update, context)
        elif message.photo:
            await _handle_photo_message(update, context)
        elif message.voice:
            await _handle_voice_message(update, context)
        elif message.document:
            await _handle_document_message(update, context)
        else:
            await message.reply_text("❓ Неизвестный тип сообщения. Попробуйте отправить текст, фото, голосовое сообщение или документ.")
            
    except Exception as e:
        logger.error(f"Критическая ошибка в обработчике сообщений: {e}")
        try:
            await update.message.reply_text("❌ Произошла критическая ошибка. Обратитесь к администратору.")
        except:
            pass

async def _handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        message = update.message
        user_message = message.text
        user = update.effective_user
        
        logger.info(f"Обработка текстового сообщения от {user.id}: {user_message[:100]}...")
        
        # Отправляем сообщение о начале обработки
        processing_msg = await message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        # Имитируем обработку
        await processing_msg.edit_text("🧠 Анализирую ваш запрос...")
        
        # Небольшая задержка для реалистичности
        import asyncio
        await asyncio.sleep(1)
        
        await processing_msg.edit_text("🔍 Ищу детали в базе данных...")
        await asyncio.sleep(1)
        
        await processing_msg.edit_text("📊 Создаю результат...")
        await asyncio.sleep(1)
        
        # Отправляем результат
        current_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        
        response = f"""🤖 **Результат обработки запроса**

📝 **Ваш запрос:** {user_message}

⚠️ **Внимание:** Бот работает в легком режиме.
Полная AI функциональность будет доступна после решения проблем с зависимостями.

🔧 **Статус:** Обработка сообщений работает, но без AI анализа.

📅 **Время обработки:** {current_time}

💡 **Для полной функциональности:**
• Отправьте описание крепежа более детально
• Попробуйте использовать стандартные термины
• Используйте команду /help для получения справки"""

        await processing_msg.edit_text(response)
        
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
        
        await message.reply_text(
            "🤖 **Оцените работу бота:**\n\nСправился ли бот с вашим запросом?",
            reply_markup=reply_markup
        )
        
        logger.info(f"Успешно обработан текстовый запрос пользователя {user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке текстового сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз.")
        except:
            pass

async def _handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото"""
    try:
        message = update.message
        user = update.effective_user
        
        logger.info(f"Получено фото от {user.id}")
        
        response = f"""📸 **Фото получено!**

⚠️ **Внимание:** Бот работает в легком режиме.
Анализ изображений будет доступен после решения проблем с зависимостями.

🔧 **Статус:** Загрузка фото работает, но без AI анализа.

💡 **Для анализа фото:**
• В будущем здесь будет OCR для извлечения текста
• Пока попробуйте описать крепеж текстом"""

        await message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке фото: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке фото.")
        except:
            pass

async def _handle_voice_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    try:
        message = update.message
        user = update.effective_user
        
        logger.info(f"Получено голосовое сообщение от {user.id}")
        
        response = f"""🎤 **Голосовое сообщение получено!**

⚠️ **Внимание:** Бот работает в легком режиме.
Распознавание речи будет доступно после решения проблем с зависимостями.

🔧 **Статус:** Загрузка голосовых сообщений работает, но без распознавания речи.

💡 **Для обработки голоса:**
• В будущем здесь будет Speech-to-Text
• Пока попробуйте описать крепеж текстом"""

        await message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке голосового сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке голосового сообщения.")
        except:
            pass

async def _handle_document_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик документов"""
    try:
        message = update.message
        user = update.effective_user
        document = message.document
        
        logger.info(f"Получен документ от {user.id}: {document.file_name}")
        
        response = f"""📄 **Документ получен!**

📁 **Файл:** {document.file_name}
📊 **Размер:** {document.file_size} байт

⚠️ **Внимание:** Бот работает в легком режиме.
Парсинг документов будет доступен после решения проблем с зависимостями.

🔧 **Статус:** Загрузка документов работает, но без парсинга содержимого.

💡 **Для обработки документов:**
• В будущем здесь будет парсинг Excel/PDF файлов
• Пока попробуйте описать крепеж текстом"""

        await message.reply_text(response)
        
    except Exception as e:
        logger.error(f"Ошибка при обработке документа: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке документа.")
        except:
            pass

async def handle_rating_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатия на кнопки оценки работы бота"""
    try:
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
            
    except Exception as e:
        logger.error(f"Ошибка при обработке callback: {e}")
        try:
            await query.answer("❌ Произошла ошибка при обработке оценки.")
        except:
            pass
