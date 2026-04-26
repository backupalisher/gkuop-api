"""
Главный модуль приложения
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from config.settings import load_config
from database.db_manager import DatabaseManager
from email_processor.email_client import EmailClient
from email_processor.email_parser import EmailParser
from email_processor.ticket_processor import TicketProcessor
from utils.logger import logger
from utils.helpers import print_statistics, confirm_action, exit_with_error

# Загрузка переменных окружения
load_dotenv()

class EmailParserApplication:
    """Основное приложение"""

    def __init__(self):
        self.config = load_config()
        self.db_manager = None
        self.email_client = None
        self.email_parser = None
        self.ticket_processor = None

    def initialize(self) -> bool:
        """Инициализация всех компонентов"""
        logger.info("Инициализация приложения...")

        # Инициализация базы данных
        self.db_manager = DatabaseManager({
            'host': self.config['database'].host,
            'port': self.config['database'].port,
            'database': self.config['database'].database,
            'user': self.config['database'].user,
            'password': self.config['database'].password
        })

        if not self.db_manager.connect():
            return False

        # Инициализация почтового клиента
        self.email_client = EmailClient(
            imap_server=self.config['email'].imap_server,
            email=self.config['email'].email,
            password=self.config['email'].password,
            port=self.config['email'].port
        )

        if not self.email_client.connect():
            return False

        if not self.email_client.select_folder(self.config['email'].folder):
            return False

        # Инициализация парсера
        self.email_parser = EmailParser(
            self.config['parser'].patterns,
            subject_filters=self.config['parser'].subject_filters
        )

        # Инициализация обработчика заявок
        self.ticket_processor = TicketProcessor(self.db_manager)

        logger.info("Приложение успешно инициализировано")
        return True

    def process_emails(self, limit: int = None, since_date: datetime = None):
        """Обработка писем"""
        logger.info("Начало обработки писем...")

        # Поиск писем
        email_ids = self.email_client.search_emails(
            subject_filters=self.config['parser'].subject_filters if since_date is None else None,
            since_date=since_date,
            from_filter=self.config['parser'].from_filter
        )

        if not email_ids:
            logger.info("Нет новых писем для обработки")
            return

        # Ограничение количества
        if limit and limit < len(email_ids):
            email_ids = email_ids[:limit]
            logger.info(f"Ограничение обработки: {limit} писем")

        processed = 0
        errors = 0

        for i, email_id in enumerate(email_ids, 1):
            logger.info(f"Обработка письма {i}/{len(email_ids)}")

            # Получение письма
            email_message = self.email_client.fetch_email(email_id)
            if not email_message:
                errors += 1
                continue

            # Парсинг письма
            email_data = self.email_parser.parse_email(email_message)
            if not email_data:
                logger.warning(f"Письмо не соответствует критериям или не удалось распарсить")
                continue

            # Обработка заявки
            if self.ticket_processor.process_email(email_data):
                processed += 1
            else:
                errors += 1

        logger.info(f"Обработка завершена. Обработано: {processed}, Ошибок: {errors}")

        # Вывод статистики
        stats = self.db_manager.get_statistics()
        print_statistics(stats)

    def show_ticket_history(self, ticket_number: str):
        """Показать историю заявки"""
        history = self.db_manager.get_ticket_history(ticket_number)

        if not history:
            print(f"Заявка #{ticket_number} не найдена или не имеет комментариев")
            return

        print(f"\n{'='*60}")
        print(f"ИСТОРИЯ ЗАЯВКИ #{ticket_number}")
        print(f"{'='*60}")

        for i, event in enumerate(history, 1):
            print(f"\n{i}. Дата: {event['date']}")
            print(f"   Комментарий: {event['comment']}")
            if event['status_before'] != event['status_after']:
                print(f"   Статус: {event['status_before']} → {event['status_after']}")
            if event['changes']:
                print(f"   Изменения: {event['changes']}")

        print(f"{'='*60}\n")

    def rebuild_database(self):
        """Обработка всех писем из почты (без фильтра по дате)"""
        if not self.initialize():
            exit_with_error("Не удалось инициализировать приложение")

        try:
            limit = self.config['parser'].max_emails_per_run
            self.process_emails(limit=limit)
        finally:
            self.close()

    def run_once(self):
        """Однократный запуск"""
        if not self.initialize():
            exit_with_error("Не удалось инициализировать приложение")

        try:
            limit = self.config['parser'].max_emails_per_run
            # Ищем письма с 1 апреля 2026
            since_date = datetime(2026, 4, 1)
            self.process_emails(limit=limit, since_date=since_date)
        finally:
            self.close()

    def run_interactive(self):
        """Интерактивный режим"""
        if not self.initialize():
            exit_with_error("Не удалось инициализировать приложение")

        while True:
            print("\n" + "="*50)
            print("МЕНЮ:")
            print("1. Обработать новые письма")
            print("2. Показать статистику")
            print("3. Показать историю заявки")
            print("4. Выйти")
            print("="*50)

            choice = input("Выберите действие (1-4): ").strip()

            if choice == '1':
                limit = input("Введите лимит писем (Enter для всех): ").strip()
                limit = int(limit) if limit else self.config['parser'].max_emails_per_run
                self.process_emails(limit=limit)

            elif choice == '2':
                stats = self.db_manager.get_statistics()
                print_statistics(stats)

            elif choice == '3':
                ticket_number = input("Введите номер заявки: ").strip()
                if ticket_number:
                    self.show_ticket_history(ticket_number)

            elif choice == '4':
                print("До свидания!")
                break

            else:
                print("Неверный выбор, попробуйте снова")

        self.close()

    def close(self):
        """Закрытие всех соединений"""
        if self.email_client:
            self.email_client.close()
        if self.db_manager:
            self.db_manager.close()
        logger.info("Приложение завершило работу")

def main():
    """Точка входа"""
    app = EmailParserApplication()

    # Проверка аргументов командной строки
    if len(sys.argv) > 1:
        if sys.argv[1] == '--once':
            app.run_once()
        elif sys.argv[1] == '--rebuild':
            app.rebuild_database()
        elif sys.argv[1] == '--history' and len(sys.argv) > 2:
            if app.initialize():
                app.show_ticket_history(sys.argv[2])
                app.close()
        else:
            print("Использование:")
            print("  python main.py                # Интерактивный режим")
            print("  python main.py --once         # Однократный запуск")
            print("  python main.py --rebuild      # Полная перезагрузка БД")
            print("  python main.py --history #    # Показать историю")
    else:
        app.run_interactive()

if __name__ == "__main__":
    main()