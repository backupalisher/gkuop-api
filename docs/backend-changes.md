# Backend changes for mobile Offline-First

## Проблема

Существующий API позволяет list/detail/mutations, но **нет**:

- incremental pull для клиента;
- идемпотентности POST (риск дублей при retry);
- optimistic concurrency на PUT.

## Почему недостаточно текущих endpoints

Полная пагинация `GET /api/tickets` после каждого reconnect:

- тяжело на больших объёмах;
- не отдаёт стабильно новые comments/images/tasks без N+1 detail;
- повтор complete/comment/upload без ключа создаёт дубликаты.

## Предлагаемые изменения (обратно совместимые)

### 1. `GET /api/sync/changes`

Новый read-only endpoint. Не меняет существующие контракты.

### 2. Таблица `client_idempotency_keys`

Хранит `key`, `username`, `method`, `path`, `status_code`, `response_body`, `created_at`.  
TTL очистки: 7 дней (lazy на insert).

Middleware/helper: если заголовок `Idempotency-Key` присутствует на мутации — replay или сохранить ответ.

### 3. `If-Match` на `PUT /api/tickets/{n}`

Опциональный заголовок. Если отсутствует — поведение как раньше (web UI не ломается).  
Если присутствует и не совпадает с `last_updated_date` — 409.

### 4. Soft-tombstone для снятия задачи (опционально v2)

В v1 удаление задачи в sync определяется через `operation: delete` при явном событии или периодическом полном snapshot `GET /api/tasks`.  
Для v1: при pull отдаём текущие tasks + при DELETE task пишем запись в `sync_events` если понадобится позже.

Минимальный v1: sync отдаёт upsert tickets/comments/images; tasks — upsert при наличии в `ticket_tasks`, а клиент дополнительно периодически сверкает `GET /api/tasks`.

## Совместимость

- Web-клиент без новых заголовков работает без изменений.
- Старые mobile/скрипты без sync продолжают использовать list/detail.

## Миграция

Автосоздание таблиц при старте lifespan (как существующие миграции колонок).
