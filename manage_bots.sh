#!/bin/bash

echo "🤖 Управление ботами крепежа"

# Функция проверки статуса
check_status() {
    echo "📊 Статус ботов:"
    
    # Проверяем working_bot.py
    if pgrep -f "working_bot.py" > /dev/null; then
        echo "  ✅ working_bot.py запущен (PID: $(pgrep -f "working_bot.py"))"
    else
        echo "  ❌ working_bot.py НЕ запущен"
    fi
    
    # Проверяем bot.py
    if pgrep -f "bot.py" > /dev/null; then
        echo "  ✅ bot.py запущен (PID: $(pgrep -f "bot.py"))"
    else
        echo "  ❌ bot.py НЕ запущен"
    fi
    
    echo ""
}

# Функция остановки старого бота
stop_old_bot() {
    echo "🛑 Останавливаю старый бот (working_bot.py)..."
    
    if pgrep -f "working_bot.py" > /dev/null; then
        pkill -f "working_bot.py"
        echo "  ✅ working_bot.py остановлен"
    else
        echo "  ⚠️  working_bot.py уже не запущен"
    fi
    
    echo ""
}

# Функция запуска нового бота
start_new_bot() {
    echo "🚀 Запускаю новый бот (bot.py)..."
    
    if pgrep -f "bot.py" > /dev/null; then
        echo "  ⚠️  bot.py уже запущен"
    else
        echo "  📝 Запускаю в фоне..."
        nohup python3 bot.py > bot.log 2>&1 &
        echo "  ✅ bot.py запущен в фоне (PID: $!)"
        echo "  📝 Логи: bot.log"
    fi
    
    echo ""
}

# Функция перезапуска
restart_bots() {
    echo "🔄 Перезапускаю боты..."
    
    # Останавливаем все
    pkill -f "working_bot.py"
    pkill -f "bot.py"
    
    # Ждем завершения
    sleep 2
    
    # Запускаем новый
    nohup python3 bot.py > bot.log 2>&1 &
    echo "  ✅ Новый бот запущен (PID: $!)"
    
    echo ""
}

# Основное меню
case "$1" in
    "status")
        check_status
        ;;
    "stop-old")
        stop_old_bot
        check_status
        ;;
    "start-new")
        start_new_bot
        check_status
        ;;
    "restart")
        restart_bots
        check_status
        ;;
    "switch")
        stop_old_bot
        start_new_bot
        check_status
        ;;
    *)
        echo "Использование: $0 {status|stop-old|start-new|restart|switch}"
        echo ""
        echo "Команды:"
        echo "  status    - показать статус ботов"
        echo "  stop-old  - остановить старый бот (working_bot.py)"
        echo "  start-new - запустить новый бот (bot.py)"
        echo "  restart   - перезапустить все боты"
        echo "  switch    - переключиться на новый бот"
        echo ""
        echo "Примеры:"
        echo "  $0 status    # Проверить что запущено"
        echo "  $0 switch    # Переключиться на новый бот"
        echo "  $0 restart   # Полный перезапуск"
        ;;
esac
