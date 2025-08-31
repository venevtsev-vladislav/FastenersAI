#!/usr/bin/env python3
"""
Простой синхронный Telegram Bot
"""

import logging
import time
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
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
    
    update.message.reply_text(welcome_message.strip())
    logger.info(f"Пользователь {user.id} запустил бота")

def help_command(update: Update, context: CallbackContext):
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
    
    update.message.reply_text(help_message.strip())
    logger.info(f"Пользователь {update.effective_user.id} запросил помощь")

def echo(update: Update, context: CallbackContext):
    """Обработчик всех сообщений"""
    try:
        user = update.effective_user
        chat_id = update.effective_chat.id
        
        logger.info(f"Получено сообщение от пользователя {user.id} в чате {chat_id}")
        
        # Отправляем сообщение о начале обработки
        processing_msg = update.message.reply_text("🔄 Обрабатываю ваше сообщение...")
        
        # Простая обработка текстовых сообщений
        if update.message.text:
            text = update.message.text.strip()
            processing_msg.edit_text(f"✅ Получил ваш запрос: '{text}'\n\n🔍 Ищу подходящие детали...")
            
            # Имитируем поиск
            time.sleep(2)
            
            # Отправляем заглушку
            update.message.reply_text("📊 Найдено несколько подходящих деталей!\n\n🔧 Функция генерации Excel файлов пока в разработке.\n\n💡 Попробуйте запрос: 'болт М8х20' или 'саморез по дереву'")
            
        else:
            processing_msg.edit_text("📱 Получил ваше сообщение!\n\n🔧 Обработка медиафайлов пока в разработке.\n\n💡 Попробуйте отправить текстовое описание нужной детали")
        
        processing_msg.delete()
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        try:
            update.message.reply_text("❌ Произошла ошибка при обработке. Попробуйте еще раз.")
        except:
            pass

def main():
    """Основная функция запуска бота"""
    try:
        logger.info("Запускаю синхронного бота...")
        
        # Создаем updater
        updater = Updater(token="8108399357:AAGlKlnQj6uA849saCV_7ORkJb28QecobnQ", use_context=True)
        dispatcher = updater.dispatcher
        
        # Добавляем обработчики команд
        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("help", help_command))
        
        # Добавляем обработчик всех сообщений
        dispatcher.add_handler(MessageHandler(Filters.all, echo))
        
        logger.info("Бот запущен успешно!")
        
        # Запускаем бота
        updater.start_polling()
        updater.idle()
        
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

