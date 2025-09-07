#!/usr/bin/env python3
"""
Простая версия Telegram Bot для тестирования на Railway
"""

import logging
import asyncio
import os
import sys

# Добавляем текущую директорию в Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import TELEGRAM_TOKEN

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    await update.message.reply_html(
        f"Привет, {user.mention_html()}!\n\n"
        f"Я FastenersAI Bot - помощник для поиска крепежных деталей.\n"
        f"Отправьте мне описание детали, и я найду подходящие варианты."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help"""
    help_text = """
🤖 FastenersAI Bot - Помощник по поиску крепежных деталей

📋 Доступные команды:
/start - Начать работу с ботом
/help - Показать это сообщение

💡 Как использовать:
Просто отправьте описание нужной детали, например:
• "Болт М8х20"
• "Гайка М6"
• "Шайба пружинная"

Бот найдет подходящие варианты в каталоге.
    """
    await update.message.reply_text(help_text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user = update.effective_user
    
    logger.info(f"Получено сообщение от {user.username}: {user_message}")
    
    # Простой ответ для тестирования
    response = f"""
🔍 Поиск по запросу: "{user_message}"

✅ Бот работает на Railway!
📊 Статус: Активен
🌐 Хостинг: Railway.app

Это тестовая версия бота. Полная функциональность будет доступна после исправления проблем с зависимостями.
    """
    
    await update.message.reply_text(response)

def main():
    """Основная функция запуска бота"""
    try:
        # Получаем порт для Railway (если не указан, используем 8000)
        port = int(os.getenv('PORT', 8000))
        logger.info(f"Запуск на порту: {port}")
        
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Добавляем обработчик для текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("Бот запущен успешно")
        
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
