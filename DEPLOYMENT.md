# Инструкции по развертыванию FastenersAI

## Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/venevtsev-vladislav/FastenersAI.git
cd FastenersAI
```

### 2. Настройка виртуального окружения

```bash
# Создание виртуального окружения
python -m venv venv

# Активация (macOS/Linux)
source venv/bin/activate

# Активация (Windows)
venv\Scripts\activate
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка переменных окружения

```bash
# Копирование примера конфигурации
cp env_example.txt .env

# Редактирование файла .env
# Добавьте ваши API ключи и настройки
```

### 5. Настройка базы данных

Следуйте инструкциям в `SUPABASE_SETUP.md` для настройки Supabase.

### 6. Запуск бота

```bash
python working_bot.py
```

## Требования к системе

- **Python:** 3.13+
- **Операционная система:** macOS, Linux, Windows
- **Память:** Минимум 2GB RAM
- **Дисковое пространство:** 1GB свободного места

## Переменные окружения

Создайте файл `.env` со следующими переменными:

```env
# Telegram Bot
TELEGRAM_TOKEN=your_telegram_bot_token

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# Supabase
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Логирование
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

## Структура проекта

```
FastenersAI/
├── handlers/           # Обработчики команд
├── services/          # Бизнес-логика
├── database/          # Работа с БД
├── utils/             # Утилиты
├── supabase/          # Supabase функции
├── Source/            # Исходные данные
├── logs/              # Логи
├── reports/           # Отчеты
├── working_bot.py     # Основной файл бота
├── requirements.txt   # Зависимости
└── README.md          # Документация
```

## Мониторинг и логи

### Просмотр логов

```bash
# Логи в реальном времени
tail -f logs/bot_$(date +%Y%m%d).log

# Проверка статуса бота
./check_background.sh
```

### Управление ботом

```bash
# Запуск
python working_bot.py

# Остановка
Ctrl+C

# Перезапуск
./manage_bots.sh restart
```

## Тестирование

```bash
# Запуск всех тестов
python -m pytest tests/

# Тестирование конкретного модуля
python test_validation.py
```

## Обновление проекта

```bash
# Получение последних изменений
git pull origin main

# Обновление зависимостей
pip install -r requirements.txt

# Перезапуск бота
./manage_bots.sh restart
```

## Устранение неполадок

### Проблемы с зависимостями

```bash
# Очистка кэша pip
pip cache purge

# Переустановка зависимостей
pip install --force-reinstall -r requirements.txt
```

### Проблемы с базой данных

```bash
# Проверка подключения
python test_database_connection.py

# Проверка содержимого БД
python check_supabase.py
```

### Проблемы с Telegram API

```bash
# Проверка токена
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

## Безопасность

- Никогда не коммитьте файлы с API ключами
- Используйте `.env` файл для конфиденциальных данных
- Регулярно обновляйте зависимости
- Мониторьте логи на предмет подозрительной активности

## Поддержка

При возникновении проблем:

1. Проверьте логи в папке `logs/`
2. Убедитесь, что все переменные окружения настроены
3. Проверьте подключение к интернету
4. Создайте issue в GitHub репозитории

## Лицензия

MIT License - см. файл LICENSE для подробностей.
