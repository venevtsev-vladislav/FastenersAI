#!/usr/bin/env python3
"""
Тестирование SmartParser
"""

import asyncio
import logging
from services.smart_parser import SmartParser

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_smart_parser():
    """Тестирует SmartParser на различных запросах"""
    
    parser = SmartParser()
    
    # Тестовые запросы
    test_queries = [
        # Простые запросы (НЕ нужен GPT)
        "винт M6 20 мм",
        "гайка M8",
        "шайба M6 нержавеющая сталь",
        "болт M10 30 мм оцинкованный",
        "DIN 965 M6x20",
        "DIN 985 M6 A2",
        
        # Сложные запросы (НУЖЕН GPT)
        "нужно 12 разных деталей для сборки мебели",
        "что-то подходящее для крепления дерева",
        "винт с шестигранной головкой, длиной 20 мм, для наружного применения",
        "комплект крепежа для сборки стола",
        "заказать набор болтов и гаек для ремонта",
        "требуется несколько видов саморезов для гипсокартона"
    ]
    
    print("🧪 Тестирование SmartParser\n")
    
    for i, query in enumerate(test_queries, 1):
        print(f"🔍 Тест {i}: {query}")
        
        try:
            result = parser.parse_query(query)
            
            if result['need_gpt']:
                print(f"   ❌ GPT НУЖЕН: {result['reason']}")
            else:
                print(f"   ✅ GPT НЕ нужен: {result['reason']}")
                print(f"   📊 Разобранные параметры:")
                user_intent = result['user_intent']
                for key, value in user_intent.items():
                    if value is not None:
                        print(f"      {key}: {value}")
            
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_smart_parser())
