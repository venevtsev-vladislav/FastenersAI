#!/usr/bin/env python3
"""
Тест поиска в Supabase для конкретного запроса пользователя
Проверяем, что вернет Supabase в ответ на предоставленный JSON
"""

import asyncio
import json
import sys
import os
import aiohttp
from typing import Dict, List, Any

# Добавляем родительскую папку в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database.supabase_client import SupabaseClient

# Данные из запроса пользователя
USER_REQUEST_DATA = {
    "items": [
        {
            "type": "анкер",
            "diameter": "M8",
            "length": "10х100 мм",
            "material": None,
            "coating": None,
            "quantity": "30шт",
            "confidence": 0.95
        },
        {
            "type": "анкер",
            "diameter": "M12",
            "length": "16х130 мм",
            "material": None,
            "coating": None,
            "quantity": "10шт",
            "confidence": 0.95
        },
        {
            "type": "анкер костыль",
            "diameter": "8",
            "length": "40",
            "material": None,
            "coating": None,
            "quantity": "100шт",
            "confidence": 0.9
        },
        {
            "type": "дюбель металлический МОЛЛИ",
            "diameter": "5",
            "length": "52",
            "material": None,
            "coating": None,
            "quantity": "50шт",
            "confidence": 0.95
        },
        {
            "type": "дюбель металлический МОЛЛИ",
            "diameter": "6",
            "length": "52",
            "material": None,
            "coating": None,
            "quantity": "50шт",
            "confidence": 0.95
        },
        {
            "type": "дюбель металлический МОЛЛИ",
            "diameter": "6",
            "length": "80",
            "material": None,
            "coating": None,
            "quantity": "50шт",
            "confidence": 0.95
        },
        {
            "type": "шайба для поликарбоната",
            "diameter": "7",
            "length": "25",
            "material": "прозрачная",
            "coating": None,
            "quantity": "1800шт",
            "confidence": 0.9
        },
        {
            "type": "шайба кровельная",
            "diameter": "4,8",
            "length": "14",
            "material": None,
            "coating": "EPDM Черный 2.5мм",
            "quantity": "12000шт",
            "confidence": 0.95
        },
        {
            "type": "шайба кровельная",
            "diameter": "6,3",
            "length": "19",
            "material": None,
            "coating": "EPDM Черный 2.5мм",
            "quantity": "7000шт",
            "confidence": 0.95
        },
        {
            "type": "шуруп с полукольцом",
            "diameter": "4",
            "length": "65",
            "material": None,
            "coating": None,
            "quantity": "300шт",
            "confidence": 0.9
        }
    ]
}

