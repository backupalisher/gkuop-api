"""
Идемпотентность клиентских мутаций (Idempotency-Key).

Обратная совместимость: заголовок опционален; web UI без него работает как раньше.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

IDEMPOTENCY_TTL_DAYS = 7


def ensure_idempotency_table(db) -> None:
    """Создаёт таблицу ключей идемпотентности при старте."""
    db.cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS client_idempotency_keys (
            id SERIAL PRIMARY KEY,
            idem_key VARCHAR(128) NOT NULL,
            username VARCHAR(100) NOT NULL,
            method VARCHAR(16) NOT NULL,
            path TEXT NOT NULL,
            status_code INTEGER NOT NULL,
            response_body JSONB,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            UNIQUE (username, idem_key)
        )
        """
    )
    db.cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_client_idempotency_created
        ON client_idempotency_keys (created_at)
        """
    )
    db.connection.commit()


def cleanup_old_keys(db) -> None:
    try:
        db.cursor.execute(
            "DELETE FROM client_idempotency_keys WHERE created_at < %s",
            (datetime.utcnow() - timedelta(days=IDEMPOTENCY_TTL_DAYS),),
        )
        db.connection.commit()
    except Exception as e:
        logger.warning("idempotency cleanup failed: %s", e)
        try:
            db.connection.rollback()
        except Exception:
            pass


def lookup_idempotent_response(
    db,
    username: str,
    idem_key: str,
) -> Optional[Tuple[int, Any]]:
    if not idem_key or not username:
        return None
    try:
        db.cursor.execute(
            """
            SELECT status_code, response_body
            FROM client_idempotency_keys
            WHERE username = %s AND idem_key = %s
            """,
            (username, idem_key[:128]),
        )
        row = db.cursor.fetchone()
        if not row:
            return None
        return int(row["status_code"]), row["response_body"]
    except Exception as e:
        logger.warning("idempotency lookup failed: %s", e)
        try:
            db.connection.rollback()
        except Exception:
            pass
        return None


def store_idempotent_response(
    db,
    username: str,
    idem_key: str,
    method: str,
    path: str,
    status_code: int,
    response_body: Any,
) -> None:
    if not idem_key or not username:
        return
    try:
        cleanup_old_keys(db)
        db.cursor.execute(
            """
            INSERT INTO client_idempotency_keys
                (idem_key, username, method, path, status_code, response_body)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            ON CONFLICT (username, idem_key) DO NOTHING
            """,
            (
                idem_key[:128],
                username,
                method[:16],
                path,
                status_code,
                json.dumps(response_body, ensure_ascii=False, default=str),
            ),
        )
        db.connection.commit()
    except Exception as e:
        logger.warning("idempotency store failed: %s", e)
        try:
            db.connection.rollback()
        except Exception:
            pass


def extract_idempotency_key(request) -> Optional[str]:
    key = request.headers.get("Idempotency-Key") or request.headers.get("idempotency-key")
    if not key:
        return None
    key = key.strip()
    return key[:128] if key else None
