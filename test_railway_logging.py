#!/usr/bin/env python3
"""
Тест улучшенного логирования для Railway
Проверяем, что логи корректно отображаются в консоли
"""

import asyncio
import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from railway_logging import setup_railway_logging, log_gpt_request, log_gpt_response, log_processing_pipeline, log_error
from services.openai_service import OpenAIService

async def test_railway_logging():
    """Тестируем улучшенное логирование"""
    
    print("🔍 ТЕСТ УЛУЧШЕННОГО ЛОГИРОВАНИЯ ДЛЯ RAILWAY")
    print("=" * 60)
    
    # Настраиваем логирование
    setup_railway_logging()
    
    # Тестируем различные типы логов
    print("\n📝 ТЕСТИРУЕМ РАЗЛИЧНЫЕ ТИПЫ ЛОГОВ")
    print("-" * 40)
    
    # Тест 1: Логирование GPT запроса
    test_text = "Анкер с кольцом м8 10х100 (30шт)"
    log_gpt_request(test_text, user_id="12345", chat_id="67890")
    
    # Тест 2: Логирование GPT ответа
    test_response = {
        "items": [
            {
                "type": "анкер",
                "diameter": "M8",
                "length": "10х100 мм",
                "quantity": "30шт",
                "confidence": 0.95
            }
        ]
    }
    log_gpt_response(test_response, user_id="12345", chat_id="67890")
    
    # Тест 3: Логирование pipeline
    log_processing_pipeline("TEXT_MESSAGE_RECEIVED", {"text": test_text[:100]}, "12345", "67890")
    log_processing_pipeline("STARTING_PROCESSING", {"input_text": test_text[:100]}, "12345", "67890")
    log_processing_pipeline("PROCESSING_COMPLETED", {"results_count": 1}, "12345", "67890")
    
    # Тест 4: Логирование ошибки
    try:
        raise ValueError("Тестовая ошибка для логирования")
    except Exception as e:
        log_error(e, "TEST_ERROR", "12345", "67890")
    
    print("\n✅ ВСЕ ТЕСТЫ ЛОГИРОВАНИЯ ЗАВЕРШЕНЫ")
    print("=" * 60)
    
    # Тест 5: Реальный GPT запрос с логированием
    print("\n🤖 ТЕСТ РЕАЛЬНОГО GPT ЗАПРОСА С ЛОГИРОВАНИЕМ")
    print("-" * 40)
    
    try:
        openai_service = OpenAIService()
        print("✅ OpenAI сервис инициализирован")
        
        # Отправляем запрос с логированием
        result = await openai_service.analyze_with_assistant(test_text)
        
        print("✅ GPT запрос завершен с детальным логированием")
        print(f"📊 Результат: {result}")
        
    except Exception as e:
        log_error(e, "GPT_TEST_ERROR", "12345", "67890")
        print(f"❌ Ошибка при тестировании GPT: {e}")
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН!")
    print("Теперь эти же логи будут видны в Railway Dashboard")

if __name__ == "__main__":
    asyncio.run(test_railway_logging())
