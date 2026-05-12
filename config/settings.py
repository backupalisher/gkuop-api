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
    rebuild_folders: List[tuple] = field(default_factory=lambda: [
        ('INBOX', False),
        ('archive', True),
    ])

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
    pool_min_connections: int = 1
    pool_max_connections: int = 10
    retry_max_attempts: int = 3
    retry_base_delay: float = 0.5
    slow_query_threshold_ms: float = 500.0

    @classmethod
    def from_env(cls):
        """Загрузка из переменных окружения"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', 5432)),
            database=os.getenv('DB_NAME', 'ticket_system'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', ''),
            pool_min_connections=int(os.getenv('DB_POOL_MIN', '1')),
            pool_max_connections=int(os.getenv('DB_POOL_MAX', '10')),
            retry_max_attempts=int(os.getenv('DB_RETRY_MAX_ATTEMPTS', '3')),
            retry_base_delay=float(os.getenv('DB_RETRY_BASE_DELAY', '0.5')),
            slow_query_threshold_ms=float(os.getenv('DB_SLOW_QUERY_THRESHOLD_MS', '500.0')),
        )


@dataclass
class ParserConfig:
    """Конфигурация парсера"""
    subject_filters: List[str] = field(default_factory=lambda: ['Оборудование и комплектующие', 'Стационарное оборудование'])
    from_filter: str = 'gku-asupz-techsupp@transport.mos.ru'
    batch_size: int = 100
    max_emails_per_run: Optional[int] = None

    # Регулярные выражения для парсинга
    patterns: dict = field(default_factory=lambda: {
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
    })




@dataclass
class CompressionConfig:
    """Конфигурация сжатия изображений"""
    enabled: bool = True
    preset: str = 'balanced'  # max_quality, balanced, traffic_saving
    max_long_side: int = 1280
    jpeg_quality: int = 88
    webp_quality: int = 88
    target_max_size_kb: int = 600
    keep_exif: bool = True
    keep_alpha: bool = True

    @classmethod
    def from_env(cls):
        """Загрузка из переменных окружения"""
        return cls(
            enabled=os.getenv('IMAGE_COMPRESSION_ENABLED', 'true').lower() == 'true',
            preset=os.getenv('IMAGE_COMPRESSION_PRESET', 'balanced'),
            max_long_side=int(os.getenv('IMAGE_MAX_LONG_SIDE', 1280)),
            jpeg_quality=int(os.getenv('IMAGE_JPEG_QUALITY', 88)),
            webp_quality=int(os.getenv('IMAGE_WEBP_QUALITY', 88)),
            target_max_size_kb=int(os.getenv('IMAGE_TARGET_MAX_SIZE_KB', 600)),
            keep_exif=os.getenv('IMAGE_KEEP_EXIF', 'true').lower() == 'true',
            keep_alpha=os.getenv('IMAGE_KEEP_ALPHA', 'true').lower() == 'true',
        )


@dataclass
class AuthConfig:
    """Конфигурация модуля аутентификации"""
    secret_key: str = ''
    algorithm: str = 'HS256'
    access_token_expire_minutes: int = 1440  # 24 часа

    @classmethod
    def from_env(cls):
        return cls(
            secret_key=os.getenv('AUTH_SECRET_KEY', ''),
            algorithm=os.getenv('AUTH_ALGORITHM', 'HS256'),
            access_token_expire_minutes=int(os.getenv('AUTH_ACCESS_TOKEN_EXPIRE_MINUTES', '1440')),
        )


@dataclass
class StaticVersionConfig:
    """Конфигурация версионирования статических файлов"""
    enabled: bool = True
    method: str = 'hash'  # 'hash' | 'timestamp' | 'fixed'
    fixed_version: str = '1.0'

    @classmethod
    def from_env(cls):
        return cls(
            enabled=os.getenv('STATIC_VERSION_ENABLED', 'true').lower() == 'true',
            method=os.getenv('STATIC_VERSION_METHOD', 'hash'),
            fixed_version=os.getenv('STATIC_VERSION', '1.0'),
        )


@dataclass
class CORSConfig:
    """Конфигурация CORS"""
    allow_origins: List[str] = field(default_factory=lambda: ['*'])
    allow_credentials: bool = True
    allow_methods: List[str] = field(default_factory=lambda: ['*'])
    allow_headers: List[str] = field(default_factory=lambda: ['*'])

    @classmethod
    def from_env(cls):
        origins = os.getenv('CORS_ALLOW_ORIGINS', '*')
        return cls(
            allow_origins=[o.strip() for o in origins.split(',')] if origins != '*' else ['*'],
            allow_credentials=os.getenv('CORS_ALLOW_CREDENTIALS', 'true').lower() == 'true',
        )


# Загрузка конфигурации
def load_config():
    """Загрузка всех конфигураций"""
    return {
        'email': EmailConfig.from_env(),
        'database': DatabaseConfig.from_env(),
        'parser': ParserConfig(),
        'compression': CompressionConfig.from_env(),
        'auth': AuthConfig.from_env(),
        'cors': CORSConfig.from_env(),
        'static_version': StaticVersionConfig.from_env(),
    }