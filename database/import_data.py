#!/usr/bin/env python3
"""
Скрипт для импорта данных в Supabase
Импортирует aliases и normalized_skus из JSON файлов
"""

import json
import logging
import asyncio
from pathlib import Path
from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SupabaseImporter:
    def __init__(self):
        """Инициализация подключения к Supabase"""
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("SUPABASE_URL и SUPABASE_KEY должны быть настроены в .env")
        
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Подключение к Supabase установлено")
    
    async def import_aliases(self, file_path: str):
        """Импорт алиасов из JSONL файла"""
        logger.info(f"Импортирую алиасы из {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                aliases_data = []
                
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Подготовка данных для вставки
                        alias_record = {
                            'alias': data['alias'],
                            'maps_to': data['maps_to'],
                            'source_url': data.get('source_url'),
                            'confidence': data.get('confidence', 0.8),
                            'notes': data.get('notes')
                        }
                        
                        aliases_data.append(alias_record)
                        
                        # Вставляем пакетами по 100 записей
                        if len(aliases_data) >= 100:
                            await self._insert_aliases_batch(aliases_data)
                            aliases_data = []
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ошибка парсинга строки {line_num}: {e}")
                        continue
                
                # Вставляем оставшиеся записи
                if aliases_data:
                    await self._insert_aliases_batch(aliases_data)
                
                logger.info("Импорт алиасов завершен")
                
        except FileNotFoundError:
            logger.error(f"Файл {file_path} не найден")
        except Exception as e:
            logger.error(f"Ошибка при импорте алиасов: {e}")
    
    async def _insert_aliases_batch(self, aliases_data: list):
        """Вставка пакета алиасов"""
        try:
            response = self.supabase.table('aliases').insert(aliases_data).execute()
            logger.info(f"Вставлено {len(aliases_data)} алиасов")
        except Exception as e:
            logger.error(f"Ошибка при вставке пакета алиасов: {e}")
    
    async def import_normalized_skus(self, file_path: str):
        """Импорт нормализованных SKU из JSONL файла"""
        logger.info(f"Импортирую нормализованные SKU из {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                skus_data = []
                
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # Извлекаем размеры из названия
                        diameter, length = self._extract_dimensions(data['name'])
                        
                        # Подготовка данных для вставки
                        sku_record = {
                            'sku': data['sku'],
                            'name': data['name'],
                            'type': data['type'],
                            'diameter': diameter,
                            'length': length,
                            'pack_size': data.get('pack_size'),
                            'unit': data.get('unit', 'шт')
                        }
                        
                        skus_data.append(sku_record)
                        
                        # Вставляем пакетами по 100 записей
                        if len(skus_data) >= 100:
                            await self._insert_skus_batch(skus_data)
                            skus_data = []
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Ошибка парсинга строки {line_num}: {e}")
                        continue
                
                # Вставляем оставшиеся записи
                if skus_data:
                    await self._insert_skus_batch(skus_data)
                
                logger.info("Импорт нормализованных SKU завершен")
                
        except FileNotFoundError:
            logger.error(f"Файл {file_path} не найден")
        except Exception as e:
            logger.error(f"Ошибка при импорте SKU: {e}")
    
    async def _insert_skus_batch(self, skus_data: list):
        """Вставка пакета SKU"""
        try:
            response = self.supabase.table('parts_catalog').insert(skus_data).execute()
            logger.info(f"Вставлено {len(skus_data)} SKU")
        except Exception as e:
            logger.error(f"Ошибка при вставке пакета SKU: {e}")
    
    def _extract_dimensions(self, name: str) -> tuple:
        """Извлекает диаметр и длину из названия детали"""
        diameter = None
        length = None
        
        # Поиск диаметра (М8, М10, М12 и т.д.)
        import re
        diameter_match = re.search(r'М(\d+(?:\.\d+)?)', name)
        if diameter_match:
            diameter = f"М{diameter_match.group(1)}"
        
        # Поиск длины (20, 25, 30 и т.д.)
        length_match = re.search(r'(\d+)мм?', name)
        if length_match:
            length = length_match.group(1)
        
        return diameter, length
    
    async def create_search_suggestions(self):
        """Создание базовых подсказок для поиска"""
        logger.info("Создаю базовые подсказки для поиска")
        
        suggestions = [
            {'suggestion': 'болт М8х20', 'category': 'болты', 'popularity': 100},
            {'suggestion': 'гайка шестигранная М10', 'category': 'гайки', 'popularity': 90},
            {'suggestion': 'шайба пружинная', 'category': 'шайбы', 'popularity': 85},
            {'suggestion': 'анкер М12х100', 'category': 'анкеры', 'popularity': 80},
            {'suggestion': 'саморез клоп', 'category': 'саморезы', 'popularity': 75},
            {'suggestion': 'дюбель распорный', 'category': 'дюбели', 'popularity': 70},
            {'suggestion': 'винт потайной', 'category': 'винты', 'popularity': 65},
            {'suggestion': 'шуруп по дереву', 'category': 'шурупы', 'popularity': 60}
        ]
        
        try:
            response = self.supabase.table('search_suggestions').insert(suggestions).execute()
            logger.info(f"Создано {len(suggestions)} подсказок для поиска")
        except Exception as e:
            logger.error(f"Ошибка при создании подсказок: {e}")
    
    async def verify_import(self):
        """Проверка результатов импорта"""
        logger.info("Проверяю результаты импорта...")
        
        try:
            # Проверяем количество алиасов
            aliases_count = self.supabase.table('aliases').select('count', count='exact').execute()
            logger.info(f"Алиасов в базе: {aliases_count.count}")
            
            # Проверяем количество SKU
            skus_count = self.supabase.table('parts_catalog').select('count', count='exact').execute()
            logger.info(f"SKU в базе: {skus_count.count}")
            
            # Проверяем подсказки
            suggestions_count = self.supabase.table('search_suggestions').select('count', count='exact').execute()
            logger.info(f"Подсказок в базе: {suggestions_count.count}")
            
        except Exception as e:
            logger.error(f"Ошибка при проверке импорта: {e}")

async def main():
    """Основная функция"""
    try:
        # Создаем импортер
        importer = SupabaseImporter()
        
        # Пути к файлам
        source_dir = Path("Source")
        aliases_file = source_dir / "aliases.jsonl"
        skus_file = source_dir / "normalized_skus.jsonl"
        
        # Проверяем наличие файлов
        if not aliases_file.exists():
            logger.error(f"Файл {aliases_file} не найден")
            return
        
        if not skus_file.exists():
            logger.error(f"Файл {skus_file} не найден")
            return
        
        # Импортируем данные
        await importer.import_aliases(str(aliases_file))
        await importer.import_normalized_skus(str(skus_file))
        
        # Создаем базовые подсказки
        await importer.create_search_suggestions()
        
        # Проверяем результаты
        await importer.verify_import()
        
        logger.info("Импорт данных завершен успешно!")
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(main())

