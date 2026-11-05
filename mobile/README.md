# gkuop_mobile — Offline-First клиент для gkuop-api

## Назначение

Мобильное приложение для работы с заявками ГКУ ОП: просмотр, редактирование, комментарии, вложения, задачи — с полноценной работой **без интернета** после initial sync.

Платформы: **Android**, **iOS**.

## Требования

- Flutter stable ≥ 3.35 / Dart ≥ 3.9
- Android minSdk 24+
- iOS 15.0+ (Xcode на macOS)
- Backend `gkuop-api` с endpoints из `docs/sync-protocol.md`

## Запуск

```bash
cd mobile
flutter pub get
dart run build_runner build --delete-conflicting-outputs
```

### Android

```bash
flutter run \
  --dart-define=API_BASE_URL=http://10.0.2.2:8002 \
  --dart-define=ENVIRONMENT=development
```

Эмулятор Android → хост-машина: `10.0.2.2`.  
Физическое устройство: IP сервера в LAN / HTTPS production URL.

### iOS (Mac + USB iPhone)

1. Установите Xcode, откройте `ios/Runner.xcworkspace`, выберите Team в Signing & Capabilities.
2. На iPhone: доверие компьютеру; Settings → General → VPN & Device Management → доверие разработчику.
3. Запуск:

```bash
flutter devices
flutter run -d <iphone-id> \
  --dart-define=API_BASE_URL=http://<IP-Mac-или-API-в-LAN>:8002 \
  --dart-define=ENVIRONMENT=development
```

Bundle ID: `info.part4.gkuopMobile`.  
Для HTTP в локальной сети включён `NSAllowsLocalNetworking` в `Info.plist`.

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

### Android

Настройте signing в `android/key.properties` (не коммитить).  
Сборка: `flutter build apk --release --dart-define=API_BASE_URL=https://gkuop.example.com`.

### iOS

```bash
flutter build ipa --release --dart-define=API_BASE_URL=https://gkuop.example.com
```

Требуется Apple Developer Program и корректный provisioning profile в Xcode.
