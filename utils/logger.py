"""
Настройка логирования для проекта
"""

import logging
import os
from datetime import datetime

def setup_logging():
    """Настраивает логирование для проекта"""
    
    # Создаем папку для логов
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Настраиваем корневой логгер
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Логи в консоль
            logging.StreamHandler(),
            # Логи в файл
            logging.FileHandler(
                os.path.join(log_dir, f"bot_{datetime.now().strftime('%Y%m%d')}.log"),
                encoding='utf-8'
            )
        ]
    )
    
    # Устанавливаем уровень для внешних библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)
    
    # Логируем запуск
    logging.info("Логирование настроено")

