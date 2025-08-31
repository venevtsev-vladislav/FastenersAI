#!/usr/bin/env python3
"""
Тестирование исправленного SmartParser
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.smart_parser import SmartParser

def test_smart_parser():
    """Тестирует исправленный SmartParser"""
    parser = SmartParser()
    
    # Тестовые запросы
    test_queries = [
        "Болты DIN603 М6х40, цинк (тыс.шт)",           # Должен работать (как раньше)
        "болт с грибком М6 на 40, цинкованный",         # Должен работать (новый)
        "Болт DIN 603 М6×40 Zn",                        # Должен работать (новый)
        "болт М6x40 цинк",                              # Должен работать (новый)
        "винт M6 20 мм",                                # Должен работать (как раньше)
        "гайка DIN 985 M6 нержавеющая сталь A2",        # Должен работать (как раньше)
    ]
    
    print("🧪 Тестирование исправленного SmartParser\n")
    
    for query in test_queries:
        print(f"📝 Запрос: {query}")
        
        # Проверяем нужен ли GPT
        need_gpt = parser.should_use_gpt(query)
        print(f"   🤖 Нужен GPT: {need_gpt}")
        
        # Парсим запрос
        result = parser.parse_query(query)
        print(f"   📊 Результат: {result}")
        
        if not need_gpt:
            print(f"   ✅ Распознан как простой: {result.get('user_intent', {})}")
        else:
            print(f"   🔍 Отправлен в GPT: {result.get('reason', '')}")
        
        print("-" * 60)

if __name__ == "__main__":
    test_smart_parser()
