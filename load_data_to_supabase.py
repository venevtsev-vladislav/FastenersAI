#!/usr/bin/env python3
"""
Скрипт для загрузки данных из исходных файлов в Supabase
"""

import asyncio
import json
import pandas as pd
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import SOURCE_FILES
from database.supabase_client import init_supabase, create_tables

async def load_data():
    """Загружает данные в Supabase"""
    print("🚀 Начинаю загрузку данных в Supabase...")
    
    try:
        # Инициализируем Supabase
        await init_supabase()
        
        # Создаем таблицы
        print("📋 Создаю таблицы...")
        await create_tables()
        
        # Загружаем алиасы
        print("🔄 Загружаю алиасы...")
        await load_aliases()
        
        # Загружаем нормализованные SKU
        print("🔄 Загружаю нормализованные SKU...")
        await load_normalized_skus()
        
        # Загружаем основной каталог
        print("🔄 Загружаю основной каталог...")
        await load_main_catalog()
        
        print("✅ Все данные успешно загружены!")
        
    except Exception as e:
        print(f"❌ Ошибка при загрузке данных: {e}")
        import traceback
        traceback.print_exc()

async def load_aliases():
    """Загружает алиасы в БД"""
    try:
        with open(SOURCE_FILES['aliases'], 'r', encoding='utf-8') as f:
            aliases = [json.loads(line.strip()) for line in f]
        
        print(f"   📊 Найдено {len(aliases)} алиасов")
        
        # Загружаем в Supabase
        from database.supabase_client import _supabase_client
        
        if not _supabase_client:
            print("   ⚠️  Supabase не инициализирован, пропускаем загрузку")
            return
        
        # Очищаем таблицу перед загрузкой
        try:
            _supabase_client.table('aliases').delete().neq('id', 0).execute()
            print("   🗑️  Таблица aliases очищена")
        except Exception as e:
            print(f"   ⚠️  Не удалось очистить таблицу: {e}")
        
        # Загружаем данные
        insert_data = []
        for alias in aliases:
            insert_data.append({
                'alias': alias.get('alias', ''),
                'maps_to': alias.get('maps_to', {}),
                'source_url': alias.get('source_url', ''),
                'confidence': alias.get('confidence', 0.0),
                'notes': alias.get('notes', '')
            })
        
        try:
            response = _supabase_client.table('aliases').insert(insert_data).execute()
            print(f"   ✅ Успешно загружено {len(aliases)} алиасов в Supabase")
        except Exception as e:
            print(f"   ❌ Ошибка при загрузке алиасов: {e}")
            import traceback
            traceback.print_exc()
        
        # Выводим статистику
        types_count = {}
        for alias in aliases:
            alias_type = alias['maps_to'].get('type', 'Неизвестно')
            types_count[alias_type] = types_count.get(alias_type, 0) + 1
        
        print("   📈 Распределение по типам:")
        for alias_type, count in sorted(types_count.items()):
            print(f"      {alias_type}: {count}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при загрузке алиасов: {e}")
        import traceback
        traceback.print_exc()

async def load_normalized_skus():
    """Загружает нормализованные SKU в БД"""
    try:
        with open(SOURCE_FILES['normalized_skus'], 'r', encoding='utf-8') as f:
            skus = [json.loads(line.strip()) for line in f]
        
        print(f"   📊 Найдено {len(skus)} SKU")
        
        # Загружаем в Supabase
        from database.supabase_client import _supabase_client
        
        if not _supabase_client:
            print("   ⚠️  Supabase не инициализирован, пропускаем загрузку")
            return
        
        # Очищаем таблицу перед загрузкой
        try:
            _supabase_client.table('parts_catalog').delete().neq('id', 0).execute()
            print("   🗑️  Таблица parts_catalog очищена")
        except Exception as e:
            print(f"   ⚠️  Не удалось очистить таблицу: {e}")
        
        # Загружаем данные порциями
        batch_size = 100
        total_loaded = 0
        
        for i in range(0, len(skus), batch_size):
            batch = skus[i:i + batch_size]
            
            # Подготавливаем данные для вставки
            insert_data = []
            for sku in batch:
                insert_data.append({
                    'sku': sku.get('sku', ''),
                    'name': sku.get('name', ''),
                    'type': sku.get('type', ''),
                    'pack_size': sku.get('pack_size', 0),
                    'unit': sku.get('unit', 'шт')
                })
            
            try:
                response = _supabase_client.table('parts_catalog').insert(insert_data).execute()
                total_loaded += len(batch)
                print(f"   📥 Загружено {total_loaded}/{len(skus)} SKU")
            except Exception as e:
                print(f"   ❌ Ошибка при загрузке батча {i//batch_size + 1}: {e}")
        
        print(f"   ✅ Успешно загружено {total_loaded} SKU в Supabase")
        
        # Выводим статистику
        types_count = {}
        pack_sizes = {}
        
        for sku in skus:
            sku_type = sku.get('type', 'Неизвестно')
            pack_size = sku.get('pack_size', 0)
            
            types_count[sku_type] = types_count.get(sku_type, 0) + 1
            pack_sizes[pack_size] = pack_sizes.get(pack_size, 0) + 1
        
        print("   📈 Топ-5 типов деталей:")
        sorted_types = sorted(types_count.items(), key=lambda x: x[1], reverse=True)
        for i, (sku_type, count) in enumerate(sorted_types[:5]):
            print(f"      {i+1}. {sku_type}: {count}")
            
        print("   📦 Топ-5 размеров упаковок:")
        sorted_pack_sizes = sorted(pack_sizes.items(), key=lambda x: x[1], reverse=True)
        for i, (size, count) in enumerate(sorted_pack_sizes[:5]):
            print(f"      {i+1}. {size}: {count}")
            
    except Exception as e:
        print(f"   ❌ Ошибка при загрузке SKU: {e}")
        import traceback
        traceback.print_exc()

async def load_main_catalog():
    """Загружает основной каталог в БД"""
    try:
        # Читаем Excel файл
        df = pd.read_excel(SOURCE_FILES['excel_catalog'])
        
        print(f"   📊 Найдено {len(df)} строк в каталоге")
        
        # Анализируем структуру
        print("   📋 Структура каталога:")
        print(f"      Колонки: {df.columns.tolist()}")
        print(f"      Размер: {df.shape}")
        
        # Показываем примеры данных
        print("   📝 Примеры данных:")
        for i in range(3, min(8, len(df))):
            row = df.iloc[i]
            if pd.notna(row['Unnamed: 1']) and pd.notna(row['Unnamed: 2']):
                print(f"      Строка {i}: {row['Unnamed: 1'][:50]}...")
        
        # TODO: Реализовать загрузку в Supabase
        # Пока просто выводим статистику
        
    except Exception as e:
        print(f"   ❌ Ошибка при загрузке каталога: {e}")

if __name__ == "__main__":
    print("🔧 Скрипт загрузки данных в Supabase")
    print("=" * 50)
    
    # Проверяем наличие исходных файлов
    missing_files = []
    for file_type, file_path in SOURCE_FILES.items():
        if not os.path.exists(file_path):
            missing_files.append(f"{file_type}: {file_path}")
    
    if missing_files:
        print("❌ Отсутствуют исходные файлы:")
        for missing in missing_files:
            print(f"   {missing}")
        print("\nУбедитесь, что все файлы находятся в папке Source/")
        sys.exit(1)
    
    # Запускаем загрузку
    asyncio.run(load_data())

