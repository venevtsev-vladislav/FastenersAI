#!/usr/bin/env python3
"""
Анализ данных в Supabase
Проверяем что сохраняется и что находится в базе данных
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

async def analyze_supabase_data():
    """Анализируем данные в Supabase"""
    
    print("🔍 АНАЛИЗ ДАННЫХ В SUPABASE")
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
        
        # 1. Анализируем таблицу user_requests
        print("\n📊 АНАЛИЗ ТАБЛИЦЫ user_requests")
        print("-" * 40)
        
        try:
            response = supabase_client.client.table('user_requests').select('*').order('created_at', desc=True).limit(10).execute()
            
            if response.data:
                print(f"✅ Найдено {len(response.data)} записей в user_requests")
                
                for i, record in enumerate(response.data, 1):
                    print(f"\n📝 Запись {i}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  User ID: {record.get('user_id')}")
                    print(f"  Chat ID: {record.get('chat_id')}")
                    print(f"  Тип: {record.get('request_type')}")
                    print(f"  Оригинальный контент: {record.get('original_content', '')[:100]}...")
                    print(f"  Обработанный текст: {record.get('processed_text', '')[:100]}...")
                    
                    # Парсим user_intent
                    user_intent = record.get('user_intent')
                    if user_intent:
                        try:
                            if isinstance(user_intent, str):
                                user_intent = json.loads(user_intent)
                            print(f"  User Intent: {json.dumps(user_intent, ensure_ascii=False, indent=2)}")
                        except:
                            print(f"  User Intent: {user_intent}")
                    
                    print(f"  Создано: {record.get('created_at')}")
            else:
                print("❌ Нет данных в user_requests")
                
        except Exception as e:
            print(f"❌ Ошибка при чтении user_requests: {e}")
        
        # 2. Анализируем таблицу parts_catalog
        print("\n📊 АНАЛИЗ ТАБЛИЦЫ parts_catalog")
        print("-" * 40)
        
        try:
            response = supabase_client.client.table('parts_catalog').select('*').limit(10).execute()
            
            if response.data:
                print(f"✅ Найдено {len(response.data)} записей в parts_catalog")
                
                for i, record in enumerate(response.data, 1):
                    print(f"\n🔧 Деталь {i}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  SKU: {record.get('sku')}")
                    print(f"  Название: {record.get('name')}")
                    print(f"  Тип: {record.get('type')}")
                    print(f"  Упаковка: {record.get('pack_size')}")
                    print(f"  Единица: {record.get('unit')}")
                    print(f"  Создано: {record.get('created_at')}")
            else:
                print("❌ Нет данных в parts_catalog")
                
        except Exception as e:
            print(f"❌ Ошибка при чтении parts_catalog: {e}")
        
        # 3. Анализируем таблицу aliases
        print("\n📊 АНАЛИЗ ТАБЛИЦЫ aliases")
        print("-" * 40)
        
        try:
            response = supabase_client.client.table('aliases').select('*').limit(10).execute()
            
            if response.data:
                print(f"✅ Найдено {len(response.data)} записей в aliases")
                
                for i, record in enumerate(response.data, 1):
                    print(f"\n🏷️ Алиас {i}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  Алиас: {record.get('alias')}")
                    print(f"  Maps to: {record.get('maps_to')}")
                    print(f"  Уверенность: {record.get('confidence')}")
                    print(f"  Создано: {record.get('created_at')}")
            else:
                print("❌ Нет данных в aliases")
                
        except Exception as e:
            print(f"❌ Ошибка при чтении aliases: {e}")
        
        # 4. Проверяем новые таблицы (если они существуют)
        print("\n📊 ПРОВЕРКА НОВЫХ ТАБЛИЦ")
        print("-" * 40)
        
        new_tables = ['requests', 'request_lines', 'candidates', 'items', 'sku_aliases']
        
        for table_name in new_tables:
            try:
                response = supabase_client.client.table(table_name).select('count').execute()
                print(f"✅ Таблица {table_name} существует")
            except Exception as e:
                print(f"❌ Таблица {table_name} не существует: {e}")
        
        # 5. Анализируем последние запросы пользователя
        print("\n📊 АНАЛИЗ ПОСЛЕДНИХ ЗАПРОСОВ ПОЛЬЗОВАТЕЛЯ")
        print("-" * 40)
        
        try:
            # Ищем последние запросы от конкретного пользователя
            response = supabase_client.client.table('user_requests').select('*').eq('user_id', '225663491').order('created_at', desc=True).limit(5).execute()
            
            if response.data:
                print(f"✅ Найдено {len(response.data)} записей от пользователя 225663491")
                
                for i, record in enumerate(response.data, 1):
                    print(f"\n👤 Запрос пользователя {i}:")
                    print(f"  ID: {record.get('id')}")
                    print(f"  Тип: {record.get('request_type')}")
                    print(f"  Оригинальный контент: {record.get('original_content', '')}")
                    print(f"  Обработанный текст: {record.get('processed_text', '')}")
                    
                    # Детальный анализ user_intent
                    user_intent = record.get('user_intent')
                    if user_intent:
                        try:
                            if isinstance(user_intent, str):
                                user_intent = json.loads(user_intent)
                            
                            print(f"  User Intent JSON:")
                            print(f"    {json.dumps(user_intent, ensure_ascii=False, indent=4)}")
                            
                            # Если это GPT результат
                            if 'items' in user_intent:
                                print(f"  🎯 GPT Результат: {len(user_intent['items'])} позиций")
                                for j, item in enumerate(user_intent['items'], 1):
                                    print(f"    Позиция {j}: {item.get('type')} {item.get('diameter')} {item.get('length')} {item.get('quantity')}")
                            
                        except Exception as json_error:
                            print(f"  User Intent (raw): {user_intent}")
                    
                    print(f"  Создано: {record.get('created_at')}")
            else:
                print("❌ Нет записей от пользователя 225663491")
                
        except Exception as e:
            print(f"❌ Ошибка при анализе запросов пользователя: {e}")
        
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    print("\n🎉 АНАЛИЗ ЗАВЕРШЕН!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(analyze_supabase_data())
