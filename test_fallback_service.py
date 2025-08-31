#!/usr/bin/env python3
"""
Тестирование fallback сервиса для неудачных запросов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from services.query_fallback_service import QueryFallbackService

async def test_fallback_service():
    """Тестирует fallback сервис"""
    fallback_service = QueryFallbackService()
    
    # Тестовые неудачные запросы
    test_queries = [
        "какая-то штука для крепления",           # Неясный запрос
        "болт с чем-то там",                       # Неполный запрос
        "винт для мебели",                         # Неясное назначение
        "что-то металлическое",                    # Очень неясный запрос
        "болт с грибком М6 на 40, цинкованный",   # Сложный, но понятный
        "винт мебельный 6 мм длиной 40",          # Нестандартная формулировка
        "гайка шестигранная М8",                   # Неполная информация
    ]
    
    print("🧪 Тестирование fallback сервиса\n")
    
    for query in test_queries:
        print(f"📝 Запрос: {query}")
        
        # Обрабатываем неудачный запрос
        fallback_result = await fallback_service.process_failed_query(
            original_query=query,
            search_results=[]  # Пустые результаты
        )
        
        print(f"   📊 Результат: {fallback_result.get('reason', '')}")
        print(f"   🤖 Может нормализовать: {fallback_result.get('can_normalize', False)}")
        
        if fallback_result.get('can_normalize'):
            print(f"   ✅ Нормализованный запрос: {fallback_result.get('normalized_query', '')}")
        else:
            print(f"   ❌ Обратная связь: {fallback_result.get('ai_feedback', '')[:100]}...")
        
        # Получаем понятное сообщение для пользователя
        user_message = fallback_service.get_user_friendly_message(fallback_result)
        print(f"   💬 Сообщение пользователю: {user_message[:100]}...")
        
        print("-" * 60)

if __name__ == "__main__":
    asyncio.run(test_fallback_service())
