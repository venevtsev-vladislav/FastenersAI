#!/bin/bash

echo "🔍 Детальная проверка процессов в фоне"
echo "======================================"

echo ""
echo "📊 Python процессы:"
echo "-------------------"
ps aux | grep python | grep -v grep

echo ""
echo "🤖 Процессы ботов:"
echo "------------------"
if pgrep -f "bot.py" > /dev/null; then
    echo "✅ bot.py запущен:"
    ps aux | grep "bot.py" | grep -v grep
else
    echo "❌ bot.py НЕ запущен"
fi

if pgrep -f "working_bot.py" > /dev/null; then
    echo "✅ working_bot.py запущен:"
    ps aux | grep "working_bot.py" | grep -v grep
else
    echo "❌ working_bot.py НЕ запущен"
fi

echo ""
echo "🌐 Сетевые соединения:"
echo "----------------------"
if command -v lsof >/dev/null 2>&1; then
    echo "Порты в LISTEN:"
    lsof -i -P | grep LISTEN | head -10
else
    echo "lsof не установлен, используем netstat..."
    if command -v netstat >/dev/null 2>&1; then
        netstat -tulpn | grep python | head -10
    else
        echo "netstat не доступен"
    fi
fi

echo ""
echo "📁 Логи ботов:"
echo "--------------"
if [ -f "bot.log" ]; then
    echo "✅ bot.log найден (размер: $(du -h bot.log | cut -f1))"
    echo "Последние 5 строк:"
    tail -5 bot.log
else
    echo "❌ bot.log не найден"
fi

if [ -f "logs/bot_$(date +%Y%m%d).log" ]; then
    echo "✅ Лог за сегодня найден"
    echo "Последние 3 строки:"
    tail -3 "logs/bot_$(date +%Y%m%d).log"
else
    echo "❌ Лог за сегодня не найден"
fi

echo ""
echo "💾 Использование памяти:"
echo "------------------------"
ps aux | grep -E "(bot|working_bot)" | grep -v grep | awk '{print $6 " KB - " $11}' | head -5

echo ""
echo "🔧 Рекомендации:"
echo "----------------"
if pgrep -f "bot.py" > /dev/null && pgrep -f "working_bot.py" > /dev/null; then
    echo "⚠️  ОБА бота запущены! Рекомендуется остановить старый:"
    echo "   ./manage_bots.sh stop-old"
elif pgrep -f "bot.py" > /dev/null; then
    echo "✅ Только новый бот (bot.py) запущен - отлично!"
elif pgrep -f "working_bot.py" > /dev/null; then
    echo "⚠️  Только старый бот (working_bot.py) запущен. Запустите новый:"
    echo "   ./manage_bots.sh start-new"
else
    echo "❌ Ни один бот не запущен. Запустите новый:"
    echo "   ./manage_bots.sh start-new"
fi

echo ""
echo "======================================"
