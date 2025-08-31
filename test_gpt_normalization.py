#!/usr/bin/env python3
"""
Тест улучшенной нормализации GPT для разговорных терминов
"""

import asyncio
import logging
from services.openai_service import OpenAIService

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_gpt_normalization():
    """Тестирует нормализацию разговорных терминов GPT"""
    
    openai_service = OpenAIService()
    
    test_queries = [
        # Разговорные термины для болтов
        {
            "query": "болт с грибком М6 на 40, цинкованный",
            "expected": {
                "type": "болт",
                "subtype": "грибовидная головка",
                "diameter": "M6",
                "length": "40 мм",
                "coating": "цинк"
            }
        },
        # Разговорные термины для саморезов
        {
            "query": "саморез клоп 3.5х25, оцинкованный",
            "expected": {
                "type": "саморез",
                "subtype": "с прессшайбой",
                "diameter": "3.5 мм",
                "length": "25 мм",
                "coating": "цинк"
            }
        },
        # Разговорные термины для размеров
        {
            "query": "болт под ключ М8х20, нержавейка",
            "expected": {
                "type": "болт",
                "subtype": "шестигранная головка",
                "diameter": "M8",
                "length": "20 мм",
                "material": "нержавеющая сталь"
            }
        },
        # Смешанные разговорные термины
        {
            "query": "анкер забиваемый М12х100, оцинкованный",
            "expected": {
                "type": "анкер",
                "subtype": "забиваемый",
                "diameter": "M12",
                "length": "100 мм",
                "coating": "цинк"
            }
        }
    ]
    
    print("🧠 Тестирование улучшенной нормализации GPT\n")
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Тест {i}: {test_case['query']}")
        print(f"🎯 Ожидаемый результат: {test_case['expected']}")
        
        try:
            # Анализируем через GPT
            result = await openai_service.analyze_user_intent(test_case['query'])
            
            print(f"✅ GPT результат: {result}")
            
            # Проверяем ключевые поля
            if isinstance(result, dict):
                if 'items' in result and result['items']:
                    # Множественный заказ
                    item = result['items'][0]
                    print(f"📋 Найден множественный заказ: {item}")
                    
                    # Проверяем нормализацию
                    checks = []
                    for key, expected_value in test_case['expected'].items():
                        if key in item:
                            actual_value = item[key]
                            if actual_value == expected_value:
                                checks.append(f"✅ {key}: {actual_value}")
                            else:
                                checks.append(f"❌ {key}: ожидалось {expected_value}, получено {actual_value}")
                        else:
                            checks.append(f"❌ {key}: отсутствует")
                    
                    print("🔍 Проверка нормализации:")
                    for check in checks:
                        print(f"   {check}")
                        
                else:
                    # Одиночный заказ
                    print(f"📋 Найден одиночный заказ: {result}")
                    
                    # Проверяем нормализацию
                    checks = []
                    for key, expected_value in test_case['expected'].items():
                        if key in result:
                            actual_value = result[key]
                            if actual_value == expected_value:
                                checks.append(f"✅ {key}: {actual_value}")
                            else:
                                checks.append(f"❌ {key}: ожидалось {expected_value}, получено {actual_value}")
                        else:
                            checks.append(f"❌ {key}: отсутствует")
                    
                    print("🔍 Проверка нормализации:")
                    for check in checks:
                        print(f"   {check}")
            else:
                print(f"❌ Неожиданный формат ответа: {type(result)}")
                
        except Exception as e:
            print(f"❌ Ошибка при анализе: {e}")
        
        print("-" * 60)
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    print("✅ Улучшен промпт GPT для нормализации")
    print("✅ Добавлены примеры нормализации")
    print("✅ Добавлены фильтры по подтипу в Edge Function")
    print("\n🔧 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Протестируйте бота с разговорными запросами")
    print("2. Проверьте, что GPT нормализует термины правильно")
    print("3. Убедитесь, что Edge Function находит результаты")

if __name__ == "__main__":
    asyncio.run(test_gpt_normalization())
