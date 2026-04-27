"""
Обработчик заявок и комментариев
"""
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
    IMMUTABLE_FIELDS = ['inventory_number', 'printer_model']

    # Статусы, которые нельзя перезаписывать при обновлении из почты
    PROTECTED_STATUSES = {'Выполнено', 'В архив'}

    def get_changed_fields(self, existing_ticket: Dict, new_data: Dict) -> Dict:
        """Определение измененных полей"""
        changed = {}

        # Защита: если у заявки уже стоит "Выполнено" или "В архив" — не перезаписываем статус
        existing_status = (existing_ticket.get('status', '') or '').strip()
        if existing_status in self.PROTECTED_STATUSES:
            # Не обновляем статус, но остальные поля можно обновлять
            pass

        for field in self.TRACKED_FIELDS:
            old_value = existing_ticket.get(field, '') or ''
            new_value = new_data.get(field, '') or ''

            # Защита от перезаписи: если поле уже есть в БД, а в новом письме оно пустое — не обновляем
            if old_value and not new_value:
                continue

            # Для immutable-полей: если значение уже есть в БД, не перезаписываем даже если пришло другое
            if field in self.IMMUTABLE_FIELDS and old_value:
                continue

            # Защита статусов "Выполнено" и "В архив" от перезаписи
            if field == 'status' and existing_status in self.PROTECTED_STATUSES:
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

        # Защита: если у заявки уже стоит "Выполнено" или "В архив" — не перезаписываем статус
        existing_status = (existing_ticket.get('status', '') or '').strip() if existing_ticket else ''

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
            old_value = existing_ticket.get(field, '') if existing_ticket else ''

            new_value = email_data.get(field, '') or ''

            # Для immutable-полей: если значение уже есть в БД, не перезаписываем
            if field in self.IMMUTABLE_FIELDS and field in seen_immutable:
                continue

            # Защита статусов "Выполнено" и "В архив" от перезаписи
            if field == 'status' and existing_status in self.PROTECTED_STATUSES:
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

            # Получаем последнюю запись истории для сравнения (чтобы сохранять только diff)
            last_history = self.db.get_last_history_record(ticket_number)

            # Всегда сохраняем снимок в историю (каждое письмо = запись в хронологии)
            # Передаём current_ticket, чтобы immutable-поля (inventory_number, printer_model)
            # не потерялись, если в текущем письме их нет
            history_record = self._build_history_record(email_data, current_ticket, last_history)
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
                # Защита: не перезаписываем статусы "Выполнено" и "В архив"
                if old_status in self.PROTECTED_STATUSES:
                    update_data.pop('status', None)
                elif old_status != new_status and 'status' not in update_data:
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