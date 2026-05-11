"""
Seed-скрипт для создания административного пользователя pamind4
"""
import sys
import os

# Добавляем корень проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager
from auth.db_manager import AuthDBManager


def seed_admin():
    # Используем DatabaseConfig.from_env() для загрузки конфигурации
    from config.settings import DatabaseConfig
    db_cfg = DatabaseConfig.from_env()
    db_config = {
        'host': db_cfg.host,
        'port': db_cfg.port,
        'database': db_cfg.database,
        'user': db_cfg.user,
        'password': db_cfg.password,
    }
    db = DatabaseManager(db_config)
    if not db.connect():
        print("✗ Не удалось подключиться к БД")
        return
    auth_db = AuthDBManager(db)

    # Создаём таблицы аутентификации (если ещё не созданы)
    auth_db.create_tables()

    # Проверяем, существует ли пользователь
    existing = auth_db.get_user('pamind4')
    if existing:
        print(f"⚠ Пользователь 'pamind4' уже существует (id={existing.id})")
        return

    # Создаём пользователя с ролью admin
    from auth.models import UserRole
    user = auth_db.create_user(
        username='pamind4',
        password='pAdmin4pass',
        role=UserRole.ADMIN,
        full_name='Administrator',
        email='admin@gkuop.ru'
    )
    print(f"✓ Пользователь 'pamind4' создан (id={user.id}, role={user.role})")
    print(f"✓ Разрешения для роли 'admin' назначены автоматически")


if __name__ == '__main__':
    seed_admin()
