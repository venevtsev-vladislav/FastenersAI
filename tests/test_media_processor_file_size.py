#!/usr/bin/env python3
"""Тест проверки ограничения размера файлов в MediaProcessor"""
import asyncio
import sys
import os
from types import SimpleNamespace

# Добавляем корень проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Устанавливаем необходимые переменные окружения для импорта config
os.environ.setdefault('TELEGRAM_BOT_TOKEN', 'test')
os.environ.setdefault('OPENAI_API_KEY', 'test')
os.environ.setdefault('SUPABASE_URL', 'test')
os.environ.setdefault('SUPABASE_KEY', 'test')

from services.media_processor import MediaProcessor
from config import MAX_FILE_SIZE

class DummyFile:
    async def download_to_drive(self, dest):
        with open(dest, 'wb') as f:
            f.write(b'')

class DummyBot:
    async def get_file(self, file_id):
        return DummyFile()

def create_message(size):
    document = SimpleNamespace(file_id="file", file_size=size,
                               file_name="test.pdf", mime_type="application/pdf")
    return SimpleNamespace(document=document, photo=None, voice=None, caption=None)

async def test_file_size():
    processor = MediaProcessor()
    context = SimpleNamespace(bot=DummyBot())

    small_message = create_message(5 * 1024 * 1024)  # 5MB
    large_message = create_message(55 * 1024 * 1024)  # 55MB

    small_result = await processor._process_document(small_message, context)
    large_result = await processor._process_document(large_message, context)

    assert 'error' not in small_result, "5MB file should be accepted"
    assert 'error' in large_result, "55MB file should be rejected"

    print("5MB result:", small_result)
    print("55MB result:", large_result)

if __name__ == "__main__":
    asyncio.run(test_file_size())

