"""Справочник аппаратов. Изменение доступно только администратору."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from auth.middleware import get_current_user, require_role
from auth.models import UserRole
from services.equipment_catalog import (
    EquipmentConflictError,
    format_equipment_label,
    parse_equipment_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["equipment"])


def _db(request: Request):
    db = getattr(request.app.state, "db", None)
    if db is not None:
        return db
    from web_api import main as web_main
    return web_main.db


def _require_admin(request: Request) -> Optional[JSONResponse]:
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Требуется авторизация"}, status_code=401)
    if user.role != UserRole.ADMIN:
        return JSONResponse(
            {"error": "Только администратор может изменять справочник аппаратов"},
            status_code=403,
        )
    return None


def _serialize(row: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(row)
    for key in ("created_at", "updated_at"):
        value = data.get(key)
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    data["label"] = format_equipment_label(
        data.get("model"),
        data.get("serial_number"),
        data.get("inventory_number"),
    )
    return data


def _read_payload(body: Any) -> Dict[str, Optional[str]]:
    if not isinstance(body, dict):
        raise ValueError("Ожидается JSON с полями модели и номеров")
    return parse_equipment_payload(
        body.get("model"),
        body.get("serial_number"),
        body.get("inventory_number"),
    )


@router.get("/api/equipment")
@require_role("admin")
async def api_list_equipment(
    request: Request,
    search: Optional[str] = Query(None),
):
    """Список аппаратов с поиском по модели, серийному и инвентарному номеру."""
    db = _db(request)
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        rows = db.list_equipment(search)
        return {"equipment": [_serialize(row) for row in rows], "total": len(rows)}
    except Exception as exc:
        logger.exception("Ошибка списка аппаратов")
        return JSONResponse({"error": str(exc)}, status_code=500)


@router.post("/api/equipment")
@require_role("admin")
async def api_create_equipment(request: Request):
    """Добавляет аппарат. Пересечение серийного или инвентарного номера — 409."""
    denied = _require_admin(request)
    if denied:
        return denied
    db = _db(request)
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        payload = _read_payload(await request.json())
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    try:
        created = db.create_equipment(payload)
        linked = db.relink_all_tickets(touch_updated=True)
        return {"status": "ok", "equipment": _serialize(created), "relinked": linked}
    except EquipmentConflictError as exc:
        return JSONResponse({"error": exc.message}, status_code=409)
    except Exception as exc:
        logger.exception("Ошибка добавления аппарата")
        return JSONResponse({"error": str(exc)}, status_code=500)


@router.put("/api/equipment/{equipment_id}")
@require_role("admin")
async def api_update_equipment(equipment_id: int, request: Request):
    """Правит модель, серийный и инвентарный номер. Пересечение — 409."""
    denied = _require_admin(request)
    if denied:
        return denied
    db = _db(request)
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        payload = _read_payload(await request.json())
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=400)
    try:
        updated = db.update_equipment(equipment_id, payload)
        if updated is None:
            return JSONResponse({"error": "Аппарат не найден"}, status_code=404)
        linked = db.relink_all_tickets(touch_updated=True)
        return {"status": "ok", "equipment": _serialize(updated), "relinked": linked}
    except EquipmentConflictError as exc:
        return JSONResponse({"error": exc.message}, status_code=409)
    except Exception as exc:
        logger.exception("Ошибка правки аппарата")
        return JSONResponse({"error": str(exc)}, status_code=500)
