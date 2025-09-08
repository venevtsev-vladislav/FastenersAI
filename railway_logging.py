"""
Улучшенное логирование для Railway с детальными логами GPT
"""

import logging
import os
import json
from datetime import datetime
from typing import Any, Dict, Optional

def setup_railway_logging():
    """Настраивает логирование для Railway с детальными логами"""
    
    # Устанавливаем уровень логирования
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, log_level, logging.INFO)
    
    # Создаем форматтер с детальной информацией
    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Очищаем существующие хендлеры
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Консольный хендлер (для Railway)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # Устанавливаем уровень для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.INFO)  # Показываем логи OpenAI
    logging.getLogger("supabase").setLevel(logging.INFO)  # Показываем логи Supabase
    
    # Логируем запуск
    logging.info("🚀 Railway логирование настроено")
    logging.info(f"📊 Уровень логирования: {log_level}")

def log_gpt_request(text: str, user_id: str = None, chat_id: str = None):
    """Логирует запрос к GPT"""
    logger = logging.getLogger('gpt_request')
    logger.info(f"🤖 GPT ЗАПРОС | user_id={user_id} | chat_id={chat_id}")
    logger.info(f"📝 Текст запроса: {text[:200]}{'...' if len(text) > 200 else ''}")

def log_gpt_response(response: Any, user_id: str = None, chat_id: str = None):
    """Логирует ответ от GPT"""
    logger = logging.getLogger('gpt_response')
    logger.info(f"✅ GPT ОТВЕТ | user_id={user_id} | chat_id={chat_id}")
    
    if isinstance(response, dict):
        if 'items' in response and isinstance(response['items'], list):
            logger.info(f"📊 Множественный заказ: {len(response['items'])} позиций")
            for i, item in enumerate(response['items'], 1):
                logger.info(f"  Позиция {i}: {item}")
        else:
            logger.info(f"📊 Одиночный заказ: {response}")
        
        # Логируем полный JSON
        logger.info(f"📋 ПОЛНЫЙ JSON: {json.dumps(response, ensure_ascii=False, indent=2)}")
    else:
        logger.info(f"📊 Ответ: {response}")

def log_telegram_message(update_data: Dict, message_type: str = "text"):
    """Логирует входящее сообщение от Telegram"""
    logger = logging.getLogger('telegram_message')
    logger.info(f"📨 TELEGRAM {message_type.upper()} | chat_id={update_data.get('message', {}).get('chat', {}).get('id')}")
    
    if message_type == "text":
        text = update_data.get('message', {}).get('text', '')
        logger.info(f"📝 Текст: {text[:200]}{'...' if len(text) > 200 else ''}")
    elif message_type == "photo":
        logger.info(f"📷 Фото получено")
    elif message_type == "voice":
        logger.info(f"🎤 Голосовое сообщение получено")
    elif message_type == "document":
        document = update_data.get('message', {}).get('document', {})
        logger.info(f"📄 Документ: {document.get('file_name', 'unknown')}")

def log_processing_pipeline(step: str, data: Any = None, user_id: str = None, chat_id: str = None):
    """Логирует этапы обработки в pipeline"""
    logger = logging.getLogger('processing_pipeline')
    logger.info(f"🔄 PIPELINE {step.upper()} | user_id={user_id} | chat_id={chat_id}")
    
    if data is not None:
        if isinstance(data, dict):
            logger.info(f"📊 Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            logger.info(f"📊 Данные: {data}")

def log_supabase_operation(operation: str, table: str = None, data: Any = None):
    """Логирует операции с Supabase"""
    logger = logging.getLogger('supabase_operation')
    logger.info(f"🗄️ SUPABASE {operation.upper()} | table={table}")
    
    if data is not None:
        if isinstance(data, dict):
            logger.info(f"📊 Данные: {json.dumps(data, ensure_ascii=False, indent=2)}")
        else:
            logger.info(f"📊 Данные: {data}")

def log_error(error: Exception, context: str = None, user_id: str = None, chat_id: str = None):
    """Логирует ошибки с контекстом"""
    logger = logging.getLogger('error')
    logger.error(f"❌ ОШИБКА | context={context} | user_id={user_id} | chat_id={chat_id}")
    logger.error(f"🔍 Детали: {str(error)}")
    logger.error(f"📊 Тип: {type(error).__name__}")

# Глобальная инициализация
setup_railway_logging()
