# Инструкция по управлению ботом "Крепеж AI"

## Текущий статус
✅ **Бот работает** (PID: 55251)

## Команды управления

### Запуск бота
```bash
cd /Users/vladislavvenevtsev/Documents/Крепеж\ 3.0/bot
source venv/bin/activate
python working_bot.py
```

### Остановка бота
```bash
# Найти PID бота
ps aux | grep "python.*working_bot" | grep -v grep

# Остановить процесс
kill <PID>
# или
pkill -f "python.*working_bot"
```

### Перезапуск бота
```bash
# 1. Остановить
pkill -f "python.*working_bot"

# 2. Запустить заново
source venv/bin/activate
python working_bot.py
```

### Просмотр логов
```bash
# Текущий лог
tail -f logs/bot_$(date +%Y%m%d).log

# Все логи
ls -la logs/
cat logs/bot_*.log
```

## Функции бота
- `/start` - приветствие
- `/help` - справка
- Обработка текстовых запросов
- Имитация поиска крепежных деталей

## Мониторинг
- Проверка статуса: `ps aux | grep "python.*working_bot"`
- Проверка API: `curl -s "https://api.telegram.org/bot<TOKEN>/getMe"`
- Логи: `tail -f logs/bot_$(date +%Y%m%d).log`

## Контакты
- Username: @fasteners1234_bot
- Имя: Крепеж AI
- ID: 8108399357

