"""
Middleware и декораторы для проверки прав доступа.

Аутентификация основана на signed токенах (HMAC-SHA256).
Токен передаётся в заголовке Authorization: Bearer <token>.
"""
import functools
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Callable, List, Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

from .models import Permission, User
from .db_manager import AuthDBManager

logger = logging.getLogger(__name__)


# ─── JWT-like токены (HMAC-SHA256, без внешних зависимостей) ─────

# Секретный ключ для подписи токенов.
# В production ОБЯЗАТЕЛЬНО должен задаваться через переменную окружения AUTH_SECRET_KEY.
# Если ключ не задан — генерируется случайный при первом запуске (только для разработки).
# При перезапуске сервера без AUTH_SECRET_KEY все существующие токены станут невалидными.
_SECRET_KEY = None
_SECRET_KEY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    '.auth_secret_key'
)


def _get_secret_key() -> str:
    """Получение секретного ключа для подписи токенов.

    Приоритет:
    1. Переменная окружения AUTH_SECRET_KEY
    2. Файл .auth_secret_key в корне проекта (если существует)
    3. Генерация случайного ключа (только для разработки)
    """
    global _SECRET_KEY
    if _SECRET_KEY is not None:
        return _SECRET_KEY

    # 1. Пробуем переменную окружения
    env_key = os.environ.get('AUTH_SECRET_KEY')
    if env_key:
        _SECRET_KEY = env_key
        logger.info("✓ AUTH_SECRET_KEY загружен из переменной окружения")
        return _SECRET_KEY

    # 2. Пробуем файл .auth_secret_key
    if os.path.isfile(_SECRET_KEY_FILE):
        try:
            with open(_SECRET_KEY_FILE, 'r') as f:
                file_key = f.read().strip()
            if file_key:
                _SECRET_KEY = file_key
                logger.info(f"✓ AUTH_SECRET_KEY загружен из {_SECRET_KEY_FILE}")
                return _SECRET_KEY
        except (OSError, IOError) as e:
            logger.warning(f"Не удалось прочитать {_SECRET_KEY_FILE}: {e}")

    # 3. Генерируем случайный ключ и сохраняем в файл
    import secrets
    _SECRET_KEY = secrets.token_hex(32)
    try:
        with open(_SECRET_KEY_FILE, 'w') as f:
            f.write(_SECRET_KEY)
        os.chmod(_SECRET_KEY_FILE, 0o600)  # Только владелец
        logger.warning(
            f"AUTH_SECRET_KEY не задан. Сгенерирован случайный ключ и сохранён в "
            f"{_SECRET_KEY_FILE}. Установите переменную окружения AUTH_SECRET_KEY "
            f"для production-развёртывания."
        )
    except (OSError, IOError) as e:
        logger.warning(
            f"AUTH_SECRET_KEY не задан. Сгенерирован случайный ключ, но не удалось "
            f"сохранить в файл: {e}. Все токены будут сброшены при следующем запуске!"
        )

    return _SECRET_KEY


def create_token(username: str, expires_in: int = 86400) -> str:
    """
    Создание signed токена для пользователя.

    Args:
        username: имя пользователя
        expires_in: время жизни токена в секундах (по умолчанию 24 часа)

    Returns:
        Токен в формате: base64(payload).signature
    """
    payload = {
        'username': username,
        'exp': int(time.time()) + expires_in,
        'iat': int(time.time()),
    }
    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64 = _base64url_encode(payload_json.encode())

    signature = _sign(payload_b64)
    return f"{payload_b64}.{signature}"


def verify_token(token: str) -> Optional[str]:
    """
    Проверка токена и извлечение username.

    Args:
        token: токен в формате payload.signature

    Returns:
        username если токен валиден, иначе None
    """
    try:
        parts = token.split('.')
        if len(parts) != 2:
            return None

        payload_b64, signature = parts

        # Проверяем подпись
        expected_sig = _sign(payload_b64)
        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Декодируем payload
        payload_json = _base64url_decode(payload_b64)
        payload = json.loads(payload_json)

        # Проверяем срок действия
        if payload.get('exp', 0) < time.time():
            return None

        return payload.get('username')
    except Exception as e:
        logger.debug(f"Ошибка проверки токена: {e}")
        return None


def _sign(data: str) -> str:
    """Подпись данных HMAC-SHA256."""
    key = _get_secret_key().encode()
    sig = hmac.new(key, data.encode(), hashlib.sha256).digest()
    return _base64url_encode(sig)


def _base64url_encode(data: bytes) -> str:
    """Base64url encoding без padding."""
    import base64
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode()


def _base64url_decode(data: str) -> bytes:
    """Base64url decoding с восстановлением padding."""
    import base64
    padding = 4 - len(data) % 4
    if padding != 4:
        data += '=' * padding
    return base64.urlsafe_b64decode(data)


# ─── Хранилище текущего пользователя в контексте запроса ────────

def get_current_user(request: Request) -> Optional[User]:
    """Получение текущего пользователя из request.state"""
    return getattr(request.state, 'current_user', None)


def set_current_user(request: Request, user: Optional[User]):
    """Установка текущего пользователя в request.state"""
    request.state.current_user = user


# ─── Middleware для FastAPI ──────────────────────────────────────

