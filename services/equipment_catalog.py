"""
Справочник аппаратов: нормализация номеров, запрет пересечений и связь с заявкой.

Сопоставление не использует модель: одна модель стоит на многих аппаратах.
Связь ставится только когда кандидат ровно один.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

logger = logging.getLogger(__name__)

_EMPTY_INVENTORY = {'', '-', '—', '*'}
_LETTER_RE = re.compile(r'[A-Za-zА-Яа-яЁё]')
_MIN_SUFFIX = 4

DEFAULT_CATALOG_PATH = (
    Path(__file__).resolve().parent.parent / 'data' / 'equipment_catalog.xlsx'
)


class EquipmentConflictError(Exception):
    """Новый аппарат пересекается с уже существующим."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def normalize_serial_key(value: Optional[str]) -> str:
    """Ключ серийного номера: без пробелов, в верхнем регистре."""
    return re.sub(r'\s+', '', (value or '')).upper()


def digits_only(value: Optional[str]) -> str:
    """Оставляет только цифры, сохраняя ведущие нули."""
    return re.sub(r'\D', '', value or '')


def significant_digits(digits: str) -> str:
    """Цифры без ведущих нулей. Для строки из одних нулей возвращает ``0``."""
    if not digits:
        return ''
    stripped = digits.lstrip('0')
    return stripped or '0'


def format_equipment_label(
    model: Optional[str],
    serial_number: Optional[str],
    inventory_number: Optional[str],
) -> str:
    """Строка «Модель - серийный - инвентарный». Без инвентарного — две части."""
    parts = [(model or '').strip(), (serial_number or '').strip()]
    inventory = (inventory_number or '').strip()
    if inventory and inventory not in _EMPTY_INVENTORY:
        parts.append(inventory)
    return ' - '.join(part for part in parts if part)


def inventories_cross(left: str, right: str) -> bool:
    """
    Два инвентарных номера пересекаются, если совпадают целиком,
    совпадают без ведущих нулей или один является хвостом другого
    длиной не меньше 4 цифр.
    """
    if not left or not right:
        return False
    if left == right or significant_digits(left) == significant_digits(right):
        return True
    shorter, longer = (left, right) if len(left) <= len(right) else (right, left)
    return len(shorter) >= _MIN_SUFFIX and longer.endswith(shorter)


def find_equipment_conflict(
    serial_number: str,
    inventory_digits: Optional[str],
    existing: Sequence[Dict[str, Any]],
    exclude_id: Optional[int] = None,
) -> Optional[str]:
    """
    Возвращает текст конфликта или None.

    ``existing`` — строки справочника с полями id, model, serial_number,
    inventory_number, inventory_digits.
    """
    serial_key = normalize_serial_key(serial_number)
    serial_digits = _numeric_identifier(serial_number)
    for other in existing:
        if exclude_id is not None and other.get('id') == exclude_id:
            continue
        if normalize_serial_key(other.get('serial_number')) == serial_key:
            return (
                'Серийный номер совпадает с аппаратом '
                f'{_describe_equipment(other)}'
            )
        other_digits = other.get('inventory_digits') or ''
        other_serial_digits = _numeric_identifier(other.get('serial_number'))
        if inventory_digits and (
            inventories_cross(inventory_digits, other_digits)
            or inventories_cross(inventory_digits, other_serial_digits)
        ):
            return (
                'Инвентарный номер пересекается с аппаратом '
                f'{_describe_equipment(other)}'
            )
        if serial_digits and inventories_cross(serial_digits, other_digits):
            return (
                'Серийный номер пересекается с инвентарным номером аппарата '
                f'{_describe_equipment(other)}'
            )
    return None


