#!/usr/bin/env python3
"""
Тест встроенного SmartParser для проекта FastenersAI
Тестируем логику определения сложности запроса
"""

import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import types

# Создаем минимальный мок модуля telegram для импортов в MessageProcessor
telegram_mock = types.ModuleType("telegram")

class DummyMessage:
    pass

telegram_mock.Message = DummyMessage
sys.modules['telegram'] = telegram_mock

# Добавляем подмодуль telegram.ext с ContextTypes
telegram_ext = types.ModuleType("telegram.ext")

class ContextTypes:
    class DEFAULT_TYPE:
        pass

telegram_ext.ContextTypes = ContextTypes
sys.modules['telegram.ext'] = telegram_ext
telegram_mock.ext = telegram_ext

# Мок модуля openai, чтобы избежать реальных зависимостей
openai_mock = types.ModuleType("openai")

class AsyncOpenAI:
    def __init__(self, *args, **kwargs):
        pass

openai_mock.AsyncOpenAI = AsyncOpenAI
sys.modules['openai'] = openai_mock

# Мок для dotenv.load_dotenv
dotenv_mock = types.ModuleType("dotenv")

def load_dotenv(*args, **kwargs):
    return None

dotenv_mock.load_dotenv = load_dotenv
sys.modules['dotenv'] = dotenv_mock

# Устанавливаем необходимые переменные окружения для config
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test')
os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('SUPABASE_URL', 'http://localhost')
os.environ.setdefault('SUPABASE_KEY', 'test')

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
            "query": "болт M6 10 шт",
            "expected": "Простой формат",
            "description": "Простой запрос с количеством",
            "expected_quantity": 10
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
                if 'expected_quantity' in test_case:
                    if basic_intent.get('quantity') == test_case['expected_quantity']:
                        print(f"📦 Количество распознано: {basic_intent['quantity']}")
                    else:
                        print(f"❌ Неверное количество: {basic_intent.get('quantity')} (ожидалось {test_case['expected_quantity']})")
                        passed -= 1
                
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
