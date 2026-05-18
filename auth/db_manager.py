"""
Менеджер базы данных для модуля аутентификации и авторизации
"""
import hashlib
import secrets
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from psycopg2.sql import SQL, Identifier

from .models import (
    User, UserRole, Permission, UserPermission, UserOfficePermission,
    DEFAULT_ROLE_PERMISSIONS
)

logger = logging.getLogger(__name__)


class AuthDBManager:
    """Управление таблицами users, permissions, user_permissions"""

    # SQL для создания таблиц
    CREATE_TABLES_SQL = [
        # Таблица пользователей
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(256) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'operator',
            full_name VARCHAR(200),
            email VARCHAR(200),
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
        """,
        # Таблица разрешений (справочник)
        """
        CREATE TABLE IF NOT EXISTS permissions (
            id SERIAL PRIMARY KEY,
            code VARCHAR(100) UNIQUE NOT NULL,
            name VARCHAR(200) NOT NULL,
            description TEXT,
            category VARCHAR(50)
        )
        """,
        # Таблица связей пользователь-разрешение
        """
        CREATE TABLE IF NOT EXISTS user_permissions (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            permission_code VARCHAR(100) NOT NULL REFERENCES permissions(code) ON DELETE CASCADE,
            granted BOOLEAN DEFAULT TRUE,
            UNIQUE(username, permission_code)
        )
        """,
        # Индексы
        """
        CREATE INDEX IF NOT EXISTS idx_user_permissions_username ON user_permissions(username);
        CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
        CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
        """,
        # Таблица прав доступа к офисам
        """
        CREATE TABLE IF NOT EXISTS user_office_permissions (
            id SERIAL PRIMARY KEY,
            username VARCHAR(100) NOT NULL REFERENCES users(username) ON DELETE CASCADE,
            office_address TEXT NOT NULL,
            UNIQUE(username, office_address)
        )
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_uop_username ON user_office_permissions(username);
        CREATE INDEX IF NOT EXISTS idx_uop_office ON user_office_permissions(office_address);
        """,
    ]

    # SQL для заполнения справочника разрешений
    SEED_PERMISSIONS_SQL = """
        INSERT INTO permissions (code, name, description, category)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (code) DO NOTHING
    """

    PERMISSION_SEEDS = [
        (Permission.VIEW_TICKETS.value, 'Просмотр заявок', 'Просмотр списка заявок', 'tickets'),
        (Permission.VIEW_TICKET_DETAIL.value, 'Просмотр деталей заявки', 'Просмотр полной информации о заявке', 'tickets'),
        (Permission.CREATE_TICKETS.value, 'Создание заявок', 'Создание новых заявок', 'tickets'),
        (Permission.EDIT_TICKETS.value, 'Редактирование заявок', 'Редактирование существующих заявок', 'tickets'),
        (Permission.DELETE_TICKETS.value, 'Удаление заявок', 'Удаление заявок из системы', 'tickets'),
        (Permission.ARCHIVE_TICKETS.value, 'Архивирование', 'Архивирование и восстановление заявок', 'tickets'),
        (Permission.COMPLETE_TICKETS.value, 'Отметка выполнения', 'Отметка заявки как выполненной', 'tickets'),
        (Permission.ASSIGN_TASKS.value, 'Назначение задач', 'Назначение задач исполнителям', 'tasks'),
        (Permission.MANAGE_TASKS.value, 'Управление задачами', 'Добавление/удаление задач', 'tasks'),
        (Permission.UPLOAD_IMAGES.value, 'Загрузка изображений', 'Загрузка изображений к заявкам', 'images'),
        (Permission.DELETE_IMAGES.value, 'Удаление изображений', 'Удаление изображений из системы', 'images'),
        (Permission.MANAGE_USERS.value, 'Управление пользователями', 'Создание, редактирование, удаление пользователей', 'users'),
        (Permission.MANAGE_PERMISSIONS.value, 'Управление правами', 'Настройка прав доступа пользователей', 'users'),
        (Permission.VIEW_USERS.value, 'Просмотр пользователей', 'Просмотр списка пользователей системы', 'users'),
        (Permission.ACCESS_SETTINGS.value, 'Настройки системы', 'Доступ к системным настройкам', 'system'),
        (Permission.VIEW_LOGS.value, 'Просмотр логов', 'Просмотр системных логов', 'system'),
        (Permission.REBUILD_DATA.value, 'Перестроение данных', 'Перестроение базы данных из писем', 'system'),
        (Permission.EXPORT_DATA.value, 'Экспорт данных', 'Экспорт данных из системы', 'system'),
    ]

    def __init__(self, db_manager):
        """
        Args:
            db_manager: Экземпляр DatabaseManager из database/db_manager.py
        """
        self.db = db_manager
        self._current_user: Optional[User] = None

    # ─── Инициализация таблиц ────────────────────────────────────

    def create_tables(self):
        """Создание таблиц модуля аутентификации"""
        old_autocommit = self.db.connection.autocommit
        try:
            self.db.connection.set_session(autocommit=True)
            for query in self.CREATE_TABLES_SQL:
                self.db.cursor.execute(query)
            # Заполняем справочник разрешений
            for perm_data in self.PERMISSION_SEEDS:
                self.db.cursor.execute(self.SEED_PERMISSIONS_SQL, perm_data)
            self.db.connection.commit()
            logger.info("✓ Таблицы аутентификации созданы/проверены")
        except Exception as e:
            logger.error(f"✗ Ошибка создания таблиц аутентификации: {e}")
            self.db.connection.rollback()
        finally:
            try:
                self.db.connection.set_session(autocommit=old_autocommit)
            except Exception:
                pass

    # ─── Хеширование паролей ─────────────────────────────────────

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хеширование пароля с использованием scrypt и случайной соли.
        Формат: $scrypt$<salt>$<hash>
        """
        salt = secrets.token_hex(16)
        key = hashlib.scrypt(
            password.encode(),
            salt=salt.encode(),
            n=16384, r=8, p=1,
            dklen=32
        )
        return f"$scrypt${salt}${key.hex()}"

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """
        Проверка пароля против хеша, созданного hash_password().
        Поддерживает как новый формат ($scrypt$...), так и старый (SHA-256 без соли).
        """
        if password_hash.startswith('$scrypt$'):
            parts = password_hash.split('$')
            if len(parts) != 4:
                return False
            _, _, salt, stored_hash = parts
            key = hashlib.scrypt(
                password.encode(),
                salt=salt.encode(),
                n=16384, r=8, p=1,
                dklen=32
            )
            return key.hex() == stored_hash
        else:
            # Старый формат (SHA-256 без соли) — для обратной совместимости
            return hashlib.sha256(password.encode()).hexdigest() == password_hash

    # ─── CRUD пользователей ──────────────────────────────────────

    def create_user(self, username: str, password: str, role: UserRole,
                    full_name: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        """Создание нового пользователя с базовым набором прав по роли"""
        try:
            password_hash = self.hash_password(password)
            self.db.cursor.execute(
                """INSERT INTO users (username, password_hash, role, full_name, email)
                   VALUES (%s, %s, %s, %s, %s)
                   RETURNING id, created_at""",
                (username, password_hash, role.value, full_name, email)
            )
            result = self.db.cursor.fetchone()
            self.db.connection.commit()

            # Назначаем базовые разрешения по роли
            self._assign_default_permissions(username, role)

            user = User(
                id=result['id'],
                username=username,
                password_hash=password_hash,
                role=role,
                full_name=full_name,
                email=email,
                is_active=True,
                created_at=result['created_at'],
            )
            logger.info(f"✓ Создан пользователь {username} с ролью {role.value}")
            return user
        except Exception as e:
            logger.error(f"✗ Ошибка создания пользователя {username}: {e}")
            self.db.connection.rollback()
            # Автоматическое восстановление sequence при duplicate key
            if 'duplicate key' in str(e).lower() and 'users_pkey' in str(e):
                try:
                    self.db.cursor.execute(
                        "SELECT setval('users_id_seq', "
                        "COALESCE((SELECT MAX(id) FROM users), 0) + 1, false)"
                    )
                    self.db.connection.commit()
                    logger.info("Sequence users_id_seq восстановлен после duplicate key")
                except Exception as seq_err:
                    logger.error(f"Не удалось восстановить sequence users: {seq_err}")
                    try:
                        self.db.connection.rollback()
                    except Exception:
                        pass
            return None

    def get_user(self, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        self.db.cursor.execute(
            "SELECT * FROM users WHERE username = %s",
            (username,)
        )
        row = self.db.cursor.fetchone()
        if row:
            return self._row_to_user(row)
        return None

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        self.db.cursor.execute(
            "SELECT * FROM users WHERE id = %s",
            (user_id,)
        )
        row = self.db.cursor.fetchone()
        if row:
            return self._row_to_user(row)
        return None

    def get_all_users(self, include_inactive: bool = False) -> List[Dict]:
        """Получение списка всех пользователей (без паролей)"""
        query = "SELECT * FROM users"
        if not include_inactive:
            query += " WHERE is_active = TRUE"
        query += " ORDER BY created_at DESC"

        self.db.cursor.execute(query)
        rows = self.db.cursor.fetchall()
        return [self._row_to_user(r).to_dict() for r in rows]

    def update_user(self, username: str, updates: Dict) -> bool:
        """Обновление данных пользователя"""
        try:
            allowed_fields = {'full_name', 'email', 'role', 'is_active'}
            filtered = {k: v for k, v in updates.items() if k in allowed_fields}

            if not filtered:
                return True

            # Если обновляем роль — переназначаем базовые разрешения
            role_changed = 'role' in filtered

            # Если role передана как строка — конвертируем
            if 'role' in filtered and isinstance(filtered['role'], str):
                filtered['role'] = UserRole(filtered['role']).value

            set_parts = []
            values = []
            for key, value in filtered.items():
                set_parts.append(SQL("{} = %s").format(Identifier(key)))
                values.append(value)

            set_parts.append(SQL("updated_at = CURRENT_TIMESTAMP"))
            values.append(username)

            query = SQL("UPDATE users SET {} WHERE username = %s").format(SQL(", ").join(set_parts))
            self.db.cursor.execute(query, values)
            self.db.connection.commit()

            # Если роль изменилась — переназначаем базовые разрешения
            if role_changed:
                new_role = UserRole(filtered['role']) if isinstance(filtered['role'], str) else filtered['role']
                self._assign_default_permissions(username, new_role)

            logger.info(f"✓ Обновлён пользователь {username}")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка обновления пользователя {username}: {e}")
            self.db.connection.rollback()
            return False

    def update_password(self, username: str, new_password: str) -> bool:
        """Обновление пароля пользователя"""
        try:
            password_hash = self.hash_password(new_password)
            self.db.cursor.execute(
                "UPDATE users SET password_hash = %s, updated_at = CURRENT_TIMESTAMP WHERE username = %s",
                (password_hash, username)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка обновления пароля {username}: {e}")
            self.db.connection.rollback()
            return False

    def delete_user(self, username: str) -> bool:
        """Удаление пользователя с каскадным очищением связанных прав.
        Защита от самоудаления последнего администратора."""
        try:
            # Проверка: не является ли пользователь последним администратором
            if self._is_last_admin(username):
                logger.warning(f"✗ Невозможно удалить последнего администратора {username}")
                return False

            # Каскадное удаление: user_permissions удалится автоматически (ON DELETE CASCADE)
            self.db.cursor.execute(
                "DELETE FROM users WHERE username = %s",
                (username,)
            )
            self.db.connection.commit()
            logger.info(f"✓ Удалён пользователь {username}")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка удаления пользователя {username}: {e}")
            self.db.connection.rollback()
            return False

    def authenticate(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя"""
        user = self.get_user(username)
        if not user:
            return None
        if not user.is_active:
            return None

        if not self.verify_password(password, user.password_hash):
            return None

        # Обновляем last_login
        try:
            self.db.cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = %s",
                (username,)
            )
            self.db.connection.commit()
        except Exception:
            pass

        self._current_user = user
        return user

    # ─── Управление разрешениями ─────────────────────────────────

    def _assign_default_permissions(self, username: str, role: UserRole):
        """Назначение базовых разрешений по роли"""
        default_perms = DEFAULT_ROLE_PERMISSIONS.get(role, [])
        try:
            # Удаляем старые разрешения для пользователя
            self.db.cursor.execute(
                "DELETE FROM user_permissions WHERE username = %s",
                (username,)
            )
            # Назначаем новые
            for perm in default_perms:
                self.db.cursor.execute(
                    """INSERT INTO user_permissions (username, permission_code, granted)
                       VALUES (%s, %s, TRUE)
                       ON CONFLICT (username, permission_code) DO UPDATE SET granted = TRUE""",
                    (username, perm.value)
                )
            self.db.connection.commit()
        except Exception as e:
            logger.error(f"✗ Ошибка назначения разрешений для {username}: {e}")
            self.db.connection.rollback()
            # Автоматическое восстановление sequence при duplicate key
            if 'duplicate key' in str(e).lower() and 'user_permissions_pkey' in str(e):
                try:
                    self.db.cursor.execute(
                        "SELECT setval('user_permissions_id_seq', "
                        "COALESCE((SELECT MAX(id) FROM user_permissions), 0) + 1, false)"
                    )
                    self.db.connection.commit()
                    logger.info("Sequence user_permissions_id_seq восстановлен после duplicate key")
                except Exception as seq_err:
                    logger.error(f"Не удалось восстановить sequence user_permissions: {seq_err}")
                    try:
                        self.db.connection.rollback()
                    except Exception:
                        pass

    def get_user_permissions(self, username: str) -> List[str]:
        """Получение списка разрешений пользователя (коды)"""
        self.db.cursor.execute(
            """SELECT permission_code FROM user_permissions
               WHERE username = %s AND granted = TRUE""",
            (username,)
        )
        rows = self.db.cursor.fetchall()
        return [row['permission_code'] for row in rows]

    def get_user_permissions_detailed(self, username: str) -> List[Dict]:
        """Получение детального списка разрешений пользователя"""
        self.db.cursor.execute(
            """SELECT up.permission_code, up.granted,
                      p.name, p.description, p.category
               FROM user_permissions up
               JOIN permissions p ON up.permission_code = p.code
               WHERE up.username = %s
               ORDER BY p.category, p.name""",
            (username,)
        )
        rows = self.db.cursor.fetchall()
        return [dict(r) for r in rows]

    def get_all_permissions_catalog(self) -> List[Dict]:
        """Получение полного каталога разрешений"""
        self.db.cursor.execute(
            "SELECT * FROM permissions ORDER BY category, name"
        )
        rows = self.db.cursor.fetchall()
        return [dict(r) for r in rows]

    def set_user_permission(self, username: str, permission_code: str, granted: bool) -> bool:
        """Установка конкретного разрешения для пользователя"""
        try:
            self.db.cursor.execute(
                """INSERT INTO user_permissions (username, permission_code, granted)
                   VALUES (%s, %s, %s)
                   ON CONFLICT (username, permission_code)
                   DO UPDATE SET granted = %s""",
                (username, permission_code, granted, granted)
            )
            self.db.connection.commit()
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка установки разрешения {permission_code} для {username}: {e}")
            self.db.connection.rollback()
            # Автоматическое восстановление sequence при duplicate key
            if 'duplicate key' in str(e).lower() and 'user_permissions_pkey' in str(e):
                try:
                    self.db.cursor.execute(
                        "SELECT setval('user_permissions_id_seq', "
                        "COALESCE((SELECT MAX(id) FROM user_permissions), 0) + 1, false)"
                    )
                    self.db.connection.commit()
                    logger.info("Sequence user_permissions_id_seq восстановлен после duplicate key")
                except Exception as seq_err:
                    logger.error(f"Не удалось восстановить sequence user_permissions: {seq_err}")
                    try:
                        self.db.connection.rollback()
                    except Exception:
                        pass
            return False

    def set_user_permissions_bulk(self, username: str, permissions: Dict[str, bool]) -> bool:
        """Массовое обновление разрешений пользователя.
        Args:
            username: имя пользователя
            permissions: словарь {permission_code: granted}
        """
        try:
            for code, granted in permissions.items():
                self.db.cursor.execute(
                    """INSERT INTO user_permissions (username, permission_code, granted)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (username, permission_code)
                       DO UPDATE SET granted = %s""",
                    (username, code, granted, granted)
                )
            self.db.connection.commit()
            logger.info(f"✓ Обновлены разрешения для {username}: {len(permissions)} прав")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка массового обновления разрешений для {username}: {e}")
            self.db.connection.rollback()
            # Автоматическое восстановление sequence при duplicate key
            if 'duplicate key' in str(e).lower() and 'user_permissions_pkey' in str(e):
                try:
                    self.db.cursor.execute(
                        "SELECT setval('user_permissions_id_seq', "
                        "COALESCE((SELECT MAX(id) FROM user_permissions), 0) + 1, false)"
                    )
                    self.db.connection.commit()
                    logger.info("Sequence user_permissions_id_seq восстановлен после duplicate key")
                except Exception as seq_err:
                    logger.error(f"Не удалось восстановить sequence user_permissions: {seq_err}")
                    try:
                        self.db.connection.rollback()
                    except Exception:
                        pass
            return False

    def reset_user_permissions_to_role(self, username: str) -> bool:
        """Сброс разрешений пользователя до базовых по его роли"""
        user = self.get_user(username)
        if not user:
            return False
        self._assign_default_permissions(username, user.role)
        return True

    # ─── Управление правами на офисы ─────────────────────────────

    def get_user_offices(self, username: str) -> List[str]:
        """Получение списка офисов, доступных пользователю для просмотра"""
        self.db.cursor.execute(
            "SELECT office_address FROM user_office_permissions "
            "WHERE username = %s ORDER BY office_address",
            (username,)
        )
        rows = self.db.cursor.fetchall()
        return [row['office_address'] for row in rows]

    def set_user_offices(self, username: str, offices: List[str]) -> bool:
        """Установка списка офисов для пользователя (заменяет текущий список).
        
        Args:
            username: имя пользователя
            offices: список адресов офисов, к которым предоставляется доступ
        
        Returns:
            True в случае успеха
        """
        try:
            # Удаляем старые записи
            self.db.cursor.execute(
                "DELETE FROM user_office_permissions WHERE username = %s",
                (username,)
            )
            # Вставляем новые
            for office in offices:
                office = office.strip()
                if office:
                    self.db.cursor.execute(
                        "INSERT INTO user_office_permissions (username, office_address) "
                        "VALUES (%s, %s) ON CONFLICT (username, office_address) DO NOTHING",
                        (username, office)
                    )
            self.db.connection.commit()
            logger.info(f"✓ Установлены права на офисы для {username}: {len(offices)} офисов")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка установки прав на офисы для {username}: {e}")
            self.db.connection.rollback()
            return False

    def add_user_office(self, username: str, office_address: str) -> bool:
        """Добавление одного офиса в список доступных пользователю"""
        try:
            self.db.cursor.execute(
                "INSERT INTO user_office_permissions (username, office_address) "
                "VALUES (%s, %s) ON CONFLICT (username, office_address) DO NOTHING",
                (username, office_address)
            )
            self.db.connection.commit()
            logger.info(f"✓ Добавлен офис '{office_address}' для {username}")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка добавления офиса '{office_address}' для {username}: {e}")
            self.db.connection.rollback()
            return False

    def remove_user_office(self, username: str, office_address: str) -> bool:
        """Удаление офиса из списка доступных пользователю"""
        try:
            self.db.cursor.execute(
                "DELETE FROM user_office_permissions "
                "WHERE username = %s AND office_address = %s",
                (username, office_address)
            )
            self.db.connection.commit()
            logger.info(f"✓ Удалён офис '{office_address}' для {username}")
            return True
        except Exception as e:
            logger.error(f"✗ Ошибка удаления офиса '{office_address}' для {username}: {e}")
            self.db.connection.rollback()
            return False

    def get_all_offices_from_tickets(self) -> List[str]:
        """Получение списка всех уникальных офисов из таблицы заявок"""
        self.db.cursor.execute(
            "SELECT DISTINCT office FROM tickets "
            "WHERE office IS NOT NULL AND office != '' "
            "ORDER BY office"
        )
        rows = self.db.cursor.fetchall()
        return [row['office'] for row in rows]

    def get_offices_for_user(self, username: str) -> Dict:
        """Получение информации о правах на офисы для пользователя.
        
        Returns:
            Dict с полями:
                - username: str
                - offices: List[str] — список доступных офисов
                - all_offices: List[str] — полный справочник офисов из заявок
        """
        user_offices = self.get_user_offices(username)
        all_offices = self.get_all_offices_from_tickets()
        return {
            "username": username,
            "offices": user_offices,
            "all_offices": all_offices,
        }

    # ─── Проверка прав ───────────────────────────────────────────

    def check_permission(self, username: str, permission: Permission) -> bool:
        """Проверка наличия конкретного разрешения у пользователя"""
        perms = self.get_user_permissions(username)
        return permission.value in perms

    def check_permissions(self, username: str, permissions: List[Permission]) -> Dict[str, bool]:
        """Проверка нескольких разрешений сразу"""
        user_perms = set(self.get_user_permissions(username))
        return {p.value: p.value in user_perms for p in permissions}

    def require_permission(self, username: str, permission: Permission) -> bool:
        """Строгая проверка разрешения (с логированием отказа)"""
        if not self.check_permission(username, permission):
            logger.warning(f"⛔ Доступ запрещён: {username} не имеет права {permission.value}")
            return False
        return True

    # ─── Вспомогательные методы ──────────────────────────────────

    def _is_last_admin(self, username: str) -> bool:
        """Проверка, является ли пользователь последним активным администратором"""
        self.db.cursor.execute(
            "SELECT COUNT(*) as cnt FROM users WHERE role = 'admin' AND is_active = TRUE"
        )
        result = self.db.cursor.fetchone()
        admin_count = result['cnt'] if result else 0

        # Проверяем, что удаляемый пользователь — администратор
        user = self.get_user(username)
        if user and user.role == UserRole.ADMIN and admin_count <= 1:
            return True
        return False

    @staticmethod
    def _row_to_user(row: Dict) -> User:
        """Преобразование строки БД в объект User"""
        return User(
            id=row['id'],
            username=row['username'],
            password_hash=row['password_hash'],
            role=UserRole(row['role']),
            full_name=row.get('full_name'),
            email=row.get('email'),
            is_active=row.get('is_active', True),
            created_at=row.get('created_at'),
            updated_at=row.get('updated_at'),
            last_login=row.get('last_login'),
        )

    def set_current_user(self, username: Optional[str]):
        """Установка текущего пользователя (для контекста запроса)"""
        if username:
            self._current_user = self.get_user(username)
        else:
            self._current_user = None

    def get_current_user(self) -> Optional[User]:
        """Получение текущего пользователя"""
        return self._current_user
