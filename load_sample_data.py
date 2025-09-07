"""
Скрипт для загрузки тестовых данных в Supabase
"""

import asyncio
import logging
from database.supabase_client_v2 import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def load_sample_data():
    """Загружает тестовые данные в Supabase"""
    try:
        client = await get_supabase_client()
        
        if not client.client:
            logger.error("Supabase client not initialized")
            return
        
        # Загружаем тестовые товары
        items_data = [
            {
                'ku': 'BOLT-M10x30-8.8',
                'name': 'Болт DIN 933 кл.пр.8.8 М10х30, цинк',
                'pack_qty': 100,
                'price': 2.50,
                'is_active': True,
                'specs_json': {
                    'diameter': 'M10',
                    'length': '30',
                    'strength_class': '8.8',
                    'coating': 'цинк'
                }
            },
            {
                'ku': 'BOLT-M12x40-8.8',
                'name': 'Болт DIN 933 кл.пр.8.8 М12х40, цинк',
                'pack_qty': 50,
                'price': 3.20,
                'is_active': True,
                'specs_json': {
                    'diameter': 'M12',
                    'length': '40',
                    'strength_class': '8.8',
                    'coating': 'цинк'
                }
            },
            {
                'ku': 'ANCHOR-M10x100',
                'name': 'Анкер клиновой оцинк. М10х100',
                'pack_qty': 25,
                'price': 15.80,
                'is_active': True,
                'specs_json': {
                    'diameter': 'M10',
                    'length': '100',
                    'type': 'клиновой',
                    'coating': 'оцинк'
                }
            },
            {
                'ku': 'ANCHOR-M12x120',
                'name': 'Анкер клиновой оцинк. М12х120',
                'pack_qty': 20,
                'price': 18.50,
                'is_active': True,
                'specs_json': {
                    'diameter': 'M12',
                    'length': '120',
                    'type': 'клиновой',
                    'coating': 'оцинк'
                }
            }
        ]
        
        # Вставляем товары
        for item in items_data:
            try:
                response = client.client.table('items').insert(item).execute()
                logger.info(f"Inserted item: {item['ku']}")
            except Exception as e:
                logger.warning(f"Item {item['ku']} might already exist: {e}")
        
        # Загружаем алиасы
        aliases_data = [
            {'alias': 'болт м10х30', 'ku': 'BOLT-M10x30-8.8', 'weight': 1.0},
            {'alias': 'болт din 933 м10х30', 'ku': 'BOLT-M10x30-8.8', 'weight': 1.0},
            {'alias': 'болт м12х40', 'ku': 'BOLT-M12x40-8.8', 'weight': 1.0},
            {'alias': 'болт din 933 м12х40', 'ku': 'BOLT-M12x40-8.8', 'weight': 1.0},
            {'alias': 'анкер м10х100', 'ku': 'ANCHOR-M10x100', 'weight': 1.0},
            {'alias': 'анкер клиновой м10х100', 'ku': 'ANCHOR-M10x100', 'weight': 1.0},
            {'alias': 'анкер м12х120', 'ku': 'ANCHOR-M12x120', 'weight': 1.0},
            {'alias': 'анкер клиновой м12х120', 'ku': 'ANCHOR-M12x120', 'weight': 1.0}
        ]
        
        # Вставляем алиасы
        for alias in aliases_data:
            try:
                response = client.client.table('sku_aliases').insert(alias).execute()
                logger.info(f"Inserted alias: {alias['alias']} -> {alias['ku']}")
            except Exception as e:
                logger.warning(f"Alias {alias['alias']} might already exist: {e}")
        
        logger.info("✅ Sample data loaded successfully!")
        
    except Exception as e:
        logger.error(f"Error loading sample data: {e}")

if __name__ == "__main__":
    asyncio.run(load_sample_data())
