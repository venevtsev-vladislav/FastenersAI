"""
Улучшенное логирование с correlation ID и структурированными логами
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from contextvars import ContextVar

# Context variable для correlation ID
correlation_id: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class CorrelationFilter(logging.Filter):
    """Фильтр для добавления correlation ID в логи"""
    
    def filter(self, record):
        record.correlation_id = correlation_id.get() or 'no-id'
        return True


class StructuredFormatter(logging.Formatter):
    """Структурированный форматтер для логов"""
    
    def format(self, record):
        # Добавляем correlation ID
        if hasattr(record, 'correlation_id'):
            record.correlation_id = record.correlation_id
        else:
            record.correlation_id = correlation_id.get() or 'no-id'
        
        # Добавляем timestamp
        record.timestamp = datetime.now().isoformat()
        
        # Форматируем сообщение
        formatted = super().format(record)
        
        # Добавляем структурированные поля
        extra_fields = []
        if hasattr(record, 'user_id'):
            extra_fields.append(f"user_id={record.user_id}")
        if hasattr(record, 'chat_id'):
            extra_fields.append(f"chat_id={record.chat_id}")
        if hasattr(record, 'request_type'):
            extra_fields.append(f"request_type={record.request_type}")
        
        if extra_fields:
            formatted += f" | {' | '.join(extra_fields)}"
        
        return formatted


def setup_logging(log_level: str = "INFO") -> None:
    """Настраивает логирование для проекта"""
    
    # Создаем папку для логов
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Устанавливаем уровень логирования
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Очищаем существующие хендлеры
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Создаем форматтер
    formatter = StructuredFormatter(
        fmt="%(timestamp)s | %(correlation_id)s | %(name)s | %(levelname)s | %(message)s"
    )
    
    # Консольный хендлер
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    console_handler.addFilter(CorrelationFilter())
    root_logger.addHandler(console_handler)
    
    # Файловый хендлер
    file_handler = logging.FileHandler(
        os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log"),
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    file_handler.addFilter(CorrelationFilter())
    root_logger.addHandler(file_handler)
    
    # Устанавливаем уровень для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    
    # Логируем запуск
    logging.info("Логирование настроено")


def get_logger(name: str) -> logging.Logger:
    """Получает логгер с именем"""
    return logging.getLogger(name)


def set_correlation_id(corr_id: Optional[str] = None) -> str:
    """Устанавливает correlation ID для текущего контекста"""
    if corr_id is None:
        corr_id = str(uuid.uuid4())[:8]
    
    correlation_id.set(corr_id)
    return corr_id


def get_correlation_id() -> Optional[str]:
    """Получает текущий correlation ID"""
    return correlation_id.get()


def log_with_context(logger: logging.Logger, level: str, message: str, **context) -> None:
    """Логирует сообщение с контекстом"""
    # Добавляем correlation ID в контекст
    context['correlation_id'] = get_correlation_id()
    
    # Логируем с контекстом
    log_method = getattr(logger, level.lower())
    log_method(f"{message} | {' | '.join(f'{k}={v}' for k, v in context.items())}")


def log_user_request(logger: logging.Logger, user_id: int, chat_id: int, request_type: str, message: str) -> None:
    """Логирует запрос пользователя с контекстом"""
    log_with_context(
        logger, 'info', message,
        user_id=user_id,
        chat_id=chat_id,
        request_type=request_type
    )


def log_error_with_context(logger: logging.Logger, error: Exception, context: str, **extra_context) -> None:
    """Логирует ошибку с контекстом"""
    log_with_context(
        logger, 'error', f"Ошибка в {context}: {error}",
        error_type=type(error).__name__,
        **extra_context
    )
