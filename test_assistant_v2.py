#!/usr/bin/env python3
"""
Тест OpenAI Assistant API v2
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_assistant_v2():
    """Тестирует OpenAI Assistant API v2"""
    print("🧪 Тестирую OpenAI Assistant API v2...")
    
    try:
        from services.openai_assistant_service import OpenAIAssistantService
        
        # Создаем сервис
        assistant_service = OpenAIAssistantService()
        
        print("✅ Сервис создан")
        print(f"📋 Assistant ID: {assistant_service.assistant_id}")
        
        # Тест 1: Создание thread
        print("\n1. Тестирую создание thread...")
        thread_id = await assistant_service.create_thread()
        print(f"   ✅ Thread создан: {thread_id}")
        
        # Тест 2: Простой запрос
        print("\n2. Тестирую простой запрос...")
        test_message = "Привет! Как дела?"
        
        try:
            response = await assistant_service.process_user_request(test_message, thread_id)
            print(f"   ✅ Assistant ответил: {response}")
        except Exception as e:
            print(f"   ❌ Ошибка при обработке: {e}")
            
            # Пробуем альтернативный способ
            print("\n3. Пробую альтернативный способ...")
            await test_alternative_approach(assistant_service, thread_id, test_message)
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

async def test_alternative_approach(assistant_service, thread_id, message):
    """Тестирует альтернативный подход"""
    try:
        from openai import AsyncOpenAI
        from config import OPENAI_API_KEY
        
        # Создаем новый клиент напрямую
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            default_headers={"OpenAI-Beta": "assistants=v2"}
        )
        
        print("   🔧 Создаю новый клиент...")
        
        # Отправляем сообщение
        await client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=message
        )
        print("   ✅ Сообщение отправлено")
        
        # Запускаем Assistant
        run = await client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_service.assistant_id
        )
        print(f"   ✅ Run создан: {run.id}")
        
        # Ждем завершения
        while True:
            run_status = await client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            
            if run_status.status in ["completed", "failed", "cancelled"]:
                print(f"   📊 Run завершен со статусом: {run_status.status}")
                break
                
            await asyncio.sleep(1)
        
        if run_status.status == "completed":
            # Получаем ответ
            messages = await client.beta.threads.messages.list(thread_id=thread_id)
            for msg in messages.data:
                if msg.role == "assistant":
                    print(f"   💬 Ответ Assistant: {msg.content[0].text.value}")
                    break
        
    except Exception as e:
        print(f"   ❌ Альтернативный подход тоже не работает: {e}")

async def check_openai_version():
    """Проверяет версию OpenAI библиотеки"""
    try:
        import openai
        print(f"📦 Версия OpenAI библиотеки: {openai.__version__}")
        
        # Проверяем доступные методы
        print("\n🔍 Доступные методы beta:")
        if hasattr(openai, 'beta'):
            beta_methods = dir(openai.beta)
            print(f"   {beta_methods}")
        else:
            print("   ❌ beta модуль не найден")
            
    except Exception as e:
        print(f"❌ Ошибка при проверке версии: {e}")

if __name__ == "__main__":
    print("🚀 Тест OpenAI Assistant API v2")
    print("=" * 40)
    
    # Проверяем версию
    asyncio.run(check_openai_version())
    
    print("\n" + "=" * 40)
    
    # Тестируем Assistant
    asyncio.run(test_assistant_v2())
