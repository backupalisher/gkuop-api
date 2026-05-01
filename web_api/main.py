"""
FastAPI приложение — точки входа API и HTML-рендеринг
"""
import os
import sys
import re
import logging
from pathlib import Path
from datetime import datetime
from contextlib import asynccontextmanager
from typing import List, Optional

logger = logging.getLogger(__name__)

# Добавляем корень проекта в sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request, Query, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from psycopg2.sql import SQL, Identifier

from database.db_manager import DatabaseManager
from database.models import TicketImage
from config.settings import load_config
from email_processor.email_client import EmailClient
from email_processor.email_parser import EmailParser
from email_processor.ticket_processor import TicketProcessor
from services.image_manager import ImageManager, ImageValidationError

load_dotenv()

# Глобальные экземпляры
db: DatabaseManager = None
image_manager: ImageManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация и завершение работы приложения"""
    global db, image_manager
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
    image_manager = ImageManager(upload_dir='uploads')
    print("✓ ImageManager инициализирован")
    yield
    if db:
        db.close()


app = FastAPI(
    title="ГКУ ОП Заявки",
    description="Веб-интерфейс для просмотра заявок на оборудование",
    version="1.0.0",
    lifespan=lifespan,
)

# Шаблоны
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Статические файлы (CSS)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ─── API эндпоинты ────────────────────────────────────────────────


@app.post("/api/auth/login")
async def api_login(request: Request):
    """Аутентификация по хешированным учётным данным из переменных окружения"""
    try:
        body = await request.json()
        login = body.get("login", "").strip()
        password = body.get("password", "").strip()

        login_hash_expected = os.getenv("WEB_USER_HASH")
        password_hash_expected = os.getenv("WEB_PASSWORD_HASH")
        if not login_hash_expected or not password_hash_expected:
            logger.critical("WEB_USER_HASH или WEB_PASSWORD_HASH не заданы в .env")
            return JSONResponse(
                {"status": "error", "message": "Ошибка конфигурации сервера"},
                status_code=500
            )

        # Хешируем введённые данные и сравниваем
        import hashlib
        login_hash = hashlib.sha256(login.encode()).hexdigest()
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        if login_hash == login_hash_expected and password_hash == password_hash_expected:
            return {"status": "ok", "username": login}
        return JSONResponse(
            {"status": "error", "message": "Неверный логин или пароль"},
            status_code=401
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets")
async def api_get_tickets(
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
                   ) THEN TRUE ELSE FALSE END AS has_files
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

        return {
            "tickets": [dict(r) for r in rows],
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, (total + per_page - 1) // per_page),
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/api/tickets/{ticket_number}")
async def api_get_ticket(ticket_number: str):
    """Получить детали заявки, историю и изображения"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

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

        return {"ticket": ticket, "history": history, "images": images}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.put("/api/tickets/{ticket_number}")
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
        body = await request.json()

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

        changed_fields = {"status": "Выполнено", "is_archived": False}
        now = datetime.now()

        # Сохраняем в историю
        from database.models import TicketHistoryRecord
        history_record = TicketHistoryRecord(
            ticket_number=ticket_number,
            received_date=now,
            email_hash=f"manual_complete_{now.timestamp()}",
            changed_fields=changed_fields,
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
async def api_archive_ticket(ticket_number: str):
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
async def api_restore_ticket(ticket_number: str):
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


# ─── API эндпоинты для изображений ──────────────────────────────────


@app.post("/api/tickets/{ticket_number}/images")
async def api_upload_images(ticket_number: str, files: List[UploadFile] = File(...)):
    """Загрузить одно или несколько изображений для заявки"""
    if not db:
        return JSONResponse({"error": "БД не подключена"}, status_code=503)

    try:
        # Проверяем существование заявки
        ticket = db.get_ticket(ticket_number)
        if not ticket:
            return JSONResponse({"error": "Заявка не найдена"}, status_code=404)

        uploaded = []
        errors = []

        for file in files:
            try:
                file_bytes = await file.read()
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

        # Для изображений — inline, для документов — attachment
        if ext in ('.jpg', '.jpeg', '.png', '.gif'):
            disposition = f'inline; filename="{filename}"'
        else:
            disposition = f'attachment; filename="{filename}"'

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
async def api_delete_image(image_id: int):
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
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/tickets/{ticket_number}", response_class=HTMLResponse)
async def ticket_detail(request: Request, ticket_number: str):
    """Страница деталей заявки"""
    return templates.TemplateResponse(
        "ticket_detail.html",
        {"request": request, "ticket_number": ticket_number},
    )


# ─── Запуск ────────────────────────────────────────────────────────


def main():
    import uvicorn
    port = int(os.getenv("WEB_PORT", "8000"))
    host = os.getenv("WEB_HOST", "0.0.0.0")
    uvicorn.run("web_api.main:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    main()
