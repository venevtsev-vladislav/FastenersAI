#!/usr/bin/env python3
"""
Telegram Bot с использованием API версии 20.7
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
from utils.logger import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    welcome_message = f"""
Привет, {user.first_name}! 👋

Я бот для поиска крепежных деталей. Отправьте мне:
• Текстовое описание нужной детали
• Голосовое сообщение
• Фото детали
• Аудио файл

И я найду подходящие варианты в нашем каталоге!

Команды:
/help - показать справку
/start - начать заново
    """
    
    await update.message.reply_text(welcome_message.strip())
    logger.info(f"Пользователь {user.id} запустил бота")

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_message = """
🔧 Помощь по использованию бота

📝 Как использовать:
1. Отправьте описание нужной детали текстом
2. Или запишите голосовое сообщение
3. Или отправьте фото детали
4. Или загрузите аудио файл

💡 Примеры запросов:
• "Нужен болт М8х20 с шестигранной головкой"
• "Ищу саморез по дереву 4х50"
• "Анкер для бетона М10"

📊 Результат:
Бот создаст Excel файл с подходящими деталями, включая:
• Артикул (SKU)
• Наименование
• Количество в упаковке
• И другие характеристики

❓ Если что-то не работает, попробуйте переформулировать запрос
    """
    
    await update.message.reply_text(help_message.strip())
    logger.info(f"Пользователь {update.effective_user.id} запросил помощь")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
        
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        # Простая обработка текстовых сообщений
        if update.message.text:
            text = update.message.text.strip()
            await processing_msg.edit_text(f"✅ Получил ваш запрос: '{text}'\n\n🔍 Ищу подходящие детали...")
            
            # Имитируем поиск
            import asyncio
            await asyncio.sleep(2)
            
            # Отправляем заглушку
            await update.message.reply_text("📊 Найдено несколько подходящих деталей!\n\n🔧 Функция генерации Excel файлов пока в разработке.\n\n💡 Попробуйте запрос: 'болт М8х20' или 'саморез по дереву'")
            
        else:
            await processing_msg.edit_text("📱 Получил ваше сообщение!\n\n🔧 Обработка медиафайлов пока в разработке.\n\n💡 Попробуйте отправить текстовое описание нужной детали")
        
        await processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз.")
        except:
            pass

async def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запускаю бота...")
        
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("help", handle_help))
        
        # Добавляем обработчик всех сообщений
        application.add_handler(MessageHandler(filters.ALL, handle_message))
        
        logger.info("Бот запущен успешно!")
        
        # Запускаем бота
        await application.run_polling()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    try:
        import asyncio
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
