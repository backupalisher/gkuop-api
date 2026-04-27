"""
Модели данных для базы данных
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from psycopg2.extras import Json


@dataclass
class Ticket:
    """Модель заявки"""
    ticket_number: str
    subject: Optional[str] = None
    inventory_number: Optional[str] = None
    printer_model: Optional[str] = None
    office: Optional[str] = None
    cabinet: Optional[str] = None
    component: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    author_name: Optional[str] = None
    contact_phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    current_note: Optional[str] = None
    required_action: Optional[str] = None
    cause: Optional[str] = None
    fault_description: Optional[str] = None
    work_done: Optional[str] = None
    tech_conclusion: Optional[str] = None
    soglasovano_line: Optional[str] = None
    first_received_date: Optional[datetime] = None
    last_updated_date: Optional[datetime] = None
    email_hash: Optional[str] = None
    is_active: bool = True

    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        return asdict(self)

    def get_insert_params(self) -> tuple:
        """Параметры для вставки в БД"""
        return (
            self.ticket_number,
            self.subject,
            self.inventory_number,
            self.printer_model,
            self.office,
            self.cabinet,
            self.component,
            self.status,
            self.priority,
            self.assigned_to,
            self.author_name,
            self.contact_phone,
            self.department,
            self.position,
            self.current_note,
            self.required_action,
            self.cause,
            self.fault_description,
            self.work_done,
            self.tech_conclusion,
            self.soglasovano_line,
            self.first_received_date,
            self.last_updated_date,
            self.email_hash,
            self.is_active
        )


@dataclass
class TicketComment:
    """Модель комментария к заявке"""
    ticket_number: str
    comment_text: str
    changed_fields: Dict[str, Any]
    status_before: str
    status_after: str
    received_date: datetime
    email_hash: str

    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        data = asdict(self)
        data['changed_fields'] = Json(data['changed_fields'])
        return data

    def get_insert_params(self) -> tuple:
        """Параметры для вставки в БД"""
        return (
            self.ticket_number,
            self.comment_text,
            Json(self.changed_fields),
            self.status_before,
            self.status_after,
            self.received_date,
            self.email_hash
        )


@dataclass
class TicketHistoryRecord:
    """
    Модель записи хронологии заявки.
    Хранит только те поля, которые фактически изменились на момент письма
    (сравнение с предыдущим состоянием заявки).
    Каждое письмо по заявке создаёт одну запись в истории.
    """
    ticket_number: str
    received_date: datetime
    email_hash: str

    # Словарь изменившихся полей: {field_name: new_value}
    changed_fields: Dict[str, Any]

    # Все поля заявки на момент письма (для обратной совместимости)
    subject: Optional[str] = None
    inventory_number: Optional[str] = None
    printer_model: Optional[str] = None
    office: Optional[str] = None
    cabinet: Optional[str] = None
    component: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    author_name: Optional[str] = None
    contact_phone: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    current_note: Optional[str] = None
    required_action: Optional[str] = None
    cause: Optional[str] = None
    fault_description: Optional[str] = None
    work_done: Optional[str] = None
    tech_conclusion: Optional[str] = None
    soglasovano_line: Optional[str] = None

    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        data = asdict(self)
        data['changed_fields'] = Json(data['changed_fields'])
        return data

    def get_insert_params(self) -> tuple:
        """Параметры для вставки в БД"""
        return (
            self.ticket_number,
            self.received_date,
            self.email_hash,
            Json(self.changed_fields),
            self.subject,
            self.inventory_number,
            self.printer_model,
            self.office,
            self.cabinet,
            self.component,
            self.status,
            self.priority,
            self.assigned_to,
            self.author_name,
            self.contact_phone,
            self.department,
            self.position,
            self.current_note,
            self.required_action,
            self.cause,
            self.fault_description,
            self.work_done,
            self.tech_conclusion,
            self.soglasovano_line
        )


@dataclass
class TicketImage:
    """Модель изображения, прикреплённого к заявке"""
    ticket_number: str
    file_path: str
    original_filename: str
    mime_type: str
    file_size: int
    thumbnail_path: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    is_deleted: bool = False

    def to_dict(self) -> Dict:
        """Преобразование в словарь"""
        return asdict(self)

    def get_insert_params(self) -> tuple:
        """Параметры для вставки в БД"""
        return (
            self.ticket_number,
            self.file_path,
            self.original_filename,
            self.mime_type,
            self.file_size,
            self.thumbnail_path,
            self.uploaded_at or datetime.now(),
            self.is_deleted,
        )