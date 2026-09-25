# gkuop-api

Backend и веб-интерфейс заявок ГКУ ОП + Offline-First Android-клиент.

## Структура

| Путь | Описание |
|------|----------|
| `web_api/` | FastAPI HTML/API |
| `auth/` | Пользователи, роли, permissions |
| `database/` | PostgreSQL models / manager |
| `email_processor/` | Парсинг почты → заявки |
| `mobile/` | Flutter Offline-First Android-клиент |
| `docs/` | Архитектура, sync-протокол, backend-changes |

## Мобильный клиент

См. [`mobile/README.md`](mobile/README.md) и:

- [`docs/architecture.md`](docs/architecture.md) — карта Backend → API → Flutter → SQLite → Sync
- [`docs/offline-first.md`](docs/offline-first.md)
- [`docs/sync-protocol.md`](docs/sync-protocol.md)
- [`docs/backend-changes.md`](docs/backend-changes.md)

Новые backend endpoints (обратно совместимы):

- `GET /api/sync/changes` — incremental pull
- `Idempotency-Key` на мутациях
- опциональный `If-Match` на `PUT /api/tickets/{n}`

## Backend (кратко)

```bash
./run.sh setup
./run.sh start   # :8002
```
