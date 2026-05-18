"""
FastAPI приложение — точки входа API и HTML-рендеринг
"""
import os
import sys
import re
import json
import hashlib
import logging
import asyncio
import threading
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, Query, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

from psycopg2.sql import SQL, Identifier

from database.db_manager import DatabaseManager
from database.models import TicketImage, UserComment
from config.settings import load_config
from email_processor.email_client import EmailClient
from email_processor.email_parser import EmailParser
from email_processor.ticket_processor import TicketProcessor
from services.image_manager import ImageManager, ImageValidationError
from services.image_compressor import (
    ImageCompressor, CompressionConfig as CompressorConfig,
    CompressionPreset
)

# Импорт модуля аутентификации и авторизации
from auth.middleware import AuthMiddleware, require_permission, get_current_user
from auth.db_manager import AuthDBManager
from auth.router import router as auth_router
from auth.models import Permission, UserRole

# Импорт системы мониторинга аварийных завершений
from utils.helpers import abbreviate_office
from utils.crash_monitor import (
    install_crash_monitor,
    uninstall_crash_monitor,
    set_last_request,
    set_shutdown_callback,
    mark_manual_stop,
    get_crash_monitor_status,
    list_crash_reports,
    save_crash_report,
    build_crash_report,
)

load_dotenv()

# Глобальные экземпляры
db: DatabaseManager = None
image_manager: ImageManager = None
auth_db: AuthDBManager = None

# Версия статических файлов (вычисляется при старте)
static_version: str = "1"

# Хранилище статуса фоновой перестройки БД
_rebuild_progress = {
    "running": False,
    "total": 0,
    "processed": 0,
    "errors": 0,
    "message": "",
    "status": "idle",  # idle | running | completed | error
    "result": None,
}


