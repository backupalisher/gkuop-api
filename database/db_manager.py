"""
Менеджер базы данных
"""
import logging
import time
import psycopg2
from psycopg2 import pool as psycopg2_pool
from psycopg2.extras import RealDictCursor
from psycopg2.sql import SQL, Identifier
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime
from contextlib import contextmanager
from functools import wraps

from .models import Ticket, TicketComment, TicketHistoryRecord, TicketImage, UserComment

logger = logging.getLogger(__name__)

# Коды ошибок PostgreSQL для временных сбоев, при которых допустим retry
RETRYABLE_PG_CODES = {'40001', '40P01', '55P03', '53000', '53100', '53200', '53300', '53400'}


def _retry_on_db_error(
    max_attempts: int = 3,
    base_delay: float = 0.5,
    retryable_codes: set = None,
):
    """
    Декоратор для повторных попыток выполнения методов БД при временных ошибках.

    Args:
        max_attempts: Максимальное количество попыток.
        base_delay: Базовая задержка между попытками (сек), удваивается после каждой.
        retryable_codes: Множество кодов SQLSTATE, при которых выполняется retry.
    """
    if retryable_codes is None:
        retryable_codes = RETRYABLE_PG_CODES

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(self, *args, **kwargs)
                except psycopg2.Error as e:
                    pgcode = getattr(e, 'pgcode', '')
                    if pgcode in retryable_codes and attempt < max_attempts:
                        delay = base_delay * (2 ** (attempt - 1))
                        logger.warning(
                            f"[RETRY] {func.__name__}: попытка {attempt}/{max_attempts} "
                            f"не удалась (pgcode={pgcode}), повтор через {delay:.1f}с: {e}"
                        )
                        time.sleep(delay)
                        last_exception = e
                    else:
                        raise
                except Exception:
                    raise
            raise last_exception
        return wrapper
    return decorator


