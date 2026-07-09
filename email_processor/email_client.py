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

        for attempt in range(1, max_attempts + 1):
            try:
                status, messages = self.imap.search(None, criteria)
                if status == 'OK':
                    email_ids = messages[0].split() if messages[0] else []
                    print(f"✓ Найдено писем: {len(email_ids)}")
                    return email_ids

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