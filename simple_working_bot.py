#!/usr/bin/env python3
"""
Простой рабочий Telegram Bot для поиска крепежных деталей
"""

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text('Привет! Я бот для поиска крепежных деталей. Отправьте мне описание нужной детали.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text('Отправьте текстовое описание нужной детали, например: "болт М8х20"')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    if update.message.text:
        text = update.message.text
        await update.message.reply_text(f'Получил ваш запрос: "{text}". Ищу подходящие детали...')
        
        # Имитируем поиск
        import asyncio
        await asyncio.sleep(2)
        
        await update.message.reply_text('Найдено несколько подходящих деталей! Функция Excel пока в разработке.')

def main():
    """Основная функция"""
    logger.info("Запускаю бота...")
    
    # Создаем приложение
    app = Application.builder().token("8108399357:AAGlKlnQj6uA849saCV_7ORkJb28QecobnQ").build()
    
    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    
    logger.info("Бот запущен!")
    
    # Запускаем
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Ошибка: {e}")

