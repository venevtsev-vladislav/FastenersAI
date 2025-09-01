#!/usr/bin/env python3
"""
Тест для конкретного запроса: DIN 603 Винт мебельный 6 × 40 Zn — 200 шт
"""

import asyncio
import json
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_specific_query():
    """Тестирует конкретный запрос"""
    print("🧪 Тестирую запрос: DIN 603 Винт мебельный 6 × 40 Zn — 200 шт")
    
    try:
        # Импортируем необходимые модули
        from database.supabase_client import search_parts
        
        # Тестовый запрос
        test_query = "DIN 603 Винт мебельный 6 × 40 Zn — 200 шт"
        
        print(f"📝 Запрос: {test_query}")
        print("🔍 Выполняю поиск...")
        
        # Выполняем поиск
        results = await search_parts(
            query=test_query,
            user_intent={}
        )
        
        if not results:
            print("❌ Результаты не найдены")
            return
        
        print(f"✅ Найдено результатов: {len(results)}")
        
        # Анализируем первые 5 результатов
        for i, result in enumerate(results[:5], 1):
            print(f"\n📊 Результат {i}:")
            print(f"   Название: {result.get('name', 'N/A')}")
            print(f"   SKU: {result.get('sku', 'N/A')}")
            print(f"   probability_percent: {result.get('probability_percent', 'N/A')}%")
            print(f"   relevance_score: {result.get('relevance_score', 'N/A')}")
            print(f"   match_reason: {result.get('match_reason', 'N/A')}")
            
            # Проверяем explanation
            explanation = result.get('explanation', '')
            if explanation:
                print(f"   explanation:")
                for line in explanation.split('\n'):
                    if line.strip():
                        print(f"     {line}")
            
            # Проверяем matched_tokens
            matched_tokens = result.get('matched_tokens', [])
            if matched_tokens:
                print(f"   matched_tokens: {matched_tokens}")
        
        # Статистика по вероятностям
        probabilities = [r.get('probability_percent', 0) for r in results]
        print(f"\n📈 Статистика вероятностей:")
        print(f"   Минимальная: {min(probabilities)}%")
        print(f"   Максимальная: {max(probabilities)}%")
        print(f"   Средняя: {sum(probabilities) / len(probabilities):.1f}%")
        
        # Анализ ожидаемых совпадений для этого запроса
        print(f"\n🔍 Ожидаемые совпадения для 'DIN 603 Винт мебельный 6 × 40 Zn':")
        print(f"   ✅ Стандарт DIN: DIN 603 (40% веса)")
        print(f"   ✅ Тип детали: Винт (25% веса)")
        print(f"   ✅ Размеры: 6 × 40 (30% веса)")
        print(f"   ✅ Покрытие: Zn (15% веса)")
        print(f"   🎯 Бонус за стандарт + размеры: +15%")
        print(f"   🎯 Бонус за тип + размеры: +10%")
        print(f"   🎯 Бонус за полное совпадение: +20%")
        print(f"   📊 Ожидаемая вероятность: ~100% (40+25+30+15+15+10+20 = 155%, ограничено до 100%)")
        
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_query())
