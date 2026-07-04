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

    admin_username = os.getenv('SEED_ADMIN_USERNAME', 'pamind4')
    admin_password = os.getenv('SEED_ADMIN_PASSWORD')
    admin_email = os.getenv('SEED_ADMIN_EMAIL', 'admin@gkuop.ru')
    if not admin_password:
        print("✗ Укажите SEED_ADMIN_PASSWORD в окружении перед запуском seed-скрипта")
        return

    # Проверяем, существует ли пользователь
    existing = auth_db.get_user(admin_username)
    if existing:
        print(f"⚠ Пользователь '{admin_username}' уже существует (id={existing.id})")
        return

    # Создаём пользователя с ролью admin
    from auth.models import UserRole
    user = auth_db.create_user(
        username=admin_username,
        password=admin_password,
        role=UserRole.ADMIN,
        full_name='Administrator',
        email=admin_email,
    )
    if not user:
        print("✗ Не удалось создать административного пользователя")
        return
    print(f"✓ Пользователь '{admin_username}' создан (id={user.id}, role={user.role})")
    print(f"✓ Разрешения для роли 'admin' назначены автоматически")


if __name__ == '__main__':
    seed_admin()
