"""
Общая логика синхронизации писем между CLI и Web API.

IMAP-критерий SINCE работает только с точностью до дня, поэтому при
инкрементальном обновлении нужен отступ назад, иначе письма предыдущего
дня (например, #424662 от 08.07 17:54) выпадают из выборки.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from email.message import Message

    from email_processor.email_client import EmailClient
    from email_processor.email_parser import EmailParser
    from email_processor.ticket_processor import TicketProcessor

logger = logging.getLogger(__name__)


def compute_imap_since_date(reference: datetime) -> datetime:
    """
    Вычисляет дату для IMAP SINCE с запасом в 1 сутки.

    Args:
        reference: опорная дата (checkpoint или last_update)

    Returns:
        datetime: начало суток за день до reference
    """
    search_from = reference - timedelta(days=1)
    return search_from.replace(hour=0, minute=0, second=0, microsecond=0)


def normalize_email_datetime(value: Optional[datetime]) -> Optional[datetime]:
    """Приводит datetime письма к timezone-naive виду для сравнения."""
    if value is None:
        return None
    if value.tzinfo is not None:
        return value.replace(tzinfo=None)
    return value


def compute_checkpoint_date(
    processed_dates: List[datetime],
    fallback: Optional[datetime] = None,
) -> Optional[datetime]:
    """
    Определяет дату checkpoint по обработанным письмам.

    Checkpoint не должен прыгать на текущее время — только на максимальную
    дату реально обработанного письма.
    """
    normalized = [
        dt for dt in (normalize_email_datetime(item) for item in processed_dates)
        if dt is not None
    ]
    if not normalized:
        return fallback
    return max(normalized)


def process_email_messages(
    email_client: EmailClient,
    email_parser: EmailParser,
    ticket_processor: TicketProcessor,
    email_ids: List[bytes],
    progress_callback=None,
) -> Dict[str, object]:
    """
    Обрабатывает список IMAP UID с аудитом пропусков.

    Returns:
        dict с ключами processed, errors, skipped, skip_details, received_dates
    """
    processed = 0
    errors = 0
    skipped = 0
    skip_details: List[Dict[str, str]] = []
    received_dates: List[datetime] = []
    total = len(email_ids)

    for idx, email_id in enumerate(email_ids, 1):
        email_message = email_client.fetch_email(email_id)
        if not email_message:
            errors += 1
            logger.error("Не удалось получить письмо UID=%s", email_id)
            if progress_callback:
                progress_callback(idx, total, processed, errors, skipped)
            continue

        email_data, skip_reason = email_parser.parse_email_detailed(email_message)
        if skip_reason:
            skipped += 1
            subject = email_parser.decode_header_value(email_message.get('Subject', ''))
            from_addr = email_parser.decode_header_value(email_message.get('From', ''))
            date_str = email_message.get('Date', '')
            skip_details.append({
                'uid': email_id.decode() if isinstance(email_id, bytes) else str(email_id),
                'subject': subject[:200],
                'from': from_addr[:200],
                'date': date_str,
                'reason': skip_reason,
            })
            logger.warning(
                "Пропущено письмо UID=%s: %s | subject=%r",
                email_id,
                skip_reason,
                subject[:120],
            )
            if progress_callback:
                progress_callback(idx, total, processed, errors, skipped)
            continue

        if ticket_processor.process_email(email_data):
            processed += 1
            received_date = normalize_email_datetime(email_data.get('received_date'))
            if received_date:
                received_dates.append(received_date)
        else:
            errors += 1
            logger.error(
                "Ошибка обработки заявки #%s (UID=%s)",
                email_data.get('ticket_number'),
                email_id,
            )

        if progress_callback:
            progress_callback(idx, total, processed, errors, skipped)

    if skip_details:
        logger.warning(
            "Аудит синхронизации: пропущено %s писем из %s",
            skipped,
            total,
        )

    return {
        'processed': processed,
        'errors': errors,
        'skipped': skipped,
        'skip_details': skip_details,
        'received_dates': received_dates,
    }
