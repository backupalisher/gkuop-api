# gkuop_mobile — Offline-First Android клиент для gkuop-api

## Назначение

Мобильное приложение для работы с заявками ГКУ ОП: просмотр, редактирование, комментарии, вложения, задачи — с полноценной работой **без интернета** после initial sync.

## Требования

- Flutter stable ≥ 3.35 / Dart ≥ 3.9
- Android minSdk 24+
- Backend `gkuop-api` с endpoints из `docs/sync-protocol.md`

## Запуск

```bash
cd mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
flutter run \
  --dart-define=API_BASE_URL=http://10.0.2.2:8002 \
  --dart-define=ENVIRONMENT=development
```

Эмулятор Android → хост-машина: `10.0.2.2`.  
Физическое устройство: IP сервера в LAN / HTTPS production URL.

## Environments

| Define | Описание |
|--------|----------|
| `API_BASE_URL` | Базовый URL API (без trailing slash) |
| `ENVIRONMENT` | `development` / `staging` / `production` |

## Архитектура

См. `../docs/architecture.md`, `../docs/offline-first.md`, `../docs/sync-protocol.md`.

## Тесты

```bash
dart format .
flutter analyze
flutter test
```

## Release

Настройте signing в `android/key.properties` (не коммитить).  
Сборка: `flutter build apk --release --dart-define=API_BASE_URL=https://gkuop.example.com`.
