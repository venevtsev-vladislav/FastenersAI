#!/usr/bin/env python3
"""
Тест поиска в Supabase для проекта FastenersAI
Тестируем поиск соответствий по результатам GPT парсинга
"""

import asyncio
import json
import sys
import os

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.supabase_client import SupabaseClient

async def test_supabase_search():
    """Тестируем поиск в Supabase по результатам GPT"""
    
    print("🔍 ТЕСТ ПОИСКА В SUPABASE")
    print("=" * 50)
    
    # Данные от GPT (результат парсинга)
    gpt_items = [
        {
            "type": "анкер забиваемый",
            "diameter": "6",
            "length": None,
            "material": "латунь",
            "coating": None,
            "quantity": None,
            "confidence": 0.9
        },
        {
            "type": "анкер клиновой",
            "diameter": "8",
            "length": "50",
            "material": None,
            "coating": None,
            "quantity": None,
            "confidence": 0.9
        },
        {
            "type": "анкерный болт с кольцом",
            "diameter": "16",
            "length": "130",
            "material": None,
            "coating": None,
            "quantity": None,
            "confidence": 0.9
        },
        {
            "type": "болт DIN 603",
            "diameter": "10",
            "length": "120",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 603",
            "diameter": "6",
            "length": "60",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 933 кл.пр.8.8",
            "diameter": "14",
            "length": "80",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 933 кл.пр.8.8",
            "diameter": "16",
            "length": "60",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 933 кл.пр.8.8",
            "diameter": "16",
            "length": "70",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 933 кл.пр.8.8",
            "diameter": "18",
            "length": "40",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        },
        {
            "type": "болт DIN 933 кл.пр.8.8",
            "diameter": "5",
            "length": "16",
            "material": None,
            "coating": "оцинкованный",
            "quantity": "1 кг",
            "confidence": 0.9
        }
    ]
    
    print(f"📝 Ищем соответствия для {len(gpt_items)} позиций от GPT")
    print("=" * 50)
    
    try:
        # Создаем клиент Supabase
        supabase_client = SupabaseClient()
        
        print("✅ Supabase клиент создан")
        
        # Ожидаемые SKU (из скрина)
        expected_skus = {
            "анкер забиваемый латунный М6": "5-0010170",
            "Клиновой анкер 8х50": "5-0012030", 
            "Анкерный болт с кольцом М16x130": "9990121573",
            "Болты DIN603 М10х120, цинк (кг)": "12-0013800",
            "Болты DIN603 M6х60, цинк (кг)": "12-0014130",
            "Болт DIN 933 кл.пр.8.8 М14х80, цинк (кг)": "6-0049020",
            "Болт DIN 933 кл.пр.8.8 М16х60, цинк (кг)": "6-0049210",
            "Болт DIN 933 кл.пр.8.8 М16х70, цинк (кг)": "6-0049230",
            "Болт DIN 933 кл.пр.8.8 М18х40, цинк (кг)": "9990085037",
            "Болт DIN 933 кл.пр.8.8 М5х16, цинк (кг)": "6-0049680"
        }
        
        print("\n🎯 Ожидаемые соответствия SKU:")
        for desc, sku in expected_skus.items():
            print(f"  {sku} -> {desc}")
        
        print("\n" + "=" * 50)
        
        # Тестируем поиск для каждой позиции
        found_matches = 0
        total_items = len(gpt_items)
        
        for i, item in enumerate(gpt_items, 1):
            print(f"\n🧪 Тест {i}: {item['type']} M{item['diameter']}x{item['length'] or 'N/A'}")
            
            try:
                # Формируем поисковый запрос
                search_query = f"{item['type']}"
                if item['diameter']:
                    search_query += f" M{item['diameter']}"
                if item['length']:
                    search_query += f"x{item['length']}"
                if item['coating']:
                    search_query += f" {item['coating']}"
                if item['material']:
                    search_query += f" {item['material']}"
                
                print(f"🔍 Поисковый запрос: {search_query}")
                
                # Вызываем РЕАЛЬНУЮ Edge Function с правильным форматом
                edge_function_url = f"{supabase_url}/functions/v1/fastener-search"
                headers = {
                    'Authorization': f'Bearer {supabase_key}',
                    'Content-Type': 'application/json'
                }
                
                # Правильный формат запроса для Edge Function
                payload = {
                    "search_query": search_query,
                    "user_intent": {
                        "type": item['type'],
                        "diameter": item['diameter'],
                        "length": item['length'],
                        "coating": item['coating'],
                        "material": item['material'],
                        "is_simple_parsed": False
                    }
                }
                
                print(f"🌐 Вызываем Edge Function: {edge_function_url}")
                print(f"📤 Отправляем payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(edge_function_url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            search_results = await response.json()
                            print(f"✅ Edge Function ответ получен: {response.status}")
                        else:
                            print(f"❌ Ошибка Edge Function: {response.status}")
                            error_text = await response.text()
                            print(f"💥 Детали ошибки: {error_text}")
                            search_results = []
                
                # Отладочная информация о структуре ответа
                print(f"🔍 Тип ответа: {type(search_results)}")
                print(f"🔍 Содержимое ответа: {json.dumps(search_results, ensure_ascii=False, indent=2)}")
                
                # Проверяем структуру ответа Edge Function
                if isinstance(search_results, dict) and 'results' in search_results:
                    results_list = search_results['results']
                    print(f"✅ Данные извлечены из поля 'results': {len(results_list)} результатов")
                else:
                    results_list = []
                    print("❌ Неожиданный формат ответа")
                
                if results_list and len(results_list) > 0:
                    print(f"✅ Найдено {len(results_list)} результатов")
                    
                    # Показываем первые результаты
                    for j, result in enumerate(results_list[:3], 1):
                        if isinstance(result, dict):
                            sku = result.get('sku', 'N/A')
                            name = result.get('name', 'N/A')
                            print(f"  {j}. SKU: {sku} | {name}")
                        else:
                            print(f"  {j}. Результат: {result}")
                    
                    # Проверяем, есть ли ожидаемый SKU
                    found_expected = False
                    for result in results_list:
                        if isinstance(result, dict):
                            sku = result.get('sku', '')
                            if sku in expected_skus.values():
                                print(f"🎯 НАЙДЕН ОЖИДАЕМЫЙ SKU: {sku}")
                                found_expected = True
                                found_matches += 1
                                break
                    
                    if not found_expected:
                        print("❌ Ожидаемый SKU НЕ найден")
                        
                else:
                    print("❌ Результаты не найдены")
                    
            except Exception as e:
                print(f"💥 ОШИБКА при поиске: {e}")
        
        print("\n" + "=" * 50)
        print(f"📊 ИТОГИ ПОИСКА:")
        print(f"✅ Найдено соответствий: {found_matches}/{total_items}")
        print(f"❌ Не найдено: {total_items - found_matches}/{total_items}")
        
        # Определяем успех
        success_rate = found_matches / total_items
        if success_rate >= 0.7:  # 70% успешность
            print(f"\n🎉 ТЕСТ ПРОЙДЕН! Успешность: {success_rate:.1%}")
            return True
        else:
            print(f"\n❌ ТЕСТ НЕ ПРОЙДЕН! Успешность: {success_rate:.1%}")
            return False
            
    except Exception as e:
        print(f"\n💥 ОШИБКА при создании Supabase клиента: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Запуск теста поиска в Supabase...")
    
    # Запускаем асинхронный тест
    result = asyncio.run(test_supabase_search())
    
    if result:
        print("\n🎉 ТЕСТ ПОИСКА ПРОЙДЕН УСПЕШНО!")
        print("Supabase корректно находит соответствия для GPT результатов")
    else:
        print("\n❌ ТЕСТ ПОИСКА НЕ ПРОЙДЕН!")
        print("Есть проблемы с поиском в базе данных")
    
    sys.exit(0 if result else 1)
