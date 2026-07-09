"""
FastAPI приложение — точки входа API и HTML-рендеринг
"""
import os
import sys
import re
import json
import hashlib
import logging
import threading
import tempfile
import asyncio
import gc
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from uuid import UUID
from contextlib import asynccontextmanager
from typing import List, Optional, Any
from urllib.parse import quote

logger = logging.getLogger(__name__)

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, Query, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from dotenv import load_dotenv

from psycopg2.sql import SQL, Identifier

from database.db_manager import DatabaseManager
from database.models import UserComment
from config.settings import load_config
from email_processor.email_client import EmailClient
from email_processor.email_parser import EmailParser
from email_processor.ticket_processor import TicketProcessor
from services.image_manager import ImageManager, ImageValidationError, MAX_FILE_SIZE as IMAGE_MAX_FILE_SIZE
from services.image_compressor import CompressionConfig as CompressorConfig, CompressionPreset
from services.db_backup import (
    DatabaseBackupError,
    build_dump_filename,
    create_database_dump,
    restore_database_dump,
)
from utils.email_sync import (
    compute_checkpoint_date,
    compute_imap_since_date,
    process_email_messages,
)

# Импорт модуля аутентификации и авторизации
from auth.middleware import AuthMiddleware, require_permission, require_role, get_current_user
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
)

load_dotenv()

# Глобальные экземпляры
db: DatabaseManager = None
image_manager: ImageManager = None
auth_db: AuthDBManager = None
_upload_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="upload")

# Версия статических файлов (вычисляется при старте)
static_version: str = "1"

# Хранилище статуса фоновой перестройки БД
_rebuild_progress = {
    "running": False,
    "total": 0,
    "processed": 0,
    "errors": 0,
    "skipped": 0,
    "message": "",
    "status": "idle",  # idle | running | completed | error
    "result": None,
}

EDITABLE_TICKET_FIELDS = {
    'inventory_number', 'printer_model', 'office', 'cabinet', 'component',
    'status', 'priority', 'current_note', 'required_action', 'cause',
    'fault_description', 'work_done', 'tech_conclusion', 'soglasovano_line',
    'department',
}

HISTORY_EXCLUDED_FIELDS = {
    'assigned_to', 'contact_phone', 'author_name', 'position', 'subject',
}


def _error_response(message: str, status_code: int) -> JSONResponse:
    """Единый JSON-ответ для ошибок доступа и валидации."""
    return JSONResponse({"error": message}, status_code=status_code)


def _user_can_access_ticket(user: Any, ticket: dict) -> bool:
    """Проверяет доступ пользователя к заявке по офису."""
    if not user:
        return False
    if user.role == UserRole.ADMIN:
        return True
    ticket_office = (ticket.get('office') or '').strip()
    if not ticket_office:
        return True
    user_offices = auth_db.get_user_offices(user.username) if auth_db else []
    return ticket_office in user_offices