async def test_single_item(item: Dict[str, Any], item_index: int) -> Dict[str, Any]:
    """Тестирует поиск для одного элемента"""
    
    print(f"\n{'='*60}")
    print(f"🧪 ТЕСТ {item_index + 1}: {item['type']}")
    print(f"{'='*60}")
    
    # Извлекаем размеры из строки length (например, "10х100 мм" -> diameter="10", length="100")
    diameter = item['diameter']
    length = item['length']
    
    # Обрабатываем диаметр (убираем M если есть)
    if diameter and diameter.startswith('M'):
        diameter = diameter[1:]
    
    # Обрабатываем длину (извлекаем первое число из "10х100 мм")
    if length and 'х' in length:
        length_parts = length.split('х')
        if len(length_parts) >= 2:
            # Берем вторую часть как длину
            length = length_parts[1].replace(' мм', '').strip()
    
    print(f"📋 Исходные данные:")
    print(f"   Тип: {item['type']}")
    print(f"   Диаметр: {item['diameter']} -> {diameter}")
    print(f"   Длина: {item['length']} -> {length}")
    print(f"   Материал: {item['material']}")
    print(f"   Покрытие: {item['coating']}")
    print(f"   Количество: {item['quantity']}")
    print(f"   Уверенность: {item['confidence']}")
    
    # Формируем поисковый запрос
    search_query = f"{item['type']}"
    if diameter:
        search_query += f" M{diameter}"
    if length:
        search_query += f"x{length}"
    if item['coating']:
        search_query += f" {item['coating']}"
    if item['material']:
        search_query += f" {item['material']}"
    
    print(f"\n🔍 Поисковый запрос: {search_query}")
    
    try:
        # Получаем конфигурацию Supabase из config
        from config import SUPABASE_URL, SUPABASE_KEY
        supabase_url = SUPABASE_URL
        supabase_key = SUPABASE_KEY
        
        # Вызываем Edge Function
        edge_function_url = f"{supabase_url}/functions/v1/fastener-search"
        headers = {
            'Authorization': f'Bearer {supabase_key}',
            'Content-Type': 'application/json'
        }
        
        # Формируем payload для Edge Function
        payload = {
            "search_query": search_query,
            "user_intent": {
                "type": item['type'],
                "diameter": diameter,
                "length": length,
                "coating": item['coating'],
                "material": item['material'],
                "is_simple_parsed": False
            }
        }
        
        print(f"🌐 Вызываем Edge Function: {edge_function_url}")
        print(f"📤 Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        async with aiohttp.ClientSession() as session:
            async with session.post(edge_function_url, json=payload, headers=headers) as response:
                if response.status == 200:
                    search_results = await response.json()
                    print(f"✅ Edge Function ответ получен: {response.status}")
                else:
                    print(f"❌ Ошибка Edge Function: {response.status}")
                    error_text = await response.text()
                    print(f"💥 Детали ошибки: {error_text}")
                    return {
                        "item_index": item_index,
                        "success": False,
                        "error": f"HTTP {response.status}: {error_text}",
                        "results": []
                    }
        
        # Обрабатываем результаты
        if isinstance(search_results, dict) and 'results' in search_results:
            results_list = search_results['results']
            print(f"✅ Найдено результатов: {len(results_list)}")
            
            # Показываем детальную информацию о результатах
            if results_list:
                print(f"\n📊 РЕЗУЛЬТАТЫ ПОИСКА:")
                for i, result in enumerate(results_list[:5], 1):  # Показываем топ-5
                    if isinstance(result, dict):
                        sku = result.get('sku', 'N/A')
                        name = result.get('name', 'N/A')
                        probability = result.get('probability_percent', 0)
                        match_reason = result.get('match_reason', 'N/A')
                        
                        print(f"  {i}. SKU: {sku}")
                        print(f"     Название: {name}")
                        print(f"     Вероятность: {probability}%")
                        print(f"     Причина совпадения: {match_reason}")
                        
                        # Показываем объяснение для первого результата
                        if i == 1 and 'explanation' in result:
                            print(f"     Объяснение:")
                            for line in result['explanation'].split('\n'):
                                if line.strip():
                                    print(f"       {line}")
                        print()
                
                # Анализируем качество результатов
                best_result = results_list[0] if results_list else None
                if best_result:
                    best_probability = best_result.get('probability_percent', 0)
                    print(f"🎯 ЛУЧШИЙ РЕЗУЛЬТАТ:")
                    print(f"   SKU: {best_result.get('sku', 'N/A')}")
                    print(f"   Название: {best_result.get('name', 'N/A')}")
                    print(f"   Вероятность совпадения: {best_probability}%")
                    
                    # Оценка качества
                    if best_probability >= 80:
                        quality = "ОТЛИЧНО"
                        emoji = "🟢"
                    elif best_probability >= 60:
                        quality = "ХОРОШО"
                        emoji = "🟡"
                    elif best_probability >= 40:
                        quality = "УДОВЛЕТВОРИТЕЛЬНО"
                        emoji = "🟠"
                    else:
                        quality = "ПЛОХО"
                        emoji = "🔴"
                    
                    print(f"   Качество совпадения: {emoji} {quality}")
            else:
                print("❌ Результаты не найдены")
            
            return {
                "item_index": item_index,
                "success": True,
                "search_query": search_query,
                "results_count": len(results_list),
                "results": results_list,
                "best_result": results_list[0] if results_list else None
            }
        else:
            print("❌ Неожиданный формат ответа")
            return {
                "item_index": item_index,
                "success": False,
                "error": "Неожиданный формат ответа",
                "results": []
            }
            
    except Exception as e:
        print(f"💥 ОШИБКА при поиске: {e}")
        import traceback
        traceback.print_exc()
        return {
            "item_index": item_index,
            "success": False,
            "error": str(e),
            "results": []
        }

async def test_user_request():
    """Основная функция тестирования"""
    
    print("🔍 ТЕСТ ПОИСКА В SUPABASE ДЛЯ ЗАПРОСА ПОЛЬЗОВАТЕЛЯ")
    print("=" * 80)
    print(f"📝 Тестируем {len(USER_REQUEST_DATA['items'])} позиций из запроса пользователя")
    print("=" * 80)
    
    # Результаты тестирования
    test_results = []
    successful_searches = 0
    total_items = len(USER_REQUEST_DATA['items'])
    
    # Тестируем каждый элемент
    for i, item in enumerate(USER_REQUEST_DATA['items']):
        result = await test_single_item(item, i)
        test_results.append(result)
        
        if result['success'] and result['results_count'] > 0:
            successful_searches += 1
    
    # Итоговая статистика
    print("\n" + "=" * 80)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 80)
    
    print(f"✅ Успешных поисков: {successful_searches}/{total_items}")
    print(f"❌ Неудачных поисков: {total_items - successful_searches}/{total_items}")
    
    success_rate = successful_searches / total_items
    print(f"📈 Процент успешности: {success_rate:.1%}")
    
    # Детальная статистика по качеству результатов
    excellent_matches = 0
    good_matches = 0
    satisfactory_matches = 0
    poor_matches = 0
    
    for result in test_results:
        if result['success'] and result['best_result']:
            probability = result['best_result'].get('probability_percent', 0)
            if probability >= 80:
                excellent_matches += 1
            elif probability >= 60:
                good_matches += 1
            elif probability >= 40:
                satisfactory_matches += 1
            else:
                poor_matches += 1
    
    print(f"\n🎯 КАЧЕСТВО СОВПАДЕНИЙ:")
    print(f"   🟢 Отлично (≥80%): {excellent_matches}")
    print(f"   🟡 Хорошо (60-79%): {good_matches}")
    print(f"   🟠 Удовлетворительно (40-59%): {satisfactory_matches}")
    print(f"   🔴 Плохо (<40%): {poor_matches}")
    
    # Показываем проблемные случаи
    print(f"\n⚠️  ПРОБЛЕМНЫЕ СЛУЧАИ:")
    for result in test_results:
        if not result['success']:
            item = USER_REQUEST_DATA['items'][result['item_index']]
            print(f"   ❌ {item['type']} - {result.get('error', 'Неизвестная ошибка')}")
        elif result['results_count'] == 0:
            item = USER_REQUEST_DATA['items'][result['item_index']]
            print(f"   ⚠️  {item['type']} - Результаты не найдены")
        elif result['best_result'] and result['best_result'].get('probability_percent', 0) < 40:
            item = USER_REQUEST_DATA['items'][result['item_index']]
            probability = result['best_result'].get('probability_percent', 0)
            print(f"   ⚠️  {item['type']} - Низкое качество совпадения ({probability}%)")
    
    # Сохраняем результаты в файл
    results_file = "test_results_user_request.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "test_summary": {
                "total_items": total_items,
                "successful_searches": successful_searches,
                "success_rate": success_rate,
                "excellent_matches": excellent_matches,
                "good_matches": good_matches,
                "satisfactory_matches": satisfactory_matches,
                "poor_matches": poor_matches
            },
            "detailed_results": test_results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 Детальные результаты сохранены в файл: {results_file}")
    
    return success_rate >= 0.7  # Считаем тест пройденным при 70% успешности

if __name__ == "__main__":
    print("🚀 Запуск теста поиска для запроса пользователя...")
    
    # Запускаем асинхронный тест
    result = asyncio.run(test_user_request())
    
    if result:
        print("\n🎉 ТЕСТ ПРОЙДЕН УСПЕШНО!")
        print("Supabase корректно обрабатывает запрос пользователя")
    else:
        print("\n❌ ТЕСТ НЕ ПРОЙДЕН!")
        print("Есть проблемы с поиском в базе данных")
    
    sys.exit(0 if result else 1)
