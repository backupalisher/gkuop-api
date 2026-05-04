"""
Модуль внешнего мониторинга (супервизора) для отслеживания состояния
web-сервера и CLI-процессов.

Обеспечивает:
- Health-check через HTTP-endpoint
- Мониторинг процесса по PID (жив/мёртв, потребление ресурсов)
- Детектирование внезапного исчезновения процесса
- Сбор системных метрик (dmesg, syslog) при обнаружении мёртвого процесса
- Ведение лога супервизора с ротацией
- Автоматический перезапуск (опционально)
"""

import os
import sys
import time
import json
import signal
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

# ─── Конфигурация ─────────────────────────────────────────────────────

SUPERVISOR_LOG_DIR = Path("logs/supervisor")
SUPERVISOR_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Максимальное количество логов супервизора
MAX_SUPERVISOR_LOGS = 50

# Интервал проверки (сек)
DEFAULT_CHECK_INTERVAL = 30

# Таймаут HTTP health-check (сек)
HEALTH_CHECK_TIMEOUT = 10

# Количество последовательных неудачных проверок до объявления краха
FAILURE_THRESHOLD = 3


# ─── Вспомогательные функции ─────────────────────────────────────────

def _get_timestamp() -> str:
    """Получение временной метки в ISO формате."""
    return datetime.now(timezone.utc).isoformat()


def _get_local_timestamp() -> str:
    """Получение локальной временной метки."""
    return datetime.now(timezone.utc).astimezone().isoformat()


def _read_pid_file(pid_file: str) -> Optional[int]:
    """Чтение PID из файла."""
    try:
        with open(pid_file, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError, OSError):
        return None


def _is_process_alive(pid: int) -> bool:
    """Проверка, жив ли процесс с указанным PID."""
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False
    except PermissionError:
        # Процесс существует, но нет прав — считаем живым
        return True


