#!/usr/bin/env python3
"""
FastenersAI Bot - Исправленная версия для Railway
С health check endpoint
"""

import os
import logging
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram import Update
from telegram.ext import ContextTypes
from fastapi import FastAPI
import uvicorn
import asyncio
from threading import Thread

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

# FastAPI приложение для health check
app = FastAPI()

@app.get("/")
async def health_check():
    """Health check endpoint для Railway"""
    return {"status": "FastenersAI Bot is running! 🚀", "webhook_url": WEBHOOK_URL}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "bot": "FastenersAI"}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "🚀 **FastenersAI Bot** запущен!\n\n"
        "Я помогу вам найти крепежные изделия.\n"
        "Отправьте мне описание или фото крепежа."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📋 **Доступные команды:**\n"
        "/start - Запуск бота\n"
        "/help - Показать эту справку\n"
        "/status - Статус бота\n\n"
        "💡 **Как использовать:**\n"
        "Отправьте описание крепежа или фото для поиска."
    )

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /status"""
    await update.message.reply_text(
        "✅ **Статус бота:**\n"
        "🟢 Онлайн и готов к работе\n"
        "🌐 Режим: Webhook\n"
        "🔧 Версия: Lightweight (без NumPy/Pandas)\n"
        "📡 Платформа: Railway"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    user_message = update.message.text
    user_id = update.from_user.id
    username = update.from_user.username or "Unknown"
    
    logger.info(f"Получено сообщение от {username} ({user_id}): {user_message}")
    
    # Простой ответ (заглушка для AI функциональности)
    response = (
        f"🤖 **Получено ваше сообщение:**\n"
        f"📝 {user_message}\n\n"
        f"⚠️ **Внимание:** Бот работает в легком режиме.\n"
        f"Полная AI функциональность будет доступна после решения проблем с зависимостями.\n\n"
        f"🔧 **Статус:** Обработка сообщений работает, но без AI анализа."
    )
    
    await update.message.reply_text(response)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик фото"""
    user_id = update.from_user.id
    username = update.from_user.username or "Unknown"
    
    logger.info(f"Получено фото от {username} ({user_id})")
    
    response = (
        f"📸 **Фото получено!**\n\n"
        f"⚠️ **Внимание:** Бот работает в легком режиме.\n"
        f"Анализ изображений будет доступен после решения проблем с зависимостями.\n\n"
        f"🔧 **Статус:** Загрузка фото работает, но без AI анализа."
    )
    
    await update.message.reply_text(response)

def run_fastapi():
    """Запуск FastAPI сервера"""
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="info")

def main():
    """Основная функция запуска бота"""
    try:
        logger.info(f"Запуск FastenersAI Bot (Lightweight версия)")
        logger.info(f"Порт: {PORT}")
        logger.info(f"Webhook URL: {WEBHOOK_URL}")
        
        # Создание приложения
        application = Application.builder().token(TOKEN).build()
        
        # Добавление обработчиков
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("status", status))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.add_handler(MessageHandler(filters.PHOTO, handle_photo))
        
        # Запуск FastAPI в отдельном потоке
        fastapi_thread = Thread(target=run_fastapi, daemon=True)
        fastapi_thread.start()
        
        # Запуск webhook
        logger.info("Запуск webhook...")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT + 1,  # Используем другой порт для webhook
            url_path=WEBHOOK_PATH,
            webhook_url=WEBHOOK_URL
        )
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise

if __name__ == '__main__':
    main()
