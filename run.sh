#!/bin/bash

# ============================================================
# Скрипт управления веб-сервером ГКУ ОП Заявки
# Использование:
#   ./run.sh start          — запустить веб-сервер
#   ./run.sh stop           — остановить веб-сервер
#   ./run.sh restart        — перезапустить веб-сервер
#   ./run.sh supervisor     — запустить супервизор (фоновый мониторинг)
#   ./run.sh supervisor-stop — остановить супервизор
#   ./run.sh status         — показать статус сервера и супервизора
#   ./run.sh crash-logs     — показать последние crash-отчёты
#
# ВНИМАНИЕ: Запускать без sudo!
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PID_FILE="$SCRIPT_DIR/.gkuop_web.pid"
SUPERVISOR_PID_FILE="$SCRIPT_DIR/.gkuop_supervisor.pid"
LOG_FILE="$SCRIPT_DIR/.gkuop_web.log"
SUPERVISOR_LOG_FILE="$SCRIPT_DIR/.gkuop_supervisor.log"
PORT=8002
HEALTH_CHECK_URL="http://127.0.0.1:${PORT}/api/health"

# Определяем Python из виртуального окружения, если оно есть
if [ -f "$SCRIPT_DIR/.venv/bin/uvicorn" ]; then
    UVICORN="$SCRIPT_DIR/.venv/bin/uvicorn"
    PYTHON="$SCRIPT_DIR/.venv/bin/python"
elif [ -f "$SCRIPT_DIR/venv/bin/uvicorn" ]; then
    UVICORN="$SCRIPT_DIR/venv/bin/uvicorn"
    PYTHON="$SCRIPT_DIR/venv/bin/python"
else
    UVICORN="uvicorn"
    PYTHON="python3"
fi

# ─── Маркер ручной остановки ──────────────────────────────────────
# Перед отправкой сигнала процессу создаём маркерный файл,
# чтобы crash_monitor понял, что остановка была ручной.
set_manual_stop_marker() {
    local pid="$1"
    # Создаём временный скрипт, который выполнится в контексте процесса
    # через отправку сигнала USR1 (если нужно) или просто пишем маркер
    # в файл, который crash_monitor проверяет
    echo "🔄 Установка маркера ручной остановки для PID $pid..."
    # Используем Python для вызова mark_manual_stop() через HTTP,
    # если сервер ещё отвечает, или через файл-маркер
    local marker_file="$SCRIPT_DIR/.gkuop_manual_stop"
    echo "$pid" > "$marker_file"
    echo "   Маркер сохранён: $marker_file"
}

clear_manual_stop_marker() {
    local marker_file="$SCRIPT_DIR/.gkuop_manual_stop"
    [ -f "$marker_file" ] && rm -f "$marker_file"
}

# ─── Функции управления ───────────────────────────────────────────

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

    clear_manual_stop_marker

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
        clear_manual_stop_marker
        return 0
    fi

    echo "🛑 Остановка сервера (PID: $PID)..."

    # Устанавливаем маркер ручной остановки
    set_manual_stop_marker "$PID"

    # Отправляем SIGTERM
    kill "$PID" 2>/dev/null
    sleep 1

    # Проверяем, остановился ли
    if kill -0 "$PID" 2>/dev/null; then
        echo "   Принудительная остановка..."
        kill -9 "$PID" 2>/dev/null
        sleep 1
    fi

    rm -f "$PID_FILE"
    clear_manual_stop_marker
    echo "✅ Сервер остановлен"
}

restart() {
    stop
    sleep 1
    start
}

# ─── Супервизор ───────────────────────────────────────────────────

