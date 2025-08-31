#!/usr/bin/env python3
"""
Скрипт для тестирования подключения к Supabase и проверки RLS политик
"""

import asyncio
import logging
from database.supabase_client import init_supabase, save_user_request
from config import SUPABASE_URL, SUPABASE_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """Тестирует подключение к базе данных"""
    print("🔍 Тестирование подключения к Supabase...")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Не настроены переменные окружения SUPABASE_URL и SUPABASE_KEY")
        return False
    
    print(f"📡 URL: {SUPABASE_URL}")
    print(f"🔑 Key: {SUPABASE_KEY[:20]}...")
    
    try:
        await init_supabase()
        print("✅ Подключение к Supabase установлено")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

async def test_save_user_request():
    """Тестирует сохранение запроса пользователя"""
    print("\n💾 Тестирование сохранения запроса пользователя...")
    
    try:
        await save_user_request(
            user_id=12345,
            chat_id=12345,
            request_type="test",
            original_content="тестовый запрос",
            processed_text="тестовый запрос",
            user_intent={"type": "test", "confidence": 0.9}
        )
        print("✅ Запрос успешно сохранен в БД")
        return True
    except Exception as e:
        print(f"❌ Ошибка сохранения: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    print("🚀 Запуск тестирования базы данных\n")
    
    # Тест подключения
    if not await test_database_connection():
        print("\n❌ Не удалось подключиться к базе данных")
        return
    
    # Тест сохранения
    await test_save_user_request()
    
    print("\n📋 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 50)
    
    print("\n🔧 ЕСЛИ ЕСТЬ ОШИБКИ RLS:")
    print("1. Откройте Supabase Dashboard")
    print("2. Перейдите в SQL Editor")
    print("3. Выполните команды из файла database/fix_rls_policies.sql")
    print("4. Или отключите RLS для таблиц бота:")
    print("   ALTER TABLE user_requests DISABLE ROW LEVEL SECURITY;")
    print("   ALTER TABLE file_uploads DISABLE ROW LEVEL SECURITY;")
    
    print("\n📚 ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:")
    print("- Проверьте файл database/fix_rls_policies.sql")
    print("- Проверьте настройки в config.py")
    print("- Убедитесь, что таблицы созданы в Supabase")

if __name__ == "__main__":
    asyncio.run(main())
