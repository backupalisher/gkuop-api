"""
API-роутер для управления пользователями и разграничения доступа
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from .models import (
    User, UserRole, Permission, UserPermission,
    DEFAULT_ROLE_PERMISSIONS
)
from .db_manager import AuthDBManager
from .middleware import (
    require_permission, require_role, require_any_permission,
    get_current_user, create_token
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_auth_db(request: Request) -> AuthDBManager:
    """Получение экземпляра AuthDBManager из состояния приложения"""
    auth_db: AuthDBManager = getattr(request.app.state, 'auth_db', None)
    if not auth_db:
        raise HTTPException(status_code=503, detail="Модуль аутентификации не инициализирован")
    return auth_db


# ─── Аутентификация ─────────────────────────────────────────────

@router.post("/login-new")
@router.post("/login")
async def api_login_new(request: Request):
    """
    Аутентификация пользователя через модуль управления пользователями.
    Возвращает username, роль, список разрешений и токен доступа.
    """
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"status": "error", "message": "Неверный формат JSON"}, status_code=400)

    username = body.get("username", "") or body.get("login", "")
    username = username.strip()
    password = body.get("password", "").strip()

    if not username or not password:
        return JSONResponse(
            {"status": "error", "message": "Логин и пароль обязательны"},
            status_code=400
        )

    auth_db = get_auth_db(request)
    user = auth_db.authenticate(username, password)

    if not user:
        return JSONResponse(
            {"status": "error", "message": "Неверный логин или пароль"},
            status_code=401
        )

    # Получаем разрешения пользователя
    permissions = auth_db.get_user_permissions(username)

    # Получаем список доступных офисов (для операторов — только назначенные, для админов — все)
    if user.role == UserRole.ADMIN:
        offices = auth_db.get_all_offices_from_tickets()
    else:
        offices = auth_db.get_user_offices(username)

    # Создаём токен доступа
    token = create_token(username)

    return {
        "status": "ok",
        "token": token,
        "user": user.to_dict(),
        "permissions": permissions,
        "offices": offices,
    }


@router.get("/me")
async def api_get_current_user(request: Request):
    """Получение информации о текущем аутентифицированном пользователе"""
    auth_db = get_auth_db(request)
    user = get_current_user(request)

    if not user:
        return JSONResponse(
            {"error": "Не аутентифицирован"},
            status_code=401
        )

    permissions = auth_db.get_user_permissions(user.username)
    return {
        "user": user.to_dict(),
        "permissions": permissions,
    }


@router.get("/permissions/catalog")
async def api_get_permissions_catalog(request: Request):
    """Получение полного каталога всех доступных разрешений"""
    auth_db = get_auth_db(request)
    catalog = auth_db.get_all_permissions_catalog()
    return {"permissions": catalog}


# ─── Управление пользователями (требуют MANAGE_USERS) ───────────

@router.get("/users")
async def api_get_users(request: Request):
    """Получение списка всех пользователей"""
    auth_db = get_auth_db(request)
    user = get_current_user(request)

    if not user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Проверка прав: ADMIN или MANAGE_USERS или VIEW_USERS
    if user.role != UserRole.ADMIN:
        has_view = auth_db.check_permission(user.username, Permission.VIEW_USERS)
        has_manage = auth_db.check_permission(user.username, Permission.MANAGE_USERS)
        if not has_view and not has_manage:
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    users = auth_db.get_all_users()
    return {"users": users, "count": len(users)}


@router.get("/users/{username}")
async def api_get_user(username: str, request: Request):
    """Получение информации о конкретном пользователе"""
    auth_db = get_auth_db(request)
    user = get_current_user(request)

    if not user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Проверка прав
    if user.role != UserRole.ADMIN and user.username != username:
        has_view = auth_db.check_permission(user.username, Permission.VIEW_USERS)
        has_manage = auth_db.check_permission(user.username, Permission.MANAGE_USERS)
        if not has_view and not has_manage:
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    permissions = auth_db.get_user_permissions_detailed(username)

    return {
        "user": target_user.to_dict(),
        "permissions": permissions,
    }


@router.post("/users")
async def api_create_user(request: Request):
    """Создание нового пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_USERS
    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_USERS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    role_str = body.get("role", "operator").strip()
    full_name = body.get("full_name", "").strip() or None
    email = body.get("email", "").strip() or None

    # Валидация
    if not username or not password:
        return JSONResponse({"error": "Логин и пароль обязательны"}, status_code=400)

    if len(username) < 3:
        return JSONResponse({"error": "Логин должен содержать минимум 3 символа"}, status_code=400)

    if len(password) < 4:
        return JSONResponse({"error": "Пароль должен содержать минимум 4 символа"}, status_code=400)

    try:
        role = UserRole(role_str)
    except ValueError:
        return JSONResponse(
            {"error": f"Недопустимая роль. Допустимые: {[r.value for r in UserRole]}"},
            status_code=400
        )

    # Проверка на дубликат
    existing = auth_db.get_user(username)
    if existing:
        return JSONResponse({"error": "Пользователь с таким логином уже существует"}, status_code=409)

    user = auth_db.create_user(
        username=username,
        password=password,
        role=role,
        full_name=full_name,
        email=email,
    )

    if not user:
        return JSONResponse({"error": "Не удалось создать пользователя"}, status_code=500)

    permissions = auth_db.get_user_permissions(username)

    return {
        "status": "ok",
        "message": f"Пользователь {username} создан",
        "user": user.to_dict(),
        "permissions": permissions,
    }


