# Архитектура мобильного клиента gkuop (Offline-First)

## Источник истины

Backend: существующий `gkuop-api` (FastAPI + PostgreSQL).  
Клиент: Flutter Android в каталоге `mobile/`.

## Ключевые выводы аудита backend

| Тема | Факт |
|------|------|
| Auth | HMAC-токен 24ч, `Authorization: Bearer`, **без refresh** |
| Создание заявок | **только из email**, API create нет |
| Мутации API | PUT ticket, complete/uncomplete, archive/restore, comments, images, tasks |
| Incremental sync | **не было** → добавлен `GET /api/sync/changes` |
| Optimistic lock | **не было** → `If-Match: <last_updated_date ISO>` на PUT |
| Idempotency | **не было** → заголовок `Idempotency-Key` на POST-мутациях |

## Карта Backend → API → Flutter → SQLite → Sync

| Backend entity | API | Flutter domain | Drift table | Sync strategy |
|----------------|-----|----------------|-------------|---------------|
| `users` / session | `POST /api/auth/login`, `GET /api/auth/me` | `AuthSession`, `AppUser` | `auth_sessions` (secure: token в SecureStorage) | Login online; offline reopen по сохранённой сессии до exp |
| `permissions` | login/`/me` payload | `Permission` codes | `user_permissions` | Pull при login/sync boot |
| offices ACL | login offices / `GET /api/offices` | `Office` | `offices` | Pull справочник |
| `tickets` | `GET /api/tickets`, detail, `PUT`, complete, archive | `Ticket` | `tickets` | **Pull** via `/api/sync/changes`; **Push** PUT/complete/archive через Outbox |
| `ticket_history` | detail only | `TicketHistoryItem` | `ticket_history` | Pull-only (read-only на клиенте) |
| `user_comments` | POST comments; list in detail | `UserComment` | `user_comments` | Pull sync; Push CREATE via Outbox + Idempotency-Key |
| `ticket_images` | upload/list/download/delete | `TicketAttachment` | `ticket_attachments` | Pull meta; Push upload/delete; file cache local |
| `ticket_tasks` | POST/DELETE/GET task, list | `TicketTaskFlag` | `ticket_tasks` | Pull + Push add/remove |
| statuses | `GET /api/statuses` | `StatusRef` | `statuses` | Pull TTL |
| sync cursor | `GET /api/sync/changes` | `SyncCursor` | `sync_metadata` | Cursor opaque server |
| outbox | — | — | `sync_outbox` | Local only → push |

## Offline-допустимые операции (по permissions)

| Операция | Offline | Push |
|----------|---------|------|
| Просмотр списка/карточки | да (локальная БД) | — |
| Поиск по синхронизированным | да (SQLite) | optional online search |
| Редактирование полей заявки | да | PUT + If-Match |
| Комментарий | да | POST + Idempotency-Key |
| Загрузка файла | да (pendingUpload) | multipart upload |
| Удаление файла | да (tombstone) | DELETE |
| Выполнено / архив / задача | да | POST/DELETE |
| Создание заявки | **нет** (нет API) | — |
| Hard-delete заявки | **нет** | — |

## Слои Flutter

```text
UI (Riverpod) → UseCase → Repository → Local Drift (source of truth for UI)
                                      ↘ SyncEngine → Dio → gkuop-api
```

## Auth offline

После login токен и профиль в Secure Storage + локальные permissions.  
При старте без сети: доступ к данным **того же username**.  
При 401 online: экран `authentication required`, локальная БД аккаунта **не удаляется**.

## Конфликты

PUT с `If-Match: <base last_updated_date>`.  
Ответ 409 → conflict UI (локальная vs серверная версия).
