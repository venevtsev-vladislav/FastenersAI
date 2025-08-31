#!/usr/bin/env python3
"""
Отладочная версия Telegram Bot для поиска крепежных деталей
"""

import logging
import sys
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Настройка подробного логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_bot.log')
    ]
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    logger.info(f"Получена команда /start от пользователя {update.effective_user.id}")
    await update.message.reply_text('Привет! Я бот для поиска крепежных деталей. Отправьте мне описание нужной детали.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    logger.info(f"Получена команда /help от пользователя {update.effective_user.id}")
    await update.message.reply_text('Отправьте текстовое описание нужной детали, например: "болт М8х20"')

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик всех сообщений"""
    if update.message.text:
        text = update.message.text
        user_id = update.effective_user.id
        logger.info(f"Получено сообщение от пользователя {user_id}: {text}")
        
        await update.message.reply_text(f'Получил ваш запрос: "{text}". Ищу подходящие детали...')
        
        # Имитируем поиск
        import asyncio
        await asyncio.sleep(2)
        
        await update.message.reply_text('Найдено несколько подходящих деталей! Функция Excel пока в разработке.')
        logger.info(f"Ответ отправлен пользователю {user_id}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Ошибка при обработке обновления {update}: {context.error}")

def main():
    """Основная функция"""
    logger.info("=== ЗАПУСК ОТЛАДОЧНОГО БОТА ===")
    
    try:
        # Создаем приложение
        logger.info("Создаю приложение Telegram...")
        app = Application.builder().token("8108399357:AAGlKlnQj6uA849saCV_7ORkJb28QecobnQ").build()
        logger.info("Приложение создано успешно")
        
        # Добавляем обработчики
        logger.info("Добавляю обработчики...")
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("help", help_command))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
        
        # Добавляем обработчик ошибок
        app.add_error_handler(error_handler)
        logger.info("Обработчики добавлены успешно")
        
        logger.info("Бот готов к запуску!")
        
        # Запускаем
        logger.info("Запускаю polling...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Критическая ошибка при запуске: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)