@router.put("/users/{username}")
async def api_update_user(username: str, request: Request):
    """Обновление данных пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_USERS
    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_USERS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    updates = {}

    if "full_name" in body:
        updates["full_name"] = body["full_name"].strip() or None
    if "email" in body:
        updates["email"] = body["email"].strip() or None
    if "role" in body:
        try:
            role = UserRole(body["role"].strip())
            updates["role"] = role.value
        except ValueError:
            return JSONResponse(
                {"error": f"Недопустимая роль. Допустимые: {[r.value for r in UserRole]}"},
                status_code=400
            )
    if "is_active" in body:
        # Защита от деактивации последнего администратора
        if not body["is_active"] and target_user.role == UserRole.ADMIN:
            if auth_db._is_last_admin(username):
                return JSONResponse(
                    {"error": "Нельзя деактивировать последнего администратора"},
                    status_code=400
                )
        updates["is_active"] = bool(body["is_active"])

    if "password" in body and body["password"].strip():
        if len(body["password"].strip()) < 4:
            return JSONResponse({"error": "Пароль должен содержать минимум 4 символа"}, status_code=400)
        auth_db.update_password(username, body["password"].strip())

    if not updates:
        return {"status": "ok", "message": "Нет изменений"}

    if auth_db.update_user(username, updates):
        updated_user = auth_db.get_user(username)
        return {
            "status": "ok",
            "message": f"Пользователь {username} обновлён",
            "user": updated_user.to_dict() if updated_user else None,
        }

    return JSONResponse({"error": "Не удалось обновить пользователя"}, status_code=500)


@router.delete("/users/{username}")
async def api_delete_user(username: str, request: Request):
    """Удаление пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_USERS
    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_USERS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    # Защита от самоудаления
    if current_user.username == username:
        return JSONResponse(
            {"error": "Нельзя удалить самого себя"},
            status_code=400
        )

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    if auth_db.delete_user(username):
        return {
            "status": "ok",
            "message": f"Пользователь {username} удалён",
        }

    return JSONResponse(
        {"error": "Не удалось удалить пользователя. Возможно, это последний администратор."},
        status_code=400
    )


# ─── Управление разрешениями (требуют MANAGE_PERMISSIONS) ───────

@router.get("/users/{username}/permissions")
async def api_get_user_permissions(username: str, request: Request):
    """Получение разрешений пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Проверка прав
    if current_user.role != UserRole.ADMIN:
        has_manage = auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS)
        has_view = auth_db.check_permission(current_user.username, Permission.VIEW_USERS)
        if not has_manage and not has_view and current_user.username != username:
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    permissions = auth_db.get_user_permissions_detailed(username)
    catalog = auth_db.get_all_permissions_catalog()

    return {
        "user": target_user.to_dict(),
        "permissions": permissions,
        "catalog": catalog,
    }


@router.put("/users/{username}/permissions")
async def api_update_user_permissions(username: str, request: Request):
    """Массовое обновление разрешений пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_PERMISSIONS
    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    permissions = body.get("permissions", {})
    if not isinstance(permissions, dict):
        return JSONResponse({"error": "Поле permissions должно быть объектом {code: bool}"}, status_code=400)

    # Проверяем, что все коды разрешений существуют в каталоге
    catalog = auth_db.get_all_permissions_catalog()
    valid_codes = {p['code'] for p in catalog}
    invalid_codes = [code for code in permissions if code not in valid_codes]
    if invalid_codes:
        return JSONResponse(
            {"error": f"Неизвестные коды разрешений: {', '.join(invalid_codes)}"},
            status_code=400
        )

    if auth_db.set_user_permissions_bulk(username, permissions):
        updated_permissions = auth_db.get_user_permissions_detailed(username)
        return {
            "status": "ok",
            "message": f"Разрешения для {username} обновлены",
            "permissions": updated_permissions,
        }

    return JSONResponse({"error": "Не удалось обновить разрешения"}, status_code=500)