class AuthMiddleware:
    """
    Middleware для аутентификации через signed токены (Bearer).

    Токен извлекается из заголовка Authorization: Bearer <token>.
    Для публичных путей (login, static) аутентификация не требуется.

    Используется как dispatch-функция для BaseHTTPMiddleware:
        app.add_middleware(BaseHTTPMiddleware, dispatch=AuthMiddleware())
    """

    def __init__(self, auth_db: Optional[AuthDBManager] = None):
        self.auth_db = auth_db

    async def __call__(self, request: Request, call_next: Callable):
        # Пропускаем пути, не требующие аутентификации
        if self._is_public_path(request.url.path):
            return await call_next(request)

        # Получаем auth_db из состояния приложения, если не передан в конструктор
        auth_db = self.auth_db or getattr(request.app.state, 'auth_db', None)
        if not auth_db:
            logger.debug(f"[DEBUG AuthMiddleware] auth_db не найден, path={request.url.path}")
            set_current_user(request, None)
            return await call_next(request)

        # Извлекаем токен из заголовка Authorization
        auth_header = request.headers.get('Authorization', '')
        token = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        logger.debug(
            f"[DEBUG AuthMiddleware] path={request.url.path}, "
            f"auth_header_present={'yes' if auth_header else 'no'}, "
            f"token={'present' if token else 'missing'}"
        )

        if token:
            username = verify_token(token)
            logger.debug(
                f"[DEBUG AuthMiddleware] verify_token result: "
                f"username={username!r}"
            )
            if username:
                user = auth_db.get_user(username)
                logger.debug(
                    f"[DEBUG AuthMiddleware] get_user({username!r}): "
                    f"user={'found' if user else 'not_found'}, "
                    f"is_active={user.is_active if user else 'N/A'}"
                )
                if user and user.is_active:
                    set_current_user(request, user)
                    logger.debug(f"[DEBUG AuthMiddleware] Аутентификация успешна: {username}")
                    return await call_next(request)
                else:
                    logger.debug(f"[DEBUG AuthMiddleware] Пользователь неактивен или не найден: {username}")
            else:
                logger.debug(f"[DEBUG AuthMiddleware] Токен невалиден (verify_token вернул None)")

        # Если токен невалидный или отсутствует — пользователь не аутентифицирован
        logger.debug(f"[DEBUG AuthMiddleware] Пользователь НЕ аутентифицирован, path={request.url.path}")
        set_current_user(request, None)
        return await call_next(request)

    @staticmethod
    def _is_public_path(path: str) -> bool:
        """Проверка, является ли путь публичным (не требует аутентификации)"""
        public_paths = [
            '/api/auth/login',
            '/api/auth/login-new',  # новый логин для модуля пользователей
            '/static/',
            '/favicon.ico',
        ]
        for p in public_paths:
            if path.startswith(p):
                return True
        return False


# ─── Декораторы для проверки прав ───────────────────────────────

def require_permission(permission: Permission):
    """
    Декоратор для проверки наличия конкретного разрешения у пользователя.

    Использование:
        @router.get("/api/some-endpoint")
        @require_permission(Permission.VIEW_TICKETS)
        async def my_endpoint(request: Request):
            ...

    В случае отсутствия права возвращает 403 Forbidden.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']

            if not request:
                logger.error("require_permission: Request object not found in arguments")
                return JSONResponse(
                    {"error": "Внутренняя ошибка сервера"},
                    status_code=500
                )

            user = get_current_user(request)
            if not user:
                return JSONResponse(
                    {"message": "Недостаточно прав для выполнения операции"},
                    status_code=401
                )

            # Администратор имеет все права
            if user.role.value == 'admin':
                return await func(*args, **kwargs)

            # Проверяем конкретное разрешение
            auth_db: Optional[AuthDBManager] = getattr(request.app.state, 'auth_db', None)
            if auth_db and not auth_db.check_permission(user.username, permission):
                logger.warning(
                    f"⛔ Доступ запрещён: {user.username}" # -> {permission.value}"
                )
                return JSONResponse(
                    {"error": f"Недостаточно прав для выполнения операции"},
                    status_code=403
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Декоратор, требующий наличия ХОТЯ БЫ ОДНОГО из перечисленных разрешений.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']

            if not request:
                return JSONResponse({"error": "Внутренняя ошибка сервера"}, status_code=500)

            user = get_current_user(request)
            if not user:
                return JSONResponse({"message": "Недостаточно прав для выполнения операции"}, status_code=401)

            if user.role.value == 'admin':
                return await func(*args, **kwargs)

            auth_db: Optional[AuthDBManager] = getattr(request.app.state, 'auth_db', None)
            if auth_db:
                for perm in permissions:
                    if auth_db.check_permission(user.username, perm):
                        return await func(*args, **kwargs)

            logger.warning(
                f"⛔ Доступ запрещён: {user.username} -> требуется одно из {[p.value for p in permissions]}"
            )
            return JSONResponse(
                {"error": "Недостаточно прав для выполнения операции"},
                status_code=403
            )
        return wrapper
    return decorator


def require_role(role: str):
    """
    Декоратор для проверки роли пользователя.

    Использование:
        @router.get("/api/admin-only")
        @require_role("admin")
        async def admin_endpoint(request: Request):
            ...
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break
            if not request and 'request' in kwargs:
                request = kwargs['request']

            if not request:
                return JSONResponse({"error": "Внутренняя ошибка сервера"}, status_code=500)

            user = get_current_user(request)
            if not user:
                return JSONResponse({"message": "Недостаточно прав для выполнения операции"}, status_code=401)

            if user.role.value != role:
                logger.warning(
                    f"⛔ Доступ запрещён: {user.username} требует роль {role}"
                )
                return JSONResponse(
                    {"error": f"Требуется роль {role}"},
                    status_code=403
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator
