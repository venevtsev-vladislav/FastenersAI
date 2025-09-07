#!/usr/bin/env python3
"""
Тест парсинга GPT для запроса с множественными позициями
"""

import asyncio
import sys
import os
import json

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.message_processor import MessagePipeline
from services.message_processor import MessageProcessor

async def test_gpt_parsing():
    """Тестируем парсинг GPT для множественного запроса"""
    
    print("🔍 ТЕСТ ПАРСИНГА GPT ДЛЯ МНОЖЕСТВЕННОГО ЗАПРОСА")
    print("=" * 70)
    
    # Тестовый запрос
    test_query = """Анкер двухраспорный 8х100х12 с крюком
Анкер забиваемый латунный М10
Анкер забиваемый латунный М12х38мм с насечками
Анкерный болт 10х120
Анкер клиновой оцинк. М16/70х180 Bullit
Анкерный болт 12х130
Анкерный болт с гайкой М12х129
Болт DIN 933 кл.пр.8.8 М10х30, цинк
Винт DIN 7985 М4х40, цинк
Гвоздь строительный 4,0х120"""
    
    user_id = 12345
    
    try:
        # Создаем mock Message объект
        from unittest.mock import Mock
        mock_message = Mock()
        mock_message.text = test_query
        mock_message.from_user.id = user_id
        mock_message.chat.id = user_id
        
        print(f"📝 Тестовый запрос:")
        print(f"'{test_query}'")
        print(f"👤 User ID: {user_id}")
        
        # ЭТАП 1: Тестируем MessageProcessor напрямую
        print("\n" + "="*70)
        print("🔍 ЭТАП 1: ТЕСТИРУЕМ MESSAGEPROCESSOR НАПРЯМУЮ")
        print("="*70)
        
        message_processor = MessageProcessor()
        
        # Тестируем парсинг
        parsed_result = await message_processor.process_message(mock_message)
        
        print(f"✅ Результат парсинга MessageProcessor:")
        print(f"  - Тип: {type(parsed_result)}")
        if parsed_result:
            print(f"  - Содержимое: {json.dumps(parsed_result, ensure_ascii=False, indent=2)}")
        else:
            print("  - Результат: None")
        
        # ЭТАП 2: Тестируем Pipeline
        print("\n" + "="*70)
        print("🔍 ЭТАП 2: ТЕСТИРУЕМ PIPELINE")
        print("="*70)
        
        pipeline = MessagePipeline(bot=None)
        
        # Тестируем парсинг через pipeline
        pipeline_result = await pipeline._parse_and_normalize(mock_message)
        
        print(f"✅ Результат парсинга Pipeline:")
        print(f"  - Тип: {type(pipeline_result)}")
        if pipeline_result:
            print(f"  - Обработанный текст: {pipeline_result.get('processed_text', 'N/A')}")
            print(f"  - User intent: {json.dumps(pipeline_result.get('user_intent', {}), ensure_ascii=False, indent=2)}")
            print(f"  - Confidence: {pipeline_result.get('confidence', 'N/A')}")
            
            # Проверяем items
            user_intent = pipeline_result.get('user_intent', {})
            if user_intent.get('is_multiple_order') and user_intent.get('items'):
                print(f"  - Количество позиций: {len(user_intent['items'])}")
                print(f"  - Первые 3 позиции:")
                for i, item in enumerate(user_intent['items'][:3], 1):
                    print(f"    {i}. {item}")
        else:
            print("  - Результат: None")
        
        # ЭТАП 3: Тестируем поиск
        print("\n" + "="*70)
        print("🔍 ЭТАП 3: ТЕСТИРУЕМ ПОИСК")
        print("="*70)
        
        if pipeline_result:
            search_results = await pipeline._search_database(pipeline_result)
            
            print(f"✅ Результат поиска:")
            print(f"  - Найдено результатов: {len(search_results)}")
            
            if search_results:
                print(f"  - Первый результат:")
                first_result = search_results[0]
                for key, value in first_result.items():
                    print(f"    {key}: {value}")
            else:
                print("  - Результаты не найдены!")
        
        return True
        
    except Exception as e:
        print(f"\n💥 ОШИБКА В ТЕСТЕ: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_single_item_parsing():
    """Тестируем парсинг одной позиции"""
    
    print("\n" + "="*70)
    print("🔍 ДОПОЛНИТЕЛЬНЫЙ ТЕСТ: ПАРСИНГ ОДНОЙ ПОЗИЦИИ")
    print("="*70)
    
    # Тест одной позиции
    single_query = "Анкер забиваемый латунный М10"
    
    try:
        from unittest.mock import Mock
        mock_message = Mock()
        mock_message.text = single_query
        mock_message.from_user.id = 12345
        mock_message.chat.id = 12345
        
        print(f"📝 Тестовый запрос: '{single_query}'")
        
        # Тестируем MessageProcessor
        message_processor = MessageProcessor()
        parsed_result = await message_processor.process_message(mock_message)
        
        print(f"✅ Результат парсинга одной позиции:")
        print(f"  - Содержимое: {json.dumps(parsed_result, ensure_ascii=False, indent=2)}")
        
        return True
        
    except Exception as e:
        print(f"💥 ОШИБКА в тесте одной позиции: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста парсинга GPT...")
    
    # Запускаем асинхронные тесты
    async def run_tests():
        # Тест множественного запроса
        multiple_test = await test_gpt_parsing()
        
        # Тест одной позиции
        single_test = await test_single_item_parsing()
        
        return multiple_test and single_test
    
    result = asyncio.run(run_tests())
    
    if result:
        print("\n🎉 ВСЕ ТЕСТЫ ПАРСИНГА ПРОЙДЕНЫ!")
    else:
        print("\n❌ ЕСТЬ ПРОБЛЕМЫ В ТЕСТАХ ПАРСИНГА!")
    
    sys.exit(0 if result else 1)
