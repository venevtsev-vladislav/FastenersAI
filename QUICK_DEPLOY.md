# Быстрый деплой FastenersAI

## 🚀 Варианты деплоя

### 1. Railway (Рекомендуется)

Railway - отличная платформа для Python приложений с бесплатным тарифом.

#### Шаги:
1. Зарегистрируйтесь на [Railway.app](https://railway.app)
2. Подключите ваш GitHub репозиторий
3. Railway автоматически определит Python проект
4. Добавьте переменные окружения:
   ```
   TELEGRAM_TOKEN=your_bot_token
   OPENAI_API_KEY=your_openai_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
5. Нажмите Deploy

### 2. Heroku

#### Шаги:
1. Создайте аккаунт на [Heroku.com](https://heroku.com)
2. Установите Heroku CLI
3. Выполните команды:
   ```bash
   heroku login
   heroku create your-app-name
   git push heroku main
   heroku config:set TELEGRAM_TOKEN=your_bot_token
   heroku config:set OPENAI_API_KEY=your_openai_key
   heroku config:set SUPABASE_URL=your_supabase_url
   heroku config:set SUPABASE_KEY=your_supabase_key
   ```

### 3. Docker + VPS

#### Шаги:
1. Соберите Docker образ:
   ```bash
   docker build -t fastenersai .
   ```
2. Запустите контейнер:
   ```bash
   docker run -d \
     --name fastenersai-bot \
     -e TELEGRAM_TOKEN=your_bot_token \
     -e OPENAI_API_KEY=your_openai_key \
     -e SUPABASE_URL=your_supabase_url \
     -e SUPABASE_KEY=your_supabase_key \
     fastenersai
   ```

### 4. Локальный сервер

#### Шаги:
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/venevtsev-vladislav/FastenersAI.git
   cd FastenersAI
   ```
2. Создайте виртуальное окружение:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # или
   venv\Scripts\activate     # Windows
   ```
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Создайте .env файл:
   ```env
   TELEGRAM_TOKEN=your_bot_token
   OPENAI_API_KEY=your_openai_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
5. Запустите бота:
   ```bash
   python working_bot.py
   ```

## 🔧 Настройка переменных окружения

### Обязательные переменные:

| Переменная | Описание | Пример |
|------------|----------|---------|
| `TELEGRAM_TOKEN` | Токен Telegram бота | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `OPENAI_API_KEY` | Ключ OpenAI API | `sk-...` |
| `SUPABASE_URL` | URL Supabase проекта | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Anon ключ Supabase | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |

### Опциональные переменные:

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `LOG_LEVEL` | Уровень логирования | `INFO` |
| `LOG_FILE` | Файл для логов | `logs/bot.log` |

## 📋 Чек-лист деплоя

- [ ] Получен токен Telegram бота от @BotFather
- [ ] Получен API ключ OpenAI
- [ ] Настроен Supabase проект
- [ ] Получены Supabase URL и ключ
- [ ] Все переменные окружения настроены
- [ ] Бот успешно запущен
- [ ] Протестирована команда /start
- [ ] Проверена работа поиска

## 🐛 Устранение проблем

### Бот не отвечает
1. Проверьте правильность TELEGRAM_TOKEN
2. Убедитесь, что бот не заблокирован
3. Проверьте логи на ошибки

### Ошибки с OpenAI
1. Проверьте правильность OPENAI_API_KEY
2. Убедитесь, что у вас есть кредиты на счете
3. Проверьте лимиты API

### Ошибки с Supabase
1. Проверьте правильность SUPABASE_URL и SUPABASE_KEY
2. Убедитесь, что таблицы созданы
3. Проверьте права доступа

### Проблемы с зависимостями
1. Обновите requirements.txt
2. Переустановите зависимости
3. Проверьте версию Python (должна быть 3.13+)

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения настроены
3. Создайте issue в GitHub репозитории
4. Опишите проблему подробно с логами

## 🔄 Обновление

Для обновления бота:

1. Получите последние изменения:
   ```bash
   git pull origin main
   ```

2. Перезапустите приложение:
   - **Railway/Heroku**: Автоматически при push
   - **Docker**: `docker-compose up -d --build`
   - **Локально**: `python working_bot.py`

## 📊 Мониторинг

### Логи
- Логи сохраняются в папке `logs/`
- Формат: `bot_YYYYMMDD.log`
- Для просмотра: `tail -f logs/bot_$(date +%Y%m%d).log`

### Статус
- Проверка статуса: `./check_background.sh`
- Управление: `./manage_bots.sh`

## 🎯 Готово!

После успешного деплоя ваш бот будет доступен в Telegram по имени, которое вы указали при создании через @BotFather.
