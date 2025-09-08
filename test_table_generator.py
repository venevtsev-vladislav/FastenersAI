#!/usr/bin/env python3
"""
Тест сервиса генерации таблиц
"""

import asyncio
import sys
import os
import json

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from table_generator_service import get_table_generator_service
from railway_logging import setup_railway_logging

async def test_table_generator():
    """Тестируем сервис генерации таблиц"""
    
    print("🔍 ТЕСТ СЕРВИСА ГЕНЕРАЦИИ ТАБЛИЦ")
    print("=" * 50)
    
    # Настраиваем логирование
    setup_railway_logging()
    
    try:
        # Получаем сервис
        service = get_table_generator_service()
        
        # Тестируем получение данных
        print("\n📊 ТЕСТИРУЕМ ПОЛУЧЕНИЕ ДАННЫХ")
        print("-" * 30)
        
        data = await service.get_analysis_data(days=30)
        
        print(f"✅ Запросов: {len(data['requests'])}")
        print(f"✅ Позиций: {len(data['items'])}")
        print(f"✅ Статистика: {json.dumps(data['statistics'], ensure_ascii=False, indent=2)}")
        
        # Тестируем генерацию Excel
        print("\n📊 ТЕСТИРУЕМ ГЕНЕРАЦИЮ EXCEL")
        print("-" * 30)
        
        excel_file = await service.generate_excel_report(days=30)
        
        if excel_file:
            print(f"✅ Excel файл создан: {excel_file}")
            if os.path.exists(excel_file):
                file_size = os.path.getsize(excel_file)
                print(f"📁 Размер: {file_size / 1024:.1f} KB")
        else:
            print("❌ Не удалось создать Excel файл")
        
        # Тестируем генерацию CSV
        print("\n📊 ТЕСТИРУЕМ ГЕНЕРАЦИЮ CSV")
        print("-" * 30)
        
        csv_file = await service.generate_csv_report(days=30)
        
        if csv_file:
            print(f"✅ CSV файл создан: {csv_file}")
            if os.path.exists(csv_file):
                file_size = os.path.getsize(csv_file)
                print(f"📁 Размер: {file_size / 1024:.1f} KB")
        else:
            print("❌ Не удалось создать CSV файл")
        
        # Тестируем сводный отчет
        print("\n📊 ТЕСТИРУЕМ СВОДНЫЙ ОТЧЕТ")
        print("-" * 30)
        
        summary = await service.get_summary_report(days=30)
        print(f"✅ Сводный отчет: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n🎉 ТЕСТ ЗАВЕРШЕН!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_table_generator())
