# Развертывание FastenersAI Bot на Railway

## Подготовка к развертыванию

### 1. Установка Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Авторизация в Railway
```bash
railway login
```

### 3. Создание проекта
```bash
railway init
```

## Настройка переменных окружения

В Railway Dashboard добавьте следующие переменные окружения:

- `TELEGRAM_BOT_TOKEN` - токен вашего Telegram бота
- `OPENAI_API_KEY` - API ключ OpenAI
- `SUPABASE_URL` - URL вашего Supabase проекта
- `SUPABASE_KEY` - анонимный ключ Supabase

## Развертывание

### Автоматическое развертывание
```bash
railway up
```

### Или через GitHub интеграцию
1. Подключите ваш GitHub репозиторий к Railway
2. Выберите ветку `refactor/revision-20250101` или тег `v2.0`
3. Railway автоматически развернет приложение

## Проверка развертывания

После развертывания проверьте:
1. Логи в Railway Dashboard
2. Работоспособность бота в Telegram
3. Подключение к Supabase

## Структура проекта

- `bot.py` - основной файл бота
- `Procfile` - конфигурация для Railway
- `runtime.txt` - версия Python
- `requirements.txt` - зависимости Python
- `config.py` - конфигурация приложения

## Устранение неполадок

1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте подключение к внешним сервисам (Supabase, OpenAI)
