#!/usr/bin/env python3
"""
Скрипт для проверки состояния таблиц в Supabase
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Загружаем переменные окружения
load_dotenv()

def check_supabase():
    """Проверяет состояние Supabase"""
    
    # Получаем данные подключения
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Ошибка: SUPABASE_URL или SUPABASE_KEY не настроены в .env")
        return
    
    print(f"🔗 Подключаюсь к Supabase: {supabase_url}")
    
    try:
        # Создаем клиент
        supabase: Client = create_client(supabase_url, supabase_key)
        print("✅ Подключение к Supabase установлено")
        
        # Проверяем существующие таблицы
        print("\n📊 Проверяю таблицы...")
        
        # Проверяем aliases
        try:
            response = supabase.table('aliases').select('count', count='exact').execute()
            print(f"📋 aliases: {response.count} записей")
        except Exception as e:
            print(f"❌ aliases: ошибка - {e}")
        
        # Проверяем parts_catalog
        try:
            response = supabase.table('parts_catalog').select('count', count='exact').execute()
            print(f"📦 parts_catalog: {response.count} записей")
        except Exception as e:
            print(f"❌ parts_catalog: ошибка - {e}")
        
        # Проверяем search_suggestions
        try:
            response = supabase.table('search_suggestions').select('count', count='exact').execute()
            print(f"💡 search_suggestions: {response.count} записей")
        except Exception as e:
            print(f"❌ search_suggestions: ошибка - {e}")
        
        # Проверяем user_requests
        try:
            response = supabase.table('user_requests').select('count', count='exact').execute()
            print(f"📝 user_requests: {response.count} записей")
        except Exception as e:
            print(f"❌ user_requests: ошибка - {e}")
        
        # Проверяем file_uploads
        try:
            response = supabase.table('file_uploads').select('count', count='exact').execute()
            print(f"📁 file_uploads: {response.count} записей")
        except Exception as e:
            print(f"❌ file_uploads: ошибка - {e}")
        
        # Проверяем search_history
        try:
            response = supabase.table('search_history').select('count', count='exact').execute()
            print(f"🔍 search_history: {response.count} записей")
        except Exception as e:
            print(f"❌ search_history: ошибка - {e}")
        
        # Проверяем bot_statistics
        try:
            response = supabase.table('bot_statistics').select('count', count='exact').execute()
            print(f"📈 bot_statistics: {response.count} записей")
        except Exception as e:
            print(f"❌ bot_statistics: ошибка - {e}")
        
        print("\n✅ Проверка завершена")
        
    except Exception as e:
        print(f"❌ Ошибка подключения к Supabase: {e}")

if __name__ == "__main__":
    check_supabase()

