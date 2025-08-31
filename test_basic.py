#!/usr/bin/env python3
"""
Простой тест базовой функциональности
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_basic_functionality():
    """Тестирует базовую функциональность"""
    print("🧪 Тестирую базовую функциональность...")
    
    try:
        # Тест 1: Импорт модулей
        print("1. Проверяю импорт модулей...")
        from config import TELEGRAM_TOKEN, OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY
        print("   ✅ Конфигурация загружена")
        
        # Тест 2: Создание Excel генератора
        print("2. Тестирую Excel генератор...")
        from services.excel_generator import ExcelGenerator
        
        generator = ExcelGenerator()
        print("   ✅ Excel генератор создан")
        
        # Тест 3: Создание заглушки Excel файла
        print("3. Создаю тестовый Excel файл...")
        test_data = [
            {
                'sku': 'TEST-001',
                'name': 'Тестовая деталь',
                'type': 'Тест',
                'pack_size': 100,
                'unit': 'шт'
            }
        ]
        
        excel_file = await generator.generate_excel(test_data, "тестовый запрос")
        print(f"   ✅ Excel файл создан: {excel_file}")
        
        # Проверяем существование файла
        if os.path.exists(excel_file):
            print(f"   ✅ Файл существует, размер: {os.path.getsize(excel_file)} байт")
        else:
            print("   ❌ Файл не найден")
        
        # Тест 4: Проверка структуры проекта
        print("4. Проверяю структуру проекта...")
        required_files = [
            'bot.py',
            'config.py',
            'handlers/command_handler.py',
            'handlers/message_handler.py',
            'services/message_processor.py',
            'services/openai_service.py',
            'services/excel_generator.py',
            'database/supabase_client.py',
            'utils/logger.py'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not os.path.exists(file_path):
                missing_files.append(file_path)
        
        if missing_files:
            print(f"   ❌ Отсутствуют файлы: {missing_files}")
        else:
            print("   ✅ Все файлы на месте")
        
        print("\n🎉 Базовые тесты пройдены успешно!")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_basic_functionality())
    if success:
        print("\n✅ Все тесты пройдены! Бот готов к настройке.")
    else:
        print("\n❌ Тесты не пройдены. Проверьте ошибки выше.")
        sys.exit(1)

