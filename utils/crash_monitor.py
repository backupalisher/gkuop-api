"""
Модуль расширенного мониторинга и логирования аварийных завершений сервиса.

Обеспечивает:
- Перехват всех сигналов завершения (SIGTERM, SIGINT, SIGQUIT, SIGHUP)
- Перехват критических ошибок интерпретатора (sys.excepthook)
- Сбор расширенной диагностики: traceback, память, CPU, PID, последний запрос
- Детектирование ручной остановки через run.sh
- Ведение структурированного crash-лога с временными метками
- Ротацию crash-логов
"""

import os
import sys
import signal
import traceback
import threading
import time
import json
import logging
import atexit
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, Callable

logger = logging.getLogger(__name__)


# ─── Конфигурация ─────────────────────────────────────────────────────

CRASH_LOG_DIR = Path("logs/crashes")
CRASH_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Максимальное количество crash-логов (старые удаляются)
MAX_CRASH_LOGS = 50

# Флаг: был ли сервис остановлен вручную через run.sh
_manual_stop_detected = False

# Путь к маркерному файлу ручной остановки (создаётся run.sh)
MANUAL_STOP_MARKER_FILE = Path(".gkuop_manual_stop")

# Флаг: была ли уже вызвана процедура shutdown (чтобы избежать рекурсии)
_shutdown_in_progress = False
_shutdown_lock = threading.Lock()

# Последний обработанный запрос/задача
_last_request: Dict[str, Any] = {
    "method": None,
    "path": None,
    "client_ip": None,
    "timestamp": None,
    "body_preview": None,
}

# PID процесса
_PID = os.getpid()

# Время запуска процесса
_PROCESS_START_TIME = time.time()

# Ссылка на callback для graceful shutdown
_shutdown_callback: Optional[Callable] = None


# ─── Вспомогательные функции ─────────────────────────────────────────

def _get_process_info() -> Dict[str, Any]:
    """Сбор информации о процессе: память, CPU, файловые дескрипторы."""
    info = {
        "pid": _PID,
        "ppid": os.getppid(),
        "uptime_seconds": round(time.time() - _PROCESS_START_TIME, 2),
        "process_start_time": datetime.fromtimestamp(
            _PROCESS_START_TIME, tz=timezone.utc
        ).isoformat(),
    }
    try:
        import psutil
        process = psutil.Process(_PID)
        mem_info = process.memory_info()
        info["memory"] = {
            "rss_bytes": mem_info.rss,
            "rss_mb": round(mem_info.rss / 1024 / 1024, 2),
            "vms_bytes": mem_info.vms,
            "vms_mb": round(mem_info.vms / 1024 / 1024, 2),
            "percent": process.memory_percent(),
        }
        info["cpu"] = {
            "percent": process.cpu_percent(interval=0.1),
            "num_threads": process.num_threads(),
            "cpu_times": {
                "user": round(process.cpu_times().user, 2),
                "system": round(process.cpu_times().system, 2),
            },
        }
        info["open_fds"] = process.num_fds()
        info["connections"] = len(process.connections())

        # Системная память
        sys_mem = psutil.virtual_memory()
        info["system_memory"] = {
            "total_mb": round(sys_mem.total / 1024 / 1024, 2),
            "available_mb": round(sys_mem.available / 1024 / 1024, 2),
            "used_mb": round(sys_mem.used / 1024 / 1024, 2),
            "percent": sys_mem.percent,
        }
        # Swap
        swap = psutil.swap_memory()
        info["swap"] = {
            "total_mb": round(swap.total / 1024 / 1024, 2),
            "used_mb": round(swap.used / 1024 / 1024, 2),
            "percent": swap.percent,
        }
    except ImportError:
        info["memory"] = {"error": "psutil not installed"}
        info["cpu"] = {"error": "psutil not installed"}
    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
        info["memory"] = {"error": str(e)}
        info["cpu"] = {"error": str(e)}
    return info