def _require_ticket_access(request: Request, ticket: dict) -> Optional[JSONResponse]:
    """Возвращает ошибку доступа к заявке или None, если доступ разрешён."""
    current_user = get_current_user(request)
    if not current_user:
        return _error_response("Требуется авторизация", 401)
    if not _user_can_access_ticket(current_user, ticket):
        return _error_response("Недостаточно прав для данной заявки", 403)
    return None


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

    # Миграция: добавление колонок last_status, completed_by, completed_at в таблицу tickets
    try:
        db.cursor.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tickets' AND column_name = 'last_status'
                ) THEN
                    ALTER TABLE tickets ADD COLUMN last_status VARCHAR(100);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tickets' AND column_name = 'completed_by'
                ) THEN
                    ALTER TABLE tickets ADD COLUMN completed_by VARCHAR(200);
                END IF;
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'tickets' AND column_name = 'completed_at'
                ) THEN
                    ALTER TABLE tickets ADD COLUMN completed_at TIMESTAMP;
                END IF;
            END $$;
        """)
        db.connection.commit()
        logger.info("Миграция БД: колонки last_status, completed_by, completed_at добавлены/проверены")
    except Exception as mig_err:
        logger.warning(f"Не удалось выполнить миграцию БД: {mig_err}")
        try:
            db.connection.rollback()
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
    _upload_executor.shutdown(wait=False, cancel_futures=True)
    if db:
        db.close()


class CustomJSONEncoder(json.JSONEncoder):
    """Кастомный JSONEncoder для сериализации datetime и других нестандартных типов."""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, date):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, bytes):
            return obj.decode('utf-8', errors='replace')
        return super().default(obj)


class CustomJSONResponse(JSONResponse):
    """JSONResponse с кастомным энкодером для поддержки datetime и других типов."""
    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            cls=CustomJSONEncoder,
            ensure_ascii=False,
            allow_nan=True,
            indent=None,
            separators=(", ", ":"),
        ).encode("utf-8")


app = FastAPI(
    title="ГКУ ОП Заявки",
    description="Веб-интерфейс для просмотра заявок на оборудование",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=CustomJSONResponse,
)


# Глобальный обработчик исключений — все ошибки возвращаются как JSON
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Перехватывает любые необработанные исключения и возвращает JSON."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return CustomJSONResponse(
        status_code=500,
        content={"error": "Внутренняя ошибка сервера"},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Перехватывает HTTPException и возвращает JSON."""
    return CustomJSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
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
    body_preview = None
    if request.method in {"POST", "PUT", "PATCH"}:
        content_length = request.headers.get("content-length")
        content_type = request.headers.get("content-type", "")
        if content_length:
            body_preview = f"content-length={content_length}"
            if "multipart/form-data" in content_type:
                body_preview += "; multipart upload"

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
@require_permission(Permission.VIEW_TICKETS)
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
    month: str = Query(None),
    office: str = Query(None),
):
    """Получить список заявок с пагинацией и фильтрацией.
    archived=0 — только активные (по умолчанию),
    archived=1 — только архивированные,
    archived=all — все.
    has_images=true — только с изображениями,
    has_images=false — только без изображений,
    has_images=null (по умолчанию) — все.
    month=MM-YYYY — фильтр по месяцу выполнения (статус "Выполнено").
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

        # ─── Фильтрация по месяцу выполнения ──────────────────────
        # Формат month: MM-YYYY (например, "01-2025" или "05-2026")
        if month:
            import re as re_month
            month_match = re_month.match(r'^(\d{2})-(\d{4})$', month)
            if month_match:
                month_num = month_match.group(1)
                year_num = month_match.group(2)
                # Показываем только заявки со статусом "Выполнено",
                # у которых completed_at попадает в указанный месяц/год
                where_clauses.append("t.status = 'Выполнено'")
                where_clauses.append(
                    "EXTRACT(MONTH FROM COALESCE("
                    "(SELECT th.received_date FROM ticket_history th "
                    "WHERE th.ticket_number = t.ticket_number "
                    "AND (th.changed_fields::jsonb @> '{\"status\": \"Выполнено\"}'::jsonb OR th.status = 'Выполнено') "
                    "ORDER BY th.received_date DESC LIMIT 1), "
                    "t.last_updated_date)) = %s"
                )
                params.append(int(month_num))
                where_clauses.append(
                    "EXTRACT(YEAR FROM COALESCE("
                    "(SELECT th.received_date FROM ticket_history th "
                    "WHERE th.ticket_number = t.ticket_number "
                    "AND (th.changed_fields::jsonb @> '{\"status\": \"Выполнено\"}'::jsonb OR th.status = 'Выполнено') "
                    "ORDER BY th.received_date DESC LIMIT 1), "
                    "t.last_updated_date)) = %s"
                )
                params.append(int(year_num))

        # ─── Фильтрация по адресу офиса ─────────────────────────
        if office:
            where_clauses.append("t.office = %s")
            params.append(office)

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
        with db._lock:
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
                   ) AS completed_at,
                   t.last_status,
                   t.completed_by
            FROM tickets t
        """) + SQL(where_sql) + SQL(" ORDER BY t.{} {} LIMIT %s OFFSET %s").format(
            sort_column, SQL(sort_order)
        )
        with db._lock:
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


@app.get("/api/offices")
@require_permission(Permission.VIEW_TICKETS)
async def api_get_offices(request: Request):
    """Получить список уникальных адресов офисов из заявок."""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        offices = db.get_offices()
        return {"offices": offices}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets/{ticket_number}")
