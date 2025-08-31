#!/usr/bin/env python3
"""
Тест работы GPT интеграции
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_gpt():
    """Тестирует работу GPT"""
    print("🧠 Тестирую GPT интеграцию...")
    
    try:
        # Импортируем сервис
        from services.openai_service import OpenAIService
        
        # Создаем экземпляр
        gpt_service = OpenAIService()
        print("   ✅ GPT сервис создан")
        
        # Тестируем анализ запроса
        test_query = "Нужен болт М8х20 с шестигранной головкой"
        print(f"   🔍 Тестирую запрос: '{test_query}'")
        
        result = await gpt_service.analyze_user_intent(test_query)
        print("   ✅ GPT анализ завершен")
        
        # Показываем результат
        print("   📊 Результат анализа:")
        for key, value in result.items():
            if value is not None:
                print(f"      {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_gpt())
    if success:
        print("\n✅ GPT тест пройден! OpenAI API работает.")
    else:
        print("\n❌ GPT тест не пройден. Проверьте API ключ.")
        sys.exit(1)

