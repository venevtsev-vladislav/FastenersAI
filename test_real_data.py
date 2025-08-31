#!/usr/bin/env python3
"""
Тест работы с реальными данными из Supabase
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_real_data():
    """Тестирует работу с реальными данными"""
    print("🧪 Тестирую работу с реальными данными...")
    
    try:
        # Тест 1: Инициализация Supabase
        print("1. Инициализирую Supabase...")
        from database.supabase_client import init_supabase, search_parts
        
        await init_supabase()
        print("   ✅ Supabase инициализирован")
        
        # Тест 2: Поиск деталей
        print("2. Тестирую поиск деталей...")
        
        test_queries = [
            "болт М8",
            "саморез кровельный",
            "анкерный болт",
            "шайба пружинная"
        ]
        
        for query in test_queries:
            print(f"   🔍 Поиск: '{query}'")
            results = await search_parts(query, {})
            
            if results:
                print(f"      ✅ Найдено {len(results)} результатов")
                # Показываем первые 3 результата
                for i, result in enumerate(results[:3]):
                    print(f"         {i+1}. {result.get('name', 'N/A')} (SKU: {result.get('sku', 'N/A')})")
            else:
                print(f"      ❌ Результатов не найдено")
        
        # Тест 3: Генерация Excel с реальными данными
        print("3. Тестирую генерацию Excel с реальными данными...")
        
        # Ищем болты М8
        search_results = await search_parts("болт М8", {})
        
        if search_results:
            from services.excel_generator import ExcelGenerator
            
            generator = ExcelGenerator()
            excel_file = await generator.generate_excel(
                search_results=search_results[:10],  # Берем первые 10 результатов
                user_request="болт М8"
            )
            
            if os.path.exists(excel_file):
                file_size = os.path.getsize(excel_file)
                print(f"   ✅ Excel файл создан: {excel_file}")
                print(f"   📊 Размер файла: {file_size} байт")
                print(f"   📋 Количество результатов: {len(search_results[:10])}")
                
                # Удаляем временный файл
                os.remove(excel_file)
                print("   🗑️  Временный файл удален")
            else:
                print("   ❌ Excel файл не создан")
        else:
            print("   ⚠️  Нет данных для тестирования Excel генератора")
        
        print("✅ Все тесты завершены!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_real_data())
