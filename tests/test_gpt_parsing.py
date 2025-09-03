#!/usr/bin/env python3
"""
Тест GPT парсинга для проекта FastenersAI
Тестируем обработку запроса с анкерами и болтами
"""

import asyncio
import json
import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.openai_service import OpenAIService
from services.message_processor import MessageProcessor

async def test_gpt_parsing():
    """Тестируем GPT парсинг запроса"""
    
    # Тестовый запрос (как на скрине)
    test_query = """
    Анкер забиваемый латунный М6
    Клиновой анкер 8х50
    Анкерный болт с кольцом М16x130
    Болты DIN603 М10х120, цинк (кг)
    Болты DIN603 М6х60, цинк (кг)
    Болт DIN 933 кл.пр.8.8 М14х80, цинк (кг)
    Болт DIN 933 кл.пр.8.8 М16х60, цинк (кг)
    Болт DIN 933 кл.пр.8.8 М16х70, цинк (кг)
    Болт DIN 933 кл.пр.8.8 М18х40, цинк (кг)
    Болт DIN 933 кл.пр.8.8 М5х16, цинк (кг)
    """
    
    print("🔍 ТЕСТ GPT ПАРСИНГА")
    print("=" * 50)
    print(f"📝 Тестовый запрос:\n{test_query.strip()}")
    print("=" * 50)
    
    try:
        # Создаем сервисы
        openai_service = OpenAIService()
        message_processor = MessageProcessor()
        
        print("🚀 Тестируем GPT анализ...")
        
        # Тестируем GPT анализ напрямую
        gpt_result = await openai_service.analyze_with_assistant(test_query)
        
        print("✅ GPT анализ завершен!")
        print(f"📊 Результат GPT:\n{json.dumps(gpt_result, indent=2, ensure_ascii=False)}")
        
        # Тестируем через MessageProcessor
        print("\n🚀 Тестируем через MessageProcessor...")
        
        # Создаем mock сообщение
        class MockMessage:
            def __init__(self, text):
                self.text = text
        
        mock_message = MockMessage(test_query)
        
        # Обрабатываем через MessageProcessor
        processor_result = await message_processor.process_message(mock_message)
        
        print("✅ MessageProcessor обработка завершена!")
        print(f"📊 Результат MessageProcessor:\n{json.dumps(processor_result, indent=2, ensure_ascii=False)}")
        
        # Проверяем, что результат содержит items
        if processor_result and processor_result.get('user_intent'):
            user_intent = processor_result['user_intent']
            
            if isinstance(user_intent, dict) and 'items' in user_intent:
                items = user_intent['items']
                print(f"\n🎯 УСПЕХ! Найдено {len(items)} позиций:")
                
                for i, item in enumerate(items, 1):
                    print(f"  {i}. {item.get('type', 'N/A')} - M{item.get('diameter', 'N/A')}x{item.get('length', 'N/A')}")
                
                return True
            else:
                print(f"\n❌ ОШИБКА: user_intent не содержит items")
                print(f"user_intent: {user_intent}")
                return False
        else:
            print(f"\n❌ ОШИБКА: MessageProcessor не вернул результат")
            return False
            
    except Exception as e:
        print(f"\n💥 ОШИБКА при тестировании: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста GPT парсинга...")
    
    # Запускаем асинхронный тест
    result = asyncio.run(test_gpt_parsing())
    
    if result:
        print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("GPT корректно обработал запрос и вернул структурированный результат")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН!")
        print("Есть проблемы с обработкой запроса")
    
    sys.exit(0 if result else 1)
