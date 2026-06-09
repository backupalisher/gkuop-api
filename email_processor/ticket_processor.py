"""
Обработчик заявок и комментариев
"""
import re
from typing import Dict, Optional
from datetime import datetime
from database.models import Ticket, TicketComment, TicketHistoryRecord
from database.db_manager import DatabaseManager


class TicketProcessor:
    """Обработка и сохранение заявок"""

    # Все поля, которые отслеживаем и сохраняем в тикете
    TRACKED_FIELDS = [
        'status', 'priority', 'assigned_to', 'current_note', 'office', 'cabinet',
        'required_action', 'cause', 'fault_description', 'work_done', 'tech_conclusion',
        'inventory_number', 'printer_model'
    ]

    # Человеческие названия полей для комментариев
    FIELD_LABELS = {
        'status': 'Статус',
        'priority': 'Приоритет',
        'assigned_to': 'Назначена',
        'current_note': 'Примечание',
        'office': 'Офис',
        'cabinet': 'Кабинет',
        'required_action': 'Требуется',
        'cause': 'Причина обращения',
        'fault_description': 'Описание неисправности',
        'work_done': 'Проведены работы',
        'tech_conclusion': 'Тех. вывод',
        'inventory_number': 'Инвентарный номер',
        'printer_model': 'Оборудование',
    }

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def generate_comment_text(self, changed_fields: Dict, old_status: str, new_status: str) -> str:
        """Генерация текста комментария на основе изменений"""
        comments = []

        if old_status != new_status:
            comments.append(f"Статус изменён с '{old_status}' на '{new_status}'")

        for field, new_value in changed_fields.items():
            if field == 'status':
                continue  # уже обработано выше
            label = self.FIELD_LABELS.get(field, field)
            comments.append(f"{label}: {new_value}")

        if comments:
            return "; ".join(comments)
        return "Обновление информации по заявке"

    # Поля, которые фиксируются при первом появлении и не перезаписываются пустыми значениями
    # printer_model — immutable (модель принтера не меняется),
    # inventory_number — НЕ immutable, т.к. может быть заменён с серийного на правильный
    IMMUTABLE_FIELDS = ['printer_model']

    def get_changed_fields(self, existing_ticket: Dict, new_data: Dict) -> Dict:
        """Определение измененных полей"""
        changed = {}

        # Поля, которые не должны попадать в changed_fields
        _excluded = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}

        for field in self.TRACKED_FIELDS:
            # Пропускаем поля, исключённые из отслеживания изменений
            if field in _excluded:
                continue

            old_value = existing_ticket.get(field, '') or ''
            new_value = new_data.get(field, '') or ''

            # Защита от перезаписи: если поле уже есть в БД, а в новом письме оно пустое — не обновляем
            if old_value and not new_value:
                continue

            # Для immutable-полей: если значение уже есть в БД, не перезаписываем даже если пришло другое
            if field in self.IMMUTABLE_FIELDS and old_value:
                continue

            if old_value != new_value and new_value:
                changed[field] = new_value

        return changed

    def _build_ticket_from_data(self, email_data: Dict) -> Ticket:
        """Создание объекта Ticket из данных письма"""
        return Ticket(
            ticket_number=email_data['ticket_number'],
            subject=email_data.get('subject'),
            inventory_number=email_data.get('inventory_number'),
            printer_model=email_data.get('printer_model'),
            office=email_data.get('office'),
            cabinet=email_data.get('cabinet'),
            component=email_data.get('component'),
            status=email_data.get('status'),
            priority=email_data.get('priority'),
            assigned_to=email_data.get('assigned_to'),
            author_name=email_data.get('full_name') or email_data.get('author'),
            contact_phone=email_data.get('phone'),
            department=email_data.get('department'),
            position=email_data.get('position'),
            current_note=email_data.get('note'),
            soglasovano_line=email_data.get('soglasovano_line'),
            required_action=email_data.get('required_action'),
            cause=email_data.get('cause'),
            fault_description=email_data.get('fault_description'),
            work_done=email_data.get('work_done'),
            tech_conclusion=email_data.get('tech_conclusion'),
            first_received_date=email_data['received_date'],
            last_updated_date=email_data['received_date'],
            email_hash=email_data['email_hash']
        )

    def _compute_changed_fields(self, email_data: Dict, existing_ticket: Dict = None,
                                 last_history_record: Dict = None) -> Dict:
        """
        Вычисляет словарь изменившихся полей между текущим письмом
        и актуальным состоянием заявки в БД (existing_ticket).
        Возвращает только те поля, которые реально изменились.
        """
        changed = {}

        # Поля, которые не должны попадать в changed_fields истории
        HISTORY_EXCLUDED_FIELDS = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}

        # Поля, которые отслеживаем в истории
        tracked_history_fields = [
            'status', 'priority', 'assigned_to', 'current_note', 'office', 'cabinet',
            'required_action', 'cause', 'fault_description', 'work_done', 'tech_conclusion',
            'inventory_number', 'printer_model', 'subject', 'soglasovano_line',
            'author_name', 'contact_phone', 'department', 'position', 'component'
        ]

        # Для immutable-полей собираем все значения, которые уже были записаны
        # (из existing_ticket ИЛИ из последней записи истории)
        seen_immutable = set()
        if existing_ticket:
            for f in self.IMMUTABLE_FIELDS:
                if existing_ticket.get(f):
                    seen_immutable.add(f)
        if last_history_record and last_history_record.get('changed_fields'):
            for f in self.IMMUTABLE_FIELDS:
                if last_history_record['changed_fields'].get(f):
                    seen_immutable.add(f)

        # Сравниваем с актуальным состоянием заявки из БД (existing_ticket)
        for field in tracked_history_fields:
            # Пропускаем поля, которые не должны отображаться в истории
            if field in HISTORY_EXCLUDED_FIELDS:
                continue

            old_value = existing_ticket.get(field, '') if existing_ticket else ''

            new_value = email_data.get(field, '') or ''

            # Для immutable-полей: если значение уже есть в БД, не перезаписываем
            if field in self.IMMUTABLE_FIELDS and field in seen_immutable:
                continue

            # Нормализуем для сравнения
            old_str = str(old_value).strip() if old_value else ''
            new_str = str(new_value).strip() if new_value else ''

            if old_str != new_str and new_str:
                changed[field] = new_value

        return changed

    def _build_history_record(self, email_data: Dict, existing_ticket: Dict = None,
                               last_history_record: Dict = None) -> TicketHistoryRecord:
        """Создание записи хронологии (только изменившиеся поля) из данных письма"""
        # Вычисляем diff относительно предыдущего состояния
        changed_fields = self._compute_changed_fields(email_data, existing_ticket, last_history_record)

        # Для полей, которые фиксируются при первом появлении:
        # если в письме их нет, но они есть в существующей заявке — берём оттуда
        def get_value(field):
            val = email_data.get(field)
            if val:
                return val
            if existing_ticket and field in self.IMMUTABLE_FIELDS:
                return existing_ticket.get(field)
            return val

        return TicketHistoryRecord(
            ticket_number=email_data['ticket_number'],
            received_date=email_data['received_date'],
            email_hash=email_data['email_hash'],
            changed_fields=changed_fields,
            subject=email_data.get('subject'),
            inventory_number=get_value('inventory_number'),
            printer_model=get_value('printer_model'),
            office=email_data.get('office'),
            cabinet=email_data.get('cabinet'),
            component=email_data.get('component'),
            status=email_data.get('status'),
            priority=email_data.get('priority'),
            assigned_to=email_data.get('assigned_to'),
            author_name=email_data.get('full_name') or email_data.get('author'),
            contact_phone=email_data.get('phone'),
            department=email_data.get('department'),
            position=email_data.get('position'),
            current_note=email_data.get('note'),
            soglasovano_line=email_data.get('soglasovano_line'),
            required_action=email_data.get('required_action'),
            cause=email_data.get('cause'),
            fault_description=email_data.get('fault_description'),
            work_done=email_data.get('work_done'),
            tech_conclusion=email_data.get('tech_conclusion'),
        )

    def process_new_ticket(self, email_data: Dict) -> bool:
        """Обработка новой заявки"""
        try:
            # Если в письме серийный номер (с буквами) вместо инвентарного,
            # и нет корректного инвентарного — сохраняем серийный как временный
            serial_number = email_data.get('serial_number')
            if serial_number and not email_data.get('inventory_number'):
                # Добавляем серийный номер как временный inventory_number
                email_data['inventory_number'] = serial_number
                # Добавляем пометку в current_note
                note_suffix = f"Инвентарный номер: {serial_number} (серийный номер)"
                old_note = (email_data.get('note') or '').strip()
                if old_note:
                    if note_suffix not in old_note:
                        email_data['note'] = f"{old_note}\n{note_suffix}"
                else:
                    email_data['note'] = note_suffix

            ticket = self._build_ticket_from_data(email_data)
            result = self.db.save_ticket(ticket)
            if result:
                # Сохраняем первый снимок в историю
                history_record = self._build_history_record(email_data)
                self.db.save_history_record(history_record)
                print(f"✓ Создана новая заявка #{email_data['ticket_number']}")
            return result

        except Exception as e:
            print(f"✗ Ошибка создания заявки: {e}")
            return False

    def _is_partial_inventory(self, value: str) -> bool:
        """
        Проверяет, является ли значение неполным инвентарным номером.
        Неполным считается номер из цифр, длина которого != 12.
        """
        if not value:
            return False
        if not re.match(r'^\d+$', value):
            return False
        return len(value) != 12

    def _is_serial_number(self, value: str) -> bool:
        """Проверяет, является ли значение серийным номером (содержит буквы)."""
        if not value:
            return False
        return bool(re.search(r'[a-zA-Zа-яА-ЯёЁ]', value))

    def _handle_serial_number(self, current_ticket: Dict, email_data: Dict,
                               changed_fields: Dict) -> Dict:
        """
        Обработка серийного номера или неполного инвентарного номера,
        ошибочно указанных в поле "Инвентарный номер".

        Логика:
        1. В письме серийный номер (с буквами), inventory_number отсутствует:
           - Если в БД ещё нет inventory_number — сохраняем серийный как временный
             с пометкой в current_note.
           - Если в БД уже есть inventory_number — игнорируем.
        2. В письме корректный inventory_number (только цифры, >= 6 знаков):
           - Если в БД сейчас серийный номер (с буквами) — заменяем, добавляем запись
             в current_note: "Инвентарный номер: X (Y)".
           - Если в БД сейчас неполный номер (< 6 цифр) — заменяем на полный,
             добавляем запись в current_note.
        3. В письме неполный инвентарный номер (< 6 цифр):
           - Если в БД ещё нет inventory_number — сохраняем как есть.
           - Если в БД уже есть — штатная логика get_changed_fields.

        Возвращает обновлённый changed_fields.
        """
        serial_number = email_data.get('serial_number')
        new_inventory = email_data.get('inventory_number')
        old_inventory = (current_ticket.get('inventory_number') or '').strip()

        # Случай 1: в письме серийный номер, инвентарного нет
        if serial_number and not new_inventory:
            if not old_inventory:
                # В БД ещё нет inventory_number — сохраняем серийный как временный
                changed_fields['inventory_number'] = serial_number
                # Добавляем пометку в current_note
                note_suffix = f"Инвентарный номер: {serial_number} (серийный номер)"
                old_note = (current_ticket.get('current_note') or '').strip()
                if old_note:
                    if note_suffix not in old_note:
                        changed_fields['current_note'] = f"{old_note}\n{note_suffix}"
                else:
                    changed_fields['current_note'] = note_suffix
            # Если в БД уже есть inventory_number — игнорируем серийный номер
            return changed_fields

        # Случай 2: в письме корректный инвентарный номер (только цифры, >= 6 знаков)
        if new_inventory and not self._is_partial_inventory(new_inventory):
            if old_inventory and self._is_serial_number(old_inventory):
                # В БД сейчас серийный номер — заменяем на правильный
                changed_fields['inventory_number'] = new_inventory
                note_suffix = f"Инвентарный номер: {new_inventory} ({old_inventory})"
                old_note = (current_ticket.get('current_note') or '').strip()
                if old_note:
                    if note_suffix not in old_note:
                        changed_fields['current_note'] = f"{old_note}\n{note_suffix}"
                else:
                    changed_fields['current_note'] = note_suffix
            elif old_inventory and self._is_partial_inventory(old_inventory):
                # В БД сейчас неполный номер — заменяем на полный
                changed_fields['inventory_number'] = new_inventory
                note_suffix = f"Инвентарный номер: {new_inventory} (ранее был указан неполный номер: {old_inventory})"
                old_note = (current_ticket.get('current_note') or '').strip()
                if old_note:
                    if note_suffix not in old_note:
                        changed_fields['current_note'] = f"{old_note}\n{note_suffix}"
                else:
                    changed_fields['current_note'] = note_suffix
            # Если в БД корректный инвентарный или его нет — штатная логика get_changed_fields сработает

        return changed_fields

    def _enrich_email_data_for_history(self, email_data: Dict, changed_fields: Dict) -> Dict:
        """
        Создаёт копию email_data, обогащённую изменениями из changed_fields,
        чтобы запись истории отражала актуальное состояние после обработки.
        """
        enriched = dict(email_data)
        for field, value in changed_fields.items():
            enriched[field] = value
        # Поле current_note в email_data приходит как 'note', а в changed_fields как 'current_note'
        if 'current_note' in changed_fields:
            enriched['note'] = changed_fields['current_note']
        return enriched

    def process_existing_ticket(self, existing_ticket: Dict, email_data: Dict) -> bool:
        """Обработка существующей заявки (обновление + комментарий + снимок в историю)"""
        try:
            ticket_number = email_data['ticket_number']

            # Всегда получаем свежий тикет из БД для точного сравнения
            # (предотвращает дублирование полей при последовательной обработке писем)
            current_ticket = self.db.get_ticket(ticket_number) or existing_ticket

            # Определяем изменения относительно актуального состояния в БД
            changed_fields = self.get_changed_fields(current_ticket, email_data)
            old_status = current_ticket.get('status', '') or ''
            new_status = email_data.get('status', old_status) or ''

            # Обработка серийного номера (ошибочно указанного как инвентарный)
            changed_fields = self._handle_serial_number(current_ticket, email_data, changed_fields)

            # Получаем последнюю запись истории для сравнения (чтобы сохранять только diff)
            last_history = self.db.get_last_history_record(ticket_number)

            # Создаём обогащённую копию email_data для записи истории,
            # чтобы она отражала изменения, внесённые _handle_serial_number
            history_email_data = self._enrich_email_data_for_history(email_data, changed_fields)

            # Всегда сохраняем снимок в историю (каждое письмо = запись в хронологии)
            history_record = self._build_history_record(history_email_data, current_ticket, last_history)
            self.db.save_history_record(history_record)

            # Если нет изменений, не создаем комментарий
            if not changed_fields and old_status == new_status:
                print(f"ℹ Заявка #{ticket_number} - нет изменений, снимок сохранён")
                return True

            # Создаем комментарий
            comment_text = self.generate_comment_text(changed_fields, old_status, new_status)

            comment = TicketComment(
                ticket_number=ticket_number,
                comment_text=comment_text,
                changed_fields=changed_fields,
                status_before=old_status,
                status_after=new_status,
                received_date=email_data['received_date'],
                email_hash=email_data['email_hash']
            )

            # Сохраняем комментарий
            if not self.db.save_comment(comment):
                return False

            # Обновляем все изменившиеся поля в тикете
            if changed_fields or old_status != new_status:
                update_data = dict(changed_fields)
                if old_status != new_status and 'status' not in update_data:
                    update_data['status'] = new_status
                if update_data:
                    # Передаём received_date из письма как last_updated_date,
                    # чтобы поле хранило время последнего письма, а не момент обновления
                    self.db.update_ticket(
                        ticket_number, update_data,
                        last_updated_date=email_data['received_date']
                    )

            print(f"✓ Обновлена заявка #{ticket_number} - добавлен комментарий и снимок")
            return True

        except Exception as e:
            print(f"✗ Ошибка обработки существующей заявки: {e}")
            return False

    def process_email(self, email_data: Dict) -> bool:
        """Основная логика обработки письма"""
        if not email_data or 'ticket_number' not in email_data:
            return False

        ticket_number = email_data['ticket_number']

        # Проверяем существование заявки
        if self.db.ticket_exists(ticket_number):
            existing_ticket = self.db.get_ticket(ticket_number)
            return self.process_existing_ticket(existing_ticket, email_data)
        else:
            return self.process_new_ticket(email_data)