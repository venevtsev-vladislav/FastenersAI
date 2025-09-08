import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# ========================================
# КОНФИГУРАЦИЯ FASTENERSAI BOT
# Оптимизированная версия - убраны дубли
# ========================================

# Telegram Bot конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# OpenAI конфигурация
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-4')

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не установлен в переменных окружения")

# Supabase конфигурация
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def get_telegram_token() -> str:
    """Возвращает токен Telegram бота, проверяя его наличие при обращении."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
    return token

def get_supabase_credentials() -> tuple[str, str]:
    """Возвращает настройки Supabase, проверяя их наличие при обращении."""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        raise ValueError("SUPABASE_URL и SUPABASE_KEY должны быть установлены в переменных окружения")
    return url, key

# Конфигурация базы данных
DB_TABLES = {
    'user_requests': 'user_requests',
    'parts_catalog': 'parts_catalog',
    'aliases': 'aliases'
}

# Лимиты
MAX_EXCEL_ROWS = 1000  # Максимальное количество строк в Excel файле
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB максимальный размер файла

# Фильтрация результатов
MIN_PROBABILITY_THRESHOLD = 25  # Минимальная вероятность для включения в результаты (в процентах)

# Пути к файлам (автоматически определяем)
def get_source_files():
    """Автоматически определяет пути к исходным файлам"""
    source_dir = "Source"
    files = {}
    
    if os.path.exists(source_dir):
        for file in os.listdir(source_dir):
            if file.endswith('.xlsx'):
                files['excel_catalog'] = os.path.join(source_dir, file)
            elif file.endswith('normalized_skus.jsonl'):
                files['normalized_skus'] = os.path.join(source_dir, file)
            elif file.endswith('aliases.jsonl'):
                files['aliases'] = os.path.join(source_dir, file)
    
    return files

SOURCE_FILES = get_source_files()
