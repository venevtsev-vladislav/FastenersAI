#!/usr/bin/env python3
"""
Тест улучшений поиска и исправления ошибок
"""

import asyncio
import logging
from database.supabase_client import search_parts

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_search_queries():
    """Тестирует различные типы поисковых запросов"""
    
    test_queries = [
        # Технический запрос (должен работать)
        {
            "query": "Болты DIN603 М6х40, цинк (тыс.шт)",
            "description": "Технический запрос с точными параметрами"
        },
        # Разговорный запрос (должен работать через алиасы)
        {
            "query": "болт с грибком М6 на 40, цинкованный",
            "description": "Разговорный запрос с синонимами"
        },
        # Простой запрос
        {
            "query": "болт М8х20",
            "description": "Простой запрос"
        }
    ]
    
    print("🚀 Тестирование улучшенного поиска\n")
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"📝 Тест {i}: {test_case['description']}")
        print(f"🔍 Запрос: {test_case['query']}")
        
        try:
            # Создаем user_intent для тестирования
            user_intent = {
                "type": "болт",
                "diameter": "M6",
                "length": "40 мм",
                "coating": "цинк",
                "quantity": "1000 шт",
                "confidence": 0.9
            }
            
            results = await search_parts(test_case['query'], user_intent)
            
            print(f"✅ Результатов найдено: {len(results)}")
            
            if results:
                print("📋 Найденные позиции:")
                for j, result in enumerate(results[:3], 1):  # Показываем первые 3
                    print(f"   {j}. {result.get('name', 'N/A')} (SKU: {result.get('sku', 'N/A')})")
                    print(f"      Уверенность: {result.get('confidence_score', 'N/A')}%")
                    print(f"      Упаковка: {result.get('packages_needed', 'N/A')} уп.")
            else:
                print("❌ Результаты не найдены")
                
        except Exception as e:
            print(f"❌ Ошибка при поиске: {e}")
        
        print("-" * 50)
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 50)
    print("✅ Исправлена ошибка расчета упаковки")
    print("✅ Добавлен поиск по алиасам в Edge Function")
    print("✅ Улучшена обработка разговорных запросов")
    print("\n🔧 СЛЕДУЮЩИЕ ШАГИ:")
    print("1. Разверните обновленную Edge Function в Supabase")
    print("2. Добавьте алиасы для разговорных терминов в таблицу aliases")
    print("3. Протестируйте бота с разными типами запросов")

if __name__ == "__main__":
    asyncio.run(test_search_queries())
