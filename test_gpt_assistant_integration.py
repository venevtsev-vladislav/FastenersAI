#!/usr/bin/env python3
"""
Тест интеграции GPT ассистента в message_handler_v2
Проверяем, что GPT ассистент используется вместо старого pipeline
"""

import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from handlers.message_handler_v2 import MessageHandlerV2
from railway_logging import setup_railway_logging

async def test_gpt_assistant_integration():
    """Тестируем интеграцию GPT ассистента"""
    
    print("🔍 ТЕСТ ИНТЕГРАЦИИ GPT АССИСТЕНТА В MESSAGE_HANDLER_V2")
    print("=" * 60)
    
    # Настраиваем логирование
    setup_railway_logging()
    
    # Создаем мок для Supabase клиента
    mock_supabase_client = Mock()
    mock_supabase_client.create_request = AsyncMock(return_value="test-request-id")
    
    # Создаем обработчик
    handler = MessageHandlerV2()
    handler.supabase_client = mock_supabase_client
    
    # Тестовый текст
    test_text = "Анкер с кольцом м8 10х100 (30шт)\nАнкер с кольцом м12 16х130 (10шт)"
    
    print(f"📝 Тестовый текст: {test_text}")
    
    # Тестируем конвертацию GPT результата
    print("\n🔄 ТЕСТИРУЕМ КОНВЕРТАЦИЮ GPT РЕЗУЛЬТАТА")
    print("-" * 40)
    
    # Мок GPT результата
    mock_gpt_result = {
        "items": [
            {
                "type": "анкер",
                "diameter": "M8",
                "length": "10х100 мм",
                "quantity": "30шт",
                "confidence": 0.95
            },
            {
                "type": "анкер",
                "diameter": "M12",
                "length": "16х130 мм",
                "quantity": "10шт",
                "confidence": 0.95
            }
        ]
    }
    
    # Конвертируем результат
    results = handler._convert_gpt_result_to_processing_results(mock_gpt_result, "test-request-id")
    
    print(f"✅ Конвертировано {len(results)} результатов")
    for i, result in enumerate(results, 1):
        print(f"  Результат {i}: {result.raw_text} | статус: {result.status} | метод: {result.chosen_method}")
    
    # Тестируем полный процесс (без реального GPT вызова)
    print("\n🤖 ТЕСТИРУЕМ ПОЛНЫЙ ПРОЦЕСС (БЕЗ РЕАЛЬНОГО GPT)")
    print("-" * 40)
    
    # Мокаем GPT сервис
    handler.openai_service.analyze_with_assistant = AsyncMock(return_value=mock_gpt_result)
    
    # Мокаем Excel генератор
    handler.excel_generator.generate_excel = AsyncMock(return_value="/tmp/test.xlsx")
    
    # Создаем мок сообщения
    mock_message = Mock()
    mock_message.text = test_text
    mock_message.reply_text = AsyncMock()
    mock_message.reply_document = AsyncMock()
    
    try:
        # Тестируем обработку текстового сообщения
        await handler._handle_text_message(mock_message, "12345", "67890")
        
        print("✅ Обработка текстового сообщения завершена успешно")
        
        # Проверяем, что GPT ассистент был вызван
        handler.openai_service.analyze_with_assistant.assert_called_once_with(test_text)
        print("✅ GPT ассистент был вызван")
        
        # Проверяем, что Excel был сгенерирован
        handler.excel_generator.generate_excel.assert_called_once()
        print("✅ Excel файл был сгенерирован")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("Теперь message_handler_v2 использует GPT ассистента напрямую!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_gpt_assistant_integration())