def _get_process_info_external(pid: int) -> Dict[str, Any]:
    """Получение информации о процессе через /proc (без psutil)."""
    info = {"pid": pid, "alive": _is_process_alive(pid)}

    if not info["alive"]:
        return info

    try:
        # Чтение из /proc/[pid]/status
        with open(f"/proc/{pid}/status", "r") as f:
            for line in f:
                if line.startswith("Name:"):
                    info["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("VmRSS:"):
                    info["memory_rss_kb"] = int(
                        line.split(":", 1)[1].strip().split()[0]
                    )
                elif line.startswith("Threads:"):
                    info["threads"] = int(line.split(":", 1)[1].strip())
                elif line.startswith("State:"):
                    info["state"] = line.split(":", 1)[1].strip()
    except (FileNotFoundError, OSError, ValueError):
        pass

    try:
        # Время запуска
        with open(f"/proc/{pid}/stat", "r") as f:
            parts = f.read().split()
            if len(parts) > 21:
                clock_ticks = os.sysconf(os.sysconf_names["SC_CLK_TCK"])
                start_time_ticks = int(parts[21])
                info["start_time"] = start_time_ticks / clock_ticks
    except (FileNotFoundError, OSError, ValueError, KeyError):
        pass

    try:
        # Командная строка
        with open(f"/proc/{pid}/cmdline", "r") as f:
            cmdline = f.read().replace("\0", " ").strip()
            if cmdline:
                info["cmdline"] = cmdline
    except (FileNotFoundError, OSError):
        pass

    return info


def _get_system_oom_info() -> List[str]:
    """Получение информации об OOM из системных логов."""
    entries = []
    try:
        # dmesg — поиск OOM-killer сообщений
        result = subprocess.run(
            ["dmesg", "--level=err,warn", "--since", "10 minutes ago"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if "oom" in line.lower() or "killed" in line.lower() or "out of memory" in line.lower():
                    entries.append(line.strip())
    except Exception:
        pass

    try:
        # journalctl
        result = subprocess.run(
            ["journalctl", "-q", "--since", "10 minutes ago",
             "--grep", "oom|killed|out of memory", "-o", "short-iso"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.splitlines():
                entries.append(f"[journalctl] {line.strip()}")
    except Exception:
        pass

    return entries


def _get_system_load() -> Dict[str, Any]:
    """Получение системной нагрузки."""
    try:
        load_avg = os.getloadavg()
        return {
            "load_1min": round(load_avg[0], 2),
            "load_5min": round(load_avg[1], 2),
            "load_15min": round(load_avg[2], 2),
        }
    except OSError:
        return {"error": "could not get load average"}


def _get_memory_info() -> Dict[str, Any]:
    """Получение информации о памяти из /proc/meminfo."""
    meminfo = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                if len(parts) == 2:
                    key = parts[0].strip()
                    value_str = parts[1].strip()
                    # Парсим "12345 kB"
                    if value_str.endswith(" kB"):
                        try:
                            meminfo[key] = int(value_str.split()[0])
                        except ValueError:
                            meminfo[key] = value_str
                    else:
                        meminfo[key] = value_str
    except (FileNotFoundError, OSError):
        pass
    return meminfo


# ─── Класс SupervisorMonitor ─────────────────────────────────────────

class SupervisorMonitor:
    """Внешний мониторинг процесса-сервера."""

    def __init__(
        self,
        pid_file: str,
        health_check_url: Optional[str] = None,
        check_interval: int = DEFAULT_CHECK_INTERVAL,
        failure_threshold: int = FAILURE_THRESHOLD,
        auto_restart: bool = False,
        restart_command: Optional[str] = None,
        service_name: str = "gkuop-web",
    ):
        """
        Args:
            pid_file: путь к PID-файлу
            health_check_url: URL для HTTP health-check
            check_interval: интервал проверки в секундах
            failure_threshold: количество неудачных проверок до объявления краха
            auto_restart: автоматический перезапуск при обнаружении краха
            restart_command: команда для перезапуска
            service_name: имя сервиса для логов
        """
        self.pid_file = pid_file
        self.health_check_url = health_check_url
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold
        self.auto_restart = auto_restart
        self.restart_command = restart_command
        self.service_name = service_name

        self._running = False
        self._consecutive_failures = 0
        self._last_known_pid: Optional[int] = None
        self._last_known_alive_time: Optional[float] = None
        self._last_health_check_time: Optional[float] = None
        self._last_health_check_status: Optional[bool] = None

        # Лог-файл супервизора
        self._log_file = SUPERVISOR_LOG_DIR / f"supervisor_{service_name}.log"
        self._log_fh: Optional[open] = None

    def _log(self, level: str, message: str, data: Optional[Dict] = None):
        """Запись в лог супервизора."""
        entry = {
            "timestamp": _get_timestamp(),
            "timestamp_local": _get_local_timestamp(),
            "level": level,
            "service": self.service_name,
            "message": message,
        }
        if data:
            entry["data"] = data

        line = json.dumps(entry, ensure_ascii=False, default=str)

        # В файл
        if self._log_fh:
            try:
                self._log_fh.write(line + "\n")
                self._log_fh.flush()
            except OSError:
                pass

        # В stdout
        print(f"[supervisor] {level}: {message}", file=sys.stderr)

    def _open_log(self):
        """Открытие лог-файла супервизора."""
        try:
            self._log_fh = open(self._log_file, "a", encoding="utf-8")
        except OSError as e:
            print(f"[supervisor] Cannot open log file: {e}", file=sys.stderr)

    def _close_log(self):
        """Закрытие лог-файла."""
        if self._log_fh:
            try:
                self._log_fh.close()
            except OSError:
                pass
            self._log_fh = None

    def _rotate_log(self):
        """Ротация лога супервизора."""
        try:
            log_files = sorted(
                SUPERVISOR_LOG_DIR.glob(f"supervisor_{self.service_name}.log*"),
                key=lambda f: f.stat().st_mtime,
                reverse=True,
            )
            if len(log_files) > MAX_SUPERVISOR_LOGS:
                for f in log_files[MAX_SUPERVISOR_LOGS:]:
                    f.unlink()
        except OSError:
            pass

    def _perform_health_check(self) -> bool:
        """Выполнение HTTP health-check."""
        if not self.health_check_url:
            return True  # Нет URL — пропускаем

        try:
            import urllib.request
            import urllib.error

            req = urllib.request.Request(
                self.health_check_url,
                method="GET",
                headers={"User-Agent": "SupervisorMonitor/1.0"},
            )
            with urllib.request.urlopen(req, timeout=HEALTH_CHECK_TIMEOUT) as resp:
                status = resp.status == 200
                self._last_health_check_status = status
                self._last_health_check_time = time.time()
                return status
        except (urllib.error.URLError, ConnectionRefusedError,
                TimeoutError, OSError) as e:
            self._last_health_check_status = False
            self._last_health_check_time = time.time()
            self._log("WARNING", f"Health-check failed: {e}")
            return False

    def _detect_crash(self, pid: int, was_alive: bool) -> Dict[str, Any]:
        """Детектирование краха процесса и сбор информации."""
        crash_report = {
            "timestamp": _get_timestamp(),
            "timestamp_local": _get_local_timestamp(),
            "service": self.service_name,
            "pid": pid,
            "was_alive_before": was_alive,
            "detection_method": "pid_check" if not was_alive else "health_check",
        }

        # Системная информация
        crash_report["system_load"] = _get_system_load()
        crash_report["system_memory"] = _get_memory_info()
        crash_report["oom_info"] = _get_system_oom_info()

        # Информация о процессе из /proc (если ещё доступен)
        proc_info = _get_process_info_external(pid)
        crash_report["last_known_process_info"] = proc_info

        # Поиск в dmesg сообщений о нашем процессе
        try:
            result = subprocess.run(
                ["dmesg", "--level=err,warn", "--since", "30 minutes ago"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0:
                relevant = []
                for line in result.stdout.splitlines():
                    if str(pid) in line or self.service_name in line.lower():
                        relevant.append(line.strip())
                if relevant:
                    crash_report["dmesg_entries"] = relevant
        except Exception:
            pass

        # Поиск core dump
        try:
            result = subprocess.run(
                ["journalctl", "-q", "--since", "30 minutes ago",
                 "--grep", f"core dump.*{pid}|{pid}.*core dump|SIGSEGV.*{pid}",
                 "-o", "short-iso"],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                crash_report["core_dump_entries"] = [
                    line.strip() for line in result.stdout.splitlines()
                ]
        except Exception:
            pass

        return crash_report

    def _save_crash_report(self, report: Dict[str, Any]):
        """Сохранение отчёта о крахе."""
        crash_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = SUPERVISOR_LOG_DIR / f"crash_detected_{crash_id}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            self._log("CRITICAL", f"Crash-отчёт супервизора сохранён: {filename}")
        except OSError as e:
            self._log("ERROR", f"Не удалось сохранить crash-отчёт: {e}")

    def _auto_restart_process(self):
        """Автоматический перезапуск процесса."""
        if not self.auto_restart or not self.restart_command:
            self._log("INFO", "Автоперезапуск отключён или не задана команда")
            return

        self._log("INFO", f"Автоматический перезапуск: {self.restart_command}")
        try:
            result = subprocess.run(
                self.restart_command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                self._log("INFO", "Процесс успешно перезапущен")
                self._consecutive_failures = 0
            else:
                self._log("ERROR", f"Ошибка перезапуска: {result.stderr}")
        except subprocess.TimeoutExpired:
            self._log("ERROR", "Таймаут при перезапуске процесса")
        except Exception as e:
            self._log("ERROR", f"Исключение при перезапуске: {e}")

    def check_once(self) -> Dict[str, Any]:
        """Однократная проверка состояния процесса.

        Returns:
            Dict с результатами проверки
        """
        result = {
            "timestamp": _get_timestamp(),
            "pid": None,
            "alive": False,
            "health_check_ok": None,
            "crash_detected": False,
        }

        # Читаем PID
        pid = _read_pid_file(self.pid_file)
        result["pid"] = pid

        if pid is None:
            self._log("WARNING", "PID-файл не найден или пуст")
            result["alive"] = False
            return result

        # Проверяем, жив ли процесс
        alive = _is_process_alive(pid)
        result["alive"] = alive

        if alive:
            self._last_known_pid = pid
            self._last_known_alive_time = time.time()
            self._consecutive_failures = 0

            # Health-check
            health_ok = self._perform_health_check()
            result["health_check_ok"] = health_ok

            if not health_ok and self.health_check_url:
                self._consecutive_failures += 1
                self._log(
                    "WARNING",
                    f"Health-check не пройден ({self._consecutive_failures}/{self.failure_threshold})",
                    {"pid": pid, "failures": self._consecutive_failures},
                )

                if self._consecutive_failures >= self.failure_threshold:
                    self._log(
                        "CRITICAL",
                        f"Порог неудачных health-check достигнут! Процесс {pid} не отвечает",
                    )
                    crash_report = self._detect_crash(pid, was_alive=True)
                    self._save_crash_report(crash_report)
                    result["crash_detected"] = True
                    self._auto_restart_process()
            else:
                self._consecutive_failures = 0
        else:
            # Процесс мёртв
            self._log(
                "CRITICAL",
                f"Процесс {pid} не обнаружен в системе!",
                {"pid": pid, "last_known_alive": self._last_known_alive_time},
            )
            crash_report = self._detect_crash(pid, was_alive=False)
            self._save_crash_report(crash_report)
            result["crash_detected"] = True
            self._auto_restart_process()

        return result

    def run_forever(self):
        """Запуск цикла мониторинга."""
        self._running = True
        self._open_log()
        self._rotate_log()

        self._log("INFO", f"Запуск супервизора для сервиса {self.service_name}")
        self._log("INFO", f"PID-файл: {self.pid_file}")
        self._log("INFO", f"Health-check URL: {self.health_check_url or 'не задан'}")
        self._log("INFO", f"Интервал проверки: {self.check_interval}с")
        self._log("INFO", f"Порог ошибок: {self.failure_threshold}")
        self._log("INFO", f"Автоперезапуск: {'включён' if self.auto_restart else 'выключен'}")

        try:
            while self._running:
                result = self.check_once()
                if result.get("crash_detected"):
                    self._log("CRITICAL", "КРАХ ПРОЦЕССА ОБНАРУЖЕН!")
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self._log("INFO", "Супервизор остановлен пользователем (Ctrl+C)")
        except Exception as e:
            self._log("CRITICAL", f"Критическая ошибка супервизора: {e}")
            import traceback
            self._log("CRITICAL", traceback.format_exc())
        finally:
            self._running = False
            self._close_log()

    def stop(self):
        """Остановка цикла мониторинга."""
        self._running = False
        self._log("INFO", "Супервизор остановлен")


# ─── Утилиты для run.sh ──────────────────────────────────────────────

def start_supervisor_daemon(
    pid_file: str,
    health_check_url: Optional[str] = None,
    check_interval: int = DEFAULT_CHECK_INTERVAL,
    auto_restart: bool = False,
    restart_command: Optional[str] = None,
    service_name: str = "gkuop-web",
    daemonize: bool = True,
):
    """Запуск супервизора как демона.

    Args:
        pid_file: путь к PID-файлу отслеживаемого процесса
        health_check_url: URL для HTTP health-check
        check_interval: интервал проверки
        auto_restart: автоматический перезапуск
        restart_command: команда перезапуска
        service_name: имя сервиса
        daemonize: запустить в фоне (fork)
    """
    if daemonize:
        pid = os.fork()
        if pid > 0:
            # Родительский процесс — выходим
            print(f"[supervisor] Запущен супервизор (PID: {pid})")
            return

    # Дочерний процесс
    monitor = SupervisorMonitor(
        pid_file=pid_file,
        health_check_url=health_check_url,
        check_interval=check_interval,
        failure_threshold=FAILURE_THRESHOLD,
        auto_restart=auto_restart,
        restart_command=restart_command,
        service_name=service_name,
    )
    monitor.run_forever()


def check_process_health(pid_file: str, health_check_url: Optional[str] = None) -> Dict[str, Any]:
    """Однократная проверка здоровья процесса (для cron/скриптов)."""
    monitor = SupervisorMonitor(
        pid_file=pid_file,
        health_check_url=health_check_url,
    )
    return monitor.check_once()
