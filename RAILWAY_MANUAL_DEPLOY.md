# Ручное развертывание FastenersAI Bot на Railway

## Шаг 1: Подготовка проекта

### 1.1 Убедитесь, что все файлы готовы:
- ✅ `bot.py` - основной файл бота
- ✅ `Procfile` - конфигурация для Railway
- ✅ `requirements.txt` - зависимости Python
- ✅ `runtime.txt` - версия Python
- ✅ `config.py` - конфигурация приложения

### 1.2 Проверьте переменные окружения:
Создайте файл `.env` локально для тестирования:
```bash
TELEGRAM_BOT_TOKEN=your_actual_token
OPENAI_API_KEY=your_actual_key
SUPABASE_URL=your_actual_url
SUPABASE_KEY=your_actual_key
PORT=8000
```

## Шаг 2: Установка Railway CLI

### 2.1 Установите Railway CLI:
```bash
npm install -g @railway/cli
```

### 2.2 Авторизуйтесь в Railway:
```bash
railway login
```

## Шаг 3: Создание проекта в Railway

### 3.1 Инициализируйте проект:
```bash
cd /Users/vladislavvenevtsev/Documents/Крепеж\ 3.0/bot
railway init
```

### 3.2 Выберите опции:
- Создать новый проект: `y`
- Название проекта: `fasteners-ai-bot`
- Описание: `Telegram bot for fastener search`

## Шаг 4: Настройка переменных окружения

### 4.1 Добавьте переменные через CLI:
```bash
railway variables set TELEGRAM_BOT_TOKEN=your_actual_token
railway variables set OPENAI_API_KEY=your_actual_key
railway variables set SUPABASE_URL=your_actual_url
railway variables set SUPABASE_KEY=your_actual_key
railway variables set PORT=8000
```

### 4.2 Или через веб-интерфейс:
1. Откройте Railway Dashboard
2. Выберите ваш проект
3. Перейдите в раздел "Variables"
4. Добавьте все переменные из `railway.env`

## Шаг 5: Развертывание

### 5.1 Загрузите код:
```bash
railway up
```

### 5.2 Или подключите GitHub:
1. В Railway Dashboard нажмите "Connect GitHub"
2. Выберите ваш репозиторий
3. Выберите ветку `refactor/revision-20250101`
4. Railway автоматически развернет приложение

## Шаг 6: Проверка развертывания

### 6.1 Проверьте логи:
```bash
railway logs
```

### 6.2 Или в веб-интерфейсе:
1. Откройте Railway Dashboard
2. Выберите ваш проект
3. Перейдите в раздел "Deployments"
4. Нажмите на последний деплой
5. Проверьте логи на наличие ошибок

### 6.3 Проверьте работоспособность:
1. Найдите ваш бот в Telegram
2. Отправьте команду `/start`
3. Проверьте, что бот отвечает

## Шаг 7: Устранение неполадок

### 7.1 Частые ошибки:

**Ошибка: "TELEGRAM_BOT_TOKEN не установлен"**
- Проверьте, что переменная `TELEGRAM_BOT_TOKEN` установлена в Railway
- Убедитесь, что токен правильный

**Ошибка: "Module not found"**
- Проверьте `requirements.txt`
- Убедитесь, что все зависимости указаны

**Ошибка: "Port already in use"**
- Railway автоматически назначает порт
- Убедитесь, что в коде используется `os.getenv('PORT', 8000)`

### 7.2 Полезные команды:
```bash
# Просмотр переменных
railway variables

# Просмотр логов
railway logs

# Перезапуск сервиса
railway redeploy

# Просмотр статуса
railway status
```

## Шаг 8: Мониторинг

### 8.1 Настройте мониторинг:
1. В Railway Dashboard перейдите в "Metrics"
2. Настройте алерты для ошибок
3. Мониторьте использование ресурсов

### 8.2 Логирование:
- Логи автоматически сохраняются в Railway
- Используйте `railway logs` для просмотра
- Настройте ротацию логов при необходимости

## Дополнительные настройки

### Настройка домена:
1. В Railway Dashboard перейдите в "Settings"
2. Нажмите "Generate Domain"
3. Или подключите собственный домен

### Настройка автодеплоя:
1. Подключите GitHub репозиторий
2. Включите автодеплой для нужной ветки
3. Railway будет автоматически развертывать изменения

## Контакты и поддержка

При возникновении проблем:
1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все переменные окружения установлены
3. Проверьте подключение к внешним сервисам (Supabase, OpenAI)
4. Обратитесь к документации Railway: https://docs.railway.app/
