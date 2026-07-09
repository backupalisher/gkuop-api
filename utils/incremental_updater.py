"""
Модуль инкрементального обновления базы данных из почты.

Запоминает временную метку последнего успешного обновления в файле
last_update.txt и использует её для фильтрации писем при следующем запуске.
"""
import os
from datetime import datetime
from typing import Optional

from utils.email_sync import compute_imap_since_date


# Константы
LAST_UPDATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'last_update.txt'
)
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
INITIAL_DATE = datetime(2026, 1, 1, 0, 0, 0)


class IncrementalUpdater:
    """
    Менеджер инкрементального обновления.

    Хранит временную метку последнего успешного обновления в файле
    last_update.txt и вычисляет диапазон дат для выборки писем.
    """

    def __init__(self, filepath: str = LAST_UPDATE_FILE):
        self.filepath = filepath

    def get_last_update_date(self) -> datetime:
        """
        Читает дату последнего успешного обновления из файла.

        Если файл отсутствует, повреждён или содержит некорректный
        формат даты — возвращает INITIAL_DATE (01.01.2025 00:00:00).

        Returns:
            datetime: дата последнего успешного обновления
        """
        if not os.path.exists(self.filepath):
            return INITIAL_DATE

        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            if not content:
                return INITIAL_DATE
            return datetime.strptime(content, DATE_FORMAT)
        except (ValueError, OSError, IOError):
            # Файл повреждён или содержит некорректный формат
            return INITIAL_DATE

    def get_search_since_date(self, last_update: Optional[datetime] = None) -> datetime:
        """
        Вычисляет дату начала поиска писем.

        Формула: last_update - 1 день, начало суток (00:00:00).
        Это гарантирует захват изменений, произошедших в тот же день,
        но без дублирования уже обработанных данных.

        Args:
            last_update: дата последнего обновления (если None — читает из файла)

        Returns:
            datetime: дата начала поиска (начало суток за день до last_update)
        """
        if last_update is None:
            last_update = self.get_last_update_date()

        return compute_imap_since_date(last_update)

    def save_update_date(self, update_time: Optional[datetime] = None) -> bool:
        """
        Сохраняет временную метку успешного обновления в файл.

        В случае любой ошибки (например, нет прав на запись) файл
        НЕ обновляется, чтобы не потерять диапазон данных.

        Args:
            update_time: время обновления (если None — используется текущее)

        Returns:
            bool: True если сохранение успешно, False при ошибке
        """
        if update_time is None:
            update_time = datetime.now()

        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(update_time.strftime(DATE_FORMAT))
            return True
        except (OSError, IOError) as e:
            print(f"✗ Ошибка сохранения временной метки обновления: {e}")
            return False

    def get_update_range(self) -> tuple:
        """
        Возвращает кортеж (search_from, search_to) для фильтрации писем.

        - search_from: начало периода (last_update - 1 день, 00:00:00)
        - search_to: текущее время (момент запуска обновления)

        Returns:
            tuple[datetime, datetime]: (дата_начала_поиска, дата_окончания)
        """
        last_update = self.get_last_update_date()
        search_from = self.get_search_since_date(last_update)
        search_to = datetime.now()
        return search_from, search_to

    def format_range(self, search_from: datetime, search_to: datetime) -> str:
        """Форматирует диапазон для вывода в лог."""
        return (f"поиск писем с {search_from.strftime(DATE_FORMAT)} "
                f"по {search_to.strftime(DATE_FORMAT)}")

    def reset(self) -> bool:
        """
        Сбрасывает дату последнего обновления на INITIAL_DATE.
        Используется для полной перезагрузки БД (--rebuild).

        Returns:
            bool: True если успешно
        """
        return self.save_update_date(INITIAL_DATE)
