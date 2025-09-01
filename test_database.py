#!/usr/bin/env python3
"""
Тест базы данных
"""
import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Тестируем базу данных"""
    try:
        # Инициализируем Supabase
        from database.supabase_client import init_supabase
        await init_supabase()
        
        # Получаем клиент
        from database.supabase_client import _supabase_client
        
        if not _supabase_client:
            logger.error("❌ Supabase не инициализирован")
            return
        
        # Проверяем количество записей
        response = _supabase_client.table('parts_catalog').select('*', count='exact').limit(1).execute()
        count = response.count
        logger.info(f"📊 Всего записей в базе: {count}")
        
        # Получаем несколько примеров
        response = _supabase_client.table('parts_catalog').select('name, sku, type').limit(5).execute()
        examples = response.data
        
        logger.info("📋 Примеры записей:")
        for i, item in enumerate(examples, 1):
            logger.info(f"  {i}. {item.get('name', 'N/A')} (SKU: {item.get('sku', 'N/A')})")
        
        # Ищем болты
        response = _supabase_client.table('parts_catalog').select('name, sku').ilike('name', '%болт%').limit(3).execute()
        bolts = response.data
        
        logger.info(f"🔩 Найдено болтов: {len(bolts)}")
        for bolt in bolts:
            logger.info(f"  - {bolt.get('name', 'N/A')}")
        
        # Ищем винты
        response = _supabase_client.table('parts_catalog').select('name, sku').ilike('name', '%винт%').limit(3).execute()
        screws = response.data
        
        logger.info(f"🔩 Найдено винтов: {len(screws)}")
        for screw in screws:
            logger.info(f"  - {screw.get('name', 'N/A')}")
            
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании базы: {e}")

if __name__ == "__main__":
    asyncio.run(test_database())
