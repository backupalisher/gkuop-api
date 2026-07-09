"""
Сервис резервного копирования и восстановления PostgreSQL.
"""
from __future__ import annotations

import logging
import os
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict

from config.settings import DatabaseConfig

logger = logging.getLogger(__name__)


class DatabaseBackupError(Exception):
    """Ошибка резервного копирования или восстановления БД."""


def _build_pg_env(config: DatabaseConfig) -> Dict[str, str]:
    env = os.environ.copy()
    env['PGHOST'] = config.host
    env['PGPORT'] = str(config.port)
    env['PGUSER'] = config.user
    env['PGPASSWORD'] = config.password
    return env


def create_database_dump(config: DatabaseConfig) -> bytes:
    """
    Создаёт custom-dump PostgreSQL через pg_dump.

    Returns:
        bytes: содержимое дампа
    """
    with tempfile.NamedTemporaryFile(suffix='.dump', delete=False) as tmp_file:
        dump_path = tmp_file.name

    try:
        command = [
            'pg_dump',
            '--format=custom',
            '--no-owner',
            '--no-privileges',
            '--file', dump_path,
            config.database,
        ]
        result = subprocess.run(
            command,
            env=_build_pg_env(config),
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            raise DatabaseBackupError(
                result.stderr.strip() or 'pg_dump завершился с ошибкой'
            )

        dump_bytes = Path(dump_path).read_bytes()
        if not dump_bytes:
            raise DatabaseBackupError('pg_dump создал пустой файл')
        return dump_bytes
    finally:
        Path(dump_path).unlink(missing_ok=True)


def build_dump_filename(database_name: str) -> str:
    """Формирует имя файла дампа."""
    stamp = datetime.now().strftime('%d%m')
    return f'dump_{database_name}{stamp}.dump'


def restore_database_dump(config: DatabaseConfig, dump_path: str) -> None:
    """
    Восстанавливает БД из custom-dump через pg_restore.

    Args:
        config: конфигурация подключения
        dump_path: путь к файлу дампа
    """
    if not Path(dump_path).is_file():
        raise DatabaseBackupError('Файл дампа не найден')

    command = [
        'pg_restore',
        '--clean',
        '--if-exists',
        '--no-owner',
        '--no-privileges',
        '--dbname', config.database,
        dump_path,
    ]
    result = subprocess.run(
        command,
        env=_build_pg_env(config),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        # pg_restore может возвращать 1 при некритичных предупреждениях
        stderr = (result.stderr or '').strip()
        if stderr:
            logger.warning("pg_restore stderr: %s", stderr)
        raise DatabaseBackupError(
            stderr or 'pg_restore завершился с ошибкой'
        )