supervisor_start() {
    # Проверяем, не запущен ли уже супервизор
    if [ -f "$SUPERVISOR_PID_FILE" ]; then
        OLD_PID=$(cat "$SUPERVISOR_PID_FILE")
        if kill -0 "$OLD_PID" 2>/dev/null; then
            echo "❌ Супервизор уже запущен (PID: $OLD_PID)"
            echo "   Используйте: ./run.sh supervisor-stop"
            exit 1
        else
            rm -f "$SUPERVISOR_PID_FILE"
        fi
    fi

    echo "🔍 Запуск супервизора..."
    echo "   PID-файл сервера: $PID_FILE"
    echo "   Health-check URL: $HEALTH_CHECK_URL"
    cd "$SCRIPT_DIR" || exit 1

    # Запускаем супервизор через Python-модуль
    nohup "$PYTHON" -c "
import sys
sys.path.insert(0, '.')
from utils.supervisor_monitor import SupervisorMonitor

monitor = SupervisorMonitor(
    pid_file='$PID_FILE',
    health_check_url='$HEALTH_CHECK_URL',
    check_interval=30,
    failure_threshold=3,
    auto_restart=False,
    service_name='gkuop-web',
)
monitor.run_forever()
" > "$SUPERVISOR_LOG_FILE" 2>&1 &

    SUPERVISOR_PID=$!
    echo "$SUPERVISOR_PID" > "$SUPERVISOR_PID_FILE"

    sleep 1
    if kill -0 "$SUPERVISOR_PID" 2>/dev/null; then
        echo "✅ Супервизор запущен (PID: $SUPERVISOR_PID)"
        echo "   Лог супервизора: $SUPERVISOR_LOG_FILE"
    else
        echo "❌ Ошибка запуска супервизора"
        cat "$SUPERVISOR_LOG_FILE"
        rm -f "$SUPERVISOR_PID_FILE"
        exit 1
    fi
}

supervisor_stop() {
    local PID=""

    if [ -f "$SUPERVISOR_PID_FILE" ]; then
        PID=$(cat "$SUPERVISOR_PID_FILE")
    else
        PID=$(ps aux | grep "supervisor_monitor" | grep -v grep | awk '{print $2}')
    fi

    if [ -z "$PID" ]; then
        echo "✅ Супервизор не запущен"
        return 0
    fi

    echo "🛑 Остановка супервизора (PID: $PID)..."
    kill "$PID" 2>/dev/null
    sleep 1

    if kill -0 "$PID" 2>/dev/null; then
        kill -9 "$PID" 2>/dev/null
        sleep 1
    fi

    rm -f "$SUPERVISOR_PID_FILE"
    echo "✅ Супервизор остановлен"
}

# ─── Статус ───────────────────────────────────────────────────────

status() {
    echo "═══════════════════════════════════════════"
    echo "  СТАТУС СЕРВИСА ГКУ ОП"
    echo "═══════════════════════════════════════════"

    # Статус веб-сервера
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            echo "✅ Веб-сервер: ЗАПУЩЕН (PID: $PID)"
            # Проверяем health-check
            HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_CHECK_URL" 2>/dev/null || echo "000")
            if [ "$HTTP_STATUS" = "200" ]; then
                echo "   Health-check: ✅ OK (HTTP $HTTP_STATUS)"
            else
                echo "   Health-check: ❌ FAIL (HTTP $HTTP_STATUS)"
            fi
        else
            echo "❌ Веб-сервер: PID найден, но процесс не запущен"
            rm -f "$PID_FILE"
        fi
    else
        # Ищем процесс в системе
        PID=$(ps aux | grep "uvicorn web_api.main:app" | grep -v grep | awk '{print $2}')
        if [ -n "$PID" ]; then
            echo "⚠️ Веб-сервер: ЗАПУЩЕН (PID: $PID, но PID-файл отсутствует)"
        else
            echo "⏹️  Веб-сервер: НЕ ЗАПУЩЕН"
        fi
    fi

    # Статус супервизора
    if [ -f "$SUPERVISOR_PID_FILE" ]; then
        SUP_PID=$(cat "$SUPERVISOR_PID_FILE")
        if kill -0 "$SUP_PID" 2>/dev/null; then
            echo "✅ Супервизор: ЗАПУЩЕН (PID: $SUP_PID)"
        else
            echo "❌ Супервизор: PID найден, но процесс не запущен"
            rm -f "$SUPERVISOR_PID_FILE"
        fi
    else
        SUP_PID=$(ps aux | grep "supervisor_monitor" | grep -v grep | awk '{print $2}')
        if [ -n "$SUP_PID" ]; then
            echo "⚠️ Супервизор: ЗАПУЩЕН (PID: $SUP_PID, но PID-файл отсутствует)"
        else
            echo "⏹️  Супервизор: НЕ ЗАПУЩЕН"
        fi
    fi

    # Crash-логи
    CRASH_COUNT=$(ls -1 "$SCRIPT_DIR/logs/crashes/crash_"*.json 2>/dev/null | wc -l)
    echo "📋 Crash-отчётов: $CRASH_COUNT"

    echo "═══════════════════════════════════════════"
}

