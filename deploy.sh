#!/bin/bash

# Скрипт для быстрого развертывания на Railway
# Использование: ./deploy.sh

echo "🚀 Начинаем развертывание FastenersAI Bot на Railway..."

# Проверяем, установлен ли Railway CLI
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI не установлен. Устанавливаем..."
    npm install -g @railway/cli
fi

# Проверяем авторизацию
echo "🔐 Проверяем авторизацию в Railway..."
if ! railway whoami &> /dev/null; then
    echo "❌ Не авторизованы в Railway. Авторизуемся..."
    railway login
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Файл .env не найден. Создаем из примера..."
    cp railway.env.example .env
    echo "📝 Пожалуйста, заполните файл .env реальными значениями"
    echo "   Затем запустите скрипт снова: ./deploy.sh"
    exit 1
fi

# Загружаем переменные окружения
echo "📋 Загружаем переменные окружения..."
source .env

# Проверяем обязательные переменные
if [ -z "$TELEGRAM_BOT_TOKEN" ] || [ -z "$OPENAI_API_KEY" ] || [ -z "$SUPABASE_URL" ] || [ -z "$SUPABASE_KEY" ]; then
    echo "❌ Не все обязательные переменные установлены в .env файле"
    echo "   Проверьте: TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, SUPABASE_URL, SUPABASE_KEY"
    exit 1
fi

# Инициализируем проект (если еще не инициализирован)
if [ ! -f "railway.json" ]; then
    echo "🏗️  Инициализируем Railway проект..."
    railway init
fi

# Устанавливаем переменные окружения
echo "🔧 Устанавливаем переменные окружения в Railway..."
railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
railway variables set OPENAI_API_KEY="$OPENAI_API_KEY"
railway variables set SUPABASE_URL="$SUPABASE_URL"
railway variables set SUPABASE_KEY="$SUPABASE_KEY"
railway variables set PORT=8000

# Развертываем приложение
echo "🚀 Развертываем приложение..."
railway up

echo "✅ Развертывание завершено!"
echo "📊 Проверьте логи: railway logs"
echo "🌐 Откройте Railway Dashboard для мониторинга"
echo "🤖 Протестируйте бота в Telegram"
