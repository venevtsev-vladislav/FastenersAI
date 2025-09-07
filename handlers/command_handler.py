"""
Обработчики команд для Telegram бота
"""

import logging
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user = update.effective_user
        logger.info(f"🚀 Получена команда /start от пользователя {user.id} ({user.first_name}) - v2.1")
        
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
        logger.info(f"✅ Ответ на /start отправлен пользователю {user.id}")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_start: {e}")
        try:
            await update.message.reply_text("❌ Произошла ошибка при обработке команды /start")
        except:
            pass

async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_message = """
🔧 Помощь по использованию бота

📝 Как использовать:
1. Отправьте описание нужной детали текстом
2. Или запишите голосовое сообщение
3. Или отправьте фото детали
4. Или загрузите файлы (Excel, PDF, изображения)

💡 Примеры запросов:
• "Нужен болт М8х20 с шестигранной головкой"
• "Ищу саморез по дереву 4х50"
• "Анкер для бетона М10"

📁 Обработка файлов:
• Excel файлы (.xlsx, .xls) - автоматический парсинг
• PDF файлы - в разработке
• Изображения - OCR в разработке
• Можно загружать до 3 файлов одновременно

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

