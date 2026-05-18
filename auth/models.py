"""
Модели данных для модуля аутентификации и авторизации
"""
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class UserRole(str, Enum):
    """Роли пользователей"""
    ADMIN = 'admin'
    OPERATOR = 'operator'


class Permission(str, Enum):
    """
    Перечень всех функциональных разрешений в системе.
    Каждое разрешение — это отдельный «флаг», который можно включить/отключить.
    """
    # ─── Управление заявками ─────────────────────────────────────
    VIEW_TICKETS = 'view_tickets'              # Просмотр списка заявок
    VIEW_TICKET_DETAIL = 'view_ticket_detail'  # Просмотр деталей заявки
    CREATE_TICKETS = 'create_tickets'          # Создание заявок
    EDIT_TICKETS = 'edit_tickets'              # Редактирование заявок
    DELETE_TICKETS = 'delete_tickets'          # Удаление заявок
    ARCHIVE_TICKETS = 'archive_tickets'        # Архивирование/восстановление заявок
    COMPLETE_TICKETS = 'complete_tickets'      # Отметка заявки как выполненной

    # ─── Управление задачами ─────────────────────────────────────
    ASSIGN_TASKS = 'assign_tasks'              # Назначение задач
    MANAGE_TASKS = 'manage_tasks'              # Управление задачами (добавление/удаление)

    # ─── Изображения ─────────────────────────────────────────────
    UPLOAD_IMAGES = 'upload_images'            # Загрузка изображений
    DELETE_IMAGES = 'delete_images'            # Удаление изображений

    # ─── Комментарии ────────────────────────────────────────────────
    ADD_COMMENTS = 'add_comments'              # Добавление комментариев к заявкам

    # ─── Управление пользователями ───────────────────────────────
    MANAGE_USERS = 'manage_users'              # Управление пользователями (CRUD)
    MANAGE_PERMISSIONS = 'manage_permissions'  # Управление правами доступа
    VIEW_USERS = 'view_users'                  # Просмотр списка пользователей

    # ─── Системные ───────────────────────────────────────────────
    ACCESS_SETTINGS = 'access_settings'        # Доступ к настройкам системы
    VIEW_LOGS = 'view_logs'                    # Просмотр логов
    REBUILD_DATA = 'rebuild_data'              # Перестроение данных (rebuild)
    EXPORT_DATA = 'export_data'                # Экспорт данных


# ─── Разрешения по умолчанию для каждой роли ─────────────────────

DEFAULT_ROLE_PERMISSIONS: Dict[UserRole, List[Permission]] = {
    UserRole.ADMIN: [
        Permission.VIEW_TICKETS,
        Permission.VIEW_TICKET_DETAIL,
        Permission.CREATE_TICKETS,
        Permission.EDIT_TICKETS,
        Permission.DELETE_TICKETS,
        Permission.ARCHIVE_TICKETS,
        Permission.COMPLETE_TICKETS,
        Permission.ASSIGN_TASKS,
        Permission.MANAGE_TASKS,
        Permission.UPLOAD_IMAGES,
        Permission.DELETE_IMAGES,
        Permission.ADD_COMMENTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_PERMISSIONS,
        Permission.VIEW_USERS,
        Permission.ACCESS_SETTINGS,
        Permission.VIEW_LOGS,
        Permission.REBUILD_DATA,
        Permission.EXPORT_DATA,
    ],
    UserRole.OPERATOR: [
        Permission.VIEW_TICKETS,
        Permission.VIEW_TICKET_DETAIL,
        Permission.CREATE_TICKETS,
        Permission.EDIT_TICKETS,
        Permission.COMPLETE_TICKETS,
        Permission.ASSIGN_TASKS,
        Permission.MANAGE_TASKS,
        Permission.UPLOAD_IMAGES,
        Permission.ADD_COMMENTS,
        Permission.VIEW_USERS,
    ],
}


@dataclass
class User:
    """Модель пользователя системы"""
    username: str
    password_hash: str
    role: UserRole
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> Dict:
        """Преобразование в словарь (без пароля)"""
        data = asdict(self)
        data.pop('password_hash', None)
        if isinstance(data.get('role'), UserRole):
            data['role'] = data['role'].value
        return data


@dataclass
class UserPermission:
    """Модель связи пользователя с разрешением"""
    username: str
    permission: Permission
    granted: bool = True  # True — разрешено, False — явно запрещено
    id: Optional[int] = None

    def to_dict(self) -> Dict:
        data = asdict(self)
        if isinstance(data.get('permission'), Permission):
            data['permission'] = data['permission'].value
        return data


@dataclass
class UserOfficePermission:
    """
    Модель связи пользователя с офисом.
    Определяет, заявки по каким офисам может просматривать пользователь.
    Если список пуст — пользователь не видит ни одной заявки (кроме администратора).
    """
    username: str
    office_address: str  # Полный адрес офиса (например, "2-й Южнопортовый пр-д, д. 27А, стр. 1")
    id: Optional[int] = None

    def to_dict(self) -> Dict:
        return asdict(self)
