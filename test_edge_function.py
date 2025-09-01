#!/usr/bin/env python3
"""
Тест Edge Function для проверки расчета вероятности
"""

import asyncio
import aiohttp
import json
import logging
from config import SUPABASE_URL, SUPABASE_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_edge_function():
    """Тестирует Edge Function с данными из логов"""
    
    # Данные из логов пользователя
    test_data = {
        "search_query": "винт мебельный 640 оцинкованный",
        "user_intent": {
            "type": "винт мебельный",
            "diameter": "6",
            "length": "40",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "200 шт",
            "confidence": 0.9
        }
    }
    
    edge_function_url = f"{SUPABASE_URL}/functions/v1/fastener-search"
    headers = {
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(edge_function_url, json=test_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get('results', [])
                    
                    print(f"✅ Edge Function вернул {len(results)} результатов")
                    
                    # Анализируем первые 3 результата
                    for i, result in enumerate(results[:3]):
                        print(f"\n--- Результат {i+1} ---")
                        print(f"Название: {result.get('name', 'N/A')}")
                        print(f"SKU: {result.get('sku', 'N/A')}")
                        print(f"Вероятность: {result.get('probability_percent', 'N/A')}%")
                        print(f"Релевантность: {result.get('relevance_score', 'N/A')}")
                        print(f"Причина совпадения: {result.get('match_reason', 'N/A')}")
                        
                        # Детальная информация о совпадениях
                        if 'explanation' in result:
                            print("Объяснение совпадений:")
                            for line in result['explanation'].split('\n'):
                                if line.strip():
                                    print(f"  {line}")
                        
                        if 'matched_tokens' in result:
                            print(f"Совпавшие токены: {result['matched_tokens']}")
                    
                else:
                    error_text = await response.text()
                    print(f"❌ Edge Function вернул ошибку {response.status}: {error_text}")
                    
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_function())
