"""
Кастомные исключения для приложения
"""

from typing import Optional, Dict, Any


class BotError(Exception):
    """Базовое исключение для бота"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(BotError):
    """Ошибка конфигурации"""
    pass


class DatabaseError(BotError):
    """Ошибка базы данных"""
    pass


class OpenAIServiceError(BotError):
    """Ошибка сервиса OpenAI"""
    pass


class SearchError(BotError):
    """Ошибка поиска"""
    pass


class ValidationError(BotError):
    """Ошибка валидации"""
    pass


class ExcelGenerationError(BotError):
    """Ошибка генерации Excel"""
    pass


class MessageProcessingError(BotError):
    """Ошибка обработки сообщения"""
    pass


class RankingError(BotError):
    """Ошибка ранжирования результатов"""
    pass


def handle_service_error(error: Exception, context: str) -> BotError:
    """Преобразует стандартные исключения в кастомные"""
    if isinstance(error, BotError):
        return error
    
    # Преобразуем стандартные исключения
    if "openai" in str(error).lower() or "api" in str(error).lower():
        return OpenAIServiceError(f"Ошибка OpenAI API: {error}", {"original_error": str(error)})
    
    if "database" in str(error).lower() or "supabase" in str(error).lower():
        return DatabaseError(f"Ошибка базы данных: {error}", {"original_error": str(error)})
    
    if "excel" in str(error).lower() or "workbook" in str(error).lower():
        return ExcelGenerationError(f"Ошибка Excel: {error}", {"original_error": str(error)})
    
    # По умолчанию
    return BotError(f"Неожиданная ошибка в {context}: {error}", {"original_error": str(error)})
