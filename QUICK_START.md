# 🚀 Быстрый старт: Развертывание на Railway

## Вариант 1: Автоматический деплой (рекомендуется)

### 1. Подготовьте переменные окружения
```bash
# Скопируйте пример файла
cp railway.env.example .env

# Отредактируйте .env файл, заменив placeholder значения на реальные:
# - TELEGRAM_BOT_TOKEN=ваш_реальный_токен
# - OPENAI_API_KEY=ваш_реальный_ключ
# - SUPABASE_URL=ваш_реальный_url
# - SUPABASE_KEY=ваш_реальный_ключ
```

### 2. Запустите автоматический деплой
```bash
./deploy.sh
```

## Вариант 2: Ручной деплой

### 1. Установите Railway CLI
```bash
npm install -g @railway/cli
```

### 2. Авторизуйтесь
```bash
railway login
```

### 3. Инициализируйте проект
```bash
railway init
```

### 4. Установите переменные окружения
```bash
railway variables set TELEGRAM_BOT_TOKEN=ваш_токен
railway variables set OPENAI_API_KEY=ваш_ключ
railway variables set SUPABASE_URL=ваш_url
railway variables set SUPABASE_KEY=ваш_ключ
railway variables set PORT=8000
```

### 5. Разверните приложение
```bash
railway up
```

## Проверка конфигурации

Перед развертыванием проверьте конфигурацию:
```bash
python check_config.py
```

## Мониторинг

После развертывания:
```bash
# Просмотр логов
railway logs

# Проверка статуса
railway status

# Просмотр переменных
railway variables
```

## Устранение неполадок

### Бот не отвечает
1. Проверьте логи: `railway logs`
2. Убедитесь, что токен правильный
3. Проверьте, что бот не заблокирован в Telegram

### Ошибки подключения к Supabase
1. Проверьте URL и ключ Supabase
2. Убедитесь, что Supabase проект активен
3. Проверьте настройки CORS в Supabase

### Ошибки OpenAI
1. Проверьте API ключ OpenAI
2. Убедитесь, что у вас есть кредиты на счету
3. Проверьте лимиты API

## Полезные ссылки

- [Railway Dashboard](https://railway.app/dashboard)
- [Railway Documentation](https://docs.railway.app/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
