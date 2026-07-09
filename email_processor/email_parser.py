"""
Парсер HTML/текстовых писем
"""
import re
import hashlib
import html
from email.header import decode_header
from email.message import Message
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup


class EmailParser:
    """Парсер содержимого писем"""

    def __init__(self, patterns: Dict, subject_filters: Optional[list] = None):
        self.patterns = patterns
        self.subject_filters = subject_filters or ['Оборудование и комплектующие']

    @staticmethod
    def decode_header_value(header_value: str) -> str:
        """Декодирование заголовков"""
        if not header_value:
            return ""
        try:
            decoded_parts = decode_header(header_value)
            result = ""
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    if encoding:
                        result += content.decode(encoding, errors='ignore')
                    else:
                        result += content.decode('utf-8', errors='ignore')
                else:
                    result += str(content)
            return result
        except:
            return str(header_value)

    @staticmethod
    def get_email_body(email_message: Message) -> Dict[str, str]:
        """Извлечение тела письма"""
        body_text = ""
        body_html = ""

        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_text = payload.decode('utf-8', errors='ignore')
                elif content_type == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        body_html = payload.decode('utf-8', errors='ignore')
        else:
            payload = email_message.get_payload(decode=True)
            if payload:
                body_text = payload.decode('utf-8', errors='ignore')

        # Если есть HTML, но нет текста, извлекаем текст из HTML
        if body_html and not body_text:
            soup = BeautifulSoup(body_html, 'html.parser')
            body_text = soup.get_text(separator='\n')

        return {
            'text': body_text,
            'html': body_html
        }

    @staticmethod
    def parse_date(date_string: str) -> datetime:
        """Парсинг даты письма"""
        if not date_string:
            return datetime.now()

        try:
            from email.utils import parsedate_to_datetime
            return parsedate_to_datetime(date_string)
        except:
            return datetime.now()

    def extract_ticket_id(self, subject: str) -> Optional[str]:
        """Извлечение номера заявки из темы"""
        match = re.search(self.patterns['ticket_id'], subject)
        if match:
            return match.group(1)
        return None

    @staticmethod
    def _clean_note(note: str) -> str:
        """Очистка примечания от стандартного блока-подписи (футера уведомлений)"""
        if not note:
            return note

        # Точный футер, который добавляет система техподдержки в конец примечания.
        # Структура:
        #   ----------------------------------------  (строка из 40 дефисов)
        #   (пустая строка)
        #   --                                       (два дефиса с пробелом)
        #   Внимание! Отвечать на это письмо не надо! ...
        #   ...Настройка уведомлений</a>
        footer_pattern = re.compile(
            r'-{3,}\s*'
            r'--\s*'
            r'Внимание!\s*Отвечать\s*на\s*это\s*письмо\s*не\s*надо!.*?'
            r'Настройка\s*уведомлений[^<]*</?a>?\s*',
            re.DOTALL | re.IGNORECASE
        )
        note = footer_pattern.sub('', note).strip()

        # Дополнительная очистка: удаляем пустые строки-разделители, оставшиеся после удаления футера
        note = re.sub(r'\n{3,}', '\n\n', note).strip()

        # Если после очистки осталась только строка из дефисов — удаляем и её
        note = re.sub(r'^-{3,}\s*$', '', note).strip()

        return note

    @staticmethod
    def _validate_inventory_number(value: str) -> tuple:
        """
        Валидация и классификация значения поля 'Инвентарный номер'.
        Возвращает кортеж (inventory_number, serial_number, is_partial).

        Правила:
        - Если значение содержит буквы (латиница/кириллица) — это серийный номер.
        - Если значение состоит только из цифр и длина = 12 — это полный
          корректный инвентарный номер.
        - Если значение состоит только из цифр, но длина <= 6 — это неполный
          инвентарный номер (пользователь указал не все цифры), сохраняется
          с флагом is_partial=True.
        - Если значение состоит только из цифр, длина от 7 до 11 — также
          считается неполным (is_partial=True), т.к. полный номер = 12 цифр.
        - is_partial=True означает, что номер неполный и в будущем может быть заменён.
        """
        if not value:
            return None, None, False

        # Проверяем, есть ли буквы (латиница или кириллица)
        if re.search(r'[a-zA-Zа-яА-ЯёЁ]', value):
            # Это серийный номер
            return None, value, False

        # Проверяем, состоит ли только из цифр
        if re.match(r'^\d+$', value):
            digits_only = value
            if len(digits_only) == 12:
                # Ровно 12 цифр — полный корректный инвентарный номер
                return digits_only, None, False
            # Меньше или больше 12 цифр (но <= 6 или 7-11) — неполный номер
            return digits_only, None, True

        # Если не подходит ни под одно правило — возвращаем как есть
        return value, None, False

    @staticmethod
    def _clean_inline_text(value: str) -> str:
        """Нормализация пробелов внутри одной извлечённой строки."""
        value = html.unescape(value or '').replace('\xa0', ' ')
        return re.sub(r'\s+', ' ', value).strip()

    @classmethod
    def _normalize_soglasovano_source(cls, body: str) -> str:
        """Подготовка HTML/plain text тела письма для поиска согласованных позиций."""
        if not body:
            return ''

        normalized = html.unescape(body).replace('\xa0', ' ')
        normalized = re.sub(r'<\s*br\s*/?\s*>', '\n', normalized, flags=re.IGNORECASE)
        normalized = re.sub(r'</\s*(?:div|p|li|tr)\s*>', '\n', normalized, flags=re.IGNORECASE)

        if re.search(r'<[^>]+>', normalized):
            normalized = BeautifulSoup(normalized, 'html.parser').get_text(separator='\n')

        normalized = normalized.replace('\r\n', '\n').replace('\r', '\n')
        normalized = re.sub(r'[ \t]+', ' ', normalized)
        normalized = re.sub(r'\n{2,}', '\n', normalized)
        return normalized.strip()

    @classmethod
    def _extract_soglasovano_lines(cls, body: str) -> List[str]:
        """
        Извлекает все согласованные позиции из тела письма.

        Поддерживает оба формата:
        - каждая позиция на отдельной строке;
        - HTML-текст, склеенный без переносов: "... СОГЛАСОВАНО29 - ...".
        """
        normalized_body = cls._normalize_soglasovano_source(body)
        lines: List[str] = []
        seen = set()

        def add_line(value: str) -> None:
            cleaned = cls._clean_inline_text(value)
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                lines.append(cleaned)

        # Сначала разбираем построчно: это безопаснее для старого формата
        # "75    Деталь = согласовано", где HTML-пробелы уже нормализованы.
        line_pattern = re.compile(
            r'^\s*(\d+)\s*(?:[-–—]|\s+)\s*(.*?)\s*(?:[-–—=])\s*(СОГЛАСОВАНО)\b',
            re.IGNORECASE,
        )
        for raw_line in normalized_body.splitlines():
            if len(re.findall(r'СОГЛАСОВАНО', raw_line, re.IGNORECASE)) != 1:
                continue
            match = line_pattern.search(raw_line)
            if not match:
                continue
            number = match.group(1).strip()
            title = cls._clean_inline_text(match.group(2))
            status = match.group(3).upper()
            if title:
                add_line(f'{number} - {title} - {status}')

        if lines:
            return lines

        # Затем ищем inline-формат без переносов между позициями.
        # Основные форматы:
        #   "27 - Ролик отделения ADF в сборе - СОГЛАСОВАНО"
        #   "75    Ролик отделения ADF в сборе = согласовано"
        # Паттерн намеренно ищет завершение по слову СОГЛАСОВАНО, чтобы разделять
        # несколько позиций даже при отсутствии переноса между ними.
        position_pattern = re.compile(
            r'(?<!\d)(\d+)\s*(?:[-–—]|\s{2,})\s*(.*?)\s*(?:[-–—=])\s*(СОГЛАСОВАНО)',
            re.IGNORECASE | re.DOTALL,
        )
        for match in position_pattern.finditer(normalized_body):
            number = match.group(1).strip()
            title = cls._clean_inline_text(match.group(2))
            status = match.group(3).upper()
            if title:
                add_line(f'{number} - {title} - {status}')

        if lines:
            return lines

        # Fallback для писем, где строка с согласованием есть, но номер позиции
        # оформлен нестандартно или отсутствует.
        for raw_line in normalized_body.splitlines():
            if re.search(r'СОГЛАСОВАНО', raw_line, re.IGNORECASE):
                add_line(raw_line)

        if lines:
            return lines

        # Последний fallback: ограниченный контекст перед словом СОГЛАСОВАНО.
        fallback_pattern = re.compile(r'.{0,100}?СОГЛАСОВАНО', re.IGNORECASE | re.DOTALL)
        for match in fallback_pattern.finditer(normalized_body):
            add_line(match.group(0))

        return lines

    def parse_email_content(self, body: str) -> Dict:
        """Парсинг тела письма для извлечения всех полей"""
        result = {}

        # Словарь для поиска: ключ -> список паттернов (первый совпавший используется)
        # Формат писем: "* Ключ: Значение" (со звёздочкой в начале строки)
        field_patterns = {
            'inventory_number': [
                r'(?:\*\s*)?Инвентарный номер:\s*(\S+)',
                r'(?:\*\s*)?Инв\.\s*номер\s*принтера:\s*(\S+)',
            ],
            'printer_model': [
                r'(?:\*\s*)?Принтер/МФУ:\s*(.+?)(?:\n|$)',
            ],
            'status': [r'(?:\*\s*)?Статус:\s*(.+?)(?:\n|$)'],
            'priority': [r'(?:\*\s*)?Приоритет:\s*(.+?)(?:\n|$)'],
            'assigned_to': [r'(?:\*\s*)?Назначен(?:а)?:\s*(.+?)(?:\n|$)'],
            'office': [r'(?:\*\s*)?Офис(?:\s*\(новый\))?:\s*(.+?)(?:\n|$)'],
            'cabinet': [r'(?:\*\s*)?Кабинет(?:\s*\(новый\))?:\s*(.+?)(?:\n|$)'],
            'component': [r'(?:\*\s*)?Комплектующее:\s*(.+?)(?:\n|$)'],
            'author': [r'(?:\*\s*)?Автор:\s*(.+?)(?:\n|$)'],
            'phone': [r'(?:\*\s*)?Контактный телефон:\s*(\d+)(?:\n|$)'],
            'department': [r'(?:\*\s*)?Подразделение:\s*(.+?)(?:\n|$)'],
            'position': [r'(?:\*\s*)?Должность:\s*(.+?)(?:\n|$)'],
            'required_action': [r'(?:\*\s*)?Требуется:\s*(.+?)(?:\n|$)'],
            'cause': [r'(?:\*\s*)?Причина обращения:\s*(.+?)(?:\n|$)'],
        }

        # Поиск однострочных полей
        for key, patterns in field_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, body, re.MULTILINE)
                if match:
                    value = match.group(1).strip()
                    # Пропускаем пустые значения, звёздочку и прочерк (—, -)
                    if value and value not in ('*', '—', '-'):
                        result[key] = value
                        break

        # Поиск многострочных полей (с re.DOTALL)
        multiline_patterns = {
            'work_done': r'(?:\*\s*)?Проведены работы:\s*(.*?)(?:\n\s*\*|\n(?:-{3,})|\n\n|\n*$|$)',
            'tech_conclusion': r'(?:\*\s*)?Тех\.\s*вывод:\s*(.*?)(?:\n\s*\*|\n(?:-{3,})|\n\n|\n*$|$)',
            'note': r'(?:\*\s*)?Примечание:\s*(.*?)(?:\n(?:-{3,}|\n(?:\*|(?:-{3,})|$)|$)|$)',
            'fault_description': r'(?:\*\s*)?Описание неисправности:\s*(.*?)(?:\n(?:\*|(?:-{3,})|\n|$)|$)',
        }
        for key, pattern in multiline_patterns.items():
            match = re.search(pattern, body, re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Отбрасываем, если значение начинается с '* ' (захватило следующее поле)
                if value and not value.startswith('*'):
                    # Очищаем примечание от стандартного блока-подписи
                    if key == 'note':
                        value = self._clean_note(value)
                    result[key] = value

        # Парсинг модели принтера из "Оборудование: ..."
        if 'printer_model' not in result:
            equip_match = re.search(r'(?:\*\s*)?Оборудование:\s*(.+?)(?:\n|$)', body)
            if equip_match:
                equip_value = equip_match.group(1).strip()
                if equip_value and equip_value not in ('Принтер', 'Принтер/МФУ', 'МФУ'):
                    result['printer_model'] = equip_value

        soglasovano_lines = self._extract_soglasovano_lines(body)
        if soglasovano_lines:
            result['soglasovano_line'] = '\n'.join(soglasovano_lines)

        # Парсинг ФИО отдельно
        full_name_pattern = r'Фамилия:\s*(.+?)\n\s*Имя:\s*(.+?)\n\s*Отчество:\s*(.+?)(?:\n|$)'
        match = re.search(full_name_pattern, body, re.DOTALL)
        if match:
            result['full_name'] = f"{match.group(1).strip()} {match.group(2).strip()} {match.group(3).strip()}"

        # Fallback-парсинг статуса: если статус не найден через стандартный паттерн,
        # пробуем найти "Статус: ..." в любом месте текста (даже без переноса строки после)
        if 'status' not in result:
            status_fallback = re.search(
                r'Статус[:\s]*([^\n*]+?)(?:\s*[\n*]|\s*$|-\s*-\s*)',
                body, re.IGNORECASE
            )
            if status_fallback:
                value = status_fallback.group(1).strip()
                if value and value not in ('*', '—', '-'):
                    result['status'] = value

        # Альтернативный поиск инвентарного номера
        if not result.get('inventory_number'):
            match = re.search(self.patterns['inventory_number_alt'], body)
            if match:
                result['inventory_number'] = match.group(1)

        # Валидация и классификация инвентарного номера
        raw_inv = result.get('inventory_number')
        if raw_inv:
            inv_number, serial_number, is_partial = self._validate_inventory_number(raw_inv)
            if serial_number:
                # Это серийный номер — сохраняем отдельно, inventory_number не устанавливаем
                result.pop('inventory_number', None)
                result['serial_number'] = serial_number
            elif inv_number:
                result['inventory_number'] = inv_number
                # Если номер неполный (< 6 цифр), помечаем для последующей обработки
                if is_partial:
                    result['inventory_partial'] = True
                result.pop('serial_number', None)

        return result

    def get_skip_reason(self, email_message: Message) -> Optional[str]:
        """Возвращает причину пропуска письма или None, если письмо подходит."""
        subject = self.decode_header_value(email_message.get('Subject', ''))
        if not any(filter_value in subject for filter_value in self.subject_filters):
            return 'subject_filter'
        if not self.extract_ticket_id(subject):
            return 'no_ticket_id'
        return None

    def parse_email_detailed(self, email_message: Message) -> Tuple[Optional[Dict], Optional[str]]:
        """
        Полный парсинг письма с указанием причины пропуска.

        Returns:
            tuple(data, skip_reason): data — распарсенное письмо, skip_reason — код пропуска
        """
        skip_reason = self.get_skip_reason(email_message)
        if skip_reason:
            return None, skip_reason

        try:
            subject = self.decode_header_value(email_message.get('Subject', ''))
            from_addr = self.decode_header_value(email_message.get('From', ''))
            ticket_id = self.extract_ticket_id(subject)
            if not ticket_id:
                return None, 'no_ticket_id'

            body_data = self.get_email_body(email_message)
            body = body_data['text']
            date_str = email_message.get('Date', '')
            received_date = self.parse_date(date_str)
            parsed_data = self.parse_email_content(body)

            result = {
                'ticket_number': ticket_id,
                'subject': subject,
                'from_address': from_addr,
                'received_date': received_date,
                'body': body,
                **parsed_data,
            }
            hash_string = f"{ticket_id}{received_date.isoformat()}{body[:200]}"
            result['email_hash'] = hashlib.sha256(hash_string.encode()).hexdigest()
            return result, None

        except Exception as exc:
            print(f"✗ Ошибка парсинга письма: {exc}")
            return None, 'parse_error'

    def parse_email(self, email_message: Message) -> Optional[Dict]:
        """Полный парсинг письма"""
        email_data, _skip_reason = self.parse_email_detailed(email_message)
        return email_data