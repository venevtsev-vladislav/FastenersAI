"""
Тестовый скрипт для проверки системы валидации
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.validation_service import ValidationService

async def test_validation():
    """Тестирует систему валидации"""
    
    # Тестовые данные
    original_request = """1. DIN 603 Винт мебельный 6 × 40 Zn — 200 шт
2. DIN 603 Винт мебельный 8 × 80 Zn — 200 шт
3. DIN 965 M 6 × 20 Винт A2 — 100 шт
4. DIN 965 M 4 × 25 Винт ZN — 200 шт
5. DIN 965 M 6 × 25 Винт ZN — 200 шт
6. DIN 985 M 6 Гайка самоконтр. A2 — 200 шт
7. Саморезы по дереву с фрезой тарельч. 6,0 × 180 мм ж.ц TX 30 — 100 шт
8. Трос 3/4 мм в изоляции (200 м) Zn — 100 м
9. DIN 125 M 6 Шайба A2 — 500 шт
10. DIN 9021 Шайба кузовная M 8 A2 — 100 шт
11. Шуруп унив. UK APT 9050 4 × 16 A2 — 200 шт
12. Шуруп унив. UK APT 9050 6 × 70 A2 — 50 шт"""
    
    search_results = [
        # Позиция 1 - не найдено
        {
            'order_position': 1,
            'full_query': 'винт DIN 603 6 мм 40 мм металл цинк',
            'sku': 'НЕ НАЙДЕНО',
            'name': 'Деталь не найдена в каталоге',
            'type': 'винт',
            'confidence_score': 0.0
        },
        # Позиция 6 - найдено
        {
            'order_position': 6,
            'full_query': 'гайка M6 DIN 985 A2',
            'sku': '10-0023800',
            'name': 'Гайка DIN 985 A2 M6',
            'type': 'гайка',
            'confidence_score': 0.9
        },
        # Позиция 7 - найдено несколько вариантов
        {
            'order_position': 7,
            'full_query': 'саморез 6,0 мм 180 мм металл железо',
            'sku': '14-0011350',
            'name': 'Саморез конструкц.универсальный 6,0 x 80 желт.,пресс-шайба TX30, Bullit',
            'type': 'саморез',
            'confidence_score': 0.8
        },
        {
            'order_position': 7,
            'full_query': 'саморез 6,0 мм 180 мм металл железо',
            'sku': '14-0010890',
            'name': 'Саморез конструкц.универсальный 6,0 x 120 желт.,потай TX30, Bullit',
            'type': 'саморез',
            'confidence_score': 0.8
        },
        {
            'order_position': 7,
            'full_query': 'саморез 6,0 мм 180 мм металл железо',
            'sku': '14-0011250',
            'name': 'Саморез конструкц.универсальный 6,0 x 180 желт.,пресс-шайба TX30, Bullit',
            'type': 'саморез',
            'confidence_score': 0.9
        }
    ]
    
    print("🧪 Тестирую систему валидации...")
    print(f"📝 Исходный запрос: {len(original_request)} символов")
    print(f"🔍 Результатов поиска: {len(search_results)}")
    
    try:
        # Создаем сервис валидации
        validation_service = ValidationService()
        
        # Запускаем валидацию
        print("\n🔍 Запускаю валидацию...")
        validation_result = await validation_service.validate_search_results(
            original_request=original_request,
            search_results=search_results
        )
        
        # Выводим результат
        print(f"\n✅ Результат валидации:")
        print(f"Статус: {validation_result.get('status')}")
        print(f"Уверенность: {validation_result.get('confidence', 0):.2f}")
        print(f"Сообщение: {validation_result.get('message', '')}")
        
        # Формируем краткое резюме
        summary = validation_service.get_validation_summary(validation_result)
        print(f"\n📋 Краткое резюме:")
        print(summary)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Запускаем тест
    asyncio.run(test_validation())
