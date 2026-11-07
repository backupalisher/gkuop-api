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

По умолчанию API: **`https://gkuop.part4.info`** (все платформы).  
`--dart-define=API_BASE_URL=...` нужен только для локального/отладочного сервера.

### Android

```bash
flutter run
# локальный API на эмуляторе:
# flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8002
```

Эмулятор Android → хост-машина: `10.0.2.2`.

### iOS (Mac + USB iPhone)

1. Установите Xcode, откройте `ios/Runner.xcworkspace`, выберите Team в Signing & Capabilities.
2. На iPhone: доверие компьютеру; Settings → General → VPN & Device Management → доверие разработчику.
3. Запуск:

```bash
flutter devices
flutter run -d <iphone-id>
# локальный API:
# flutter run -d <iphone-id> --dart-define=API_BASE_URL=http://<IP-Mac-или-API-в-LAN>:8002
```

Bundle ID: `info.part4.gkuopMobile`.  
Для HTTP в локальной сети включён `NSAllowsLocalNetworking` в `Info.plist`.

Если Xcode пишет `Module 'flutter_secure_storage' not found`,
`Malformed version number string $(RECOMMENDED_IPHONEOS_DEPLOYMENT_TARGET)`
или сотни `Stale file ... outside of the allowed root paths`:

```bash
# в pubspec.yaml: flutter.config.enable-swift-package-manager: false
# в ios/Podfile: platform :ios, '15.0'
flutter clean
rm -rf build ios/Pods ios/Podfile.lock ios/.symlinks \
  ios/Flutter/Flutter.podspec ios/Flutter/ephemeral \
  ~/Library/Developer/Xcode/DerivedData/*
flutter pub get
cd ios && pod install && cd ..
open ios/Runner.xcworkspace   # именно .xcworkspace, не .xcodeproj
```

Предупреждения `deprecated` / `Implicit conversion` внутри `Pods/` и
`~/.pub-cache/...` (SDWebImage, file_picker, sqlite3 и т.д.) — из
зависимостей плагинов, на работу приложения не влияют; правятся
обновлением пакетов у maintainers.

## Environments

| Define | Описание |
|--------|----------|
| `API_BASE_URL` | Базовый URL API (по умолчанию `https://gkuop.part4.info`) |
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
Сборка: `flutter build apk --release` (URL по умолчанию — `https://gkuop.part4.info`).

### iOS

```bash
flutter build ipa --release
```

Требуется Apple Developer Program и корректный provisioning profile в Xcode.