@router.post("/users/{username}/permissions/reset")
async def api_reset_user_permissions(username: str, request: Request):
    """Сброс разрешений пользователя до базовых по его роли"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    if auth_db.reset_user_permissions_to_role(username):
        permissions = auth_db.get_user_permissions_detailed(username)
        return {
            "status": "ok",
            "message": f"Разрешения для {username} сброшены до базовых по роли {target_user.role.value}",
            "permissions": permissions,
        }

    return JSONResponse({"error": "Не удалось сбросить разрешения"}, status_code=500)


@router.put("/users/{username}/permissions/{permission_code}")
async def api_set_user_permission(
    username: str, permission_code: str, request: Request
):
    """Установка конкретного разрешения для пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    granted = body.get("granted", True)

    # Проверяем, что код разрешения существует
    catalog = auth_db.get_all_permissions_catalog()
    valid_codes = {p['code'] for p in catalog}
    if permission_code not in valid_codes:
        return JSONResponse({"error": f"Неизвестный код разрешения: {permission_code}"}, status_code=400)

    if auth_db.set_user_permission(username, permission_code, granted):
        return {
            "status": "ok",
            "message": f"Разрешение {permission_code} {'установлено' if granted else 'отозвано'} для {username}",
        }

    return JSONResponse({"error": "Не удалось обновить разрешение"}, status_code=500)


# ─── Проверка прав для фронтенда ────────────────────────────────

@router.post("/check-permissions")
async def api_check_permissions(request: Request):
    """
    Проверка наличия указанных разрешений у текущего пользователя.
    Используется фронтендом для динамического управления UI.

    Тело запроса: { "permissions": ["view_tickets", "edit_tickets", ...] }
    Ответ: { "results": {"view_tickets": true, "edit_tickets": false, ...} }
    """
    auth_db = get_auth_db(request)
    user = get_current_user(request)

    if not user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    perm_codes = body.get("permissions", [])
    if not isinstance(perm_codes, list):
        return JSONResponse({"error": "Поле permissions должно быть массивом"}, status_code=400)

    # Администратор имеет все права
    if user.role == UserRole.ADMIN:
        return {"results": {code: True for code in perm_codes}}

    user_perms = set(auth_db.get_user_permissions(user.username))
    results = {code: code in user_perms for code in perm_codes}

    return {"results": results}


# ─── Управление правами на офисы (требуют MANAGE_PERMISSIONS) ──

@router.get("/offices/catalog")
async def api_get_offices_catalog(request: Request):
    """Получение справочника всех офисов из заявок"""
    auth_db = get_auth_db(request)
    user = get_current_user(request)

    if not user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_PERMISSIONS
    if user.role != UserRole.ADMIN:
        if not auth_db.check_permission(user.username, Permission.MANAGE_PERMISSIONS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    offices = auth_db.get_all_offices_from_tickets()
    return {"offices": offices, "count": len(offices)}


@router.get("/users/{username}/offices")
async def api_get_user_offices(username: str, request: Request):
    """Получение списка офисов, доступных пользователю"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Проверка прав: ADMIN или MANAGE_PERMISSIONS
    if current_user.role != UserRole.ADMIN:
        has_manage = auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS)
        if not has_manage and current_user.username != username:
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    result = auth_db.get_offices_for_user(username)
    return result


@router.put("/users/{username}/offices")
async def api_set_user_offices(username: str, request: Request):
    """Установка списка офисов для пользователя"""
    auth_db = get_auth_db(request)
    current_user = get_current_user(request)

    if not current_user:
        return JSONResponse({"error": "Не аутентифицирован"}, status_code=401)

    # Только ADMIN или MANAGE_PERMISSIONS
    if current_user.role != UserRole.ADMIN:
        if not auth_db.check_permission(current_user.username, Permission.MANAGE_PERMISSIONS):
            return JSONResponse({"error": "Недостаточно прав"}, status_code=403)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

    target_user = auth_db.get_user(username)
    if not target_user:
        return JSONResponse({"error": "Пользователь не найден"}, status_code=404)

    offices = body.get("offices", [])
    if not isinstance(offices, list):
        return JSONResponse({"error": "Поле offices должно быть массивом строк"}, status_code=400)

    if auth_db.set_user_offices(username, offices):
        result = auth_db.get_offices_for_user(username)
        return {
            "status": "ok",
            "message": f"Права на офисы для {username} обновлены",
            "data": result,
        }

    return JSONResponse({"error": "Не удалось обновить права на офисы"}, status_code=500)
