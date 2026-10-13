"""
Клиент для работы с почтовым сервером
"""
import imaplib
import email
import time
from email.message import Message
from email.header import decode_header
from typing import List, Optional
from datetime import datetime
import codecs


class EmailClient:
    """Клиент для подключения и работы с почтой"""

    def __init__(self, imap_server: str, email: str, password: str, port: int = 993):
        self.imap_server = imap_server
        self.email = email
        self.password = password
        self.port = port
        self.imap = None

    def connect(self) -> bool:
        """Подключение к почтовому серверу"""
        try:
            self.imap = imaplib.IMAP4_SSL(self.imap_server, self.port)
            self.imap.login(self.email, self.password)
            print(f"✓ Подключено к почтовому серверу: {self.imap_server}")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения к почте: {e}")
            return False

    def select_folder(self, folder: str = 'INBOX') -> bool:
        """Выбор папки"""
        try:
            # Кодируем кириллицу в названии папки в IMAP UTF-7 (RFC 3501 modified UTF-7)
            # Разделитель в Яндекс.Почте — |, а не /
            parts = folder.split('/')
            encoded_parts = []
            for part in parts:
                if part.isascii():
                    encoded_parts.append(part)
                else:
                    # Кодируем в UTF-7 и заменяем ведущий + на & (RFC 3501)
                    encoded = codecs.encode(part, 'utf-7').decode('ascii')
                    # В RFC 3501 только первый символ + заменяется на &
                    if encoded.startswith('+'):
                        encoded = '&' + encoded[1:]
                    encoded_parts.append(encoded)
            encoded_folder = '|'.join(encoded_parts)
            status, data = self.imap.select(encoded_folder)
            if status == 'OK':
                print(f"✓ Выбрана папка: {folder}")
                return True
            else:
                print(f"✗ Ошибка выбора папки {folder}: {data}")
                return False
        except Exception as e:
            print(f"✗ Ошибка выбора папки {folder}: {e}")
            return False

    def _imap_search(self, criteria: str, max_attempts: int = 3) -> List[bytes]:
        """Один IMAP SEARCH с повторами. Пустой список — и при ошибке, и при нуле писем."""
        for attempt in range(1, max_attempts + 1):
            try:
                status, messages = self.imap.search(None, criteria)
                if status == 'OK':
                    return messages[0].split() if messages and messages[0] else []

                print(
                    f"✗ Ошибка поиска писем (попытка {attempt}/{max_attempts}): "
                    f"status={status}, criteria={criteria!r}, response={messages!r}"
                )
            except Exception as e:
                print(
                    f"✗ Ошибка при поиске (попытка {attempt}/{max_attempts}, "
                    f"criteria={criteria!r}): {e}"
                )

            if attempt < max_attempts:
                time.sleep(0.5 * attempt)

        return []

    def _decode_from_header(self, header_value: str) -> str:
        """Декодирует заголовок From для сравнения с фильтром отправителя."""
        if not header_value:
            return ""
        try:
            decoded_parts = decode_header(header_value)
            result = ""
            for content, encoding in decoded_parts:
                if isinstance(content, bytes):
                    result += content.decode(encoding or "utf-8", errors="ignore")
                else:
                    result += str(content)
            return result
        except Exception:
            return str(header_value)

    def _peek_from_address(self, email_id: bytes) -> str:
        """Читает только заголовок From, не помечая письмо прочитанным."""
        try:
            status, msg_data = self.imap.fetch(
                email_id, "(BODY.PEEK[HEADER.FIELDS (FROM)])"
            )
            if status != "OK" or not msg_data:
                return ""
            raw = b""
            for part in msg_data:
                if isinstance(part, tuple) and len(part) > 1 and isinstance(part[1], bytes):
                    raw += part[1]
            header = email.message_from_bytes(raw)
            return self._decode_from_header(header.get("From", ""))
        except Exception as exc:
            print(f"✗ Не удалось прочитать From у письма {email_id}: {exc}")
            return ""

    def _messages_missing_from_index(
        self,
        from_filter: str,
        matched_ids: List[bytes],
    ) -> List[bytes]:
        """
        Добрать письма, которые Яндекс ещё не включил в индекс FROM.

        Индекс отстаёт на новые письма: SINCE их видит, FROM — нет,
        хотя заголовок From совпадает. Хвост после последнего совпадения
        короткий, поэтому From проверяется уже по заголовку.
        """
        if self.imap is None or not from_filter:
            return []

        if matched_ids:
            try:
                last_seq = max(int(item) for item in matched_ids)
            except ValueError:
                return []
            tail_criteria = f"{last_seq + 1}:*"
        else:
            return []

        tail_ids = self._imap_search(tail_criteria)
        if not tail_ids:
            return []

        needle = from_filter.lower()
        matched: List[bytes] = []
        for email_id in tail_ids:
            sender = self._peek_from_address(email_id)
            if needle in sender.lower():
                matched.append(email_id)
        return matched

    def search_emails(
        self,
        subject_filters: Optional[list] = None,
        since_date: Optional[datetime] = None,
        from_filter: Optional[str] = None,
        max_attempts: int = 3,
    ) -> List[bytes]:
        """Поиск писем по критериям с повторными попытками при сбое IMAP."""
        criteria_parts = []

        if from_filter:
            criteria_parts.append(f'(FROM "{from_filter}")')

        if since_date:
            date_str = since_date.strftime("%d-%b-%Y")
            criteria_parts.append(f'(SINCE "{date_str}")')

        criteria = ' '.join(criteria_parts) if criteria_parts else 'ALL'
        email_ids = self._imap_search(criteria, max_attempts)

        extra_ids: List[bytes] = []
        if from_filter and since_date:
            # Яндекс не включает свежие письма в индекс FROM: выборка только
            # по дате их видит, пересечение FROM+SINCE — нет.
            since_ids = self._imap_search(f'(SINCE "{date_str}")', max_attempts)
            known = set(email_ids)
            candidates = [item for item in since_ids if item not in known]
            needle = from_filter.lower()
            extra_ids = [
                item for item in candidates
                if needle in self._peek_from_address(item).lower()
            ]
        elif from_filter:
            extra_ids = self._messages_missing_from_index(from_filter, email_ids)

        if extra_ids:
            known = set(email_ids)
            email_ids = email_ids + [item for item in extra_ids if item not in known]
            print(f"✓ Писем вне индекса FROM: {len(extra_ids)}")

        print(f"✓ Найдено писем: {len(email_ids)}")
        return email_ids

    def fetch_email(self, email_id: bytes) -> Optional[Message]:
        """Получение письма по ID"""
        try:
            status, msg_data = self.imap.fetch(email_id, '(RFC822)')
            if status == 'OK':
                email_message = email.message_from_bytes(msg_data[0][1])
                return email_message
            return None
        except Exception as e:
            print(f"✗ Ошибка получения письма {email_id}: {e}")
            return None

    def close(self):
        """Закрытие соединения"""
        if self.imap:
            try:
                self.imap.close()
                self.imap.logout()
            except:
                pass