class DatabaseManager:
    """Управление подключением и операциями с БД"""

    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
        self.cursor = None
        self._pool: Optional[psycopg2_pool.ThreadedConnectionPool] = None
        self._tables_initialized = False

        self._pool_min = config.get('pool_min_connections', 1)
        self._pool_max = config.get('pool_max_connections', 10)
        self._retry_max = config.get('retry_max_attempts', 3)
        self._retry_delay = config.get('retry_base_delay', 0.5)
        self._slow_query_threshold = config.get('slow_query_threshold_ms', 500.0)

    # ─── Пул соединений ──────────────────────────────────────────────

    def _init_pool(self):
        """Инициализация пула соединений (ThreadedConnectionPool)."""
        if self._pool is not None:
            return
        try:
            pool_config = {
                k: v for k, v in self.config.items()
                if k not in (
                    'pool_min_connections', 'pool_max_connections',
                    'retry_max_attempts', 'retry_base_delay',
                    'slow_query_threshold_ms',
                )
            }
            self._pool = psycopg2_pool.ThreadedConnectionPool(
                self._pool_min, self._pool_max, **pool_config,
            )
            logger.info(
                f"Пул соединений инициализирован: min={self._pool_min}, max={self._pool_max}"
            )
        except Exception as e:
            logger.error(f"Ошибка инициализации пула соединений: {e}")
            raise

    @contextmanager
    def _get_connection(self):
        """Контекстный менеджер для получения соединения из пула."""
        if self._pool is None:
            self._init_pool()
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn is not None and self._pool is not None:
                self._pool.putconn(conn)

    # ─── Инициализация схемы (однократная) ──────────────────────────

    def initialize_schema(self):
        """
        Однократное создание/проверка схемы БД и восстановление sequences.
        Должен вызываться при старте приложения, а не в каждом запросе.
        """
        if self._tables_initialized:
            return
        with self._get_connection() as conn:
            old_autocommit = conn.autocommit
            try:
                conn.set_session(autocommit=True)
                cur = conn.cursor(cursor_factory=RealDictCursor)

                # Миграция: добавляем колонку is_archived, если её нет
                try:
                    cur.execute(
                        "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE"
                    )
                except Exception:
                    pass

                for query in self._get_create_table_queries():
                    cur.execute(query)

                self._repair_sequences(conn, cur)

                cur.close()
                conn.set_session(autocommit=old_autocommit)
                self._tables_initialized = True
                logger.info("Схема БД инициализирована, sequences восстановлены")
            except Exception:
                conn.set_session(autocommit=old_autocommit)
                raise

    @staticmethod
    def _get_create_table_queries() -> List[str]:
        """Возвращает список SQL-запросов для создания таблиц."""
        return [
            """
            CREATE TABLE IF NOT EXISTS tickets
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) UNIQUE NOT NULL,
                subject TEXT,
                inventory_number VARCHAR(50),
                printer_model VARCHAR(200),
                office TEXT,
                cabinet VARCHAR(20),
                component VARCHAR(200),
                status VARCHAR(100),
                priority VARCHAR(50),
                assigned_to TEXT,
                author_name VARCHAR(200),
                contact_phone VARCHAR(20),
                department TEXT,
                position TEXT,
                current_note TEXT,
                required_action TEXT,
                cause TEXT,
                fault_description TEXT,
                work_done TEXT,
                tech_conclusion TEXT,
                soglasovano_line TEXT,
                first_received_date TIMESTAMP,
                last_updated_date TIMESTAMP,
                is_active BOOLEAN DEFAULT TRUE,
                is_archived BOOLEAN DEFAULT FALSE,
                email_hash VARCHAR(64) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_comments
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) REFERENCES tickets(ticket_number) ON DELETE CASCADE,
                comment_text TEXT,
                changed_fields JSONB,
                status_before VARCHAR(100),
                status_after VARCHAR(100),
                received_date TIMESTAMP,
                email_hash VARCHAR(64) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_history
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) REFERENCES tickets(ticket_number) ON DELETE CASCADE,
                received_date TIMESTAMP,
                email_hash VARCHAR(64) UNIQUE,
                changed_fields JSONB,
                subject TEXT, inventory_number VARCHAR(50), printer_model VARCHAR(200),
                office TEXT, cabinet VARCHAR(20), component VARCHAR(200),
                status VARCHAR(100), priority VARCHAR(50), assigned_to TEXT,
                author_name VARCHAR(200), contact_phone VARCHAR(20),
                department TEXT, position TEXT, current_note TEXT,
                required_action TEXT, cause TEXT, fault_description TEXT,
                work_done TEXT, tech_conclusion TEXT, soglasovano_line TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_ticket_number ON tickets(ticket_number);
            CREATE INDEX IF NOT EXISTS idx_inventory_number ON tickets(inventory_number);
            CREATE INDEX IF NOT EXISTS idx_ticket_status ON tickets(status);
            CREATE INDEX IF NOT EXISTS idx_comments_ticket ON ticket_comments(ticket_number);
            CREATE INDEX IF NOT EXISTS idx_ticket_active ON tickets(is_active);
            CREATE INDEX IF NOT EXISTS idx_history_ticket ON ticket_history(ticket_number);
            CREATE INDEX IF NOT EXISTS idx_history_date ON ticket_history(received_date);
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_tasks
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) UNIQUE NOT NULL REFERENCES tickets(ticket_number) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_ticket ON ticket_tasks(ticket_number);
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_images
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) REFERENCES tickets(ticket_number) ON DELETE CASCADE,
                file_path TEXT NOT NULL,
                original_filename VARCHAR(500) NOT NULL,
                mime_type VARCHAR(50) NOT NULL,
                file_size INTEGER NOT NULL,
                thumbnail_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_deleted BOOLEAN DEFAULT FALSE
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_images_ticket ON ticket_images(ticket_number);
            """,
            """
            CREATE TABLE IF NOT EXISTS user_comments
            (
                id SERIAL PRIMARY KEY,
                ticket_number VARCHAR(20) REFERENCES tickets(ticket_number) ON DELETE CASCADE,
                author_username VARCHAR(100) NOT NULL,
                author_name VARCHAR(200) NOT NULL,
                comment_text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_user_comments_ticket ON user_comments(ticket_number);
            CREATE INDEX IF NOT EXISTS idx_user_comments_created ON user_comments(created_at);
            """,
            """
            CREATE TABLE IF NOT EXISTS rebuild_checkpoint
            (
                id SERIAL PRIMARY KEY,
                checkpoint_date TIMESTAMP NOT NULL,
                processed_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """,
        ]

    # ─── Восстановление sequences ────────────────────────────────────

    @staticmethod
    def _repair_sequences(conn, cur):
        """
        Восстанавливает все последовательности (sequences) для SERIAL/id-колонок.
        Выполняется однократно после инициализации схемы.
        """
        cur.execute("""
            SELECT
                s.relname AS sequence_name,
                t.relname AS table_name,
                a.attname AS column_name
            FROM pg_class s
            JOIN pg_depend d ON d.objid = s.oid
            JOIN pg_class t ON t.oid = d.refobjid
            JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = d.refobjsubid
            WHERE s.relkind = 'S'
              AND d.deptype = 'a'
              AND t.relname IN (
                  'tickets', 'ticket_comments', 'ticket_history',
                  'ticket_tasks', 'ticket_images', 'user_comments', 'rebuild_checkpoint',
                  'users', 'permissions', 'user_permissions', 'user_office_permissions'
              )
        """)
        sequences = cur.fetchall()
        for seq in sequences:
            seq_name = seq['sequence_name']
            table_name = seq['table_name']
            column_name = seq['column_name']
            try:
                cur.execute(
                    SQL("SELECT setval({seq}, COALESCE((SELECT MAX({col}) FROM {tbl}), 1), false)").format(
                        seq=SQL(seq_name), col=Identifier(column_name), tbl=Identifier(table_name),
                    )
                )
                logger.debug(f"Sequence {seq_name} восстановлен по MAX({column_name}) из {table_name}")
            except Exception as e:
                logger.warning(f"Не удалось восстановить sequence {seq_name}: {e}")

    # ─── Подключение (legacy, для обратной совместимости) ────────────

    def connect(self) -> bool:
        """
        Подключение к базе данных (legacy).
        Создаёт одно соединение и инициализирует схему.
        Сохранено для обратной совместимости с init_db.py, seed_admin.py и main.py.
        """
        try:
            self.connection = psycopg2.connect(**{
                k: v for k, v in self.config.items()
                if k not in (
                    'pool_min_connections', 'pool_max_connections',
                    'retry_max_attempts', 'retry_base_delay',
                    'slow_query_threshold_ms',
                )
            })
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            self.initialize_schema()
            print("✓ Подключено к PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения к БД: {e}")
            return False

    # ─── Вспомогательные методы для логирования запросов ────────────

    def _log_query(self, query: str, params: tuple = None, duration_ms: float = 0.0, rows_count: int = 0):
        """Логирование выполненного SQL-запроса."""
        log_query = query.strip().replace('\n', ' ').replace('\r', ' ')
        if duration_ms > self._slow_query_threshold:
            logger.warning(
                f"[SLOW QUERY] {duration_ms:.1f}ms | rows={rows_count} | {log_query[:500]}"
            )
        else:
            logger.debug(
                f"[DB] {duration_ms:.1f}ms | rows={rows_count} | {log_query[:300]}"
            )

    # ─── Методы для работы с заявками ───────────────────────────────

    def get_checkpoint(self) -> Optional[Dict]:
        """Получить последнюю контрольную точку перестройки БД"""
        try:
            self.cursor.execute(
                "SELECT checkpoint_date, processed_count FROM rebuild_checkpoint ORDER BY id DESC LIMIT 1"
            )
            row = self.cursor.fetchone()
            if row:
                return {
                    'checkpoint_date': row['checkpoint_date'],
                    'processed_count': row['processed_count'],
                }
            return None
        except Exception:
            return None

    def save_checkpoint(self, checkpoint_date: datetime, processed_count: int):
        """Сохранить новую контрольную точку перестройки БД"""
        try:
            self.cursor.execute(
                "INSERT INTO rebuild_checkpoint (checkpoint_date, processed_count) VALUES (%s, %s)",
                (checkpoint_date, processed_count)
            )
            self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка сохранения checkpoint: {e}")

    def ticket_exists(self, ticket_number: str) -> bool:
        """Проверка существования заявки"""
        self.cursor.execute(
            "SELECT id FROM tickets WHERE ticket_number = %s", (ticket_number,)
        )
        return self.cursor.fetchone() is not None

    def get_ticket(self, ticket_number: str) -> Optional[Dict]:
        """Получение заявки по номеру"""
        self.cursor.execute(
            "SELECT * FROM tickets WHERE ticket_number = %s", (ticket_number,)
        )
        row = self.cursor.fetchone()
        return dict(row) if row else None

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def save_ticket(self, ticket: Ticket) -> bool:
        """Сохранение новой заявки"""
        try:
            self.cursor.execute(
                "SELECT id FROM tickets WHERE email_hash = %s", (ticket.email_hash,)
            )
            if self.cursor.fetchone():
                return True

            query = """
                INSERT INTO tickets (ticket_number, subject, inventory_number, printer_model,
                                     office, cabinet, component, status, priority, assigned_to,
                                     author_name, contact_phone, department, position, current_note,
                                     required_action, cause, fault_description, work_done, tech_conclusion,
                                     soglasovano_line,
                                     first_received_date, last_updated_date, email_hash, is_active)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            self.cursor.execute(query, ticket.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result is not None
        except Exception as e:
            print(f"Ошибка сохранения заявки: {e}")
            self.connection.rollback()
            return False

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def update_ticket(self, ticket_number: str, updates: Dict, last_updated_date: datetime = None) -> bool:
        """Обновление существующей заявки"""
        try:
            set_parts = [SQL("{} = %s").format(Identifier(key)) for key in updates.keys()]
            if last_updated_date is not None:
                set_parts.append(SQL("last_updated_date = %s"))
                values = list(updates.values()) + [last_updated_date, ticket_number]
            else:
                values = list(updates.values()) + [ticket_number]

            set_clause = SQL(", ").join(set_parts)
            query = SQL("UPDATE tickets SET {set_clause} WHERE ticket_number = %s").format(set_clause=set_clause)
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка обновления заявки: {e}")
            self.connection.rollback()
            return False

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def save_comment(self, comment: TicketComment) -> bool:
        """Сохранение комментария"""
        try:
            query = """
                INSERT INTO ticket_comments (ticket_number, comment_text, changed_fields,
                                             status_before, status_after, received_date, email_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email_hash) DO NOTHING
                RETURNING id
            """
            self.cursor.execute(query, comment.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result is not None
        except Exception as e:
            print(f"Ошибка сохранения комментария: {e}")
            self.connection.rollback()
            return False

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def save_history_record(self, record: TicketHistoryRecord) -> bool:
        """Сохранение записи хронологии"""
        try:
            query = """
                INSERT INTO ticket_history (
                    ticket_number, received_date, email_hash, changed_fields,
                    subject, inventory_number, printer_model, office, cabinet, component,
                    status, priority, assigned_to, author_name, contact_phone,
                    department, position, current_note, required_action, cause,
                    fault_description, work_done, tech_conclusion, soglasovano_line
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                          %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (email_hash) DO NOTHING
                RETURNING id
            """
            self.cursor.execute(query, record.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result is not None
        except Exception as e:
            print(f"Ошибка сохранения записи истории: {e}")
            self.connection.rollback()
            return False

    def get_ticket_history(self, ticket_number: str) -> List[Dict]:
        """Получение хронологии заявки"""
        self.cursor.execute(
            "SELECT * FROM ticket_history WHERE ticket_number = %s ORDER BY received_date ASC",
            (ticket_number,)
        )
        history_rows = self.cursor.fetchall()

        self.cursor.execute(
            """SELECT comment_text, changed_fields, status_before, status_after,
                      received_date, created_at
               FROM ticket_comments WHERE ticket_number = %s ORDER BY received_date ASC""",
            (ticket_number,)
        )
        comment_rows = self.cursor.fetchall()

        result = []
        for row in history_rows:
            changed_fields = row.get('changed_fields')
            if changed_fields and isinstance(changed_fields, dict):
                changes = dict(changed_fields)
            else:
                changes = {}
                _excluded = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}
                for field in ['subject', 'inventory_number', 'printer_model', 'office', 'cabinet',
                              'component', 'status', 'priority', 'assigned_to', 'author_name',
                              'contact_phone', 'department', 'position', 'current_note',
                              'required_action', 'cause', 'fault_description', 'work_done',
                              'tech_conclusion', 'soglasovano_line']:
                    if field in _excluded:
                        continue
                    val = row.get(field)
                    if val:
                        changes[field] = val
            result.append({
                'type': 'snapshot', 'date': row['received_date'],
                'created_at': row['created_at'], 'changed_fields': changes,
            })

        for row in comment_rows:
            result.append({
                'type': 'comment', 'comment': row['comment_text'],
                'changes': row['changed_fields'],
                'status_before': row['status_before'], 'status_after': row['status_after'],
                'date': row['received_date'], 'created_at': row['created_at'],
            })

        result.sort(key=lambda x: x.get('date') or x.get('created_at') or datetime.min)
        return result

    def get_last_history_record(self, ticket_number: str) -> Optional[Dict]:
        """Получение последней записи хронологии для заявки"""
        self.cursor.execute(
            "SELECT changed_fields FROM ticket_history WHERE ticket_number = %s AND changed_fields IS NOT NULL ORDER BY received_date DESC LIMIT 1",
            (ticket_number,)
        )
        row = self.cursor.fetchone()
        if row:
            cf = row['changed_fields']
            if cf and isinstance(cf, dict):
                return {'changed_fields': dict(cf)}
        return None

    def get_statistics(self) -> Dict:
        """Получение статистики по заявкам"""
        self.cursor.execute("""
            SELECT COUNT(*) as total,
                   COUNT(CASE WHEN is_active = true THEN 1 END) as active,
                   COUNT(CASE WHEN status = 'В работе' THEN 1 END) as in_progress,
                   COUNT(CASE WHEN status = 'Согласована' THEN 1 END) as approved,
                   COUNT(DISTINCT inventory_number) as unique_devices,
                   (SELECT COUNT(*) FROM tickets WHERE is_archived = TRUE) as archived
            FROM tickets WHERE (is_archived IS NULL OR is_archived = FALSE)
        """)
        return dict(self.cursor.fetchone())

    # ─── Методы для работы с задачами ────────────────────────────────

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def add_task(self, ticket_number: str) -> bool:
        """Добавить заявку в список задач"""
        try:
            self.cursor.execute(
                "INSERT INTO ticket_tasks (ticket_number) VALUES (%s) ON CONFLICT (ticket_number) DO NOTHING",
                (ticket_number,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка добавления задачи: {e}")
            self.connection.rollback()
            return False

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def remove_task(self, ticket_number: str) -> bool:
        """Удалить заявку из списка задач"""
        try:
            self.cursor.execute(
                "DELETE FROM ticket_tasks WHERE ticket_number = %s", (ticket_number,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка удаления задачи: {e}")
            self.connection.rollback()
            return False

    def is_task(self, ticket_number: str) -> bool:
        """Проверить, находится ли заявка в списке задач"""
        self.cursor.execute(
            "SELECT id FROM ticket_tasks WHERE ticket_number = %s", (ticket_number,)
        )
        return self.cursor.fetchone() is not None

    def get_task_numbers(self) -> List[str]:
        """Получить список номеров заявок, находящихся в задачах"""
        self.cursor.execute("SELECT ticket_number FROM ticket_tasks ORDER BY created_at DESC")
        return [r['ticket_number'] for r in self.cursor.fetchall()]

    def get_task_offices(self) -> Dict[str, str]:
        """Получить словарь {номер_заявки: офис} для всех заявок в задачах"""
        self.cursor.execute("""
            SELECT tt.ticket_number, t.office
            FROM ticket_tasks tt
            LEFT JOIN tickets t ON tt.ticket_number = t.ticket_number
            ORDER BY tt.created_at DESC
        """)
        return {r['ticket_number']: r['office'] for r in self.cursor.fetchall()}

    def get_task_count(self) -> int:
        """Получить количество заявок в задачах"""
        self.cursor.execute("SELECT COUNT(*) as cnt FROM ticket_tasks")
        row = self.cursor.fetchone()
        return row['cnt'] if row else 0

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def archive_old_tickets(self, before_date: datetime) -> Dict[str, Any]:
        """Массовая архивация заявок, созданных до указанной даты (включительно)."""
        result = {'success': False, 'archived_count': 0, 'archived_tickets': [], 'error': None}
        try:
            self.connection.commit()
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=False)

            self.cursor.execute(
                """SELECT ticket_number, first_received_date FROM tickets
                   WHERE (is_archived IS NULL OR is_archived = FALSE) AND first_received_date <= %s
                   ORDER BY ticket_number""",
                (before_date,)
            )
            tickets_to_archive = [dict(r) for r in self.cursor.fetchall()]

            if not tickets_to_archive:
                self.connection.commit()
                self.connection.set_session(autocommit=old_autocommit)
                result['success'] = True
                return result

            ticket_numbers = [t['ticket_number'] for t in tickets_to_archive]
            self.cursor.execute(
                "UPDATE tickets SET is_archived = TRUE WHERE ticket_number = ANY(%s)",
                (ticket_numbers,)
            )
            self.connection.commit()
            self.connection.set_session(autocommit=old_autocommit)
            result['success'] = True
            result['archived_count'] = len(ticket_numbers)
            result['archived_tickets'] = ticket_numbers
            return result
        except Exception as e:
            try:
                self.connection.rollback()
            except Exception:
                pass
            result['error'] = str(e)
            print(f"Ошибка массовой архивации: {e}")
            return result

    def clear_all_data(self) -> bool:
        """Очистка всех данных (для перезагрузки) — удаляем и пересоздаём таблицы"""
        try:
            self.connection.commit()
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=True)
            self.cursor.execute("DROP TABLE IF EXISTS ticket_history, ticket_comments, user_comments, tickets CASCADE")
            self.connection.set_session(autocommit=old_autocommit)
            print("✓ Все таблицы удалены")
            return True
        except Exception as e:
            print(f"✗ Ошибка очистки данных: {e}")
            self.connection.rollback()
            return False

    def full_cleanup(self) -> Dict[str, Any]:
        """Комплексная очистка БД: удаление, сброс sequences, пересоздание, верификация."""
        result = {'steps': [], 'success': True, 'error': None}

        def log_step(name, status, detail=None):
            entry = {'step': name, 'status': status}
            if detail:
                entry['detail'] = detail
            result['steps'].append(entry)
            logger.info(f"[FULL_CLEANUP] {name}: {status}" + (f" — {detail}" if detail else ""))

        try:
            self.connection.commit()
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=True)
            log_step("Завершение транзакции", "OK")

            self.cursor.execute("SELECT sequence_name FROM information_schema.sequences WHERE sequence_schema = 'public'")
            sequences = [r['sequence_name'] for r in self.cursor.fetchall()]
            log_step("Получение списка sequences", "OK", f"Найдено: {len(sequences)}")

            self.cursor.execute("DROP TABLE IF EXISTS ticket_history, ticket_comments, user_comments, tickets CASCADE")
            log_step("Удаление таблиц (CASCADE)", "OK", "ticket_history, ticket_comments, user_comments, tickets")

            for seq in sequences:
                self.cursor.execute(SQL("ALTER SEQUENCE IF EXISTS {} RESTART WITH 1").format(Identifier(seq)))
            log_step("Сброс sequences", "OK", f"Сброшено: {len(sequences)}")

            # Пересоздаём таблицы напрямую (без пула, т.к. full_cleanup использует прямой курсор)
            for query in self._get_create_table_queries():
                self.cursor.execute(query)
            log_step("Пересоздание таблиц", "OK")

            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('tickets', 'ticket_comments', 'ticket_history', 'user_comments')
            """)
            tables_count = self.cursor.fetchone()['cnt']
            if tables_count < 4:
                raise Exception(f"Создано только {tables_count}/4 таблиц")

            for table in ['tickets', 'ticket_comments', 'ticket_history', 'user_comments']:
                self.cursor.execute(SQL("SELECT COUNT(*) as cnt FROM {}").format(Identifier(table)))
                cnt = self.cursor.fetchone()['cnt']
                if cnt != 0:
                    raise Exception(f"Таблица {table} не пуста: {cnt} записей")

            log_step("Верификация целостности", "OK", "Все таблицы пусты, sequences сброшены")
            self.connection.set_session(autocommit=old_autocommit)
            log_step("Восстановление режима autocommit", "OK")
            result['success'] = True
            return result
        except Exception as e:
            log_step("ОШИБКА", "FAIL", str(e))
            try:
                self.connection.rollback()
            except Exception:
                pass
            result['success'] = False
            result['error'] = str(e)
            return result

    def verify_data_integrity(self) -> Dict[str, Any]:
        """Верификация целостности данных после загрузки."""
        result = {'checks': [], 'success': True, 'summary': {}}
        try:
            for table in ['tickets', 'ticket_comments', 'ticket_history', 'user_comments']:
                self.cursor.execute(SQL("SELECT COUNT(*) as cnt FROM {}").format(Identifier(table)))
                cnt = self.cursor.fetchone()['cnt']
                result['summary'][table] = cnt
                result['checks'].append({'check': f'Количество записей в {table}', 'status': 'OK', 'value': cnt})

            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM ticket_comments tc
                LEFT JOIN tickets t ON tc.ticket_number = t.ticket_number WHERE t.ticket_number IS NULL
            """)
            orphan_comments = self.cursor.fetchone()['cnt']
            if orphan_comments > 0:
                result['checks'].append({'check': 'Сиротские комментарии', 'status': 'WARN', 'value': orphan_comments})
                result['success'] = False
            else:
                result['checks'].append({'check': 'Ссылочная целостность комментариев', 'status': 'OK', 'value': 0})

            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM ticket_history th
                LEFT JOIN tickets t ON th.ticket_number = t.ticket_number WHERE t.ticket_number IS NULL
            """)
            orphan_history = self.cursor.fetchone()['cnt']
            if orphan_history > 0:
                result['checks'].append({'check': 'Сиротские записи истории', 'status': 'WARN', 'value': orphan_history})
                result['success'] = False
            else:
                result['checks'].append({'check': 'Ссылочная целостность истории', 'status': 'OK', 'value': 0})

            self.cursor.execute("""
                SELECT ticket_number, COUNT(*) as cnt FROM tickets
                GROUP BY ticket_number HAVING COUNT(*) > 1
            """)
            duplicates = self.cursor.fetchall()
            if duplicates:
                result['checks'].append({'check': 'Дубликаты ticket_number', 'status': 'WARN', 'value': [dict(d) for d in duplicates]})
                result['success'] = False
            else:
                result['checks'].append({'check': 'Дубликаты ticket_number', 'status': 'OK', 'value': 0})

            return result
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result

    # ─── Методы для работы с изображениями ──────────────────────────────

    def save_image_record(self, image: TicketImage) -> Optional[int]:
        """Сохранение записи об изображении в БД. Возвращает ID записи."""
        try:
            self.cursor.execute(
                "SELECT 1 FROM tickets WHERE ticket_number = %s", (image.ticket_number,)
            )
            if not self.cursor.fetchone():
                logger.error(f"Заявка {image.ticket_number} не найдена. Невозможно сохранить изображение.")
                return None

            query = """
                INSERT INTO ticket_images
                    (ticket_number, file_path, original_filename, mime_type,
                     file_size, thumbnail_path, uploaded_at, is_deleted)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            self.cursor.execute(query, image.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result['id'] if result else None
        except Exception as e:
            logger.error(f"Ошибка сохранения записи изображения: {e}", exc_info=True)
            try:
                self.connection.rollback()
            except Exception:
                pass
            if 'duplicate key' in str(e).lower() and 'ticket_images_pkey' in str(e):
                try:
                    self.cursor.execute(
                        "SELECT setval('ticket_images_id_seq', COALESCE((SELECT MAX(id) FROM ticket_images), 0) + 1, false)"
                    )
                    self.connection.commit()
                    logger.info("Sequence ticket_images_id_seq восстановлен после duplicate key")
                except Exception as seq_err:
                    logger.error(f"Не удалось восстановить sequence: {seq_err}")
                    try:
                        self.connection.rollback()
                    except Exception:
                        pass
            return None

    def get_ticket_images(self, ticket_number: str, include_deleted: bool = False) -> List[Dict]:
        """Получение списка изображений для заявки"""
        try:
            if include_deleted:
                self.cursor.execute(
                    "SELECT * FROM ticket_images WHERE ticket_number = %s ORDER BY uploaded_at ASC",
                    (ticket_number,)
                )
            else:
                self.cursor.execute(
                    "SELECT * FROM ticket_images WHERE ticket_number = %s AND is_deleted = FALSE ORDER BY uploaded_at ASC",
                    (ticket_number,)
                )
            rows = self.cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            print(f"Ошибка получения изображений: {e}")
            return []

    def get_image_by_id(self, image_id: int) -> Optional[Dict]:
        """Получение записи изображения по ID"""
        try:
            self.cursor.execute(
                "SELECT * FROM ticket_images WHERE id = %s",
                (image_id,)
            )
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception as e:
            print(f"Ошибка получения изображения: {e}")
            return None

    def soft_delete_image(self, image_id: int) -> bool:
        """Мягкое удаление изображения (is_deleted = TRUE)"""
        try:
            self.cursor.execute(
                "UPDATE ticket_images SET is_deleted = TRUE WHERE id = %s",
                (image_id,)
            )
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка удаления изображения: {e}")
            self.connection.rollback()
            return False

    def has_images(self, ticket_number: str) -> bool:
        """Проверка наличия изображений у заявки"""
        try:
            self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM ticket_images WHERE ticket_number = %s AND is_deleted = FALSE",
                (ticket_number,)
            )
            row = self.cursor.fetchone()
            return row['cnt'] > 0 if row else False
        except Exception as e:
            print(f"Ошибка проверки изображений: {e}")
            return False

    # ─── Методы для работы с пользовательскими комментариями ─────────

    @_retry_on_db_error(max_attempts=3, base_delay=0.5)
    def save_user_comment(self, comment: UserComment) -> Optional[int]:
        """Сохранение комментария пользователя к заявке. Возвращает ID комментария."""
        try:
            self.cursor.execute(
                "SELECT 1 FROM tickets WHERE ticket_number = %s", (comment.ticket_number,)
            )
            if not self.cursor.fetchone():
                logger.error(f"Заявка {comment.ticket_number} не найдена. Невозможно добавить комментарий.")
                return None

            query = """
                INSERT INTO user_comments (ticket_number, author_username, author_name, comment_text, created_at)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            self.cursor.execute(query, comment.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result['id'] if result else None
        except Exception as e:
            logger.error(f"Ошибка сохранения комментария пользователя: {e}", exc_info=True)
            try:
                self.connection.rollback()
            except Exception:
                pass
            return None

    def get_user_comments(self, ticket_number: str) -> List[Dict]:
        """Получение списка комментариев пользователей для заявки (в хронологическом порядке)"""
        try:
            self.cursor.execute(
                """SELECT id, ticket_number, author_username, author_name, comment_text, created_at
                   FROM user_comments
                   WHERE ticket_number = %s
                   ORDER BY created_at ASC""",
                (ticket_number,)
            )
            rows = self.cursor.fetchall()
            return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Ошибка получения комментариев пользователей: {e}")
            return []

    def get_user_comments_count(self, ticket_number: str) -> int:
        """Получение количества комментариев пользователей для заявки"""
        try:
            self.cursor.execute(
                "SELECT COUNT(*) as cnt FROM user_comments WHERE ticket_number = %s",
                (ticket_number,)
            )
            result = self.cursor.fetchone()
            return result['cnt'] if result else 0
        except Exception as e:
            logger.error(f"Ошибка получения количества комментариев: {e}")
            return 0

    def get_tickets_has_comments(self, ticket_numbers: List[str]) -> Dict[str, bool]:
        """
        Получение словаря {ticket_number: has_comments} для списка заявок.
        Возвращает True, если у заявки есть хотя бы один комментарий.
        """
        if not ticket_numbers:
            return {}
        try:
            placeholders = ", ".join(["%s"] * len(ticket_numbers))
            self.cursor.execute(
                f"""SELECT ticket_number, COUNT(*) as cnt
                    FROM user_comments
                    WHERE ticket_number IN ({placeholders})
                    GROUP BY ticket_number""",
                ticket_numbers
            )
            rows = self.cursor.fetchall()
            result = {tn: False for tn in ticket_numbers}
            for row in rows:
                result[row['ticket_number']] = row['cnt'] > 0
            return result
        except Exception as e:
            logger.error(f"Ошибка получения наличия комментариев: {e}")
            return {tn: False for tn in ticket_numbers}

    def close(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()