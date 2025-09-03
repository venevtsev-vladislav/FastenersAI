#!/usr/bin/env python3
"""
Тест встроенного SmartParser для проекта FastenersAI
Тестируем логику определения сложности запроса
"""

import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.message_processor import MessageProcessor

def test_smart_parser():
    """Тестируем встроенный SmartParser"""
    
    print("🔍 ТЕСТ ВСТРОЕННОГО SMART PARSER")
    print("=" * 50)
    
    # Создаем MessageProcessor
    processor = MessageProcessor()
    
    # Тестовые запросы
    test_cases = [
        {
            "query": "DIN 965 M6x20",
            "expected": "Простой формат",
            "description": "Стандартный DIN формат"
        },
        {
            "query": "M6 20 мм",
            "expected": "Простой формат", 
            "description": "Простой размер"
        },
        {
            "query": "винт M6",
            "expected": "Простой формат",
            "description": "Тип + размер"
        },
        {
            "query": "нужно что-то для крепления",
            "expected": "Сложный запрос",
            "description": "Сложный запрос с неопределенностью"
        },
        {
            "query": "заказать несколько разных болтов",
            "expected": "Сложный запрос",
            "description": "Множественный заказ"
        }
    ]
    
    passed = 0
    total = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🧪 Тест {i}: {test_case['description']}")
        print(f"📝 Запрос: {test_case['query']}")
        
        try:
            # Тестируем анализ сложности
            need_gpt, reason, basic_intent = processor._analyze_query_complexity(test_case['query'])
            
            print(f"🔍 Результат: need_gpt={need_gpt}, reason='{reason}'")
            
            # Проверяем ожидаемый результат
            if "Простой формат" in test_case['expected']:
                expected_need_gpt = False
            else:
                expected_need_gpt = True
            
            if need_gpt == expected_need_gpt:
                print(f"✅ ПРОЙДЕН: {reason}")
                passed += 1
            else:
                print(f"❌ НЕ ПРОЙДЕН: ожидалось need_gpt={expected_need_gpt}")
                
            # Показываем basic_intent для простых запросов
            if not need_gpt and basic_intent:
                print(f"📊 Basic intent: {basic_intent}")
                
        except Exception as e:
            print(f"💥 ОШИБКА: {e}")
    
    print(f"\n📊 ИТОГИ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    return passed == total

if __name__ == "__main__":
    print("🚀 Запуск теста встроенного SmartParser...")
    
    result = test_smart_parser()
    
    if result:
        print("\n🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("Встроенный SmartParser работает корректно")
    else:
        print("\n❌ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ!")
        print("SmartParser требует доработки")
    
    sys.exit(0 if result else 1)
