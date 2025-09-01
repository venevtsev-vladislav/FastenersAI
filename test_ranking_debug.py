#!/usr/bin/env python3
"""
Тест для отладки системы ранжирования
"""

import asyncio
import json
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_ranking_system():
    """Тестирует систему ранжирования"""
    print("🧪 Тестирую систему ранжирования...")
    
    try:
        # Импортируем необходимые модули
        from database.supabase_client import search_parts
        
        # Тестовые запросы
        test_queries = [
            {
                "query": "Болт DIN 965 M8x20 оцинкованный",
                "expected_min_probability": 80,
                "description": "Полное совпадение (стандарт + размеры + тип + покрытие)"
            },
            {
                "query": "Винт M6x30",
                "expected_min_probability": 50,
                "description": "Совпадение типа и размеров"
            },
            {
                "query": "Гайка",
                "expected_max_probability": 40,
                "description": "Только тип детали"
            }
        ]
        
        for i, test_case in enumerate(test_queries, 1):
            print(f"\n--- Тест {i}: {test_case['description']} ---")
            print(f"Запрос: {test_case['query']}")
            
            # Выполняем поиск
            results = await search_parts(
                query=test_case['query'],
                user_intent={}
            )
            
            if not results:
                print("❌ Результаты не найдены")
                continue
            
            print(f"✅ Найдено результатов: {len(results)}")
            
            # Анализируем первый результат
            first_result = results[0]
            print(f"📊 Первый результат:")
            print(f"   Название: {first_result.get('name', 'N/A')}")
            print(f"   SKU: {first_result.get('sku', 'N/A')}")
            print(f"   probability_percent: {first_result.get('probability_percent', 'N/A')}")
            print(f"   relevance_score: {first_result.get('relevance_score', 'N/A')}")
            print(f"   match_reason: {first_result.get('match_reason', 'N/A')}")
            
            # Проверяем explanation
            explanation = first_result.get('explanation', '')
            if explanation:
                print(f"   explanation: {explanation[:200]}...")
            
            # Проверяем matched_tokens
            matched_tokens = first_result.get('matched_tokens', [])
            if matched_tokens:
                print(f"   matched_tokens: {matched_tokens}")
            
            # Проверяем ожидания
            probability = first_result.get('probability_percent', 0)
            if 'expected_min_probability' in test_case:
                if probability >= test_case['expected_min_probability']:
                    print(f"✅ Вероятность {probability}% >= ожидаемого минимума {test_case['expected_min_probability']}%")
                else:
                    print(f"❌ Вероятность {probability}% < ожидаемого минимума {test_case['expected_min_probability']}%")
            
            if 'expected_max_probability' in test_case:
                if probability <= test_case['expected_max_probability']:
                    print(f"✅ Вероятность {probability}% <= ожидаемого максимума {test_case['expected_max_probability']}%")
                else:
                    print(f"❌ Вероятность {probability}% > ожидаемого максимума {test_case['expected_max_probability']}%")
            
            # Показываем топ-3 результата
            print(f"📈 Топ-3 результата:")
            for j, result in enumerate(results[:3], 1):
                print(f"   {j}. {result.get('name', 'N/A')} - {result.get('probability_percent', 'N/A')}%")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ranking_system())
