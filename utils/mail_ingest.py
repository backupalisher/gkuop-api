"""
Инкрементальная загрузка новых писем в заявки.

Использует тот же разбор, что и ручное обновление: checkpoint в БД и IMAP SINCE
с запасом в сутки. Без checkpoint берётся окно с начала вчерашних суток,
чтобы минутный опрос не перечитывал весь ящик.
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict

from config.settings import load_config
from email_processor.email_client import EmailClient
from email_processor.email_parser import EmailParser
from email_processor.ticket_processor import TicketProcessor
from utils.email_sync import (
    compute_checkpoint_date,
    compute_imap_since_date,
    process_email_messages,
)

logger = logging.getLogger(__name__)


def ingest_incremental(db: Any) -> Dict[str, Any]:
    """Забирает новые письма и сохраняет заявки. Ошибки почты не пробрасывает наружу вызывающему потоку как падение процесса — пишет в лог и возвращает статус."""
    checkpoint = None
    try:
        checkpoint = db.get_checkpoint()
    except Exception as exc:
        logger.warning('Автозагрузка: не удалось прочитать checkpoint: %s', exc)

    if checkpoint and checkpoint.get('checkpoint_date'):
        since_date = compute_imap_since_date(checkpoint['checkpoint_date'])
        fallback_checkpoint = checkpoint['checkpoint_date']
    else:
        since_date = compute_imap_since_date(datetime.now())
        fallback_checkpoint = None
        logger.info(
            'Автозагрузка без checkpoint: письма начиная с %s',
            since_date.strftime('%d.%m.%Y'),
        )

    config = load_config()
    email_client = EmailClient(
        imap_server=config['email'].imap_server,
        email=config['email'].email,
        password=config['email'].password,
        port=config['email'].port,
    )
    try:
        if not email_client.connect():
            logger.warning('Автозагрузка: не удалось подключиться к почте')
            return {'status': 'error', 'message': 'Почта недоступна'}
        if not email_client.select_folder(config['email'].folder):
            logger.warning('Автозагрузка: не удалось выбрать папку почты')
            return {'status': 'error', 'message': 'Папка почты недоступна'}

        email_parser = EmailParser(
            config['parser'].patterns,
            subject_filters=config['parser'].subject_filters,
        )
        ticket_processor = TicketProcessor(db)
        email_ids = email_client.search_emails(
            subject_filters=config['parser'].subject_filters,
            from_filter=config['parser'].from_filter,
            since_date=since_date,
        )
        if since_date and not email_ids:
            fallback_since = compute_imap_since_date(since_date)
            if fallback_since != since_date:
                email_ids = email_client.search_emails(
                    subject_filters=config['parser'].subject_filters,
                    from_filter=config['parser'].from_filter,
                    since_date=fallback_since,
                )
        if not email_ids:
            logger.info('Автозагрузка: новых писем нет')
            return {'status': 'ok', 'processed': 0, 'created': 0, 'updated': 0}

        batch = process_email_messages(
            email_client,
            email_parser,
            ticket_processor,
            email_ids,
        )
        processed = int(batch['processed'])
        if processed > 0:
            new_checkpoint = compute_checkpoint_date(
                batch['received_dates'],
                fallback=fallback_checkpoint,
            )
            if new_checkpoint:
                db.save_checkpoint(new_checkpoint, processed)
        logger.info(
            'Автозагрузка писем: создано %s, обновлено %s, пропущено %s, ошибок %s',
            batch['created'],
            batch['updated'],
            batch['skipped'],
            batch['errors'],
        )
        return {
            'status': 'ok',
            'processed': processed,
            'created': batch['created'],
            'updated': batch['updated'],
            'skipped': batch['skipped'],
            'errors': batch['errors'],
        }
    except Exception:
        logger.exception('Автозагрузка писем завершилась ошибкой')
        return {'status': 'error', 'message': 'Ошибка разбора почты'}
    finally:
        try:
            email_client.close()
        except Exception:
            pass
