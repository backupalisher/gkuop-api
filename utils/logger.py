"""
Логирование операций
"""
import logging
from datetime import datetime
from pathlib import Path


class AppLogger:
    """Класс для настройки логирования"""

    def __init__(self, name: str = 'EmailParser', log_dir: str = 'logs'):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Очищаем старые хендлеры, чтобы избежать дублирования
        self.logger.handlers.clear()

        # Создание директории для логов
        Path(log_dir).mkdir(exist_ok=True)

        # Форматирование
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )

        # Файловый handler
        log_file = Path(log_dir) / f'parser_{datetime.now().strftime("%Y%m%d")}.log'
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)

        # Консольный handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def get_logger(self):
        return self.logger


# Глобальный логгер
logger = AppLogger().get_logger()