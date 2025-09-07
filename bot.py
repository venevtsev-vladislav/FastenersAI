#!/usr/bin/env python3
"""
Telegram Bot для поиска крепежных деталей
"""

import logging
import asyncio
import os
import sys

# Добавляем текущую директорию в Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Убеждаемся, что мы не в директории numpy
if 'numpy' in current_dir:
    # Если мы в директории numpy, переходим в родительскую
    current_dir = os.path.dirname(current_dir)
    sys.path.insert(0, current_dir)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN
# from database.supabase_client import init_supabase  # Убрано - используем Edge Function
from utils.logger import setup_logging

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)

# Условный импорт для Railway
try:
    from handlers.message_handler import handle_message, handle_rating_callback
    from handlers.command_handler import handle_start, handle_help
    FULL_FUNCTIONALITY = True
    logger.info("Полная функциональность загружена")
except ImportError as e:
    logger.warning(f"Не удалось импортировать полную функциональность: {e}")
    # Создаем заглушки для основных функций
    async def handle_message(update, context):
        await update.message.reply_text("🤖 Бот работает в ограниченном режиме на Railway")
    
    async def handle_rating_callback(update, context):
        await update.callback_query.answer("Функция недоступна в ограниченном режиме")
    
    async def handle_start(update, context):
        await update.message.reply_text("Привет! Я FastenersAI Bot (Railway версия)")
    
    async def handle_help(update, context):
        await update.message.reply_text("Помощь: бот работает в ограниченном режиме")
    
    FULL_FUNCTIONALITY = False
    logger.info("Загружена ограниченная версия для Railway")

def main():
    """Основная функция запуска бота"""
    try:
        # Получаем порт для Railway (если не указан, используем 8000)
        port = int(os.getenv('PORT', 8000))
        logger.info(f"Запуск на порту: {port}")
        
        # Логируем режим работы
        if FULL_FUNCTIONALITY:
            logger.info("🚀 Полная функциональность активна")
        else:
            logger.warning("⚠️ Ограниченный режим - некоторые функции недоступны")
        
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
