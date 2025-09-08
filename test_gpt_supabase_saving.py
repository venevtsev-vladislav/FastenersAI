#!/usr/bin/env python3
"""
Тест сохранения GPT результатов в Supabase
Проверяем, что GPT результаты корректно сохраняются в базу данных
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client_legacy import get_supabase_client_legacy
from railway_logging import setup_railway_logging

async def test_gpt_supabase_saving():
    """Тестируем сохранение GPT результатов в Supabase"""
    
    print("🔍 ТЕСТ СОХРАНЕНИЯ GPT РЕЗУЛЬТАТОВ В SUPABASE")
    print("=" * 60)
    
    # Настраиваем логирование
    setup_railway_logging()
    
    try:
        # Получаем клиент Supabase
        supabase_client = await get_supabase_client_legacy()
        
        if not supabase_client or not supabase_client.client:
            print("❌ Не удалось подключиться к Supabase")
            return
        
        print("✅ Подключение к Supabase установлено")
        
        # Тестовые данные
        test_text = "Анкер с кольцом м8 10х100 (30шт)\nАнкер с кольцом м12 16х130 (10шт)"
        test_gpt_result = {
            "items": [
                {
                    "type": "анкер",
                    "diameter": "M8",
                    "length": "10х100 мм",
                    "material": None,
                    "coating": None,
                    "quantity": "30шт",
                    "confidence": 0.95
                },
                {
                    "type": "анкер",
                    "diameter": "M12",
                    "length": "16х130 мм",
                    "material": None,
                    "coating": None,
                    "quantity": "10шт",
                    "confidence": 0.95
                }
            ]
        }
        
        print(f"📝 Тестовый текст: {test_text}")
        print(f"🤖 GPT результат: {json.dumps(test_gpt_result, ensure_ascii=False, indent=2)}")
        
        # Тестируем сохранение
        print("\n💾 ТЕСТИРУЕМ СОХРАНЕНИЕ В SUPABASE")
        print("-" * 40)
        
        request_id = await supabase_client.create_request_with_gpt_result(
            chat_id="123456789",
            user_id="987654321",
            source="test",
            original_content=test_text,
            gpt_result=test_gpt_result
        )
        
        print(f"✅ Запрос сохранен с ID: {request_id}")
        
        # Проверяем сохранение
        print("\n🔍 ПРОВЕРЯЕМ СОХРАНЕННЫЕ ДАННЫЕ")
        print("-" * 40)
        
        response = supabase_client.client.table('user_requests').select('*').eq('id', request_id).execute()
        
        if response.data:
            record = response.data[0]
            print(f"✅ Запись найдена в базе данных")
            print(f"  ID: {record.get('id')}")
            print(f"  User ID: {record.get('user_id')}")
            print(f"  Chat ID: {record.get('chat_id')}")
            print(f"  Тип: {record.get('request_type')}")
            print(f"  Оригинальный контент: {record.get('original_content')}")
            print(f"  Обработанный текст: {record.get('processed_text')[:200]}...")
            
            # Проверяем user_intent
            user_intent = record.get('user_intent')
            if user_intent:
                try:
                    if isinstance(user_intent, str):
                        user_intent = json.loads(user_intent)
                    
                    print(f"  User Intent:")
                    print(f"    Источник: {user_intent.get('source')}")
                    print(f"    Оригинальный контент: {user_intent.get('original_content')}")
                    print(f"    Время обработки: {user_intent.get('processed_at')}")
                    
                    # Проверяем GPT результат
                    gpt_result_saved = user_intent.get('gpt_result')
                    if gpt_result_saved:
                        print(f"    🎯 GPT результат сохранен:")
                        print(f"      Количество позиций: {len(gpt_result_saved.get('items', []))}")
                        for i, item in enumerate(gpt_result_saved.get('items', []), 1):
                            print(f"      Позиция {i}: {item.get('type')} {item.get('diameter')} {item.get('length')} {item.get('quantity')}")
                    else:
                        print(f"    ❌ GPT результат НЕ найден в user_intent")
                    
                except Exception as json_error:
                    print(f"    ❌ Ошибка парсинга user_intent: {json_error}")
                    print(f"    Raw user_intent: {user_intent}")
            
            print(f"  Создано: {record.get('created_at')}")
            
        else:
            print("❌ Запись не найдена в базе данных")
        
        # Тестируем поиск по GPT результатам
        print("\n🔍 ТЕСТИРУЕМ ПОИСК ПО GPT РЕЗУЛЬТАТАМ")
        print("-" * 40)
        
        # Ищем записи с GPT результатами
        response = supabase_client.client.table('user_requests').select('*').contains('user_intent', {'gpt_result': {'items': []}}).execute()
        
        if response.data:
            print(f"✅ Найдено {len(response.data)} записей с GPT результатами")
            
            for i, record in enumerate(response.data, 1):
                print(f"\n📊 Запись {i}:")
                print(f"  ID: {record.get('id')}")
                print(f"  User ID: {record.get('user_id')}")
                print(f"  Оригинальный контент: {record.get('original_content', '')[:100]}...")
                
                # Парсим user_intent
                user_intent = record.get('user_intent')
                if user_intent:
                    try:
                        if isinstance(user_intent, str):
                            user_intent = json.loads(user_intent)
                        
                        gpt_result = user_intent.get('gpt_result')
                        if gpt_result and 'items' in gpt_result:
                            print(f"  🎯 GPT результат: {len(gpt_result['items'])} позиций")
                            for j, item in enumerate(gpt_result['items'], 1):
                                print(f"    Позиция {j}: {item.get('type')} {item.get('diameter')} {item.get('length')} {item.get('quantity')}")
                        else:
                            print(f"  ❌ GPT результат не найден")
                    
                    except Exception as e:
                        print(f"  ❌ Ошибка парсинга: {e}")
        else:
            print("❌ Записи с GPT результатами не найдены")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_gpt_supabase_saving())
