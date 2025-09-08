#!/usr/bin/env python3
"""
Тестовый скрипт для пошаговой проверки работы с GPT
Проверяем:
1. Получение запроса от пользователя (симуляция)
2. Передача запроса в GPT ИИ
3. Получение ответа от GPT в JSON формате
4. Логирование JSON результата
"""

import asyncio
import json
import logging
import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.openai_service import OpenAIService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

async def test_gpt_step_by_step():
    """Тестируем работу с GPT пошагово"""
    
    print("🔍 ТЕСТ ПОШАГОВОЙ РАБОТЫ С GPT")
    print("=" * 50)
    
    # Шаг 1: Получение запроса от пользователя (симуляция)
    print("\n📝 ШАГ 1: Получение запроса от пользователя")
    user_request = """Анкер с кольцом м8 10х100 (30шт)              
Анкер с кольцом м12 16х130 (10шт)              
Анкер костыль  8х 40 (100шт)              
Дюбель металлический МОЛЛИ с кольцом 5х52 (50шт)              
Дюбель металлический МОЛЛИ 6х52 (50шт)              
Дюбель металлический МОЛЛИ 6х80 (50шт)              
Шайба для поликарбоната, с зонтичным EPDM, Прозрачная 7х25  (1800шт)              
Шайба кровельная, EPDM Черный 2.5мм, 4,8х14 K (12000шт) АКЦИЯ              
Шайба кровельная, EPDM Черный 2.5мм, 6,3х19 K (7000шт)              
Шуруп с полукольцом 4х65 (300шт)"""
    
    print(f"Запрос пользователя:")
    print(f"'{user_request}'")
    print(f"Длина запроса: {len(user_request)} символов")
    
    # Шаг 2: Передача запроса в GPT ИИ
    print("\n🤖 ШАГ 2: Передача запроса в GPT ИИ")
    
    try:
        openai_service = OpenAIService()
        print("✅ OpenAI сервис инициализирован")
        
        # Используем метод analyze_with_assistant для работы с ассистентом
        print("🔄 Отправляем запрос в GPT ассистента...")
        gpt_result = await openai_service.analyze_with_assistant(user_request)
        
        print("✅ GPT ассистент ответил")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с GPT: {e}")
        return
    
    # Шаг 3: Получение ответа от GPT в JSON формате
    print("\n📊 ШАГ 3: Получение ответа от GPT в JSON формате")
    
    print(f"Тип результата: {type(gpt_result)}")
    print(f"Результат: {gpt_result}")
    
    # Шаг 4: Проверка и логирование JSON результата
    print("\n📋 ШАГ 4: Проверка и логирование JSON результата")
    
    try:
        # Проверяем, что результат - это словарь
        if isinstance(gpt_result, dict):
            print("✅ Результат - это словарь (dict)")
            
            # Проверяем структуру
            print(f"Ключи в результате: {list(gpt_result.keys())}")
            
            # Если это список элементов (множественный заказ)
            if 'items' in gpt_result and isinstance(gpt_result['items'], list):
                print(f"✅ Множественный заказ: {len(gpt_result['items'])} позиций")
                for i, item in enumerate(gpt_result['items'], 1):
                    print(f"  Позиция {i}: {item}")
            else:
                print("✅ Одиночный заказ")
                print(f"  Тип: {gpt_result.get('type', 'не указан')}")
                print(f"  Диаметр: {gpt_result.get('diameter', 'не указан')}")
                print(f"  Длина: {gpt_result.get('length', 'не указан')}")
                print(f"  Количество: {gpt_result.get('quantity', 'не указано')}")
                print(f"  Уверенность: {gpt_result.get('confidence', 'не указана')}")
            
            # Логируем полный JSON
            print("\n📝 ПОЛНЫЙ JSON РЕЗУЛЬТАТ:")
            print(json.dumps(gpt_result, ensure_ascii=False, indent=2))
            
        else:
            print(f"❌ Результат не является словарем: {type(gpt_result)}")
            print(f"Содержимое: {gpt_result}")
            
    except Exception as e:
        print(f"❌ Ошибка при обработке результата: {e}")
        return
    
    print("\n✅ ТЕСТ ЗАВЕРШЕН УСПЕШНО!")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(test_gpt_step_by_step())
