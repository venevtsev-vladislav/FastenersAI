#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Edge Function напрямую
"""

import requests
import json
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

def test_edge_function():
    """Тестируем Edge Function напрямую"""
    
    # URL Edge Function (замените на ваш)
    edge_function_url = "https://your-project.supabase.co/functions/v1/fastener-search"
    
    # Тестовые данные
    test_cases = [
        {
            "name": "Тест 1: Болт с user_intent",
            "data": {
                "search_query": "болт с грибком М6 на 40, цинкованный",
                "user_intent": {
                    "type": "болт",
                    "diameter": "M6",
                    "length": "40 мм",
                    "coating": "цинк"
                }
            }
        },
        {
            "name": "Тест 2: Только search_query",
            "data": {
                "search_query": "болт М6 40 цинк",
                "user_intent": {}
            }
        },
        {
            "name": "Тест 3: Пустой user_intent",
            "data": {
                "search_query": "болт М6 40 цинк",
                "user_intent": None
            }
        }
    ]
    
    print("🧪 Тестируем Edge Function...")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 {test_case['name']}")
        print(f"📤 Отправляем данные: {json.dumps(test_case['data'], ensure_ascii=False, indent=2)}")
        
        try:
            # Отправляем запрос
            response = requests.post(
                edge_function_url,
                json=test_case['data'],
                headers={
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {os.getenv("SUPABASE_ANON_KEY")}'
                },
                timeout=30
            )
            
            print(f"📥 Статус ответа: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Результат: {len(result.get('results', []))} найденных позиций")
                
                if result.get('results'):
                    print("📋 Первые результаты:")
                    for j, item in enumerate(result['results'][:3], 1):
                        print(f"  {j}. {item.get('name', 'N/A')} (SKU: {item.get('sku', 'N/A')})")
                else:
                    print("❌ Результатов не найдено")
            else:
                print(f"❌ Ошибка: {response.text}")
                
        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
        
        print("-" * 30)

def test_supabase_direct():
    """Тестируем Supabase напрямую"""
    
    from supabase import create_client, Client
    
    print("\n🔍 Тестируем Supabase напрямую...")
    print("=" * 50)
    
    try:
        # Создаем клиент
        supabase: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        
        # Тестовые запросы
        test_queries = [
            "SELECT * FROM parts_catalog WHERE name ILIKE '%болт%' LIMIT 5",
            "SELECT * FROM parts_catalog WHERE name ILIKE '%M6%' LIMIT 5",
            "SELECT * FROM parts_catalog WHERE name ILIKE '%цинк%' LIMIT 5"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Выполняем запрос: {query}")
            
            try:
                result = supabase.rpc('exec_sql', {'sql_query': query}).execute()
                print(f"✅ Результат: {len(result.data)} строк")
                
                if result.data:
                    for row in result.data[:3]:
                        print(f"  - {row.get('name', 'N/A')}")
                        
            except Exception as e:
                print(f"❌ Ошибка запроса: {e}")
                
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")

if __name__ == "__main__":
    print("🚀 Запуск тестирования Edge Function и Supabase")
    
    # Тестируем Edge Function
    test_edge_function()
    
    # Тестируем Supabase напрямую
    test_supabase_direct()
    
    print("\n✅ Тестирование завершено!")
