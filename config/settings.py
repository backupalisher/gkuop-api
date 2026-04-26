"""
Конфигурационные параметры приложения
"""
import os
from dataclasses import dataclass, field
from typing import Optional, List


@dataclass
class EmailConfig:
    """Конфигурация почтового сервера"""
    imap_server: str
    email: str
    password: str
    port: int = 993
    folder: str = 'INBOX'

    @classmethod
    def from_env(cls):
        """Загрузка из переменных окружения"""
        return cls(
            imap_server=os.getenv('IMAP_SERVER', 'imap.yandex.ru'),
            email=os.getenv('EMAIL', ''),
            password=os.getenv('EMAIL_PASSWORD', ''),
            folder=os.getenv('IMAP_FOLDER', 'INBOX')
        )


@dataclass
class DatabaseConfig:
    """Конфигурация базы данных"""
    host: str
    port: int
    database: str
    user: str
    password: str

    @classmethod
    def from_env(cls):
        """Загрузка из переменных окружения"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ticket_system'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )


@dataclass
class ParserConfig:
    """Конфигурация парсера"""
    subject_filters: List[str] = field(default_factory=lambda: ['Оборудование и комплектующие', 'Стационарное оборудование'])
    from_filter: str = 'gku-asupz-techsupp@transport.mos.ru'
    batch_size: int = 100
    max_emails_per_run: Optional[int] = None

    # Регулярные выражения для парсинга
    patterns: dict = None

    def __post_init__(self):
        self.patterns = {
            'ticket_id': r'#(\d+)',
            # Формат 1: "* Инвентарный номер: 110134006743 sn: ..." (Стационарное оборудование)
            # Формат 2: "* Инв. номер принтера: 110134000711" (Картриджи)
            'inventory_number': r'(?:\*\s*)?Инв(?:ентарный)?\.?\s*номер(?:\s*принтера)?:\s*(\d+)',
            'inventory_number_alt': r'L\d+\((\d+)\)',
            # Формат 1: "* Оборудование: Принтер/МФУ" или "* Оборудование: Принтер"
            # Формат 2: "* Принтер/МФУ: Xerox WorkCentre 3325"
            'printer_model': r'(?:\*\s*)?(?:Принтер/МФУ|Оборудование):\s*(.+?)(?:\n|$)',
            'status': r'(?:\*\s*)?Статус:\s*(.+?)(?:\n|$)',
            'priority': r'(?:\*\s*)?Приоритет:\s*(.+?)(?:\n|$)',
            # Формат 1: "* Назначена: Менеджеры по обслуживанию МФУ"
            # Формат 2: "* Назначен: ..."
            'assigned_to': r'(?:\*\s*)?Назначен(?:а)?:\s*(.+?)(?:\n|$)',
            # "* Офис: 2-й Южнопортовый пр-д, д. 27А, стр. 1"
            'office': r'(?:\*\s*)?Офис(?:\s*\(новый\))?:\s*(.+?)(?:\n|$)',
            # "* Кабинет: 608*" (со звёздочкой в конце)
            'cabinet': r'(?:\*\s*)?Кабинет(?:\s*\(новый\))?:\s*(\d+)\**\s*(?:\n|$)',
            'component': r'(?:\*\s*)?Комплектующее:\s*(.+?)(?:\n|$)',
            'note': r'(?:\*\s*)?Примечание:\s*(.*?)(?:\n(?:-{3,}|\n|$)|$)',
            'author': r'(?:\*\s*)?Автор:\s*(.+?)(?:\n|$)',
            'phone': r'(?:\*\s*)?Контактный телефон:\s*(\d+)(?:\n|$)',
            'department': r'(?:\*\s*)?Подразделение:\s*(.+?)(?:\n|$)',
            'position': r'(?:\*\s*)?Должность:\s*(.+?)(?:\n|$)',
            'required_action': r'(?:\*\s*)?Требуется:\s*(.+?)(?:\n|$)',
            'cause': r'(?:\*\s*)?Причина обращения:\s*(.+?)(?:\n|$)',
            # Может быть многострочным (см. заявку 403061)
            'fault_description': r'(?:\*\s*)?Описание неисправности:\s*(.+?)(?:\n(?:\*|(?:-{3,})|\n|$)|$)',
            'work_done': r'(?:\*\s*)?Проведены работы:\s*(.*?)(?:\n|$)',
            'tech_conclusion': r'(?:\*\s*)?Тех\.\s*вывод:\s*(.*?)(?:\n|$)',
        }


# Загрузка конфигурации
def load_config():
    """Загрузка всех конфигураций"""
    return {
        'email': EmailConfig.from_env(),
        'database': DatabaseConfig.from_env(),
        'parser': ParserConfig()
    }