#!/usr/bin/env python3
"""
Скрипт для обновления Vector Store в OpenAI Assistant
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def update_vector_store():
    """Обновляет Vector Store в OpenAI Assistant"""
    print("🚀 Обновляю Vector Store в OpenAI Assistant...")
    
    try:
        from services.openai_assistant_service import OpenAIAssistantService
        
        # Создаем сервис
        assistant_service = OpenAIAssistantService()
        
        # Обновляем Vector Store
        await assistant_service.update_vector_store()
        
        print("✅ Vector Store успешно обновлен!")
        print("📊 Теперь Assistant использует актуальные данные из Supabase")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении Vector Store: {e}")
        import traceback
        traceback.print_exc()

async def test_assistant():
    """Тестирует работу Assistant"""
    print("🧪 Тестирую работу OpenAI Assistant...")
    
    try:
        from services.openai_assistant_service import OpenAIAssistantService
        
        # Создаем сервис
        assistant_service = OpenAIAssistantService()
        
        # Тестовый запрос
        test_query = "Нужно 50 болтов М8х20 оцинкованных"
        
        print(f"📝 Тестовый запрос: {test_query}")
        
        # Обрабатываем через Assistant
        response = await assistant_service.process_user_request(test_query)
        
        print("✅ Assistant успешно обработал запрос!")
        print(f"📊 Получено строк: {len(response.get('rows', []))}")
        
        # Показываем первые результаты
        for i, row in enumerate(response.get('rows', [])[:3]):
            print(f"  {i+1}. {row.get('Наименование', 'N/A')} (SKU: {row.get('SKU', 'N/A')})")
        
        # Валидируем через Supabase
        validated_response = await assistant_service.validate_with_supabase(response)
        print("✅ Валидация через Supabase завершена")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании Assistant: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        asyncio.run(test_assistant())
    else:
        asyncio.run(update_vector_store())
