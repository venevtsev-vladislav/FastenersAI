#!/usr/bin/env python3
"""
Тест обработки голосовых и фото сообщений через MessageProcessor.
Проверяет, что заглушки MediaProcessor работают без исключений.
"""

import asyncio
from types import SimpleNamespace
import sys
import os

# Устанавливаем необходимые переменные окружения для теста
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "test")

# Добавляем корень проекта в путь для импорта
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.message_processor import MessageProcessor


class DummyFile:
    def __init__(self, file_path: str, file_size: int = 1000):
        self.file_path = file_path
        self.file_size = file_size


class DummyBot:
    async def get_file(self, file_id: str) -> DummyFile:  # type: ignore[override]
        return DummyFile(file_path=f"/tmp/{file_id}")


async def run_test():
    """Запускает проверки обработки голосового и фото сообщений"""
    processor = MessageProcessor(bot=DummyBot())

    # Заглушаем вызов OpenAI
    async def fake_analyze(text: str) -> dict:
        return {}

    processor.openai_service.analyze_with_assistant = fake_analyze  # type: ignore

    # Тест голосового сообщения
    voice_message = SimpleNamespace(
        voice=SimpleNamespace(file_id="voice123", duration=5),
        photo=None,
        audio=None,
        document=None,
        text=None,
    )
    voice_result = await processor._process_voice_message(voice_message)
    print("Voice result:", voice_result)

    # Тест фото сообщения
    photo_obj = SimpleNamespace(file_id="photo123", file_size=500, width=100, height=100)
    photo_message = SimpleNamespace(
        photo=[photo_obj],
        voice=None,
        audio=None,
        document=None,
        text=None,
    )
    photo_result = await processor._process_photo_message(photo_message)
    print("Photo result:", photo_result)


if __name__ == "__main__":
    asyncio.run(run_test())