def _get_recent_logs(num_lines: int = 50) -> list:
    """Чтение последних N строк из основного лога сервиса."""
    try:
        # Ищем файл лога за сегодня
        today = datetime.now().strftime("%Y%m%d")
        log_dir = Path("logs")
        if not log_dir.exists():
            return ["[log directory not found]"]

        log_files = sorted(log_dir.glob(f"parser_{today}.log"))
        if not log_files:
            log_files = sorted(log_dir.glob("*.log"))
        if not log_files:
            return ["[no log files found]"]

        latest_log = log_files[-1]
        with open(latest_log, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        tail = lines[-num_lines:] if len(lines) > num_lines else lines
        return [line.rstrip("\n") for line in tail]
    except Exception as e:
        return [f"[error reading logs: {e}]"]


def _get_system_logs_for_pid() -> list:
    """Попытка получить записи из dmesg/journalctl, связанные с OOM и процессом."""
    entries = []
    try:
        import subprocess
        proc_name = os.path.basename(sys.argv[0]) if sys.argv else "python"

        result = subprocess.run(
            ["dmesg", "--level=err,warn", "--since", "30 minutes ago"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.splitlines():
                lowered = line.lower()
                if (
                    proc_name in line
                    or "python" in lowered
                    or "uvicorn" in lowered
                    or "out of memory" in lowered
                    or "killed process" in lowered
                    or "oom" in lowered
                ):
                    entries.append(line.strip())

        journal = subprocess.run(
            [
                "journalctl", "--since", "30 minutes ago", "--no-pager", "-q",
                "-g", "killed process|Out of memory|oom-kill|uvicorn|python",
            ],
            capture_output=True, text=True, timeout=5,
        )
        if journal.returncode == 0 and journal.stdout.strip():
            for line in journal.stdout.splitlines()[-20:]:
                entries.append(line.strip())
    except Exception:
        pass
    return entries


def _get_last_request_info() -> Dict[str, Any]:
    """Получение информации о последнем обработанном запросе."""
    global _last_request
    return dict(_last_request)


def set_last_request(method: str = None, path: str = None,
                     client_ip: str = None, body_preview: str = None):
    """Установка информации о текущем запросе (вызывается из middleware)."""
    global _last_request
    _last_request = {
        "method": method,
        "path": path,
        "client_ip": client_ip,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "body_preview": body_preview,
    }


def mark_manual_stop():
    """Отметить, что остановка была инициирована вручную (из run.sh)."""
    global _manual_stop_detected
    _manual_stop_detected = True


def _check_manual_stop_marker() -> bool:
    """Проверка маркерного файла ручной остановки, созданного run.sh."""
    try:
        if MANUAL_STOP_MARKER_FILE.exists():
            marker_pid_str = MANUAL_STOP_MARKER_FILE.read_text().strip()
            try:
                marker_pid = int(marker_pid_str)
                if marker_pid == _PID or marker_pid == 0:
                    logger.info(
                        f"Обнаружен маркер ручной остановки (PID {marker_pid})"
                    )
                    return True
            except ValueError:
                pass
    except (OSError, IOError) as e:
        logger.warning(f"Ошибка чтения маркерного файла: {e}")
    return False


def set_shutdown_callback(callback: Callable):
    """Установить callback для graceful shutdown."""
    global _shutdown_callback
    _shutdown_callback = callback


# ─── Формирование crash-отчёта ───────────────────────────────────────

def build_crash_report(
    reason: str,
    signal_num: Optional[int] = None,
    exc_info: Optional[Any] = None,
    exit_code: Optional[int] = None,
    is_manual: bool = False,
) -> Dict[str, Any]:
    """Формирование структурированного crash-отчёта."""
    now = datetime.now(timezone.utc)

    report = {
        "crash_id": now.strftime("%Y%m%d_%H%M%S_%f"),
        "timestamp": now.isoformat(),
        "timestamp_local": now.astimezone().isoformat(),
        "reason": reason,
        "is_manual_stop": is_manual,
        "process": {
            "pid": _PID,
            "ppid": os.getppid(),
            "command_line": " ".join(sys.argv) if sys.argv else "unknown",
            "python_version": sys.version,
            "platform": sys.platform,
            "executable": sys.executable,
            "cwd": os.getcwd(),
        },
        "exit_code": exit_code,
        "signal": signal_num,
        "process_info": _get_process_info(),
        "last_request": _get_last_request_info(),
        "recent_logs": _get_recent_logs(50),
        "system_logs": _get_system_logs_for_pid(),
    }

    # Трассировка стека
    if exc_info:
        report["traceback"] = {
            "type": exc_info[0].__name__ if exc_info[0] else None,
            "value": str(exc_info[1]) if exc_info[1] else None,
            "formatted": "".join(
                traceback.format_exception(*exc_info)
            ) if exc_info and exc_info[0] else None,
        }
    else:
        # Текущий стек (если нет исключения)
        stack_frames = traceback.format_stack()
        report["traceback"] = {
            "type": "current_stack",
            "value": "Stack trace at shutdown moment",
            "formatted": "".join(stack_frames),
        }

    return report


def save_crash_report(report: Dict[str, Any]) -> Path:
    """Сохранение crash-отчёта в файл."""
    crash_id = report["crash_id"]
    filename = f"crash_{crash_id}.json"
    filepath = CRASH_LOG_DIR / filename

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        logger.critical(f"Crash-отчёт сохранён: {filepath}")
    except Exception as e:
        logger.critical(f"Не удалось сохранить crash-отчёт: {e}")

    # Ротация старых crash-логов
    _rotate_crash_logs()

    return filepath


def _rotate_crash_logs():
    """Удаление старых crash-логов, оставляя только MAX_CRASH_LOGS последних."""
    try:
        crash_files = sorted(CRASH_LOG_DIR.glob("crash_*.json"))
        if len(crash_files) > MAX_CRASH_LOGS:
            for f in crash_files[:-MAX_CRASH_LOGS]:
                f.unlink()
                logger.info(f"Удалён старый crash-лог: {f.name}")
    except Exception as e:
        logger.error(f"Ошибка ротации crash-логов: {e}")


def list_crash_reports(limit: int = 10) -> list:
    """Получение списка последних crash-отчётов."""
    try:
        crash_files = sorted(
            CRASH_LOG_DIR.glob("crash_*.json"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )[:limit]

        reports = []
        for f in crash_files:
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    report = json.load(fh)
                    reports.append({
                        "crash_id": report.get("crash_id"),
                        "timestamp": report.get("timestamp"),
                        "reason": report.get("reason"),
                        "is_manual_stop": report.get("is_manual_stop"),
                        "pid": report.get("process", {}).get("pid"),
                        "memory_mb": report.get("process_info", {})
                            .get("memory", {}).get("rss_mb"),
                        "file": f.name,
                    })
            except Exception:
                reports.append({"file": f.name, "error": "corrupt or unreadable"})
        return reports
    except Exception as e:
        return [{"error": str(e)}]


# ─── Обработчики сигналов ────────────────────────────────────────────

def _signal_handler(signum: int, frame):
    """Обработчик сигналов завершения."""
    global _shutdown_in_progress

    with _shutdown_lock:
        if _shutdown_in_progress:
            # Уже обрабатываем shutdown — игнорируем повторные сигналы
            return
        _shutdown_in_progress = True

    signal_name = signal.Signals(signum).name if signum in signal.Signals else str(signum)
    logger.warning(f"Получен сигнал: {signal_name} ({signum})")

    # Определяем, ручная ли это остановка (проверяем флаг и маркерный файл)
    is_manual = _manual_stop_detected or _check_manual_stop_marker()

    # Определяем причину
    if is_manual:
        reason = f"MANUAL_STOP: Сервис остановлен пользователем (сигнал {signal_name})"
    elif signum == signal.SIGTERM:
        reason = f"SIGTERM: Запрос на завершение процесса (возможно OOM Killer или systemd)"
    elif signum == signal.SIGINT:
        reason = f"SIGINT: Прерывание с клавиатуры (Ctrl+C)"
    elif signum == signal.SIGQUIT:
        reason = f"SIGQUIT: Аварийное завершение (Core dump)"
    elif signum == signal.SIGHUP:
        reason = f"SIGHUP: Обрыв соединения с терминалом"
    else:
        reason = f"SIGNAL_{signum}: Неизвестный сигнал завершения"

    # Формируем и сохраняем отчёт
    report = build_crash_report(
        reason=reason,
        signal_num=signum,
        exit_code=128 + signum,
        is_manual=is_manual,
    )
    save_crash_report(report)

    # Формируем путь к crash-отчёту (отдельно от f-string для совместимости с Python 3.10)
    crash_filename = f"crash_{report['crash_id']}.json"
    crash_path = CRASH_LOG_DIR / crash_filename

    # Если это ручная остановка — пишем однозначную запись
    if is_manual:
        logger.info(
            f"🛑 СЕРВИС ОСТАНОВЛЕН ВРУЧНУЮ: сигнал {signal_name}, "
            f"PID {_PID}. Crash-отчёт: {crash_path}"
        )
    else:
        logger.critical(
            f"💥 АВАРИЙНОЕ ЗАВЕРШЕНИЕ: сигнал {signal_name}, "
            f"PID {_PID}. Crash-отчёт: {crash_path}"
        )

    # Вызываем callback shutdown, если он установлен
    if _shutdown_callback:
        try:
            _shutdown_callback()
        except Exception as e:
            logger.critical(f"Ошибка в shutdown callback: {e}")

    # Восстанавливаем стандартный обработчик и перепосылаем сигнал себе
    # для гарантированного завершения
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


# ─── Обработчик необработанных исключений ────────────────────────────

def _global_exception_handler(exc_type, exc_value, exc_traceback):
    """Глобальный обработчик необработанных исключений."""
    global _shutdown_in_progress

    with _shutdown_lock:
        if _shutdown_in_progress:
            return
        _shutdown_in_progress = True

    logger.critical(
        f"💥 НЕОБРАБОТАННОЕ ИСКЛЮЧЕНИЕ: {exc_type.__name__}: {exc_value}"
    )

    reason = f"UNHANDLED_EXCEPTION: {exc_type.__name__}: {exc_value}"
    report = build_crash_report(
        reason=reason,
        exc_info=(exc_type, exc_value, exc_traceback),
        exit_code=1,
        is_manual=False,
    )
    save_crash_report(report)

    # Вызываем оригинальный excepthook
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


# ─── Обработчик фатальных ошибок (SIGABRT, SIGSEGV, SIGFPE, SIGBUS) ──

def _fatal_signal_handler(signum: int, frame):
    """Обработчик фатальных сигналов (SEGV, ABRT, FPE, BUS)."""
    global _shutdown_in_progress

    with _shutdown_lock:
        if _shutdown_in_progress:
            return
        _shutdown_in_progress = True

    signal_name = signal.Signals(signum).name if signum in signal.Signals else str(signum)

    # Пытаемся получить стек из фрейма
    stack_str = ""
    try:
        stack_frames = traceback.format_stack(frame)
        stack_str = "".join(stack_frames)
    except Exception:
        stack_str = "[could not extract stack]"

    reason_map = {
        signal.SIGSEGV: "SIGSEGV: Ошибка сегментации памяти (Segmentation Fault)",
        signal.SIGABRT: "SIGABRT: Аварийное завершение (Abort)",
        signal.SIGFPE:  "SIGFPE: Ошибка арифметической операции (Floating Point Exception)",
        signal.SIGBUS:  "SIGBUS: Ошибка шины (Bus Error)",
    }
    reason = reason_map.get(signum, f"SIGNAL_{signum}: Фатальный сигнал")

    logger.critical(f"💥 ФАТАЛЬНЫЙ СИГНАЛ: {signal_name} ({signum})")

    report = build_crash_report(
        reason=reason,
        signal_num=signum,
        exit_code=128 + signum,
        is_manual=False,
    )
    # Добавляем стек из фрейма
    report["traceback"]["formatted"] = (
        f"Signal: {signal_name}\n"
        f"Stack at signal moment:\n{stack_str}"
    )
    save_crash_report(report)

    # Восстанавливаем стандартный обработчик
    signal.signal(signum, signal.SIG_DFL)
    os.kill(os.getpid(), signum)


# ─── Инициализация монитора ──────────────────────────────────────────

def _atexit_handler():
    """Фиксирует неожиданное завершение процесса (в т.ч. SIGKILL/OOM без Python-исключения)."""
    if _shutdown_in_progress or _manual_stop_detected or _is_manual_stop_from_file():
        return
    marker = CRASH_LOG_DIR / f"abrupt_exit_{_PID}.json"
    if marker.exists():
        return
    try:
        report = build_crash_report(
            reason="Процесс завершился без graceful shutdown (возможен OOM/SIGKILL)",
            is_manual=False,
        )
        save_crash_report(report)
    except Exception:
        pass


def install_crash_monitor(shutdown_callback: Optional[Callable] = None):
    """Установка всех обработчиков мониторинга аварийных завершений.

    Args:
        shutdown_callback: опциональный callback для graceful shutdown
    """
    global _shutdown_callback
    if shutdown_callback:
        _shutdown_callback = shutdown_callback

    logger.info("🛡️ Установка системы мониторинга аварийных завершений...")

    # 1. Перехват сигналов завершения
    signals_to_catch = [signal.SIGTERM, signal.SIGINT, signal.SIGQUIT, signal.SIGHUP]
    for sig in signals_to_catch:
        try:
            signal.signal(sig, _signal_handler)
            logger.debug(f"  Установлен обработчик для {signal.Signals(sig).name}")
        except (ValueError, OSError) as e:
            logger.warning(f"  Не удалось установить обработчик для сигнала {sig}: {e}")

    # 2. Перехват фатальных сигналов
    fatal_signals = [signal.SIGSEGV, signal.SIGABRT, signal.SIGFPE, signal.SIGBUS]
    for sig in fatal_signals:
        try:
            signal.signal(sig, _fatal_signal_handler)
            logger.debug(f"  Установлен обработчик для {signal.Signals(sig).name}")
        except (ValueError, OSError) as e:
            logger.warning(f"  Не удалось установить обработчик для сигнала {sig}: {e}")

    # 3. Перехват необработанных исключений
    sys.excepthook = _global_exception_handler

    atexit.register(_atexit_handler)

    logger.info("✅ Система мониторинга аварийных завершений установлена")
    logger.info(f"   Crash-логи: {CRASH_LOG_DIR.resolve()}")
    logger.info(f"   PID: {_PID}")


def uninstall_crash_monitor():
    """Снятие всех обработчиков мониторинга (восстановление стандартных)."""
    logger.info("Снятие обработчиков мониторинга аварийных завершений...")

    # Восстанавливаем стандартные обработчики сигналов
    for sig in list(signal.Signals):
        try:
            signal.signal(sig, signal.SIG_DFL)
        except (ValueError, OSError, TypeError):
            pass

    # Восстанавливаем стандартный excepthook
    sys.excepthook = sys.__excepthook__

    logger.info("Обработчики мониторинга сняты")


# ─── API для внешнего использования ──────────────────────────────────

def get_crash_monitor_status() -> Dict[str, Any]:
    """Получение статуса системы мониторинга."""
    return {
        "pid": _PID,
        "uptime_seconds": round(time.time() - _PROCESS_START_TIME, 2),
        "manual_stop_detected": _manual_stop_detected,
        "shutdown_in_progress": _shutdown_in_progress,
        "crash_log_dir": str(CRASH_LOG_DIR.resolve()),
        "crash_log_count": len(list(CRASH_LOG_DIR.glob("crash_*.json"))),
        "last_request": _last_request,
        "process_info": _get_process_info(),
    }