@require_permission(Permission.VIEW_TICKET_DETAIL)
async def api_get_ticket(ticket_number: str, request: Request = None):
    """Получить детали заявки, историю и изображения"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        # ─── Проверка прав доступа к офису заявки ───────────────
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

        history = db.get_ticket_history(ticket_number)
        # Фильтруем уже сохранённые changed_fields — удаляем поля, исключённые из отображения
        _history_excluded = HISTORY_EXCLUDED_FIELDS
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
                with db._lock:
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

        # Добавляем last_status и completed_by из ticket
        last_status = ticket.get('last_status')
        completed_by = ticket.get('completed_by')

        return {
            "ticket": ticket,
            "history": history,
            "images": images,
            "user_comments": user_comments,
            "comment_count": comment_count,
            "completed_at": completed_at,
            "last_status": last_status,
            "completed_by": completed_by
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
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error

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
            if field not in EDITABLE_TICKET_FIELDS:
                continue
            old_value = existing_ticket.get(field, '') or ''
            new_str = str(new_value).strip() if new_value else ''
            old_str = str(old_value).strip() if old_value else ''
            if old_str != new_str and new_str:
                changed_fields[field] = new_value

        if not changed_fields:
            return {"status": "ok", "message": "Нет изменений", "ticket": existing_ticket}

        # Исключаем поля, которые не должны попадать в историю изменений
        changed_fields = {k: v for k, v in changed_fields.items() if k not in HISTORY_EXCLUDED_FIELDS}

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
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error

        # ─── Защита от повторного выполнения ────────────────────────────
        if existing_ticket.get('status') == 'Выполнено':
            # Проверяем, есть ли completed_at в истории
            _already_completed = False
            try:
                with db._lock:
                    db.cursor.execute("""
                        SELECT 1 FROM ticket_history th
                        WHERE th.ticket_number = %s
                          AND (
                              th.changed_fields::jsonb @> '{"status": "Выполнено"}'::jsonb
                              OR th.status = 'Выполнено'
                          )
                        LIMIT 1
                    """, (ticket_number,))
                    _already_completed = db.cursor.fetchone() is not None
            except Exception:
                pass
            if _already_completed:
                logger.warning(
                    f"Попытка повторного выполнения заявки #{ticket_number} "
                    f"(текущий статус: {existing_ticket.get('status')})"
                )
                return JSONResponse(
                    {
                        "error": "Заявка уже выполнена",
                        "code": "ALREADY_COMPLETED",
                        "ticket_number": ticket_number,
                    },
                    status_code=409,
                )
        # ─── Конец защиты от повторного выполнения ───────────────────────

        now = datetime.now()
        # Получаем текущего пользователя для записи completed_by
        current_user = get_current_user(request)
        completed_by_username = current_user.username if current_user else 'unknown'

        # Сохраняем предыдущий статус в last_status перед изменением
        previous_status = existing_ticket.get('status', '')

        # Для истории сохраняем completed_at (в таблице ticket_history поле changed_fields — JSON)
        history_changed_fields = {"status": "Выполнено", "is_archived": False, "completed_at": now.isoformat()}
        # Для обновления таблицы tickets — статус, last_status, completed_by, completed_at
        changed_fields = {
            "status": "Выполнено",
            "is_archived": False,
            "last_status": previous_status,
            "completed_by": completed_by_username,
            "completed_at": now,
        }

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
                        ticket_image = image_manager.save_file(
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


@app.post("/api/tickets/{ticket_number}/uncomplete")
@require_permission(Permission.COMPLETE_TICKETS)
async def api_uncomplete_ticket(ticket_number: str, request: Request):
    """Отменить выполнение заявки (только для администраторов).
    Восстанавливает предыдущий статус из last_status, очищает completed_at и completed_by.
    """
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        # Проверяем права администратора
        current_user = get_current_user(request)
        if not current_user or current_user.role != UserRole.ADMIN:
            return JSONResponse(
                {"error": "Только администраторы могут отменять выполнение заявки"},
                status_code=403,
            )

        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error

        # Проверяем, что заявка выполнена
        if existing_ticket.get('status') != 'Выполнено':
            return JSONResponse(
                {"error": "Отменить выполнение можно только для заявок со статусом «Выполнено»"},
                status_code=400,
            )

        # Получаем предыдущий статус из last_status
        previous_status = existing_ticket.get('last_status')
        if not previous_status:
            # Если last_status не сохранён (старые заявки), используем статус по умолчанию
            previous_status = 'Новая заявка'

        now = datetime.now()
        username = current_user.username if current_user else 'unknown'

        # Обновляем заявку: восстанавливаем статус, очищаем completed_at и completed_by
        with db._lock:
            db.cursor.execute("""
                UPDATE tickets
                SET status = %s,
                    last_status = NULL,
                    completed_by = NULL,
                    completed_at = NULL
                WHERE ticket_number = %s
            """, (previous_status, ticket_number))
            db.connection.commit()

        # Создаём запись в истории с типом uncompleted
        from database.models import TicketHistoryRecord
        history_record = TicketHistoryRecord(
            ticket_number=ticket_number,
            received_date=now,
            email_hash=f"uncomplete_{now.timestamp()}",
            changed_fields={
                "status": previous_status,
                "action": "uncompleted",
                "description": "Администратор отменил выполнение заявки",
                "uncompleted_by": username,
            },
            subject=existing_ticket.get('subject'),
            inventory_number=existing_ticket.get('inventory_number'),
            printer_model=existing_ticket.get('printer_model'),
            office=existing_ticket.get('office'),
            cabinet=existing_ticket.get('cabinet'),
            component=existing_ticket.get('component'),
            status=previous_status,
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

        logger.info(
            f"Администратор {username} отменил выполнение заявки #{ticket_number}. "
            f"Статус восстановлен: {previous_status}"
        )

        updated_ticket = db.get_ticket(ticket_number)
        return {
            "status": "ok",
            "message": "Выполнение заявки отменено",
            "ticket": updated_ticket,
        }
    except Exception as e:
        logger.exception(f"Ошибка отмены выполнения заявки {ticket_number}")
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
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error

        with db._lock:
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
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error

        # При восстановлении сбрасываем флаг архива и убираем статус "В архив",
        # но сохраняем другие статусы (например, "Выполнено")
        new_status = existing_ticket.get('status')
        if new_status == 'В архив':
            new_status = None

        with db._lock:
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
    """Добавить заявку в список задач (AJAX-friendly)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse(
                {"error": "Заявка не найдена", "is_task": False},
                status_code=404,
            )
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error
        # Проверяем, не добавлена ли уже заявка (дубликат)
        already_task = db.is_task(ticket_number)
        if already_task:
            return JSONResponse(
                {
                    "status": "duplicate",
                    "is_task": True,
                    "message": "Заявка уже находится в списке задач",
                },
                status_code=409,
            )
        if db.add_task(ticket_number):
            return {
                "status": "ok",
                "is_task": True,
                "message": "Заявка добавлена в задачи",
            }
        return JSONResponse(
            {"error": "Не удалось добавить задачу", "is_task": False},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse({"error": str(e), "is_task": False}, status_code=500)


@app.delete("/api/tickets/{ticket_number}/task")
@require_permission(Permission.MANAGE_TASKS)
async def api_remove_task(ticket_number: str, request: Request):
    """Удалить заявку из списка задач (AJAX-friendly)"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse(
                {"error": "Заявка не найдена", "is_task": True},
                status_code=404,
            )
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error
        if db.remove_task(ticket_number):
            return {
                "status": "ok",
                "is_task": False,
                "message": "Заявка удалена из задач",
            }
        return JSONResponse(
            {"error": "Не удалось удалить задачу", "is_task": True},
            status_code=500,
        )
    except Exception as e:
        return JSONResponse({"error": str(e), "is_task": True}, status_code=500)


@app.get("/api/tickets/{ticket_number}/task")
@require_permission(Permission.VIEW_TICKET_DETAIL)
async def api_check_task(ticket_number: str, request: Request):
    """Проверить, находится ли заявка в списке задач"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    try:
        existing_ticket = db.get_ticket(ticket_number)
        if not existing_ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, existing_ticket)
        if access_error:
            return access_error
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
@require_permission(Permission.VIEW_TICKETS)
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
@require_permission(Permission.VIEW_TICKETS)
async def api_get_task_tickets(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
    sort_by: str = Query("last_updated_date"),
    sort_order: str = Query("desc"),
    office: Optional[str] = Query(None),
    month: Optional[str] = Query(None),
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

        # ─── Фильтрация по адресу офиса ──────────────────────────
        if office:
            where_clauses.append("t.office = %s")
            params.append(office)

        # ─── Фильтрация по месяцу выполнения ─────────────────────
        # Формат month: MM-YYYY (например, "01-2025" или "05-2026")
        if month:
            import re as re_month
            month_match = re_month.match(r'^(\d{2})-(\d{4})$', month)
            if month_match:
                month_num = month_match.group(1)
                year_num = month_match.group(2)
                where_clauses.append("t.status = 'Выполнено'")
                where_clauses.append(
                    "EXTRACT(MONTH FROM COALESCE("
                    "(SELECT th.received_date FROM ticket_history th "
                    "WHERE th.ticket_number = t.ticket_number "
                    "AND (th.changed_fields::jsonb @> '{\"status\": \"Выполнено\"}'::jsonb OR th.status = 'Выполнено') "
                    "ORDER BY th.received_date DESC LIMIT 1), "
                    "t.last_updated_date)) = %s"
                )
                params.append(int(month_num))
                where_clauses.append(
                    "EXTRACT(YEAR FROM COALESCE("
                    "(SELECT th.received_date FROM ticket_history th "
                    "WHERE th.ticket_number = t.ticket_number "
                    "AND (th.changed_fields::jsonb @> '{\"status\": \"Выполнено\"}'::jsonb OR th.status = 'Выполнено') "
                    "ORDER BY th.received_date DESC LIMIT 1), "
                    "t.last_updated_date)) = %s"
                )
                params.append(int(year_num))

        where_sql = " AND ".join(where_clauses)

        # Сначала получаем общее количество
        count_query = f"""
            SELECT COUNT(*) as total
            FROM tickets t
            INNER JOIN ticket_tasks tt ON t.ticket_number = tt.ticket_number
            WHERE {where_sql}
        """
        with db._lock:
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
        with db._lock:
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
@require_permission(Permission.UPLOAD_IMAGES)
async def api_upload_images(ticket_number: str, request: Request, files: List[UploadFile] = File(...)):
    """Загрузить одно или несколько изображений для заявки"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)
    if not image_manager:
        return JSONResponse({"error": "Менеджер изображений не инициализирован"}, status_code=503)

    loop = asyncio.get_running_loop()

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

        uploaded = []
        errors = []
        max_file_size = IMAGE_MAX_FILE_SIZE

        for file in files:
            filename = file.filename or 'unknown'
            try:
                if file.size is not None and file.size > max_file_size:
                    errors.append({
                        "file": filename,
                        "error": (
                            f"Файл слишком большой ({file.size / 1024 / 1024:.1f} МБ). "
                            "Максимум: 10 МБ"
                        ),
                    })
                    continue

                file_bytes = await file.read()
                if len(file_bytes) > max_file_size:
                    errors.append({
                        "file": filename,
                        "error": (
                            f"Файл слишком большой ({len(file_bytes) / 1024 / 1024:.1f} МБ). "
                            "Максимум: 10 МБ"
                        ),
                    })
                    continue

                mime_type = file.content_type or 'application/octet-stream'
                logger.info(
                    "Загрузка файла для #%s: %s (%s байт, %s)",
                    ticket_number,
                    filename,
                    len(file_bytes),
                    mime_type,
                )

                def _save_uploaded_file(
                    payload: bytes = file_bytes,
                    original_name: str = filename,
                    content_type: str = mime_type,
                ) -> TicketImage:
                    return image_manager.save_file(
                        ticket_number=ticket_number,
                        file_bytes=payload,
                        original_filename=original_name,
                        mime_type=content_type,
                    )

                ticket_image = await loop.run_in_executor(_upload_executor, _save_uploaded_file)
                del file_bytes
                gc.collect()

                image_id = db.save_image_record(ticket_image)
                if image_id:
                    uploaded.append({
                        "id": image_id,
                        "original_filename": ticket_image.original_filename,
                        "file_size": ticket_image.file_size,
                        "mime_type": ticket_image.mime_type,
                    })
                    logger.info("Загружено изображение #%s для заявки %s", image_id, ticket_number)
                else:
                    logger.error(
                        "Не удалось сохранить запись в БД для файла %s (заявка %s)",
                        filename,
                        ticket_number,
                    )
                    errors.append({"file": filename, "error": "Не удалось сохранить запись в БД"})
            except ImageValidationError as exc:
                errors.append({"file": filename, "error": str(exc)})
            except Exception as exc:
                logger.exception("Ошибка загрузки файла %s для заявки %s", filename, ticket_number)
                errors.append({"file": filename, "error": f"Внутренняя ошибка: {exc}"})
            finally:
                gc.collect()

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
@require_permission(Permission.VIEW_TICKET_DETAIL)
async def api_get_ticket_images(ticket_number: str, request: Request):
    """Получить список изображений заявки"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

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
@require_permission(Permission.VIEW_TICKET_DETAIL)
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
        ticket = db.get_ticket(image_record['ticket_number'])
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

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

        # Изображения и PDF должны открываться в браузере для preview/lightbox.
        filename_part = f'filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(filename)}'
        disposition_type = 'inline' if ext in ('.jpg', '.jpeg', '.png', '.gif', '.pdf') else 'attachment'
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
@require_permission(Permission.VIEW_TICKET_DETAIL)
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
        ticket = db.get_ticket(image_record['ticket_number'])
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

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
        ticket = db.get_ticket(image_record['ticket_number'])
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)
        access_error = _require_ticket_access(request, ticket)
        if access_error:
            return access_error

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
@require_permission(Permission.VIEW_TICKETS)
async def api_get_statistics(request: Request):
    """Получить статистику"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        stats = db.get_statistics()
        return stats
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/statuses")
@require_permission(Permission.VIEW_TICKETS)
async def api_get_statuses(request: Request):
    """Получить список уникальных статусов"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        with db._lock:
            db.cursor.execute(
                "SELECT DISTINCT status FROM tickets WHERE status IS NOT NULL ORDER BY status"
            )
            rows = db.cursor.fetchall()
        return {"statuses": [r["status"] for r in rows]}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── Фоновая перестройка БД с прогрессом ──────────────────────────

