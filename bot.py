#!/usr/bin/env python3
"""
Telegram Bot для поиска крепежных деталей
"""

import logging
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
from handlers.message_handler import handle_message, handle_rating_callback
from handlers.command_handler import handle_start, handle_help
# from database.supabase_client import init_supabase  # Убрано - используем Edge Function
from utils.logger import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

def main():
    """Основная функция запуска бота"""
    try:
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("help", handle_help))
        
        # Добавляем обработчик для callback кнопок (оценка работы бота)
        application.add_handler(CallbackQueryHandler(handle_rating_callback, pattern="^rating_"))
        
        # Добавляем обработчики для разных типов сообщений
        # Текстовые сообщения
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Медиа файлы (фото, голос, документы)
        application.add_handler(MessageHandler(filters.PHOTO | filters.VOICE | filters.Document.ALL, handle_message))
        
        logger.info("Бот запущен успешно")
        
        # Инициализация Supabase убрана - используем Edge Function
        logger.info("Supabase инициализация пропущена - используем Edge Function")
        
        # Запускаем бота
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    try:
        # Запускаем бота
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
