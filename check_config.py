#!/usr/bin/env python3
"""
Скрипт для проверки конфигурации перед развертыванием
"""

import os
import sys
from dotenv import load_dotenv

def check_config():
    """Проверяет конфигурацию приложения"""
    print("🔍 Проверяем конфигурацию FastenersAI Bot...")
    
    # Загружаем переменные окружения
    load_dotenv()
    
    errors = []
    warnings = []
    
    # Проверяем обязательные переменные
    required_vars = {
        'TELEGRAM_BOT_TOKEN': 'Токен Telegram бота',
        'OPENAI_API_KEY': 'API ключ OpenAI',
        'SUPABASE_URL': 'URL Supabase',
        'SUPABASE_KEY': 'Ключ Supabase'
    }
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            errors.append(f"❌ {var} не установлен: {description}")
        elif value.startswith('your_') or value.endswith('_here'):
            errors.append(f"❌ {var} содержит placeholder значение: {description}")
        else:
            print(f"✅ {var}: установлен")
    
    # Проверяем опциональные переменные
    optional_vars = {
        'PORT': 'Порт для Railway (по умолчанию 8000)',
        'OPENAI_MODEL': 'Модель OpenAI (по умолчанию gpt-4)'
    }
    
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"ℹ️  {var}: не установлен (будет использовано значение по умолчанию)")
    
    # Проверяем файлы
    required_files = [
        'bot.py',
        'config.py',
        'Procfile',
        'requirements.txt',
        'runtime.txt'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}: найден")
        else:
            errors.append(f"❌ {file}: не найден")
    
    # Проверяем зависимости
    try:
        import telegram
        print("✅ python-telegram-bot: установлен")
    except ImportError:
        errors.append("❌ python-telegram-bot: не установлен")
    
    try:
        import openai
        print("✅ openai: установлен")
    except ImportError:
        errors.append("❌ openai: не установлен")
    
    try:
        import supabase
        print("✅ supabase: установлен")
    except ImportError:
        errors.append("❌ supabase: не установлен")
    
    # Проверяем подключение к Supabase
    if os.getenv('SUPABASE_URL') and os.getenv('SUPABASE_KEY'):
        try:
            from supabase import create_client, Client
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            supabase_client: Client = create_client(url, key)
            print("✅ Supabase: подключение успешно")
        except Exception as e:
            warnings.append(f"⚠️  Supabase: ошибка подключения - {e}")
    
    # Выводим результаты
    print("\n" + "="*50)
    print("📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ")
    print("="*50)
    
    if errors:
        print("\n❌ ОШИБКИ:")
        for error in errors:
            print(f"  {error}")
    
    if warnings:
        print("\n⚠️  ПРЕДУПРЕЖДЕНИЯ:")
        for warning in warnings:
            print(f"  {warning}")
    
    if not errors and not warnings:
        print("\n✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ УСПЕШНО!")
        print("🚀 Готово к развертыванию на Railway")
        return True
    elif not errors:
        print("\n✅ КРИТИЧЕСКИХ ОШИБОК НЕТ")
        print("⚠️  Есть предупреждения, но можно развертывать")
        return True
    else:
        print("\n❌ ЕСТЬ КРИТИЧЕСКИЕ ОШИБКИ")
        print("🔧 Исправьте ошибки перед развертыванием")
        return False

if __name__ == "__main__":
    success = check_config()
    sys.exit(0 if success else 1)