# ─── Crash-логи ───────────────────────────────────────────────────

crash_logs() {
    local limit="${2:-10}"
    echo "═══════════════════════════════════════════"
    echo "  ПОСЛЕДНИЕ CRASH-ОТЧЁТЫ (последние $limit)"
    echo "═══════════════════════════════════════════"

    local crash_dir="$SCRIPT_DIR/logs/crashes"
    if [ ! -d "$crash_dir" ]; then
        echo "   Директория crash-логов не найдена"
        return 0
    fi

    local files=($(ls -t "$crash_dir"/crash_*.json 2>/dev/null))
    local count=0

    for f in "${files[@]}"; do
        if [ $count -ge "$limit" ]; then
            break
        fi
        echo ""
        echo "─── Crash-отчёт: $(basename "$f") ───"
        # Выводим ключевые поля из JSON
        $PYTHON -c "
import json
with open('$f', 'r') as fh:
    r = json.load(fh)
print(f\"  Время: {r.get('timestamp', 'N/A')}\")
print(f\"  Причина: {r.get('reason', 'N/A')}\")
print(f\"  Ручная остановка: {r.get('is_manual_stop', 'N/A')}\")
print(f\"  PID: {r.get('process', {}).get('pid', 'N/A')}\")
mem = r.get('process_info', {}).get('memory', {})
if 'rss_mb' in mem:
    print(f\"  Память (RSS): {mem['rss_mb']} MB\")
print(f\"  Код возврата: {r.get('exit_code', 'N/A')}\")
last_req = r.get('last_request', {})
if last_req.get('method'):
    print(f\"  Последний запрос: {last_req['method']} {last_req.get('path', '')}\")
" 2>/dev/null || echo "  (ошибка чтения)"
        count=$((count + 1))
    done

    if [ $count -eq 0 ]; then
        echo "   Crash-отчётов не найдено"
    fi
    echo ""
    echo "═══════════════════════════════════════════"
}

# ─── Главный переключатель ────────────────────────────────────────
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
    supervisor)
        supervisor_start
        ;;
    supervisor-stop)
        supervisor_stop
        ;;
    status)
        status
        ;;
    crash-logs)
        crash_logs "$@"
        ;;
    *)
        echo "Использование: $0 {start|stop|restart|supervisor|supervisor-stop|status|crash-logs}"
        echo ""
        echo "  start           — запустить веб-сервер"
        echo "  stop            — остановить веб-сервер"
        echo "  restart         — перезапустить веб-сервер"
        echo "  supervisor      — запустить супервизор (фоновый мониторинг)"
        echo "  supervisor-stop — остановить супервизор"
        echo "  status          — показать статус сервера и супервизора"
        echo "  crash-logs [N]  — показать последние N crash-отчётов (по умолч. 10)"
        echo ""
        echo "  Пример: ./run.sh start"
        echo "  Пример: ./run.sh status"
        echo "  Пример: ./run.sh crash-logs 5"
        exit 1
        ;;
esac