def compute_static_version() -> str:
    """
    Вычисляет версию статических файлов на основе MD5-хеша их содержимого.
    При изменении любого из отслеживаемых файлов версия автоматически меняется.
    """
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    tracked_files = [
        os.path.join(static_dir, "css", "main.css"),
        os.path.join(static_dir, "js", "auth.js"),
    ]
    hash_md5 = hashlib.md5()
    for filepath in tracked_files:
        if os.path.isfile(filepath):
            with open(filepath, "rb") as f:
                # Читаем файл блоками для эффективности
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
        else:
            # Если файла нет — учитываем сам факт отсутствия
            hash_md5.update(filepath.encode("utf-8"))
    # Берём первые 12 символов хеша — достаточно для версионирования
    return hash_md5.hexdigest()[:12]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение работы приложения"""
    global db, image_manager, auth_db
    config = load_config()
    db_config = {
        'host': config['database'].host,
        'port': config['database'].port,
        'database': config['database'].database,
        'user': config['database'].user,
        'password': config['database'].password,
    }
    db = DatabaseManager(db_config)
    if not db.connect():
        print("✗ Не удалось подключиться к БД")

    # Инициализация модуля аутентификации
    auth_db = AuthDBManager(db)
    auth_db.create_tables()

    # Восстановление sequence user_permissions_id_seq при старте
    try:
        auth_db.db.cursor.execute(
            "SELECT setval('user_permissions_id_seq', "
            "COALESCE((SELECT MAX(id) FROM user_permissions), 0) + 1, false)"
        )
        auth_db.db.connection.commit()
        logger.info("Sequence user_permissions_id_seq восстановлен при старте")
    except Exception as seq_err:
        logger.warning(f"Не удалось восстановить sequence user_permissions: {seq_err}")
        try:
            auth_db.db.connection.rollback()
        except Exception:
            pass

    # Синхронизация разрешений всех пользователей с DEFAULT_ROLE_PERMISSIONS
    try:
        auth_db.sync_all_users_permissions()
    except Exception as sync_err:
        logger.warning(f"Не удалось синхронизировать разрешения: {sync_err}")

    app.state.auth_db = auth_db
    print("🔐 Модуль аутентификации инициализирован")

    # Инициализация ImageManager с компрессией изображений
    comp_config = config.get('compression')
    if comp_config and comp_config.enabled:
        compressor_cfg = CompressorConfig()
        preset_map = {
            'max_quality': CompressionPreset.MAX_QUALITY,
            'balanced': CompressionPreset.BALANCED,
            'traffic_saving': CompressionPreset.TRAFFIC_SAVING,
        }
        compressor_cfg.apply_preset(preset_map.get(comp_config.preset, CompressionPreset.BALANCED))
        compressor_cfg.max_long_side = comp_config.max_long_side
        compressor_cfg.jpeg_quality = comp_config.jpeg_quality
        compressor_cfg.webp_quality = comp_config.webp_quality
        compressor_cfg.target_max_size = comp_config.target_max_size_kb * 1024
        compressor_cfg.keep_exif = comp_config.keep_exif
        compressor_cfg.keep_alpha = comp_config.keep_alpha
        image_manager = ImageManager(
            upload_dir='uploads',
            compression_config=compressor_cfg,
            compression_enabled=True,
        )
        print(f"✓ ImageManager инициализирован (компрессия: {comp_config.preset})")
    else:
        image_manager = ImageManager(upload_dir='uploads', compression_enabled=False)
        print("✓ ImageManager инициализирован (компрессия выключена)")

    # Вычисление версии статических файлов
    global static_version
    sv_config = config.get('static_version', None)
    if sv_config and sv_config.enabled:
        if sv_config.method == 'hash':
            static_version = compute_static_version()
        elif sv_config.method == 'timestamp':
            static_version = str(int(datetime.now().timestamp()))
        else:  # fixed
            static_version = sv_config.fixed_version
    else:
        static_version = "1"
    print(f"📦 Версия статических файлов: {static_version}")

    # Установка системы мониторинга аварийных завершений
    def _shutdown_cleanup():
        """Callback при аварийном завершении — закрываем соединения."""
        if db:
            try:
                db.close()
            except Exception:
                pass

    install_crash_monitor(shutdown_callback=_shutdown_cleanup)
    print("🛡️ Система мониторинга аварийных завершений активирована")

    yield

    # При штатном завершении (lifespan yield завершился) — снимаем обработчики
    uninstall_crash_monitor()
    if db:
        db.close()


app = FastAPI(
    title="ГКУ ОП Заявки",
    description="Веб-интерфейс для просмотра заявок на оборудование",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware (разрешаем запросы с любых источников для production за Nginx)
# ВАЖНО: allow_origins=["*"] и allow_credentials=True несовместимы по спецификации CORS.
# Если нужны credentials, указываем конкретные origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware (проверка Bearer-токенов)
# Регистрируем после CORS, чтобы preflight-запросы OPTIONS не блокировались
app.add_middleware(
    BaseHTTPMiddleware,
    dispatch=AuthMiddleware(),
)

# Шаблоны
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Статические файлы (CSS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Подключаем роутер аутентификации
app.include_router(auth_router)

# ─── Middleware для отслеживания запросов ──────────────────────────


@app.middleware("http")
async def track_request_middleware(request: Request, call_next):
    """Middleware для записи информации о текущем запросе в crash_monitor."""
    # Получаем тело запроса (только для не-GET запросов)
    body_preview = None
    if request.method in ("POST", "PUT", "PATCH"):
        try:
            body = await request.body()
            if body:
                body_str = body.decode("utf-8", errors="replace")
                body_preview = body_str[:500]  # Ограничиваем до 500 символов
        except Exception:
            pass

    set_last_request(
        method=request.method,
        path=str(request.url.path),
        client_ip=request.client.host if request.client else None,
        body_preview=body_preview,
    )

    response = await call_next(request)
    return response


# ─── API эндпоинты ────────────────────────────────────────────────


@app.get("/api/tickets")
async def api_get_tickets(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    status: str = Query(None),
    search: str = Query(None),
    sort_by: str = Query("last_updated_date"),
    sort_order: str = Query("desc"),
    archived: str = Query("0"),
    has_images: str = Query(None),
):
    """Получить список заявок с пагинацией и фильтрацией.
    archived=0 — только активные (по умолчанию),
    archived=1 — только архивированные,
    archived=all — все.
    has_images=true — только с изображениями,
    has_images=false — только без изображений,
    has_images=null (по умолчанию) — все.
    """
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        where_clauses = []
        params = []

        if archived == "0":
            where_clauses.append("(t.is_archived IS NULL OR t.is_archived = FALSE)")
        elif archived == "1":
            where_clauses.append("t.is_archived = TRUE")

        if status:
            where_clauses.append("t.status = %s")
            params.append(status)

        if search:
            search_clean = search.strip()
            # Пропускаем пустую строку или строку только из пробелов
            if len(search_clean) < 1:
                pass  # не добавляем условий поиска
            else:
                # Экранирование специальных символов ILIKE (% и _)
                search_escaped = search_clean.replace('%', '\\%').replace('_', '\\_')
                like_val = f"%{search_escaped}%"


                # Нормализация номера заявки: удаляем разделители (дефисы, пробелы, точки, слеши)
                ticket_normalized = re.sub(r'[\s\-\./]', '', search_clean)
                like_ticket_normalized = f"%{ticket_normalized}%"

                # Цифровая часть для поиска по инвентарному номеру
                digits_only = re.sub(r'[^\d]', '', search_clean)

                conditions = []
                params_list = []

                # ─── УРОВЕНЬ 1: Поиск по ticket_number ───
                # 1a. Поиск по оригинальному ticket_number
                conditions.append("t.ticket_number ILIKE %s ESCAPE '\\'")
                params_list.append(like_val)

                # 1b. Поиск по нормализованному ticket_number (без разделителей)
                if ticket_normalized != search_clean:
                    conditions.append(
                        "REGEXP_REPLACE(t.ticket_number, '[\\s\\-\\./]', '', 'g') ILIKE %s ESCAPE '\\'"
                    )
                    params_list.append(like_ticket_normalized)

                # ─── УРОВЕНЬ 2: Поиск по inventory_number ───
                # 2a. Поиск по оригинальному inventory_number
                conditions.append("t.inventory_number ILIKE %s ESCAPE '\\'")
                params_list.append(like_val)

                # 2b. Поиск по нормализованному inventory_number (только цифры)
                if digits_only:
                    conditions.append(
                        "REGEXP_REPLACE(t.inventory_number, '[^0-9]', '', 'g') ILIKE %s ESCAPE '\\'"
                    )
                    params_list.append(f"%{digits_only}%")

                # ─── УРОВЕНЬ 3: Поиск по текстовым полям ───
                text_fields = [
                    "t.subject", "t.fault_description", "t.work_done",
                    "t.tech_conclusion", "t.cause", "t.current_note",
                    "t.required_action", "t.soglasovano_line",
                    "t.author_name", "t.printer_model", "t.office",
                    "t.cabinet", "t.component", "t.department",
                    "t.position", "t.assigned_to"
                ]
                for field in text_fields:
                    conditions.append(f"{field} ILIKE %s ESCAPE '\\'")
                    params_list.append(like_val)

                where_clauses.append("(" + " OR ".join(conditions) + ")")
                params.extend(params_list)

        # Фильтр по наличию изображений
        if has_images == "true":
            where_clauses.append(
                "EXISTS (SELECT 1 FROM ticket_images ti "
                "WHERE ti.ticket_number = t.ticket_number AND ti.is_deleted = FALSE)"
            )
        elif has_images == "false":
            where_clauses.append(
                "NOT EXISTS (SELECT 1 FROM ticket_images ti "
                "WHERE ti.ticket_number = t.ticket_number AND ti.is_deleted = FALSE)"
            )

        # ─── Фильтрация по правам доступа к офисам ───────────────
        # Администраторы видят все заявки, операторы — только по своим офисам
        current_user = get_current_user(request)
        if current_user and current_user.role != UserRole.ADMIN:
            user_offices = auth_db.get_user_offices(current_user.username)
            if user_offices:
                # Создаём плейсхолдеры для списка офисов
                placeholders = ", ".join(["%s"] * len(user_offices))
                where_clauses.append(f"t.office IN ({placeholders})")
                params.extend(user_offices)
            else:
                # Если у пользователя нет назначенных офисов — не показываем ничего
                where_clauses.append("1 = 0")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        # Сортировка
        allowed_sort = {
            "ticket_number", "status", "last_updated_date",
            "first_received_date", "author_name", "inventory_number"
        }
        if sort_by not in allowed_sort:
            sort_by = "last_updated_date"
        if sort_order not in ("asc", "desc"):
            sort_order = "desc"

        # Общее количество
        count_query = f"SELECT COUNT(*) as total FROM tickets t {where_sql}"
        db.cursor.execute(count_query, params)
        total = db.cursor.fetchone()["total"]

        # Данные
        offset = (page - 1) * per_page
        sort_column = Identifier(sort_by)
        data_query = SQL("""
            SELECT t.*,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM ticket_images ti
                       WHERE ti.ticket_number = t.ticket_number AND ti.is_deleted = FALSE
                   ) THEN TRUE ELSE FALSE END AS has_files,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM user_comments uc
                       WHERE uc.ticket_number = t.ticket_number
                   ) THEN TRUE ELSE FALSE END AS has_comments,
                   COALESCE(
                       (
                           SELECT th.received_date
                           FROM ticket_history th
                           WHERE th.ticket_number = t.ticket_number
                             AND (
                                 th.changed_fields::jsonb @> '{"status": "Выполнено"}'::jsonb
                                 OR th.status = 'Выполнено'
                             )
                           ORDER BY th.received_date DESC
                           LIMIT 1
                       ),
                       CASE WHEN t.status = 'Выполнено' THEN t.last_updated_date ELSE NULL END
                   ) AS completed_at
            FROM tickets t
        """) + SQL(where_sql) + SQL(" ORDER BY t.{} {} LIMIT %s OFFSET %s").format(
            sort_column, SQL(sort_order)
        )
        db.cursor.execute(data_query, params + [per_page, offset])
        rows = db.cursor.fetchall()

        # Сортировка результатов по уровню приоритета:
        # Уровень 1 (ticket_number) → Уровень 2 (inventory_number) → Уровень 3 (текстовые поля)
        if search and rows:
            search_lower = search_clean.lower()

            def get_match_level(ticket):
                tn = (ticket.get('ticket_number') or '').lower()
                inv = (ticket.get('inventory_number') or '').lower()
                if search_lower in tn:
                    return 0  # Уровень 1 — найден по номеру заявки
                if search_lower in inv:
                    return 1  # Уровень 2 — найден по инвентарному номеру
                return 2      # Уровень 3 — найден по текстовым полям

            rows.sort(key=get_match_level)

        # Применяем сокращение адресов офисов для отображения в списке
        tickets_data = []
        for r in rows:
            ticket_dict = dict(r)
            ticket_dict['office'] = abbreviate_office(ticket_dict.get('office'))
            tickets_data.append(ticket_dict)

        return {
            "tickets": tickets_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets/{ticket_number}")
async def api_get_ticket(ticket_number: str, request: Request = None):
    """Получить детали заявки, историю и изображения"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        # ─── Проверка прав доступа к офису заявки ───────────────
        current_user = get_current_user(request) if request else None
        if current_user and current_user.role != UserRole.ADMIN:
            user_offices = auth_db.get_user_offices(current_user.username)
            ticket_office = ticket.get('office', '')
            if ticket_office and ticket_office not in user_offices:
                return JSONResponse(
                    {"error": "Недостаточно прав для просмотра данной заявки"},
                    status_code=403
                )

        history = db.get_ticket_history(ticket_number)
        # Фильтруем уже сохранённые changed_fields — удаляем поля, исключённые из отображения
        _history_excluded = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}
        # Метки полей, которые могут встречаться в comment_text
        _excluded_labels = ['Назначена', 'Телефон', 'Автор', 'Должность', 'Тема']
        for h in history:
            cf = h.get('changed_fields')
            if cf and isinstance(cf, dict):
                h['changed_fields'] = {k: v for k, v in cf.items() if k not in _history_excluded}
            changes = h.get('changes')
            if changes and isinstance(changes, dict):
                h['changes'] = {k: v for k, v in changes.items() if k not in _history_excluded}
            # Очищаем comment_text от упоминаний исключённых полей (например, "Назначена: Кокаева Альбина;")
            comment = h.get('comment', '')
            if comment:
                for label in _excluded_labels:
                    # Удаляем подстроки вида "Назначена: Текст;" или "Назначена: Текст"
                    import re
                    comment = re.sub(r'(?:^|;\s*)' + re.escape(label) + r':\s*[^;]+(?:;|$)', '', comment).strip()
                    # Убираем лишние разделители
                    comment = re.sub(r'^;\s*', '', comment)
                    comment = re.sub(r';{2,}', ';', comment)
                    comment = comment.strip('; ').strip()
                h['comment'] = comment
        images = db.get_ticket_images(ticket_number)
        # Добавляем URL для скачивания
        for img in images:
            img['download_url'] = f"/api/images/{img['id']}/download"
            if img.get('thumbnail_path'):
                img['thumbnail_url'] = f"/api/images/{img['id']}/thumbnail"

        # Получаем пользовательские комментарии
        user_comments = db.get_user_comments(ticket_number)
        comment_count = len(user_comments)

        # Добавляем completed_at — дату фактического завершения заявки
        completed_at = None
        if ticket.get('status') == 'Выполнено':
            try:
                db.cursor.execute("""
                    SELECT th.received_date
                    FROM ticket_history th
                    WHERE th.ticket_number = %s
                      AND (
                          th.changed_fields::jsonb @> '{"status": "Выполнено"}'::jsonb
                          OR th.status = 'Выполнено'
                      )
                    ORDER BY th.received_date DESC
                    LIMIT 1
                """, (ticket_number,))
                row = db.cursor.fetchone()
                if row:
                    completed_at = row['received_date'].isoformat() if hasattr(row['received_date'], 'isoformat') else str(row['received_date'])
            except Exception:
                pass
            if not completed_at:
                completed_at = ticket.get('last_updated_date')
                if hasattr(completed_at, 'isoformat'):
                    completed_at = completed_at.isoformat()

        return {
            "ticket": ticket,
            "history": history,
            "images": images,
            "user_comments": user_comments,
            "comment_count": comment_count,
            "completed_at": completed_at
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.put("/api/tickets/{ticket_number}")
@require_permission(Permission.EDIT_TICKETS)
async def api_update_ticket(ticket_number: str, request: Request):
    """Обновить заявку через API (ручное редактирование оператором)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        # 1. Извлекаем актуальный документ из БД
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        # 2. Получаем данные из тела запроса
        try:
            body = await request.json()
        except Exception as e:
            body_raw = await request.body()
            logger.error(f"JSON parse error in PUT /api/tickets/{ticket_number}: {e}. Body preview: {body_raw[:200]}")
            return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

        # 3. Вычисляем diff между актуальным состоянием и новыми данными
        changed_fields = {}
        for field, new_value in body.items():
            old_value = existing_ticket.get(field, '') or ''
            new_str = str(new_value).strip() if new_value else ''
            old_str = str(old_value).strip() if old_value else ''
            if old_str != new_str and new_str:
                changed_fields[field] = new_value

        if not changed_fields:
            return {"status": "ok", "message": "Нет изменений", "ticket": existing_ticket}

        # Исключаем поля, которые не должны попадать в историю изменений
        _history_excluded = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}
        changed_fields = {k: v for k, v in changed_fields.items() if k not in _history_excluded}

        if not changed_fields:
            return {"status": "ok", "message": "Нет изменений", "ticket": existing_ticket}

        # 4. Сохраняем запись в историю (только changed_fields)
        from database.models import TicketHistoryRecord
        history_record = TicketHistoryRecord(
            ticket_number=ticket_number,
            received_date=datetime.now(),
            email_hash=f"manual_{datetime.now().timestamp()}",
            changed_fields=changed_fields,
            subject=body.get('subject', existing_ticket.get('subject')),
            inventory_number=body.get('inventory_number', existing_ticket.get('inventory_number')),
            printer_model=body.get('printer_model', existing_ticket.get('printer_model')),
            office=body.get('office', existing_ticket.get('office')),
            cabinet=body.get('cabinet', existing_ticket.get('cabinet')),
            component=body.get('component', existing_ticket.get('component')),
            status=body.get('status', existing_ticket.get('status')),
            priority=body.get('priority', existing_ticket.get('priority')),
            assigned_to=body.get('assigned_to', existing_ticket.get('assigned_to')),
            author_name=body.get('author_name', existing_ticket.get('author_name')),
            contact_phone=body.get('contact_phone', existing_ticket.get('contact_phone')),
            department=body.get('department', existing_ticket.get('department')),
            position=body.get('position', existing_ticket.get('position')),
            current_note=body.get('current_note', existing_ticket.get('current_note')),
            soglasovano_line=body.get('soglasovano_line', existing_ticket.get('soglasovano_line')),
            required_action=body.get('required_action', existing_ticket.get('required_action')),
            cause=body.get('cause', existing_ticket.get('cause')),
            fault_description=body.get('fault_description', existing_ticket.get('fault_description')),
            work_done=body.get('work_done', existing_ticket.get('work_done')),
            tech_conclusion=body.get('tech_conclusion', existing_ticket.get('tech_conclusion')),
        )
        db.save_history_record(history_record)

        # 5. Обновляем тикет
        # Не передаём last_updated_date — дата последнего письма не должна
        # перезаписываться при ручном редактировании заявки
        db.update_ticket(ticket_number, changed_fields)

        # 6. Возвращаем обновлённый тикет
        updated_ticket = db.get_ticket(ticket_number)
        return {
            "status": "ok",
            "message": f"Обновлено полей: {len(changed_fields)}",
            "changed_fields": changed_fields,
            "ticket": updated_ticket
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/tickets/{ticket_number}/complete")
@require_permission(Permission.COMPLETE_TICKETS)
async def api_complete_ticket(ticket_number: str, request: Request):
    """Отметить заявку как выполненную (статус = 'Выполнено').
    Опционально принимает multipart/form-data с файлами (images).
    """
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        now = datetime.now()
        # Для истории сохраняем completed_at (в таблице ticket_history поле changed_fields — JSON)
        history_changed_fields = {"status": "Выполнено", "is_archived": False, "completed_at": now.isoformat()}
        # Для обновления таблицы tickets — только поля, существующие в таблице (колонки completed_at нет)
        changed_fields = {"status": "Выполнено", "is_archived": False}

        # Сохраняем в историю
        from database.models import TicketHistoryRecord
        history_record = TicketHistoryRecord(
            ticket_number=ticket_number,
            received_date=now,
            email_hash=f"manual_complete_{now.timestamp()}",
            changed_fields=history_changed_fields,
            subject=existing_ticket.get('subject'),
            inventory_number=existing_ticket.get('inventory_number'),
            printer_model=existing_ticket.get('printer_model'),
            office=existing_ticket.get('office'),
            cabinet=existing_ticket.get('cabinet'),
            component=existing_ticket.get('component'),
            status="Выполнено",
            priority=existing_ticket.get('priority'),
            assigned_to=existing_ticket.get('assigned_to'),
            author_name=existing_ticket.get('author_name'),
            contact_phone=existing_ticket.get('contact_phone'),
            department=existing_ticket.get('department'),
            position=existing_ticket.get('position'),
            current_note=existing_ticket.get('current_note'),
            soglasovano_line=existing_ticket.get('soglasovano_line'),
            required_action=existing_ticket.get('required_action'),
            cause=existing_ticket.get('cause'),
            fault_description=existing_ticket.get('fault_description'),
            work_done=existing_ticket.get('work_done'),
            tech_conclusion=existing_ticket.get('tech_conclusion'),
        )
        db.save_history_record(history_record)
        # Не передаём last_updated_date — дата последнего письма не должна
        # перезаписываться при ручном изменении статуса на "Выполнено"
        db.update_ticket(ticket_number, changed_fields)

        # При выполнении заявки автоматически удаляем её из задач
        try:
            db.remove_task(ticket_number)
        except Exception:
            pass  # Не критично, если не было в задачах

        # Обрабатываем опциональные файлы, если они есть
        uploaded_images = []
        try:
            form = await request.form()
            files = form.getlist("files")
            if files:
                for file in files:
                    if hasattr(file, 'read') and file.filename:
                        file_bytes = await file.read()
                        mime_type = file.content_type or 'image/jpeg'
                        ticket_image = image_manager.save_image(
                            ticket_number=ticket_number,
                            file_bytes=file_bytes,
                            original_filename=file.filename,
                            mime_type=mime_type,
                        )
                        image_id = db.save_image_record(ticket_image)
                        if image_id:
                            uploaded_images.append({
                                "id": image_id,
                                "original_filename": ticket_image.original_filename,
                            })
                            logger.info(f"Загружено изображение #{image_id} при завершении заявки {ticket_number}")
        except Exception:
            pass  # Файлы опциональны, ошибка загрузки не фатальна

        updated_ticket = db.get_ticket(ticket_number)
        result = {"status": "ok", "message": "Заявка отмечена как выполненная", "ticket": updated_ticket}
        if uploaded_images:
            result["uploaded_images"] = uploaded_images
        return result
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/tickets/{ticket_number}/archive")
@require_permission(Permission.ARCHIVE_TICKETS)
async def api_archive_ticket(ticket_number: str, request: Request):
    """Архивировать заявку (is_archived = TRUE)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        db.cursor.execute(
            "UPDATE tickets SET is_archived = TRUE, status = 'В архив' WHERE ticket_number = %s",
            (ticket_number,)
        )
        db.connection.commit()

        updated_ticket = db.get_ticket(ticket_number)
        return {"status": "ok", "message": "Заявка архивирована", "ticket": updated_ticket}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/tickets/{ticket_number}/restore")
@require_permission(Permission.ARCHIVE_TICKETS)
async def api_restore_ticket(ticket_number: str, request: Request):
    """Восстановить заявку из архива (is_archived = FALSE)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        # При восстановлении сбрасываем флаг архива и убираем статус "В архив",
        # но сохраняем другие статусы (например, "Выполнено")
        new_status = existing_ticket.get('status')
        if new_status == 'В архив':
            new_status = None

        db.cursor.execute(
            "UPDATE tickets SET is_archived = FALSE, status = %s WHERE ticket_number = %s",
            (new_status, ticket_number)
        )
        db.connection.commit()

        updated_ticket = db.get_ticket(ticket_number)
        return {"status": "ok", "message": "Заявка восстановлена из архива", "ticket": updated_ticket}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── API эндпоинты для задач ────────────────────────────────────────


@app.post("/api/tickets/{ticket_number}/task")
@require_permission(Permission.MANAGE_TASKS)
async def api_add_task(ticket_number: str, request: Request):
    """Добавить заявку в список задач"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        if db.add_task(ticket_number):
            return {"status": "ok", "message": "Заявка добавлена в задачи"}
        return JSONResponse({"error": "Не удалось добавить задачу"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/tickets/{ticket_number}/task")
@require_permission(Permission.MANAGE_TASKS)
async def api_remove_task(ticket_number: str, request: Request):
    """Удалить заявку из списка задач"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        if db.remove_task(ticket_number):
            return {"status": "ok", "message": "Заявка удалена из задач"}
        return JSONResponse({"error": "Не удалось удалить задачу"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets/{ticket_number}/task")
async def api_check_task(ticket_number: str):
    """Проверить, находится ли заявка в списке задач"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        is_task = db.is_task(ticket_number)
        return {"is_task": is_task}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── API эндпоинты для комментариев ────────────────────────────────


@app.post("/api/tickets/{ticket_number}/comments")
@require_permission(Permission.ADD_COMMENTS)
async def api_add_comment(ticket_number: str, request: Request):
    """Добавить комментарий к заявке от авторизованного пользователя"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        # Проверяем существование заявки
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        # Проверяем права доступа к офису заявки
        current_user = get_current_user(request)
        if not current_user:
            return JSONResponse({"error": "Пользователь не авторизован"}, status_code=401)

        if current_user.role != UserRole.ADMIN:
            user_offices = auth_db.get_user_offices(current_user.username)
            ticket_office = existing_ticket.get('office', '')
            if ticket_office and ticket_office not in user_offices:
                return JSONResponse(
                    {"error": "Недостаточно прав для комментирования данной заявки"},
                    status_code=403
                )

        # Получаем тело запроса
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "Неверный формат JSON"}, status_code=400)

        comment_text = (body.get('comment_text') or '').strip()
        if not comment_text:
            return JSONResponse({"error": "Текст комментария не может быть пустым"}, status_code=400)

        if len(comment_text) > 5000:
            return JSONResponse({"error": "Комментарий слишком длинный (максимум 5000 символов)"}, status_code=400)

        # Создаём и сохраняем комментарий
        comment = UserComment(
            ticket_number=ticket_number,
            author_username=current_user.username,
            author_name=current_user.full_name or current_user.username,
            comment_text=comment_text,
        )

        comment_id = db.save_user_comment(comment)
        if comment_id is None:
            return JSONResponse({"error": "Не удалось сохранить комментарий"}, status_code=500)

        # Возвращаем созданный комментарий
        return {
            "status": "ok",
            "message": "Комментарий добавлен",
            "comment": {
                "id": comment_id,
                "ticket_number": ticket_number,
                "author_username": comment.author_username,
                "author_name": comment.author_name,
                "comment_text": comment_text,
                "created_at": comment.created_at.isoformat() if comment.created_at else None,
            }
        }
    except Exception as e:
        logger.exception(f"Ошибка добавления комментария к заявке {ticket_number}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tasks")
async def api_get_tasks(request: Request):
    """Получить список номеров заявок в задачах"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        # ─── Фильтрация по правам доступа к офисам ───────────────
        current_user = get_current_user(request)
        if current_user and current_user.role != UserRole.ADMIN:
            user_offices = auth_db.get_user_offices(current_user.username)
            if user_offices:
                # Получаем офисы всех задач одним запросом
                task_offices = db.get_task_offices()
                # Оставляем только задачи, чей офис есть в разрешённых
                task_numbers = [
                    tn for tn, office in task_offices.items()
                    if office in user_offices
                ]
            else:
                task_numbers = []
        else:
            task_numbers = db.get_task_numbers()

        return {"tasks": task_numbers, "count": len(task_numbers)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tasks/tickets")
async def api_get_task_tickets(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = Query("last_updated_date"),
    sort_order: str = Query("desc"),
):
    """Получить заявки из списка задач с пагинацией (только активные, не архивированные)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        allowed_sort = {
            "ticket_number", "status", "last_updated_date",
            "first_received_date", "author_name", "inventory_number"
        }
        if sort_by not in allowed_sort:
            sort_by = "last_updated_date"
        if sort_order not in ("asc", "desc"):
            sort_order = "desc"

        where_clauses = [
            "(t.is_archived IS NULL OR t.is_archived = FALSE)"
        ]
        params = []

        # ─── Фильтрация по правам доступа к офисам ───────────────
        current_user = get_current_user(request)
        if current_user and current_user.role != UserRole.ADMIN:
            user_offices = auth_db.get_user_offices(current_user.username)
            if user_offices:
                placeholders = ", ".join(["%s"] * len(user_offices))
                where_clauses.append(f"t.office IN ({placeholders})")
                params.extend(user_offices)
            else:
                where_clauses.append("1 = 0")

        where_sql = " AND ".join(where_clauses)

        # Сначала получаем общее количество
        count_query = f"""
            SELECT COUNT(*) as total
            FROM tickets t
            INNER JOIN ticket_tasks tt ON t.ticket_number = tt.ticket_number
            WHERE {where_sql}
        """
        db.cursor.execute(count_query, params)
        total = db.cursor.fetchone()["total"]

        offset = (page - 1) * per_page
        sort_column = Identifier(sort_by)
        query = SQL("""
            SELECT t.*,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM ticket_images ti
                       WHERE ti.ticket_number = t.ticket_number AND ti.is_deleted = FALSE
                   ) THEN TRUE ELSE FALSE END AS has_files,
                   CASE WHEN EXISTS (
                       SELECT 1 FROM user_comments uc
                       WHERE uc.ticket_number = t.ticket_number
                   ) THEN TRUE ELSE FALSE END AS has_comments,
                   COALESCE(
                       (
                           SELECT th.received_date
                           FROM ticket_history th
                           WHERE th.ticket_number = t.ticket_number
                             AND (
                                 th.changed_fields::jsonb @> '{"status": "Выполнено"}'::jsonb
                                 OR th.status = 'Выполнено'
                             )
                           ORDER BY th.received_date DESC
                           LIMIT 1
                       ),
                       CASE WHEN t.status = 'Выполнено' THEN t.last_updated_date ELSE NULL END
                   ) AS completed_at
            FROM tickets t
            INNER JOIN ticket_tasks tt ON t.ticket_number = tt.ticket_number
        """) + SQL(f"WHERE {where_sql}") + SQL(" ORDER BY t.{} {} LIMIT %s OFFSET %s").format(
            sort_column, SQL(sort_order)
        )
        db.cursor.execute(query, params + [per_page, offset])
        rows = db.cursor.fetchall()

        # Применяем сокращение адресов офисов для отображения в списке
        tickets_data = []
        for r in rows:
            ticket_dict = dict(r)
            ticket_dict['office'] = abbreviate_office(ticket_dict.get('office'))
            tickets_data.append(ticket_dict)

        return {
            "tickets": tickets_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── API эндпоинты для изображений ──────────────────────────────────


@app.post("/api/tickets/{ticket_number}/images")
async def api_upload_images(ticket_number: str, files: List[UploadFile] = File(...)):
    """Загрузить одно или несколько изображений для заявки"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    if not image_manager:
        return JSONResponse({"error": "Менеджер изображений не инициализирован"}, status_code=503)

    try:
        # Проверяем существование заявки
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        uploaded = []
        errors = []

        MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 МБ

        for file in files:
            try:
                # Проверяем размер файла до чтения (если Content-Length известен)
                if file.size is not None and file.size > MAX_FILE_SIZE:
                    errors.append({
                        "file": file.filename,
                        "error": f"Файл слишком большой ({file.size / 1024 / 1024:.1f} МБ). Максимум: 50 МБ"
                    })
                    continue

                file_bytes = await file.read()

                # Проверяем размер после чтения (если Content-Length не был указан)
                if len(file_bytes) > MAX_FILE_SIZE:
                    errors.append({
                        "file": file.filename,
                        "error": f"Файл слишком большой ({len(file_bytes) / 1024 / 1024:.1f} МБ). Максимум: 50 МБ"
                    })
                    continue

                mime_type = file.content_type or 'image/jpeg'

                # Сохраняем файл через ImageManager
                ticket_image = image_manager.save_file(
                    ticket_number=ticket_number,
                    file_bytes=file_bytes,
                    original_filename=file.filename or 'unknown',
                    mime_type=mime_type,
                )

                # Сохраняем запись в БД
                image_id = db.save_image_record(ticket_image)
                if image_id:
                    uploaded.append({
                        "id": image_id,
                        "original_filename": ticket_image.original_filename,
                        "file_size": ticket_image.file_size,
                        "mime_type": ticket_image.mime_type,
                    })
                    logger.info(f"Загружено изображение #{image_id} для заявки {ticket_number}")
                else:
                    logger.error(
                        f"Не удалось сохранить запись в БД для файла {file.filename} "
                        f"(заявка {ticket_number}, путь: {ticket_image.file_path})"
                    )
                    errors.append({"file": file.filename, "error": "Не удалось сохранить запись в БД"})
            except ImageValidationError as e:
                errors.append({"file": file.filename, "error": str(e)})
            except Exception as e:
                errors.append({"file": file.filename, "error": f"Внутренняя ошибка: {e}"})

        return {
            "status": "ok",
            "uploaded": uploaded,
            "errors": errors,
            "total": len(files),
            "success_count": len(uploaded),
            "error_count": len(errors),
        }
    except Exception as e:
        logger.error(f"Ошибка загрузки изображений: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets/{ticket_number}/images")
async def api_get_ticket_images(ticket_number: str):
    """Получить список изображений заявки"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        images = db.get_ticket_images(ticket_number)
        # Добавляем URL для скачивания и thumbnail
        for img in images:
            img['download_url'] = f"/api/images/{img['id']}/download"
            if img.get('thumbnail_path'):
                img['thumbnail_url'] = f"/api/images/{img['id']}/thumbnail"

        return {"images": images, "total": len(images)}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/images/{image_id}/download")
async def api_download_image(image_id: int, request: Request):
    """Скачать оригинал файла (изображение или документ)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        image_record = db.get_image_by_id(image_id)
        if not image_record:
            return JSONResponse({"error": "Файл не найден"}, status_code=404)

        if image_record.get('is_deleted'):
            return JSONResponse({"error": "Файл удалён"}, status_code=410)

        file_bytes = image_manager.get_file_bytes(image_record['file_path'])
        if file_bytes is None:
            return JSONResponse({"error": "Файл не найден на диске"}, status_code=404)

        # Определяем Content-Type и Content-Disposition
        mime = image_record['mime_type']
        filename = image_record['original_filename']
        ext = Path(filename).suffix.lower()

        # RFC 5987: для не-ASCII имён используем filename*=UTF-8''...
        try:
            filename.encode('ascii')
            # ASCII-имя — можно использовать filename= напрямую
            ascii_filename = filename
        except (UnicodeEncodeError, UnicodeDecodeError):
            # Не-ASCII — кодируем через percent-encoding для RFC 5987
            ascii_filename = 'file' + ext

        # Для изображений — inline, для документов — attachment
        filename_part = f'filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
        disposition_type = 'inline' if ext in ('.jpg', '.jpeg', '.png', '.gif') else 'attachment'
        disposition = f'{disposition_type}; {filename_part}'

        # ETag для кэширования
        etag = image_manager.get_file_etag(image_record['file_path'])

        headers = {
            "Content-Disposition": disposition,
            "Content-Length": str(len(file_bytes)),
            "Cache-Control": "public, max-age=31536000, immutable",
            "Accept-Ranges": "bytes",
        }
        if etag:
            headers["ETag"] = etag

        # Проверка If-None-Match
        if etag and request.headers.get("if-none-match") == etag:
            return Response(status_code=304)

        return Response(
            content=file_bytes,
            media_type=mime,
            headers=headers,
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/images/{image_id}/thumbnail")
async def api_get_thumbnail(image_id: int, request: Request):
    """Получить thumbnail/preview файла"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        image_record = db.get_image_by_id(image_id)
        if not image_record:
            return JSONResponse({"error": "Файл не найден"}, status_code=404)

        if image_record.get('is_deleted'):
            return JSONResponse({"error": "Файл удалён"}, status_code=410)

        thumb_path = image_record.get('thumbnail_path')
        if not thumb_path:
            # Если thumbnail не создан, для изображений отдаём оригинал
            mime = image_record['mime_type']
            if mime.startswith('image/'):
                return await api_download_image(image_id, request)
            # Для документов — заглушка
            return Response(
                content=b'',
                media_type='image/png',
                status_code=204
            )

        file_bytes = image_manager.get_file_bytes(thumb_path)
        if file_bytes is None:
            return JSONResponse({"error": "Preview не найден"}, status_code=404)

        # ETag для кэширования
        etag = image_manager.get_file_etag(thumb_path)

        headers = {
            "Content-Disposition": f'inline; filename="preview_{image_id}.png"',
            "Cache-Control": "public, max-age=86400",  # 24 часа
            "Content-Length": str(len(file_bytes)),
        }
        if etag:
            headers["ETag"] = etag

        # Проверка If-None-Match
        if etag and request.headers.get("if-none-match") == etag:
            return Response(status_code=304)

        return Response(
            content=file_bytes,
            media_type='image/png',  # Всегда PNG
            headers=headers,
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/api/images/{image_id}")
@require_permission(Permission.DELETE_IMAGES)
async def api_delete_image(image_id: int, request: Request):
    """Удалить изображение (мягкое удаление)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        image_record = db.get_image_by_id(image_id)
        if not image_record:
            return JSONResponse({"error": "Изображение не найдено"}, status_code=404)

        if image_record.get('is_deleted'):
            return JSONResponse({"error": "Изображение уже удалено"}, status_code=410)

        # Мягкое удаление в БД
        if db.soft_delete_image(image_id):
            # Опционально: удаляем файлы с диска
            image_manager.delete_image_files(image_record)
            logger.info(f"Изображение #{image_id} удалено (мягкое удаление)")
            return {"status": "ok", "message": "Изображение удалено"}
        else:
            return JSONResponse({"error": "Не удалось удалить изображение"}, status_code=500)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/statistics")
async def api_get_statistics():
    """Получить статистику"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/statuses")
async def api_get_statuses():
    """Получить список уникальных статусов"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        db.cursor.execute(
            "SELECT DISTINCT status FROM tickets WHERE status IS NOT NULL ORDER BY status"
        )
        rows = db.cursor.fetchall()
        return {"statuses": [r["status"] for r in rows]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── Фоновая перестройка БД с прогрессом ──────────────────────────

def _run_rebuild_background():
    """Фоновая задача перестройки БД (выполняется в отдельном потоке)"""
    global _rebuild_progress
    try:
        config = load_config()

        # --- Проверяем checkpoint для инкрементального обновления ---
        checkpoint = db.get_checkpoint()
        use_incremental = checkpoint is not None
        since_date = None

        if use_incremental:
            since_date = checkpoint['checkpoint_date']
            logger.info(f"Инкрементальное обновление: checkpoint от {since_date}, "
                        f"ранее обработано {checkpoint['processed_count']} писем")
            _rebuild_progress["message"] = (
                f"Инкрементальное обновление (checkpoint: {since_date.strftime('%d.%m.%Y')})…"
            )
        else:
            _rebuild_progress["message"] = "Полная перестройка БД…"

        # Шаг 1: Сохраняем пользовательские статусы
        saved_statuses = {}
        try:
            db.cursor.execute(
                "SELECT ticket_number, status, is_archived, is_active FROM tickets"
            )
            for row in db.cursor.fetchall():
                saved_statuses[row['ticket_number']] = {
                    'status': row['status'],
                    'is_archived': row['is_archived'],
                    'is_active': row['is_active'],
                }
            logger.info(f"Сохранено статусов для {len(saved_statuses)} существующих заявок")
        except Exception:
            pass

        # Шаг 2: Очистка БД (только для полной перестройки)
        if not use_incremental:
            cleanup_result = db.full_cleanup()
            if not cleanup_result['success']:
                _rebuild_progress.update({
                    "running": False,
                    "status": "error",
                    "message": "Не удалось выполнить очистку БД",
                })
                return
        else:
            logger.info("Инкрементальный режим: очистка БД пропущена")

        # Шаг 3: Подключение к почте
        email_client = EmailClient(
            imap_server=config['email'].imap_server,
            email=config['email'].email,
            password=config['email'].password,
            port=config['email'].port
        )
        if not email_client.connect():
            _rebuild_progress.update({
                "running": False,
                "status": "error",
                "message": "Не удалось подключиться к почте",
            })
            return

        if not email_client.select_folder(config['email'].folder):
            email_client.close()
            _rebuild_progress.update({
                "running": False,
                "status": "error",
                "message": "Не удалось выбрать папку",
            })
            return

        email_parser = EmailParser(
            config['parser'].patterns,
            subject_filters=config['parser'].subject_filters
        )
        ticket_processor = TicketProcessor(db)

        # Поиск писем (с фильтром по дате для инкрементального режима)
        email_ids = email_client.search_emails(
            subject_filters=config['parser'].subject_filters,
            from_filter=config['parser'].from_filter,
            since_date=since_date if use_incremental else None
        )

        if not email_ids:
            email_client.close()
            # Сохраняем checkpoint даже если писем нет (обновляем дату)
            try:
                now = datetime.now()
                db.save_checkpoint(now, 0)
                logger.info(f"Сохранён checkpoint (писем нет): {now}")
            except Exception as e:
                logger.error(f"Ошибка сохранения checkpoint: {e}")
            _rebuild_progress.update({
                "running": False,
                "total": 0,
                "processed": 0,
                "errors": 0,
                "status": "completed",
                "message": "Нет писем для обработки",
                "result": {"processed": 0, "errors": 0}
            })
            return

        total = len(email_ids)
        _rebuild_progress["total"] = total
        _rebuild_progress["message"] = f"Обработка писем — 0 из {total}"

        # Обрабатываем письма
        processed = 0
        errors = 0
        for idx, email_id in enumerate(email_ids, 1):
            email_message = email_client.fetch_email(email_id)
            if not email_message:
                errors += 1
            else:
                email_data = email_parser.parse_email(email_message)
                if email_data:
                    if ticket_processor.process_email(email_data):
                        processed += 1
                    else:
                        errors += 1

            # Обновляем прогресс
            _rebuild_progress.update({
                "processed": processed,
                "errors": errors,
                "message": f"Обработка писем — {idx} из {total}",
            })

        email_client.close()

        # Шаг 4: Восстанавливаем статусы
        restored_count = 0
        for ticket_number, saved in saved_statuses.items():
            updates = {}
            if saved.get('status'):
                updates['status'] = saved['status']
            if saved.get('is_archived') is not None:
                updates['is_archived'] = saved['is_archived']
            if saved.get('is_active') is not None:
                updates['is_active'] = saved['is_active']
            if updates:
                if db.ticket_exists(ticket_number):
                    db.update_ticket(ticket_number, updates)
                    restored_count += 1

        logger.info(f"Восстановлено статусов для {restored_count} заявок")

        # Шаг 5: Сохраняем checkpoint (только при успешной обработке)
        try:
            now = datetime.now()
            db.save_checkpoint(now, processed)
            logger.info(f"Сохранён checkpoint: {now}, обработано писем: {processed}")
        except Exception as e:
            logger.error(f"Ошибка сохранения checkpoint: {e}")

        # Шаг 6: Верификация
        integrity_result = db.verify_data_integrity()

        _rebuild_progress.update({
            "running": False,
            "status": "completed",
            "message": f"Обработано: {processed}, Ошибок: {errors}",
            "result": {
                "processed": processed,
                "errors": errors,
                "statuses_restored": restored_count,
                "integrity_result": integrity_result,
            }
        })
    except Exception as e:
        logger.exception("Ошибка фоновой перестройки БД")
        _rebuild_progress.update({
            "running": False,
            "status": "error",
            "message": str(e),
        })


@app.post("/api/rebuild/start")
async def api_rebuild_start():
    """Запустить фоновую перестройку БД с отслеживанием прогресса"""
    global _rebuild_progress
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    if _rebuild_progress["running"]:
        return JSONResponse({"error": "Перестройка уже выполняется"}, status_code=409)

    # Сбрасываем прогресс
    _rebuild_progress.update({
        "running": True,
        "total": 0,
        "processed": 0,
        "errors": 0,
        "message": "Подготовка к обработке…",
        "status": "running",
        "result": None,
    })

    # Запускаем в отдельном потоке, чтобы не блокировать event loop
    thread = threading.Thread(target=_run_rebuild_background, daemon=True)
    thread.start()

    return {"status": "started", "message": "Перестройка запущена"}


@app.get("/api/rebuild/status")
async def api_rebuild_status():
    """Получить текущий статус фоновой перестройки БД"""
    return dict(_rebuild_progress)


@app.post("/api/rebuild")
async def api_rebuild():
    """Обновление данных: переобработка всех писем из почты с сохранением пользовательских статусов"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        config = load_config()

        # Шаг 1: Сохраняем пользовательские статусы и флаги существующих заявок
        # (статусы «Выполнено», «В архив» и т.д., установленные вручную)
        saved_statuses = {}
        try:
            db.cursor.execute(
                "SELECT ticket_number, status, is_archived, is_active FROM tickets"
            )
            for row in db.cursor.fetchall():
                saved_statuses[row['ticket_number']] = {
                    'status': row['status'],
                    'is_archived': row['is_archived'],
                    'is_active': row['is_active'],
                }
            logger.info(f"Сохранено статусов для {len(saved_statuses)} существующих заявок")
        except Exception:
            # Таблицы может ещё не существовать — это нормально для первого запуска
            pass

        # Шаг 2: Комплексная очистка БД через full_cleanup()
        cleanup_result = db.full_cleanup()
        if not cleanup_result['success']:
            return JSONResponse({
                "error": "Не удалось выполнить очистку БД",
                "cleanup_result": cleanup_result
            }, status_code=500)

        # Инициализируем компоненты для обработки писем
        email_client = EmailClient(
            imap_server=config['email'].imap_server,
            email=config['email'].email,
            password=config['email'].password,
            port=config['email'].port
        )
        if not email_client.connect():
            return JSONResponse({"error": "Не удалось подключиться к почте"}, status_code=500)

        if not email_client.select_folder(config['email'].folder):
            email_client.close()
            return JSONResponse({"error": "Не удалось выбрать папку"}, status_code=500)

        email_parser = EmailParser(
            config['parser'].patterns,
            subject_filters=config['parser'].subject_filters
        )
        ticket_processor = TicketProcessor(db)

        # Поиск писем
        email_ids = email_client.search_emails(
            subject_filters=config['parser'].subject_filters,
            from_filter=config['parser'].from_filter
        )

        if not email_ids:
            email_client.close()
            return {
                "status": "ok",
                "message": "Нет писем для обработки",
                "processed": 0,
                "cleanup_result": cleanup_result
            }

        # Обрабатываем письма
        processed = 0
        errors = 0
        for email_id in email_ids:
            email_message = email_client.fetch_email(email_id)
            if not email_message:
                errors += 1
                continue

            email_data = email_parser.parse_email(email_message)
            if not email_data:
                continue

            if ticket_processor.process_email(email_data):
                processed += 1
            else:
                errors += 1

        email_client.close()

        # Шаг 3: Восстанавливаем сохранённые пользовательские статусы
        restored_count = 0
        for ticket_number, saved in saved_statuses.items():
            updates = {}
            if saved.get('status'):
                updates['status'] = saved['status']
            if saved.get('is_archived') is not None:
                updates['is_archived'] = saved['is_archived']
            if saved.get('is_active') is not None:
                updates['is_active'] = saved['is_active']

            if updates:
                # Проверяем, что заявка существует после переобработки
                if db.ticket_exists(ticket_number):
                    db.update_ticket(ticket_number, updates)
                    restored_count += 1

        logger.info(f"Восстановлено статусов для {restored_count} заявок")

        # Шаг 4: Верификация целостности после загрузки
        integrity_result = db.verify_data_integrity()

        return {
            "status": "ok",
            "message": f"Обработано: {processed}, Ошибок: {errors}",
            "processed": processed,
            "errors": errors,
            "cleanup_result": cleanup_result,
            "integrity_result": integrity_result,
            "statuses_restored": restored_count
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── HTML эндпоинты ────────────────────────────────────────────────


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Главная страница"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "static_version": static_version},
    )


@app.get("/tickets/{ticket_number}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_number: str):
    """Страница деталей заявки"""
    comment_count = 0
    if db:
        try:
            comment_count = db.get_user_comments_count(ticket_number)
        except Exception:
            pass
    return templates.TemplateResponse(
        "ticket_detail.html",
        {
            "request": request,
            "ticket_number": ticket_number,
            "comment_count": comment_count,
            "static_version": static_version,
        },
    )


# ─── Эндпоинты мониторинга ─────────────────────────────────────────


@app.get("/api/health")
async def api_health():
    """Health-check endpoint для супервизора."""
    status = get_crash_monitor_status()
    db_ok = db is not None and hasattr(db, 'connection') and db.connection is not None
    try:
        if db_ok:
            db.cursor.execute("SELECT 1")
            db_ok = db.cursor.fetchone() is not None
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "gkuop-web",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_ok else "disconnected",
        "monitor": status,
    }


@app.get("/api/crash-reports")
async def api_crash_reports(limit: int = Query(10, ge=1, le=100)):
    """Получить список последних crash-отчётов."""
    reports = list_crash_reports(limit=limit)
    return {"crash_reports": reports, "total": len(reports)}


@app.get("/api/crash-reports/{crash_id}")
async def api_crash_report_detail(crash_id: str):
    """Получить детальный crash-отчёт по ID."""
    from utils.crash_monitor import CRASH_LOG_DIR
    import json

    for f in CRASH_LOG_DIR.glob(f"crash_{crash_id}.json"):
        try:
            with open(f, "r", encoding="utf-8") as fh:
                report = json.load(fh)
            return {"crash_report": report}
        except Exception as e:
            return JSONResponse({"error": f"Ошибка чтения отчёта: {e}"}, status_code=500)

    return JSONResponse({"error": "Crash-отчёт не найден"}, status_code=404)


@app.get("/api/monitor/status")
async def api_monitor_status():
    """Получить полный статус системы мониторинга."""
    return get_crash_monitor_status()


# ─── Запуск ────────────────────────────────────────────────────────


def main():
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    uvicorn.run("web_api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
