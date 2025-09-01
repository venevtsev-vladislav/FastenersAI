# Настройка секретов для GitHub Actions

Для работы автоматического деплоя необходимо настроить секреты в GitHub репозитории.

## Как добавить секреты

1. Перейдите в ваш GitHub репозиторий
2. Нажмите на вкладку **Settings**
3. В левом меню выберите **Secrets and variables** → **Actions**
4. Нажмите **New repository secret**

## Необходимые секреты

### Основные секреты

| Имя секрета | Описание | Пример |
|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Токен вашего Telegram бота | `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz` |
| `OPENAI_API_KEY` | Ключ API OpenAI | `sk-...` |
| `SUPABASE_URL` | URL вашего Supabase проекта | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Anon ключ Supabase | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...` |

### Supabase секреты

| Имя секрета | Описание | Где найти |
|-------------|----------|-----------|
| `SUPABASE_ACCESS_TOKEN` | Access token для Supabase CLI | [Supabase Dashboard](https://supabase.com/dashboard/account/tokens) |
| `SUPABASE_PROJECT_ID` | ID вашего Supabase проекта | URL проекта: `https://supabase.com/dashboard/project/YOUR_PROJECT_ID` |
| `SUPABASE_DB_PASSWORD` | Пароль базы данных | [Supabase Dashboard](https://supabase.com/dashboard/project/YOUR_PROJECT_ID/settings/database) |

### Heroku секреты (опционально)

| Имя секрета | Описание | Где найти |
|-------------|----------|-----------|
| `HEROKU_API_KEY` | API ключ Heroku | [Heroku Account Settings](https://dashboard.heroku.com/account) |
| `HEROKU_APP_NAME` | Имя вашего Heroku приложения | Имя приложения в Heroku Dashboard |
| `HEROKU_EMAIL` | Email вашего Heroku аккаунта | Ваш email в Heroku |

### Railway секреты (опционально)

| Имя секрета | Описание | Где найти |
|-------------|----------|-----------|
| `RAILWAY_TOKEN` | Railway API токен | [Railway Dashboard](https://railway.app/account/tokens) |
| `RAILWAY_SERVICE` | Имя сервиса в Railway | Имя сервиса в Railway Dashboard |

### Docker Hub секреты (опционально)

| Имя секрета | Описание | Где найти |
|-------------|----------|-----------|
| `DOCKER_USERNAME` | Имя пользователя Docker Hub | Ваш username в Docker Hub |
| `DOCKER_PASSWORD` | Пароль или токен Docker Hub | [Docker Hub Account Settings](https://hub.docker.com/settings/security) |

### Telegram уведомления (опционально)

| Имя секрета | Описание | Как получить |
|-------------|----------|--------------|
| `TELEGRAM_BOT_TOKEN` | Токен бота для уведомлений | Создайте бота через @BotFather |
| `TELEGRAM_CHAT_ID` | ID чата для уведомлений | Отправьте сообщение боту и получите chat_id |

## Получение значений секретов

### Supabase

1. **SUPABASE_URL и SUPABASE_KEY:**
   - Перейдите в [Supabase Dashboard](https://supabase.com/dashboard)
   - Выберите ваш проект
   - Перейдите в **Settings** → **API**
   - Скопируйте **Project URL** и **anon public** ключ

2. **SUPABASE_ACCESS_TOKEN:**
   - Перейдите в [Account Settings](https://supabase.com/dashboard/account/tokens)
   - Нажмите **Generate new token**
   - Скопируйте токен

3. **SUPABASE_PROJECT_ID:**
   - Из URL вашего проекта: `https://supabase.com/dashboard/project/YOUR_PROJECT_ID`
   - Скопируйте `YOUR_PROJECT_ID`

### Telegram

1. **TELEGRAM_BOT_TOKEN:**
   - Напишите @BotFather в Telegram
   - Создайте нового бота: `/newbot`
   - Скопируйте полученный токен

2. **TELEGRAM_CHAT_ID:**
   - Напишите вашему боту
   - Перейдите по ссылке: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Найдите `chat.id` в ответе

### Heroku

1. **HEROKU_API_KEY:**
   - Перейдите в [Account Settings](https://dashboard.heroku.com/account)
   - Нажмите **Reveal** рядом с API Key

2. **HEROKU_APP_NAME:**
   - Создайте приложение в Heroku Dashboard
   - Скопируйте имя приложения

### Railway

1. **RAILWAY_TOKEN:**
   - Перейдите в [Railway Dashboard](https://railway.app/account/tokens)
   - Создайте новый токен

2. **RAILWAY_SERVICE:**
   - Создайте проект в Railway
   - Скопируйте имя сервиса

## Проверка настроек

После добавления всех секретов:

1. Сделайте push в ветку `main`
2. Перейдите в **Actions** вкладку GitHub
3. Убедитесь, что workflow запустился
4. Проверьте логи на наличие ошибок

## Безопасность

- Никогда не коммитьте секреты в код
- Регулярно обновляйте токены
- Используйте минимальные права доступа
- Мониторьте использование токенов

## Устранение проблем

### Ошибка "Secret not found"
- Проверьте правильность названия секрета
- Убедитесь, что секрет добавлен в правильный репозиторий

### Ошибка аутентификации
- Проверьте правильность токенов
- Убедитесь, что токены не истекли
- Проверьте права доступа токенов

### Ошибка деплоя
- Проверьте логи в GitHub Actions
- Убедитесь, что все зависимости установлены
- Проверьте конфигурацию платформы деплоя
