"""
Менеджер базы данных
"""
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.sql import SQL, Identifier
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import Ticket, TicketComment, TicketHistoryRecord, TicketImage


class DatabaseManager:
    """Управление подключением и операциями с БД"""

    def __init__(self, config: Dict):
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """Подключение к базе данных"""
        try:
            self.connection = psycopg2.connect(**self.config)
            self.cursor = self.connection.cursor(cursor_factory=RealDictCursor)
            self._create_tables()
            print("✓ Подключено к PostgreSQL")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения к БД: {e}")
            return False

    def _create_tables(self):
        """Создание необходимых таблиц"""
        # DDL-операции требуют autocommit
        self.connection.commit()
        old_autocommit = self.connection.autocommit
        self.connection.set_session(autocommit=True)
        # Миграция: добавляем колонку is_archived, если её нет
        try:
            self.cursor.execute(
                "ALTER TABLE tickets ADD COLUMN IF NOT EXISTS is_archived BOOLEAN DEFAULT FALSE"
            )
        except Exception:
            pass  # Таблицы может ещё не существовать

        queries = [
            """
            CREATE TABLE IF NOT EXISTS tickets
            (
                id
                SERIAL
                PRIMARY
                KEY,
                ticket_number
                VARCHAR
            (
                20
            ) UNIQUE NOT NULL,
                subject TEXT,
                inventory_number VARCHAR
            (
                50
            ),
                printer_model VARCHAR
            (
                200
            ),
                office TEXT,
                cabinet VARCHAR
            (
                20
            ),
                component VARCHAR
            (
                200
            ),
                status VARCHAR
            (
                100
            ),
                priority VARCHAR
            (
                50
            ),
                assigned_to TEXT,
                author_name VARCHAR
            (
                200
            ),
                contact_phone VARCHAR
            (
                20
            ),
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
                email_hash VARCHAR
            (
                64
            ) UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            """
            CREATE TABLE IF NOT EXISTS ticket_comments
            (
                id
                SERIAL
                PRIMARY
                KEY,
                ticket_number
                VARCHAR
            (
                20
            ) REFERENCES tickets
            (
                ticket_number
            ) ON DELETE CASCADE,
                comment_text TEXT,
                changed_fields JSONB,
                status_before VARCHAR
            (
                100
            ),
                status_after VARCHAR
            (
                100
            ),
                received_date TIMESTAMP,
                email_hash VARCHAR
            (
                64
            ) UNIQUE,
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
            """
        ]

        for query in queries:
            self.cursor.execute(query)
        self.connection.set_session(autocommit=old_autocommit)

    def ticket_exists(self, ticket_number: str) -> bool:
        """Проверка существования заявки"""
        self.cursor.execute(
            "SELECT id FROM tickets WHERE ticket_number = %s",
            (ticket_number,)
        )
        return self.cursor.fetchone() is not None

    def get_ticket(self, ticket_number: str) -> Optional[Dict]:
        """Получение заявки по номеру"""
        self.cursor.execute(
            "SELECT * FROM tickets WHERE ticket_number = %s",
            (ticket_number,)
        )
        row = self.cursor.fetchone()
        if row:
            return dict(row)
        return None

    def save_ticket(self, ticket: Ticket) -> bool:
        """Сохранение новой заявки"""
        try:
            # Сначала проверяем, существует ли запись с таким email_hash
            self.cursor.execute(
                "SELECT id FROM tickets WHERE email_hash = %s",
                (ticket.email_hash,)
            )
            if self.cursor.fetchone():
                return True  # Уже существует — не ошибка

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

    def update_ticket(self, ticket_number: str, updates: Dict, last_updated_date: datetime = None) -> bool:
        """Обновление существующей заявки

        Args:
            ticket_number: Номер заявки
            updates: Словарь обновляемых полей
            last_updated_date: Дата последнего взаимодействия (из письма).
                               Если None — не обновляет поле last_updated_date.
        """
        try:
            # Формируем SET-выражение
            set_parts = [SQL("{} = %s").format(Identifier(key)) for key in updates.keys()]

            # Если передан last_updated_date — добавляем его в SET
            if last_updated_date is not None:
                set_parts.append(SQL("last_updated_date = %s"))
                values = list(updates.values()) + [last_updated_date, ticket_number]
            else:
                values = list(updates.values()) + [ticket_number]

            set_clause = SQL(", ").join(set_parts)

            query = SQL("""
                UPDATE tickets 
                SET {set_clause}
                WHERE ticket_number = %s
            """).format(set_clause=set_clause)
            self.cursor.execute(query, values)
            self.connection.commit()
            return True
        except Exception as e:
            print(f"Ошибка обновления заявки: {e}")
            self.connection.rollback()
            return False

    def save_comment(self, comment: TicketComment) -> bool:
        """Сохранение комментария"""
        try:
            query = """
                    INSERT INTO ticket_comments (ticket_number, comment_text, changed_fields, \
                                                 status_before, status_after, received_date, email_hash) \
                    VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (email_hash) DO NOTHING
                RETURNING id \
                    """
            self.cursor.execute(query, comment.get_insert_params())
            result = self.cursor.fetchone()
            self.connection.commit()
            return result is not None
        except Exception as e:
            print(f"Ошибка сохранения комментария: {e}")
            self.connection.rollback()
            return False

    def save_history_record(self, record: TicketHistoryRecord) -> bool:
        """Сохранение записи хронологии (только изменившиеся поля на момент письма)"""
        try:
            query = """
                INSERT INTO ticket_history (
                    ticket_number, received_date, email_hash, changed_fields,
                    subject, inventory_number, printer_model,
                    office, cabinet, component, status, priority,
                    assigned_to, author_name, contact_phone,
                    department, position, current_note,
                    required_action, cause, fault_description,
                    work_done, tech_conclusion, soglasovano_line
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
        """
        Получение хронологии заявки.
        Возвращает все записи из ticket_history (полные снимки),
        а также комментарии из ticket_comments для обратной совместимости.
        """
        # Получаем полные записи хронологии
        self.cursor.execute("""
                            SELECT *
                            FROM ticket_history
                            WHERE ticket_number = %s
                            ORDER BY received_date ASC
                            """, (ticket_number,))

        history_rows = self.cursor.fetchall()

        # Получаем комментарии (изменения между письмами)
        self.cursor.execute("""
                            SELECT comment_text,
                                   changed_fields,
                                   status_before,
                                   status_after,
                                   received_date,
                                   created_at
                            FROM ticket_comments
                            WHERE ticket_number = %s
                            ORDER BY received_date ASC
                            """, (ticket_number,))

        comment_rows = self.cursor.fetchall()

        # Формируем результат: сначала полные записи хронологии,
        # затем комментарии для обратной совместимости
        result = []

        for row in history_rows:
            changed_fields = row.get('changed_fields')
            if changed_fields and isinstance(changed_fields, dict):
                changes = dict(changed_fields)
            else:
                # Для обратной совместимости: если changed_fields пуст,
                # вычисляем diff из полных полей (старый формат данных)
                changes = {}
                # Поля, исключённые из отображения в истории
                _excluded = {'assigned_to', 'contact_phone', 'author_name', 'position', 'subject'}
                for field in ['subject', 'inventory_number', 'printer_model',
                              'office', 'cabinet', 'component', 'status', 'priority',
                              'assigned_to', 'author_name', 'contact_phone',
                              'department', 'position', 'current_note',
                              'required_action', 'cause', 'fault_description',
                              'work_done', 'tech_conclusion', 'soglasovano_line']:
                    if field in _excluded:
                        continue
                    val = row.get(field)
                    if val:
                        changes[field] = val

            result.append({
                'type': 'snapshot',
                'date': row['received_date'],
                'created_at': row['created_at'],
                'changed_fields': changes,
            })

        for row in comment_rows:
            result.append({
                'type': 'comment',
                'comment': row['comment_text'],
                'changes': row['changed_fields'],
                'status_before': row['status_before'],
                'status_after': row['status_after'],
                'date': row['received_date'],
                'created_at': row['created_at']
            })

        # Сортируем по дате
        result.sort(key=lambda x: x.get('date') or x.get('created_at') or datetime.min)

        return result

    def get_last_history_record(self, ticket_number: str) -> Optional[Dict]:
        """Получение последней записи хронологии для заявки (для вычисления diff)"""
        self.cursor.execute("""
            SELECT changed_fields
            FROM ticket_history
            WHERE ticket_number = %s AND changed_fields IS NOT NULL
            ORDER BY received_date DESC
            LIMIT 1
        """, (ticket_number,))
        row = self.cursor.fetchone()
        if row:
            cf = row['changed_fields']
            if cf and isinstance(cf, dict):
                return {'changed_fields': dict(cf)}
        return None

    def get_statistics(self) -> Dict:
        """Получение статистики по заявкам"""
        self.cursor.execute("""
                            SELECT
                                   COUNT(*)                                           as total,
                                   COUNT(CASE WHEN is_active = true THEN 1 END)       as active,
                                   COUNT(CASE WHEN status = 'В работе' THEN 1 END)    as in_progress,
                                   COUNT(CASE WHEN status = 'Согласована' THEN 1 END) as approved,
                                   COUNT(DISTINCT inventory_number)                   as unique_devices,
                                   (SELECT COUNT(*) FROM tickets WHERE is_archived = TRUE) as archived
                            FROM tickets
                            WHERE (is_archived IS NULL OR is_archived = FALSE)
                            """)
        stats = self.cursor.fetchone()
        return dict(stats)

    # ─── Методы для работы с задачами ────────────────────────────────

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

    def remove_task(self, ticket_number: str) -> bool:
        """Удалить заявку из списка задач"""
        try:
            self.cursor.execute(
                "DELETE FROM ticket_tasks WHERE ticket_number = %s",
                (ticket_number,)
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
            "SELECT id FROM ticket_tasks WHERE ticket_number = %s",
            (ticket_number,)
        )
        return self.cursor.fetchone() is not None

    def get_task_numbers(self) -> List[str]:
        """Получить список номеров заявок, находящихся в задачах"""
        self.cursor.execute(
            "SELECT ticket_number FROM ticket_tasks ORDER BY created_at DESC"
        )
        rows = self.cursor.fetchall()
        return [r['ticket_number'] for r in rows]

    def get_task_count(self) -> int:
        """Получить количество заявок в задачах"""
        self.cursor.execute("SELECT COUNT(*) as cnt FROM ticket_tasks")
        row = self.cursor.fetchone()
        return row['cnt'] if row else 0

    def archive_old_tickets(self, before_date: datetime) -> Dict[str, Any]:
        """
        Массовая архивация заявок, созданных до указанной даты (включительно).

        Архивируются все заявки, у которых first_received_date < before_date
        (на следующий день после before_date), за исключением уже архивированных.

        Все связанные данные (комментарии, вложения, история) сохраняются
        благодаря внешним ключам с CASCADE.

        Операция выполняется в одной транзакции с возможностью отката при сбое.

        Args:
            before_date: Дата, до которой заявки архивируются (включительно).
                         Заявки с first_received_date <= before_date будут архивированы.

        Returns:
            Dict с ключами:
                - success: bool
                - archived_count: int
                - archived_tickets: list[str] — номера заархивированных заявок
                - error: Optional[str]
        """
        result = {
            'success': False,
            'archived_count': 0,
            'archived_tickets': [],
            'error': None
        }
        try:
            # Начинаем транзакцию
            self.connection.commit()  # завершаем предыдущую, если была
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=False)

            # Выбираем заявки для архивации:
            # - first_received_date <= before_date (включительно)
            # - не архивированные (is_archived IS NULL OR is_archived = FALSE)
            self.cursor.execute(
                """SELECT ticket_number, first_received_date
                   FROM tickets
                   WHERE (is_archived IS NULL OR is_archived = FALSE)
                     AND first_received_date <= %s
                   ORDER BY ticket_number""",
                (before_date,)
            )
            rows = self.cursor.fetchall()
            tickets_to_archive = [dict(r) for r in rows]

            if not tickets_to_archive:
                self.connection.commit()
                self.connection.set_session(autocommit=old_autocommit)
                result['success'] = True
                return result

            ticket_numbers = [t['ticket_number'] for t in tickets_to_archive]

            # Архивируем: устанавливаем is_archived = TRUE
            # Не перезаписываем last_updated_date — дата последнего письма
            # должна сохраняться даже при массовой архивации
            self.cursor.execute(
                """UPDATE tickets
                   SET is_archived = TRUE
                   WHERE ticket_number = ANY(%s)""",
                (ticket_numbers,)
            )

            # Фиксируем транзакцию
            self.connection.commit()
            self.connection.set_session(autocommit=old_autocommit)

            result['success'] = True
            result['archived_count'] = len(ticket_numbers)
            result['archived_tickets'] = ticket_numbers

            return result

        except Exception as e:
            # Откат транзакции при сбое
            try:
                self.connection.rollback()
            except Exception:
                pass
            error_msg = str(e)
            print(f"Ошибка массовой архивации: {error_msg}")
            result['error'] = error_msg
            return result

    def clear_all_data(self) -> bool:
        """Очистка всех данных (для перезагрузки) — удаляем и пересоздаём таблицы"""
        try:
            # Завершаем текущую транзакцию перед сменой режима autocommit
            self.connection.commit()
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=True)
            self.cursor.execute("DROP TABLE IF EXISTS ticket_history, ticket_comments, tickets CASCADE")
            self.connection.set_session(autocommit=old_autocommit)
            print("✓ Все таблицы удалены")
            return True
        except Exception as e:
            print(f"✗ Ошибка очистки данных: {e}")
            self.connection.rollback()
            return False

    def full_cleanup(self) -> Dict[str, Any]:
        """
        Комплексная очистка БД:
        1. Удаление всех таблиц с каскадным сбросом связей
        2. Сброс всех автоинкрементных счётчиков (sequences)
        3. Пересоздание таблиц с актуальной схемой
        4. Верификация целостности после очистки
        Возвращает словарь с результатами каждого шага.
        """
        logger = logging.getLogger(__name__)
        result = {'steps': [], 'success': True, 'error': None}

        def log_step(name, status, detail=None):
            entry = {'step': name, 'status': status}
            if detail:
                entry['detail'] = detail
            result['steps'].append(entry)
            logger.info(f"[FULL_CLEANUP] {name}: {status}" + (f" — {detail}" if detail else ""))

        try:
            # Шаг 1: Завершаем транзакцию
            self.connection.commit()
            old_autocommit = self.connection.autocommit
            self.connection.set_session(autocommit=True)
            log_step("Завершение транзакции", "OK")

            # Шаг 2: Получаем список всех sequences в схеме public
            self.cursor.execute("""
                SELECT sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """)
            sequences = [r['sequence_name'] for r in self.cursor.fetchall()]
            log_step("Получение списка sequences", "OK", f"Найдено: {len(sequences)}")

            # Шаг 3: Удаляем все таблицы с CASCADE (сбрасывает все связи, индексы, ограничения)
            self.cursor.execute("DROP TABLE IF EXISTS ticket_history, ticket_comments, tickets CASCADE")
            log_step("Удаление таблиц (CASCADE)", "OK", "ticket_history, ticket_comments, tickets")

            # Шаг 4: Сброс всех sequences
            for seq in sequences:
                self.cursor.execute(
                    SQL("ALTER SEQUENCE IF EXISTS {} RESTART WITH 1").format(Identifier(seq))
                )
            log_step("Сброс sequences", "OK", f"Сброшено: {len(sequences)}")

            # Шаг 5: Пересоздаём таблицы
            self._create_tables()
            log_step("Пересоздание таблиц", "OK")

            # Шаг 6: Верификация — проверяем, что таблицы пусты и sequences сброшены
            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND table_name IN ('tickets', 'ticket_comments', 'ticket_history')
            """)
            tables_count = self.cursor.fetchone()['cnt']
            if tables_count < 3:
                raise Exception(f"Создано только {tables_count}/3 таблиц")

            # Проверяем, что таблицы пусты
            for table in ['tickets', 'ticket_comments', 'ticket_history']:
                self.cursor.execute(
                    SQL("SELECT COUNT(*) as cnt FROM {}").format(Identifier(table))
                )
                cnt = self.cursor.fetchone()['cnt']
                if cnt != 0:
                    raise Exception(f"Таблица {table} не пуста: {cnt} записей")

            log_step("Верификация целостности", "OK", "Все таблицы пусты, sequences сброшены")

            # Восстанавливаем autocommit
            self.connection.set_session(autocommit=old_autocommit)
            log_step("Восстановление режима autocommit", "OK")

            result['success'] = True
            return result

        except Exception as e:
            error_msg = str(e)
            log_step("ОШИБКА", "FAIL", error_msg)
            try:
                self.connection.rollback()
            except Exception:
                pass
            result['success'] = False
            result['error'] = error_msg
            return result

    def verify_data_integrity(self) -> Dict[str, Any]:
        """
        Верификация целостности данных после загрузки.
        Проверяет: количество записей, ссылочную целостность, дубликаты.
        """
        result = {'checks': [], 'success': True, 'summary': {}}
        try:
            # Проверка 1: Количество записей в каждой таблице
            for table in ['tickets', 'ticket_comments', 'ticket_history']:
                self.cursor.execute(
                    SQL("SELECT COUNT(*) as cnt FROM {}").format(Identifier(table))
                )
                cnt = self.cursor.fetchone()['cnt']
                result['summary'][table] = cnt
                result['checks'].append({
                    'check': f'Количество записей в {table}',
                    'status': 'OK',
                    'value': cnt
                })

            # Проверка 2: Ссылочная целостность (ticket_number в связанных таблицах)
            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM ticket_comments tc
                LEFT JOIN tickets t ON tc.ticket_number = t.ticket_number
                WHERE t.ticket_number IS NULL
            """)
            orphan_comments = self.cursor.fetchone()['cnt']
            if orphan_comments > 0:
                result['checks'].append({
                    'check': 'Сиротские комментарии',
                    'status': 'WARN',
                    'value': orphan_comments
                })
                result['success'] = False
            else:
                result['checks'].append({
                    'check': 'Ссылочная целостность комментариев',
                    'status': 'OK',
                    'value': 0
                })

            self.cursor.execute("""
                SELECT COUNT(*) as cnt FROM ticket_history th
                LEFT JOIN tickets t ON th.ticket_number = t.ticket_number
                WHERE t.ticket_number IS NULL
            """)
            orphan_history = self.cursor.fetchone()['cnt']
            if orphan_history > 0:
                result['checks'].append({
                    'check': 'Сиротские записи истории',
                    'status': 'WARN',
                    'value': orphan_history
                })
                result['success'] = False
            else:
                result['checks'].append({
                    'check': 'Ссылочная целостность истории',
                    'status': 'OK',
                    'value': 0
                })

            # Проверка 3: Дубликаты ticket_number
            self.cursor.execute("""
                SELECT ticket_number, COUNT(*) as cnt
                FROM tickets
                GROUP BY ticket_number
                HAVING COUNT(*) > 1
            """)
            duplicates = self.cursor.fetchall()
            if duplicates:
                result['checks'].append({
                    'check': 'Дубликаты ticket_number',
                    'status': 'WARN',
                    'value': [dict(d) for d in duplicates]
                })
                result['success'] = False
            else:
                result['checks'].append({
                    'check': 'Дубликаты ticket_number',
                    'status': 'OK',
                    'value': 0
                })

            return result
        except Exception as e:
            result['success'] = False
            result['error'] = str(e)
            return result

    # ─── Методы для работы с изображениями ──────────────────────────────

    def save_image_record(self, image: TicketImage) -> Optional[int]:
        """Сохранение записи об изображении в БД. Возвращает ID записи."""
        try:
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
            print(f"Ошибка сохранения записи изображения: {e}")
            self.connection.rollback()
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

    def close(self):
        """Закрытие соединения"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()