def _run_rebuild_background(since_date_override: Optional[datetime] = None):
    """Фоновая задача перестройки БД (выполняется в отдельном потоке)"""
    global _rebuild_progress
    try:
        config = load_config()

        # --- Проверяем checkpoint для инкрементального обновления ---
        checkpoint = None if since_date_override else db.get_checkpoint()
        use_incremental = since_date_override is not None or checkpoint is not None
        since_date = None

        if since_date_override is not None:
            since_date = since_date_override
            logger.info(f"Инкрементальное обновление с указанной даты: {since_date}")
            _rebuild_progress["message"] = (
                f"Обновление с {since_date.strftime('%d.%m.%Y')}…"
            )
        elif use_incremental:
            since_date = compute_imap_since_date(checkpoint['checkpoint_date'])
            logger.info(
                "Инкрементальное обновление: checkpoint=%s, IMAP SINCE=%s, "
                "ранее обработано %s писем",
                checkpoint['checkpoint_date'],
                since_date,
                checkpoint['processed_count'],
            )
            _rebuild_progress["message"] = (
                f"Инкрементальное обновление (с {since_date.strftime('%d.%m.%Y')})…"
            )
        else:
            _rebuild_progress["message"] = "Полная перестройка БД…"

        # Шаг 1: Сохраняем пользовательские статусы только для полной перестройки.
        # В инкрементальном режиме восстановление старого статуса после обработки
        # новых писем откатывает актуальный статус из письма.
        saved_statuses = {}
        if not use_incremental:
            try:
                with db._lock:
                    db.cursor.execute(
                        """SELECT ticket_number, status, is_archived, is_active,
                                  last_status, completed_by, completed_at
                           FROM tickets"""
                    )
                    saved_rows = db.cursor.fetchall()
                for row in saved_rows:
                    saved_statuses[row['ticket_number']] = {
                        'status': row['status'],
                        'is_archived': row['is_archived'],
                        'is_active': row['is_active'],
                        'last_status': row.get('last_status'),
                        'completed_by': row.get('completed_by'),
                        'completed_at': row.get('completed_at'),
                    }
                logger.info(f"Сохранено статусов для {len(saved_statuses)} существующих заявок")
            except Exception:
                try:
                    db.connection.rollback()
                except Exception:
                    pass
        else:
            logger.info("Инкрементальный режим: восстановление старых статусов отключено")

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
        if use_incremental and since_date and not email_ids:
            fallback_since = compute_imap_since_date(since_date)
            if fallback_since != since_date:
                logger.warning(
                    "IMAP-поиск с since=%s вернул 0 писем, повтор с since=%s",
                    since_date,
                    fallback_since,
                )
                email_ids = email_client.search_emails(
                    subject_filters=config['parser'].subject_filters,
                    from_filter=config['parser'].from_filter,
                    since_date=fallback_since,
                )

        if not email_ids:
            email_client.close()
            logger.warning(
                "IMAP не вернул письма в инкрементальном режиме — checkpoint не изменён"
            )
            _rebuild_progress.update({
                "running": False,
                "total": 0,
                "processed": 0,
                "errors": 0,
                "skipped": 0,
                "status": "completed",
                "message": "Новых писем не найдено",
                "result": {
                    "processed": 0,
                    "errors": 0,
                    "skipped": 0,
                    "no_emails_found": True,
                }
            })
            return

        total = len(email_ids)
        _rebuild_progress["total"] = total
        _rebuild_progress["message"] = f"Обработка писем — 0 из {total}"

        def _update_progress(idx, total_count, processed_count, error_count, skipped_count):
            _rebuild_progress.update({
                "processed": processed_count,
                "errors": error_count,
                "skipped": skipped_count,
                "message": f"Обработка писем — {idx} из {total_count}",
            })

        batch_result = process_email_messages(
            email_client,
            email_parser,
            ticket_processor,
            email_ids,
            progress_callback=_update_progress,
        )
        processed = batch_result['processed']
        errors = batch_result['errors']
        skipped = batch_result['skipped']
        skip_details = batch_result['skip_details']
        received_dates = batch_result['received_dates']

        email_client.close()

        # Шаг 4: Восстанавливаем ручные статусы только после полной перестройки.
        # Ручное "Выполнено" сохраняется, только если после него не было новых писем.
        restored_count = 0
        if not use_incremental:
            for ticket_number, saved in saved_statuses.items():
                current_ticket = db.get_ticket(ticket_number)
                if not current_ticket:
                    continue

                updates = {}
                completed_at = saved.get('completed_at')
                last_email_date = current_ticket.get('last_updated_date')

                if (
                    saved.get('status') == 'Выполнено'
                    and completed_at
                    and (not last_email_date or last_email_date <= completed_at)
                ):
                    updates['status'] = 'Выполнено'
                    updates['last_status'] = saved.get('last_status')
                    updates['completed_by'] = saved.get('completed_by')
                    updates['completed_at'] = completed_at

                if saved.get('is_archived') is not None:
                    updates['is_archived'] = saved['is_archived']
                if saved.get('is_active') is not None:
                    updates['is_active'] = saved['is_active']

                if updates:
                    db.update_ticket(ticket_number, updates)
                    restored_count += 1

            logger.info(f"Восстановлено ручных статусов для {restored_count} заявок")
        else:
            logger.info("Инкрементальный режим: восстановление статусов пропущено")

        # Шаг 5: Сохраняем checkpoint только по датам обработанных писем
        try:
            fallback_checkpoint = checkpoint['checkpoint_date'] if checkpoint else None
            new_checkpoint_date = compute_checkpoint_date(
                received_dates,
                fallback=fallback_checkpoint,
            )
            if new_checkpoint_date and processed > 0:
                db.save_checkpoint(new_checkpoint_date, processed)
                logger.info(
                    "Сохранён checkpoint: %s, обработано писем: %s",
                    new_checkpoint_date,
                    processed,
                )
            elif processed == 0:
                logger.info("Checkpoint не изменён: новых писем не обработано")
        except Exception as e:
            logger.error(f"Ошибка сохранения checkpoint: {e}")

        # Шаг 6: Верификация
        integrity_result = db.verify_data_integrity()

        _rebuild_progress.update({
            "running": False,
            "status": "completed",
            "skipped": skipped,
            "message": f"Обработано: {processed}, Пропущено: {skipped}, Ошибок: {errors}",
            "result": {
                "processed": processed,
                "errors": errors,
                "skipped": skipped,
                "skip_details": skip_details[:20],
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
@require_permission(Permission.REBUILD_DATA)
async def api_rebuild_start(request: Request):
    """Запустить фоновую перестройку БД с отслеживанием прогресса"""
    global _rebuild_progress
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    if _rebuild_progress["running"]:
        return JSONResponse({
            "error": "Перестройка уже выполняется",
            "status": "already_running",
            "progress": dict(_rebuild_progress),
        }, status_code=409)

    since_date = None
    try:
        body = await request.json()
    except Exception:
        body = {}

    raw_since_date = (body.get("since_date") or "").strip() if isinstance(body, dict) else ""
    if raw_since_date:
        try:
            since_date = datetime.strptime(raw_since_date, "%Y-%m-%d")
        except ValueError:
            return JSONResponse(
                {"error": "Некорректная дата. Используйте формат YYYY-MM-DD."},
                status_code=400,
            )

        if since_date.date() > datetime.now().date():
            return JSONResponse(
                {"error": "Дата начала обновления не может быть в будущем."},
                status_code=400,
            )

    # Сбрасываем прогресс
    _rebuild_progress.update({
        "running": True,
        "total": 0,
        "processed": 0,
        "errors": 0,
        "skipped": 0,
        "message": (
            f"Подготовка к обработке с {since_date.strftime('%d.%m.%Y')}…"
            if since_date else
            "Подготовка к обработке…"
        ),
        "status": "running",
        "result": None,
        "since_date": raw_since_date or None,
    })

    # Запускаем в отдельном потоке, чтобы не блокировать event loop
    thread = threading.Thread(
        target=_run_rebuild_background,
        args=(since_date,),
        daemon=True,
    )
    thread.start()

    return {
        "status": "started",
        "message": "Перестройка запущена",
        "since_date": raw_since_date or None,
    }


@app.get("/api/rebuild/status")
@require_permission(Permission.REBUILD_DATA)
async def api_rebuild_status(request: Request):
    """Получить текущий статус фоновой перестройки БД"""
    return dict(_rebuild_progress)


@app.post("/api/rebuild")
@require_permission(Permission.REBUILD_DATA)
async def api_rebuild(request: Request):
    """Совместимость со старым API: запускает безопасный фоновый rebuild."""
    return await api_rebuild_start(request)


# ─── Администрирование БД (только admin) ───────────────────────────

@app.get("/api/admin/db/export")
@require_role("admin")
async def api_admin_db_export(request: Request):
    """Выгрузка дампа PostgreSQL (только для администратора)."""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    config = load_config()
    try:
        dump_bytes = create_database_dump(config['database'])
    except DatabaseBackupError as exc:
        logger.exception("Ошибка выгрузки дампа БД")
        return JSONResponse({"error": str(exc)}, status_code=500)

    filename = build_dump_filename(config['database'].database)
    return Response(
        content=dump_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-store",
        },
    )


@app.post("/api/admin/db/import")
@require_role("admin")
async def api_admin_db_import(request: Request, file: UploadFile = File(...)):
    """Загрузка дампа PostgreSQL из файла (только для администратора)."""
    global db, auth_db

    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    if _rebuild_progress["running"]:
        return JSONResponse(
            {"error": "Нельзя загрузить дамп во время перестройки данных"},
            status_code=409,
        )

    filename = (file.filename or "").lower()
    if not filename.endswith('.dump'):
        return JSONResponse(
            {"error": "Поддерживаются только файлы PostgreSQL custom dump (.dump)"},
            status_code=400,
        )

    content = await file.read()
    if not content:
        return JSONResponse({"error": "Файл дампа пуст"}, status_code=400)

    config = load_config()
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix='.dump', delete=False) as tmp_file:
            temp_path = tmp_file.name
            tmp_file.write(content)

        db.close()
        restore_database_dump(config['database'], temp_path)

        if not db.connect():
            return JSONResponse({"error": "Не удалось переподключиться к БД"}, status_code=500)

        auth_db = AuthDBManager(db)
        auth_db.create_tables()
        auth_db.sync_all_users_permissions()

        return {
            "status": "ok",
            "message": "База данных успешно восстановлена из дампа",
            "filename": file.filename,
        }
    except DatabaseBackupError as exc:
        logger.exception("Ошибка восстановления дампа БД")
        if not db.connection:
            db.connect()
        return JSONResponse({"error": str(exc)}, status_code=500)
    except Exception as exc:
        logger.exception("Непредвиденная ошибка восстановления дампа БД")
        if not db.connection:
            db.connect()
        return JSONResponse({"error": str(exc)}, status_code=500)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)


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
    db_ok = db is not None and hasattr(db, 'connection') and db.connection is not None
    try:
        if db_ok:
            with db._lock:
                db_ok = db.fetch_one("SELECT 1") is not None
    except Exception:
        db_ok = False

    return {
        "status": "ok" if db_ok else "degraded",
        "service": "gkuop-web",
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected" if db_ok else "disconnected",
    }


@app.get("/api/crash-reports")
@require_permission(Permission.VIEW_LOGS)
async def api_crash_reports(request: Request, limit: int = Query(10, ge=1, le=100)):
    """Получить список последних crash-отчётов."""
    reports = list_crash_reports(limit=limit)
    return {"crash_reports": reports, "total": len(reports)}


@app.get("/api/crash-reports/{crash_id}")
@require_permission(Permission.VIEW_LOGS)
async def api_crash_report_detail(crash_id: str, request: Request):
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
@require_permission(Permission.VIEW_LOGS)
async def api_monitor_status(request: Request):
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
