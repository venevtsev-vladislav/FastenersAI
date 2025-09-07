# 🚀 Развертывание FastenersAI Bot на Railway

## ✅ Что уже готово

Проект полностью подготовлен для развертывания на Railway:

- ✅ Конфигурация обновлена для Railway
- ✅ Добавлена обработка порта
- ✅ Проверки переменных окружения
- ✅ Обновлены зависимости
- ✅ Созданы скрипты для автоматизации
- ✅ Написаны подробные инструкции

## 🎯 Следующие шаги

### 1. Получите необходимые токены и ключи

Вам понадобятся:
- **TELEGRAM_BOT_TOKEN** - создайте бота через @BotFather в Telegram
- **OPENAI_API_KEY** - получите на https://platform.openai.com/
- **SUPABASE_URL** и **SUPABASE_KEY** - из вашего Supabase проекта

### 2. Выберите способ развертывания

#### Вариант A: Автоматический (рекомендуется)
```bash
# 1. Заполните .env файл реальными значениями
cp railway.env.example .env
# Отредактируйте .env файл

# 2. Запустите автоматический деплой
./deploy.sh
```

#### Вариант B: Ручной
Следуйте инструкциям в `RAILWAY_MANUAL_DEPLOY.md`

### 3. Проверьте развертывание

```bash
# Проверьте логи
railway logs

# Протестируйте бота в Telegram
# Отправьте команду /start
```

## 📁 Созданные файлы

- `railway.env` - пример переменных окружения
- `deploy.sh` - скрипт автоматического развертывания
- `check_config.py` - проверка конфигурации
- `RAILWAY_MANUAL_DEPLOY.md` - подробные инструкции
- `QUICK_START.md` - быстрый старт

## 🔧 Основные изменения

### bot.py
- Добавлена обработка порта для Railway
- Улучшено логирование

### config.py
- Добавлены проверки обязательных переменных
- Улучшена обработка ошибок

### requirements.txt
- Добавлен gunicorn для продакшена

## 🆘 Поддержка

При возникновении проблем:

1. **Проверьте конфигурацию:**
   ```bash
   python check_config.py
   ```

2. **Проверьте логи Railway:**
   ```bash
   railway logs
   ```

3. **Проверьте переменные окружения:**
   ```bash
   railway variables
   ```

4. **Перезапустите сервис:**
   ```bash
   railway redeploy
   ```

## 📚 Дополнительные ресурсы

- [Railway Documentation](https://docs.railway.app/)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI API](https://platform.openai.com/docs)
- [Supabase Documentation](https://supabase.com/docs)

---

**Готово к развертыванию! 🚀**
