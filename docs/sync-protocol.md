# Sync Protocol (gkuop mobile ↔ gkuop-api)

## Pull: `GET /api/sync/changes`

### Query

| Param | Type | Description |
|-------|------|-------------|
| `since` | ISO-8601 UTC | Начальная точка (первый sync: epoch / omit) |
| `cursor` | string | Opaque cursor с предыдущего ответа |
| `limit` | int | 1…200, default 100 |

### Response

```json
{
  "server_time": "2026-09-25T12:00:00Z",
  "next_cursor": "base64...",
  "has_more": true,
  "changes": [
    {
      "entity": "ticket",
      "id": "425361",
      "operation": "upsert",
      "updated_at": "2026-07-13T16:14:31Z",
      "data": { "...ticket fields...": "" }
    },
    {
      "entity": "user_comment",
      "id": "42",
      "operation": "upsert",
      "updated_at": "2026-07-13T16:20:00Z",
      "data": { "ticket_number": "425361", "comment_text": "..." }
    },
    {
      "entity": "ticket_image",
      "id": "15",
      "operation": "upsert",
      "updated_at": "2026-07-13T16:21:00Z",
      "data": { "ticket_number": "425361", "is_deleted": false, "mime_type": "image/jpeg" }
    },
    {
      "entity": "ticket_task",
      "id": "425361",
      "operation": "upsert",
      "updated_at": "2026-07-13T16:22:00Z",
      "data": { "ticket_number": "425361" }
    },
    {
      "entity": "ticket_task",
      "id": "425360",
      "operation": "delete",
      "updated_at": "2026-07-13T16:23:00Z",
      "data": null
    }
  ]
}
```

Cursor кодирует `(updated_at, entity, id)` для стабильной пагинации.

Права и office ACL совпадают с `GET /api/tickets`.

## Push: существующие endpoints + Idempotency-Key

Клиент **не** шлёт batch POST /sync для мутаций — использует текущие REST-методы:

| Outbox op | HTTP |
|-----------|------|
| UPDATE_TICKET | `PUT /api/tickets/{n}` + `If-Match` |
| COMPLETE_TICKET | `POST /api/tickets/{n}/complete` |
| UNCOMPLETE_TICKET | `POST /api/tickets/{n}/uncomplete` |
| ARCHIVE_TICKET | `POST /api/tickets/{n}/archive` |
| RESTORE_TICKET | `POST /api/tickets/{n}/restore` |
| ADD_COMMENT | `POST /api/tickets/{n}/comments` |
| UPLOAD_ATTACHMENT | `POST /api/tickets/{n}/images` |
| DELETE_ATTACHMENT | `DELETE /api/images/{id}` |
| ADD_TASK | `POST /api/tickets/{n}/task` |
| REMOVE_TASK | `DELETE /api/tickets/{n}/task` |

Заголовок на все POST/PUT/DELETE из outbox:

```http
Idempotency-Key: <uuid>
```

Повтор с тем же ключом возвращает сохранённый ответ (без дубликата).

## Конфликты

```http
PUT /api/tickets/425361
If-Match: 2026-07-13T16:14:31
```

Если `tickets.last_updated_date` на сервере новее → `409` с телом:

```json
{
  "error": "conflict",
  "code": "VERSION_CONFLICT",
  "server_ticket": { },
  "server_updated_at": "..."
}
```

## Pipeline клиента

```text
lock → auth check → health → compact outbox → push ordered → pull changes → apply TX → cursor → unlock
```
