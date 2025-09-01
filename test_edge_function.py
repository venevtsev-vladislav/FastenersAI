#!/usr/bin/env python3
"""
Тест для прямого POST запроса к Edge Function
"""

import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

async def test_edge_function():
    """Тестирует Edge Function напрямую"""
    print("🧪 Тестирую Edge Function напрямую...")
    
    # URL Edge Function
    supabase_url = os.getenv('SUPABASE_URL')
    edge_function_url = f"{supabase_url}/functions/v1/fastener-search"
    
    # API ключ
    api_key = os.getenv('SUPABASE_KEY')
    
    # Тестовые запросы
    test_cases = [
        {
            "name": "DIN 603 Винт мебельный 6 × 40 Zn — 200 шт",
            "search_query": "DIN 603 Винт мебельный 6 × 40 Zn — 200 шт",
            "user_intent": {
                "type": "винт",
                "standard": "DIN 603",
                "diameter": "6",
                "length": "40",
                "coating": "цинк"
            }
        },
        {
            "name": "Винт мебельный 640 оцинкованный",
            "search_query": "винт мебельный 640 оцинкованный",
            "user_intent": {
                "type": "винт",
                "diameter": "6",
                "length": "40",
                "coating": "оцинкованный"
            }
        },
        {
            "name": "Болт DIN 965 M8x20 оцинкованный",
            "search_query": "Болт DIN 965 M8x20 оцинкованный",
            "user_intent": {
                "type": "болт",
                "standard": "DIN 965",
                "diameter": "M8",
                "length": "20",
                "coating": "оцинкованный"
            }
        }
    ]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with aiohttp.ClientSession() as session:
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*60}")
            print(f"🧪 ТЕСТ {i}: {test_case['name']}")
            print(f"{'='*60}")
            
            payload = {
                "search_query": test_case["search_query"],
                "user_intent": test_case["user_intent"]
            }
            
            print(f"📤 Отправляю запрос:")
            print(f"   URL: {edge_function_url}")
            print(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
            
            try:
                async with session.post(edge_function_url, json=payload, headers=headers) as response:
                    print(f"📥 Получен ответ: {response.status}")
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        print(f"✅ Успешно! Найдено результатов: {len(data.get('results', []))}")
                        
                        # Анализируем первые 3 результата
                        results = data.get('results', [])
                        for j, result in enumerate(results[:3], 1):
                            print(f"\n📊 Результат {j}:")
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
                        if probabilities:
                            print(f"\n📈 Статистика вероятностей:")
                            print(f"   Минимальная: {min(probabilities)}%")
                            print(f"   Максимальная: {max(probabilities)}%")
                            print(f"   Средняя: {sum(probabilities) / len(probabilities):.1f}%")
                        
                    else:
                        error_text = await response.text()
                        print(f"❌ Ошибка {response.status}: {error_text}")
                        
            except Exception as e:
                print(f"❌ Ошибка при запросе: {e}")
    
    print(f"\n{'='*60}")
    print("✅ Тестирование завершено!")
    print(f"{'='*60}")

if __name__ == "__main__":
    asyncio.run(test_edge_function())
