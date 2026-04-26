"""
Скрипт для инициализации базы данных
"""
import sys
from database.db_manager import DatabaseManager
from config.settings import DatabaseConfig
from dotenv import load_dotenv

load_dotenv()


def init_database():
    """Инициализация базы данных"""
    config = DatabaseConfig.from_env()

    db_manager = DatabaseManager({
        'host': config.host,
        'port': config.port,
        'database': config.database,
        'user': config.user,
        'password': config.password
    })

    if db_manager.connect():
        print("✓ База данных успешно инициализирована")
        stats = db_manager.get_statistics()
        print(f"Текущая статистика: {stats}")
    else:
        print("✗ Ошибка инициализации базы данных")
        sys.exit(1)

    db_manager.close()


if __name__ == "__main__":
    init_database()