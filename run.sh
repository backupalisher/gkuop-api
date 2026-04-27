#!/bin/bash

# ============================================================
# Скрипт управления веб-сервером ГКУ ОП Заявки
# Использование:
#   ./run.sh start    — запустить веб-сервер
#   ./run.sh stop     — остановить веб-сервер
#   ./run.sh restart  — перезапустить веб-сервер
#
# ВНИМАНИЕ: Запускать без sudo!
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.gkuop_web.pid"
LOG_FILE="$SCRIPT_DIR/.gkuop_web.log"
PORT=8002

# Определяем Python из виртуального окружения, если оно есть
if [ -f "$SCRIPT_DIR/.venv/bin/uvicorn" ]; then
    UVICORN="$SCRIPT_DIR/.venv/bin/uvicorn"
elif [ -f "$SCRIPT_DIR/venv/bin/uvicorn" ]; then
    UVICORN="$SCRIPT_DIR/venv/bin/uvicorn"
else
    UVICORN="uvicorn"
fi

start() {
    # Проверяем, не запущен ли уже сервер
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "❌ Сервер уже запущен (PID: $OLD_PID)"
            echo "   Используйте: ./run.sh restart"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi

    echo "🚀 Запуск веб-сервера на порту $PORT..."
    echo "   Uvicorn: $UVICORN"
    cd "$SCRIPT_DIR" || exit 1

    nohup "$UVICORN" web_api.main:app \
        --host 127.0.0.1 \
        --port "$PORT" \
        > "$LOG_FILE" 2>&1 &

    PID=$!
    echo "$PID" > "$PID_FILE"

    # Ждём, пока сервер запустится
    sleep 2
    if kill -0 "$PID" 2>/dev/null; then
        echo "✅ Веб-сервер запущен (PID: $PID)"
        echo "   Откройте в браузере: http://localhost:$PORT"
        echo "   Лог: $LOG_FILE"
    else
        echo "❌ Ошибка запуска сервера"
        cat "$LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

stop() {
    local PID=""

    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
    else
        PID=$(ps aux | grep "uvicorn web_api.main:app" | grep -v grep | awk '{print $2}')
    fi

    if [ -z "$PID" ]; then
        echo "✅ Сервер не запущен"
        return 0
    fi

    echo "🛑 Остановка сервера (PID: $PID)..."
    kill "$PID" 2>/dev/null
    sleep 1

    # Проверяем, остановился ли
    if kill -0 "$PID" 2>/dev/null; then
        echo "   Принудительная остановка..."
        kill -9 "$PID" 2>/dev/null
        sleep 1
    fi

    rm -f "$PID_FILE"
    echo "✅ Сервер остановлен"
}

restart() {
    stop
    sleep 1
    start
}

# --- Главный переключатель ---
case "${1:-}" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    *)
        echo "Использование: $0 {start|stop|restart}"
        echo ""
        echo "  start   — запустить веб-сервер"
        echo "  stop    — остановить веб-сервер"
        echo "  restart — перезапустить веб-сервер"
        echo ""
        echo "  Пример: ./run.sh start"
        exit 1
        ;;
esac
