#!/usr/bin/env python3
"""
FastenersAI Bot - Простая версия с webhook для Railway
"""

import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import Update
from telegram.ext import ContextTypes

# Импорт обработчиков
from handlers.command_handler import handle_start, handle_help
from handlers.message_handler_lightweight import handle_message, handle_rating_callback

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получение токена
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN не установлен")

# Получение порта и webhook URL
PORT = int(os.getenv('PORT', 8000))
WEBHOOK_BASE = os.getenv('WEBHOOK_BASE', 'https://fastenersai-production.up.railway.app')
WEBHOOK_PATH = f"/webhook/{TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_BASE}{WEBHOOK_PATH}"

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    await update.message.reply_text(
        "✅ **Статус бота:**\n"
        "🟢 Онлайн и готов к работе\n"
        "🌐 Режим: Webhook\n"
        "🔧 Версия: Lightweight (без NumPy/Pandas)\n"
        "📡 Платформа: Railway"
    )


def main():
    """Основная функция запуска бота"""
    try:
        logger.info(f"Запуск FastenersAI Bot (Lightweight версия)")
        logger.info(f"Порт: {PORT}")
        logger.info(f"Webhook URL: {WEBHOOK_URL}")
        
        # Создание приложения
        global application
        application = Application.builder().token(TOKEN).build()
        
        # Добавление обработчиков
        logger.info("Регистрация обработчиков команд...")
        application.add_handler(CommandHandler("start", handle_start))
        application.add_handler(CommandHandler("help", handle_help))
        application.add_handler(CommandHandler("status", status))
        logger.info("Регистрация обработчиков сообщений...")
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_message))
        application.add_handler(MessageHandler(filters.VOICE, handle_message))
        application.add_handler(MessageHandler(filters.Document.ALL, handle_message))
        application.add_handler(CallbackQueryHandler(handle_rating_callback))
        logger.info("Все обработчики зарегистрированы успешно")
        
        # Добавляем общий обработчик для логирования всех обновлений
        async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
            logger.info(f"📨 Получено обновление: {update.update_id}, тип: {update.effective_message.content_type if update.effective_message else 'unknown'}")
        
        application.add_handler(MessageHandler(filters.ALL, log_update), group=1)
        
        # Запуск webhook
        logger.info("Запуск webhook...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=WEBHOOK_PATH,
            webhook_url=WEBHOOK_URL
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