def parse_equipment_payload(
    model: Optional[str],
    serial_number: Optional[str],
    inventory_number: Optional[str],
) -> Dict[str, Optional[str]]:
    """Проверяет поля формы и приводит их к виду для записи в БД."""
    clean_model = re.sub(r'\s+', ' ', (model or '').replace('\n', ' ')).strip()
    clean_serial = re.sub(r'\s+', '', (serial_number or '')).strip()
    if not clean_model:
        raise ValueError('Укажите модель аппарата')
    if not clean_serial:
        raise ValueError('Укажите серийный номер')
    if not _LETTER_RE.search(clean_serial) and not digits_only(clean_serial):
        raise ValueError('Серийный номер пустой')

    raw_inventory = (inventory_number or '').strip()
    if raw_inventory in _EMPTY_INVENTORY:
        stored_inventory = None
        stored_digits = None
    else:
        stored_digits = digits_only(raw_inventory)
        if len(stored_digits) < _MIN_SUFFIX:
            raise ValueError('Инвентарный номер должен содержать не меньше 4 цифр')
        stored_inventory = stored_digits

    return {
        'model': clean_model,
        'serial_number': clean_serial,
        'inventory_number': stored_inventory,
        'inventory_digits': stored_digits,
    }


def match_equipment(
    raw_value: Optional[str],
    equipment: Sequence[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    """
    Ищет единственный аппарат по значению из заявки.

    Буквы — только точный серийный номер.
    Цифры — точный инвентарный или хвост от 4 цифр.
    Ноль или несколько совпадений — связь не ставится.
    """
    value = (raw_value or '').strip()
    if not value or value in _EMPTY_INVENTORY:
        return None

    if _LETTER_RE.search(value):
        key = normalize_serial_key(value)
        hits = [
            item for item in equipment
            if normalize_serial_key(item.get('serial_number')) == key
        ]
        return hits[0] if len(hits) == 1 else None

    ticket_digits = digits_only(value)
    if not ticket_digits:
        return None

    hits: List[Dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: Dict[str, Any]) -> None:
        identity = str(item.get('id') or normalize_serial_key(item.get('serial_number')))
        if identity not in seen:
            seen.add(identity)
            hits.append(item)

    for item in equipment:
        inventory_digits = item.get('inventory_digits') or ''
        serial_digits = _numeric_identifier(item.get('serial_number'))
        if inventory_digits and inventory_digits == ticket_digits:
            add(item)
            continue
        if serial_digits and serial_digits == ticket_digits:
            add(item)
            continue
        if len(ticket_digits) < _MIN_SUFFIX or len(inventory_digits) < _MIN_SUFFIX:
            continue
        if ticket_digits.endswith(inventory_digits) or inventory_digits.endswith(ticket_digits):
            add(item)

    return hits[0] if len(hits) == 1 else None


def _numeric_identifier(value: Optional[str]) -> str:
    """Цифры идентификатора, если в нём нет букв. Иначе пустая строка."""
    text = (value or '').strip()
    if not text or _LETTER_RE.search(text):
        return ''
    return digits_only(text)


def read_catalog_xlsx(path: Path) -> List[Dict[str, Optional[str]]]:
    """Читает лист справочника: инвентарный, серийный, аппарат."""
    from openpyxl import load_workbook

    workbook = load_workbook(path, data_only=True, read_only=True)
    try:
        sheet = workbook[workbook.sheetnames[0]]
        rows: List[Dict[str, Optional[str]]] = []
        for index, row in enumerate(sheet.iter_rows(values_only=True)):
            if index == 0 or not row:
                continue
            inventory_raw = '' if row[0] is None else str(row[0])
            serial_raw = '' if len(row) < 2 or row[1] is None else str(row[1])
            model_raw = '' if len(row) < 3 or row[2] is None else str(row[2])
            if not serial_raw.strip() and not model_raw.strip():
                continue
            try:
                rows.append(parse_equipment_payload(model_raw, serial_raw, inventory_raw))
            except ValueError as exc:
                logger.warning(
                    'Строка %s справочника пропущена (%s): %s',
                    index + 1,
                    exc,
                    serial_raw,
                )
        return rows
    finally:
        workbook.close()


def _describe_equipment(row: Dict[str, Any]) -> str:
    return format_equipment_label(
        row.get('model'),
        row.get('serial_number'),
        row.get('inventory_number'),
    )


def assert_catalog_unique(rows: Iterable[Dict[str, Any]]) -> None:
    """Проверяет, что набор строк справочника не содержит пересечений."""
    accepted: List[Dict[str, Any]] = []
    for row in rows:
        conflict = find_equipment_conflict(
            row.get('serial_number') or '',
            row.get('inventory_digits'),
            accepted,
        )
        if conflict:
            raise EquipmentConflictError(conflict)
        accepted.append(row)
