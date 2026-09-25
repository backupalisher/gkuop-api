"""
Incremental sync API для мобильного Offline-first клиента.

Обратная совместимость: только новые endpoints, существующие контракты не меняются.
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

from auth.middleware import require_permission, get_current_user
from auth.models import Permission, UserRole
from utils.helpers import abbreviate_office

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


def _parse_iso(value: Optional[str]) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=timezone.utc)
    raw = value.strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _encode_cursor(updated_at: datetime, entity: str, entity_id: str) -> str:
    payload = {
        "u": _to_iso(updated_at),
        "e": entity,
        "i": str(entity_id),
    }
    return base64.urlsafe_b64encode(json.dumps(payload, ensure_ascii=False).encode("utf-8")).decode("ascii")


def _decode_cursor(cursor: Optional[str]) -> Tuple[datetime, str, str]:
    if not cursor:
        return datetime(1970, 1, 1, tzinfo=timezone.utc), "", ""
    try:
        raw = json.loads(base64.urlsafe_b64decode(cursor.encode("ascii")).decode("utf-8"))
        return _parse_iso(raw.get("u")), str(raw.get("e") or ""), str(raw.get("i") or "")
    except Exception:
        return datetime(1970, 1, 1, tzinfo=timezone.utc), "", ""


def _serialize_ticket(row: Dict[str, Any]) -> Dict[str, Any]:
    data = dict(row)
    for key in ("first_received_date", "last_updated_date", "created_at", "completed_at"):
        if key in data:
            data[key] = _to_iso(data.get(key)) if data.get(key) else None
    if "office" in data:
        data["office_abbreviated"] = abbreviate_office(data.get("office"))
    return data


def _office_filter_sql(user, auth_db) -> Tuple[str, List[Any]]:
    if not user or user.role == UserRole.ADMIN:
        return "", []
    offices = auth_db.get_user_offices(user.username) if auth_db else []
    if not offices:
        return " AND 1=0", []
    placeholders = ", ".join(["%s"] * len(offices))
    return f" AND (t.office IN ({placeholders}) OR t.office IS NULL OR TRIM(t.office) = '')", list(offices)


@router.get("/changes")
@require_permission(Permission.VIEW_TICKETS)
async def api_sync_changes(
    request: Request,
    since: Optional[str] = Query(None, description="ISO-8601 UTC lower bound"),
    cursor: Optional[str] = Query(None, description="Opaque pagination cursor"),
    limit: int = Query(100, ge=1, le=200),
):
    """
    Incremental pull изменений для мобильного клиента.
    Учитывает office ACL оператора.
    """
    db = getattr(request.app.state, "db", None)
    if db is None:
        from web_api import main as web_main
        db = web_main.db
    auth_db = getattr(request.app.state, "auth_db", None)
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    user = get_current_user(request)
    since_dt = _parse_iso(since)
    cursor_dt, cursor_entity, cursor_id = _decode_cursor(cursor)
    # Effective lower bound: max(since, cursor time)
    lower = max(since_dt, cursor_dt)

    office_sql, office_params = _office_filter_sql(user, auth_db)
    changes: List[Dict[str, Any]] = []

    try:
        with db._lock:
            # Tickets
            db.cursor.execute(
                f"""
                SELECT t.*
                FROM tickets t
                WHERE COALESCE(t.last_updated_date, t.first_received_date, t.created_at) > %s
                {office_sql}
                ORDER BY COALESCE(t.last_updated_date, t.first_received_date, t.created_at) ASC,
                         t.ticket_number ASC
                LIMIT %s
                """,
                [lower] + office_params + [limit],
            )
            for row in db.cursor.fetchall():
                ticket = dict(row)
                updated = ticket.get("last_updated_date") or ticket.get("first_received_date") or ticket.get("created_at")
                changes.append({
                    "entity": "ticket",
                    "id": ticket["ticket_number"],
                    "operation": "upsert",
                    "updated_at": _to_iso(updated),
                    "data": _serialize_ticket(ticket),
                })

            # User comments (join tickets for ACL)
            db.cursor.execute(
                f"""
                SELECT uc.*
                FROM user_comments uc
                JOIN tickets t ON t.ticket_number = uc.ticket_number
                WHERE uc.created_at > %s
                {office_sql}
                ORDER BY uc.created_at ASC, uc.id ASC
                LIMIT %s
                """,
                [lower] + office_params + [limit],
            )
            for row in db.cursor.fetchall():
                comment = dict(row)
                changes.append({
                    "entity": "user_comment",
                    "id": str(comment["id"]),
                    "operation": "upsert",
                    "updated_at": _to_iso(comment.get("created_at")),
                    "data": {
                        "id": comment["id"],
                        "ticket_number": comment["ticket_number"],
                        "author_username": comment.get("author_username"),
                        "author_name": comment.get("author_name"),
                        "comment_text": comment.get("comment_text"),
                        "created_at": _to_iso(comment.get("created_at")),
                    },
                })

            # Images (including soft-deleted)
            db.cursor.execute(
                f"""
                SELECT ti.*
                FROM ticket_images ti
                JOIN tickets t ON t.ticket_number = ti.ticket_number
                WHERE ti.uploaded_at > %s
                {office_sql}
                ORDER BY ti.uploaded_at ASC, ti.id ASC
                LIMIT %s
                """,
                [lower] + office_params + [limit],
            )
            for row in db.cursor.fetchall():
                img = dict(row)
                is_deleted = bool(img.get("is_deleted"))
                changes.append({
                    "entity": "ticket_image",
                    "id": str(img["id"]),
                    "operation": "delete" if is_deleted else "upsert",
                    "updated_at": _to_iso(img.get("uploaded_at")),
                    "data": None if is_deleted else {
                        "id": img["id"],
                        "ticket_number": img["ticket_number"],
                        "original_filename": img.get("original_filename"),
                        "mime_type": img.get("mime_type"),
                        "file_size": img.get("file_size"),
                        "uploaded_at": _to_iso(img.get("uploaded_at")),
                        "is_deleted": False,
                        "download_url": f"/api/images/{img['id']}/download",
                        "thumbnail_url": f"/api/images/{img['id']}/thumbnail",
                    },
                })

            # Tasks
            db.cursor.execute(
                f"""
                SELECT tt.*
                FROM ticket_tasks tt
                JOIN tickets t ON t.ticket_number = tt.ticket_number
                WHERE tt.created_at > %s
                {office_sql}
                ORDER BY tt.created_at ASC, tt.id ASC
                LIMIT %s
                """,
                [lower] + office_params + [limit],
            )
            for row in db.cursor.fetchall():
                task = dict(row)
                changes.append({
                    "entity": "ticket_task",
                    "id": task["ticket_number"],
                    "operation": "upsert",
                    "updated_at": _to_iso(task.get("created_at")),
                    "data": {
                        "ticket_number": task["ticket_number"],
                        "created_at": _to_iso(task.get("created_at")),
                    },
                })

        # Merge-sort by updated_at and apply cursor filter, then trim to limit
        def sort_key(item: Dict[str, Any]):
            return (
                _parse_iso(item.get("updated_at")),
                item.get("entity") or "",
                str(item.get("id") or ""),
            )

        changes.sort(key=sort_key)
        filtered: List[Dict[str, Any]] = []
        for item in changes:
            u, e, i = sort_key(item)
            if cursor and (u, e, i) <= (cursor_dt, cursor_entity, cursor_id):
                continue
            filtered.append(item)
            if len(filtered) >= limit:
                break

        has_more = len(filtered) >= limit
        next_cursor = None
        if filtered:
            last = filtered[-1]
            next_cursor = _encode_cursor(
                _parse_iso(last.get("updated_at")),
                last.get("entity") or "",
                str(last.get("id") or ""),
            )

        return {
            "server_time": _to_iso(datetime.now(timezone.utc)),
            "next_cursor": next_cursor,
            "has_more": has_more,
            "changes": filtered,
        }
    except Exception as e:
        logger.exception("sync/changes failed: %s", e)
        return JSONResponse({"error": str(e)}, status_code=500)
