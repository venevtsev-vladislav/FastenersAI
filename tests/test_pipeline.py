#!/usr/bin/env python3
"""
Тест упрощенного Pipeline для проекта FastenersAI
Тестируем 5-этапный pipeline
"""

import asyncio
import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pipeline.message_processor import MessagePipeline

async def test_pipeline():
    """Тестируем упрощенный pipeline"""
    
    print("🔍 ТЕСТ УПРОЩЕННОГО PIPELINE")
    print("=" * 50)
    
    try:
        # Создаем pipeline (без bot для тестирования)
        pipeline = MessagePipeline(bot=None)
        
        print("✅ Pipeline создан успешно")
        
        # Проверяем, что у нас есть все нужные методы
        required_methods = [
            '_parse_and_normalize',
            '_search_database', 
            '_rank_results',
            '_generate_excel',
            '_finalize_results'
        ]
        
        print("\n🔍 Проверяем наличие методов pipeline:")
        for method_name in required_methods:
            if hasattr(pipeline, method_name):
                print(f"  ✅ {method_name}")
            else:
                print(f"  ❌ {method_name} - НЕ НАЙДЕН!")
                return False
        
        print("\n✅ Все методы pipeline присутствуют")
        
        # Проверяем, что убраны старые методы
        old_methods = [
            '_validate_and_parse',
            '_normalize_with_ai',
            '_prepare_data_container',
            '_validate_relevance'
        ]
        
        print("\n🔍 Проверяем, что старые методы убраны:")
        for method_name in old_methods:
            if hasattr(pipeline, method_name):
                print(f"  ❌ {method_name} - ВСЕ ЕЩЕ ЕСТЬ!")
                return False
            else:
                print(f"  ✅ {method_name} - убран")
        
        print("\n✅ Все старые методы успешно убраны")
        
        # Проверяем структуру pipeline
        print("\n📊 СТРУКТУРА PIPELINE:")
        print("  1. Парсинг и нормализация (объединено)")
        print("  2. Поиск в базе данных")
        print("  3. Ранжирование результатов") 
        print("  4. Генерация Excel")
        print("  5. Финальная обработка")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ОШИБКА при тестировании pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста упрощенного Pipeline...")
    
    # Запускаем асинхронный тест
    result = asyncio.run(test_pipeline())
    
    if result:
        print("\n🎉 ТЕСТ PIPELINE ПРОЙДЕН УСПЕШНО!")
        print("Pipeline упрощен и оптимизирован")
    else:
        print("\n❌ ТЕСТ PIPELINE НЕ ПРОЙДЕН!")
        print("Есть проблемы с pipeline")
    
    sys.exit(0 if result else 1)
