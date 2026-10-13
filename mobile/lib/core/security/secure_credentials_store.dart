import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Безопасное хранение токена и контекста аккаунта.
///
/// Токен дублируется в памяти: FlutterSecureStorage на Android иногда
/// отдаёт null при параллельных чтениях, из‑за чего API отвечает 401
/// при живой сессии в UI.
class SecureCredentialsStore {
  SecureCredentialsStore({FlutterSecureStorage? storage})
    : _storage =
          storage ??
          const FlutterSecureStorage(
            aOptions: AndroidOptions(encryptedSharedPreferences: true),
          );

  final FlutterSecureStorage _storage;

  static const _tokenKey = 'auth_token';
  static const _usernameKey = 'auth_username';
  static const _tokenExpKey = 'auth_token_exp';
  static const _roleKey = 'auth_role';
  static const _fullNameKey = 'auth_full_name';
  static const _savedLoginKey = 'saved_login';
  static const _savedPasswordKey = 'saved_password';

  String? _cachedToken;
  String? _cachedUsername;
  String? _cachedRole;
  String? _cachedFullName;
  DateTime? _cachedExpiresAt;
  String? _cachedSavedLogin;
  String? _cachedSavedPassword;
  bool _memoryHydrated = false;
  bool _savedHydrated = false;

  Future<void> saveSession({
    required String token,
    required String username,
    required String role,
    String? fullName,
    DateTime? expiresAt,
  }) async {
    _cachedToken = token;
    _cachedUsername = username;
    _cachedRole = role;
    _cachedFullName = fullName;
    _cachedExpiresAt = expiresAt?.toUtc();
    _memoryHydrated = true;

    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _usernameKey, value: username);
    await _storage.write(key: _roleKey, value: role);
    if (fullName != null) {
      await _storage.write(key: _fullNameKey, value: fullName);
    } else {
      await _storage.delete(key: _fullNameKey);
    }
    if (expiresAt != null) {
      await _storage.write(
        key: _tokenExpKey,
        value: expiresAt.toUtc().toIso8601String(),
      );
    } else {
      await _storage.delete(key: _tokenExpKey);
    }
  }

  Future<void> _hydrateMemory() async {
    if (_memoryHydrated) return;
    _cachedToken = await _storage.read(key: _tokenKey);
    _cachedUsername = await _storage.read(key: _usernameKey);
    _cachedRole = await _storage.read(key: _roleKey);
    _cachedFullName = await _storage.read(key: _fullNameKey);
    final rawExp = await _storage.read(key: _tokenExpKey);
    _cachedExpiresAt =
        rawExp == null ? null : DateTime.tryParse(rawExp)?.toUtc();
    _memoryHydrated = true;
  }

  Future<String?> readToken() async {
    if (_cachedToken != null && _cachedToken!.isNotEmpty) {
      return _cachedToken;
    }
    await _hydrateMemory();
    if (_cachedToken != null && _cachedToken!.isNotEmpty) {
      return _cachedToken;
    }
    // Повторное чтение на случай гонки записи
    final fromDisk = await _storage.read(key: _tokenKey);
    if (fromDisk != null && fromDisk.isNotEmpty) {
      _cachedToken = fromDisk;
    }
    return _cachedToken;
  }

  Future<String?> readUsername() async {
    if (_cachedUsername != null) return _cachedUsername;
    await _hydrateMemory();
    return _cachedUsername;
  }

  Future<String?> readRole() async {
    if (_cachedRole != null) return _cachedRole;
    await _hydrateMemory();
    return _cachedRole;
  }

  Future<String?> readFullName() async {
    if (_cachedFullName != null) return _cachedFullName;
    await _hydrateMemory();
    return _cachedFullName;
  }

  Future<DateTime?> readExpiresAt() async {
    if (_cachedExpiresAt != null) return _cachedExpiresAt;
    await _hydrateMemory();
    return _cachedExpiresAt;
  }

  bool get hasCachedToken =>
      _cachedToken != null && _cachedToken!.isNotEmpty;

  Future<void> saveSavedCredentials({
    required String login,
    required String password,
  }) async {
    _cachedSavedLogin = login;
    _cachedSavedPassword = password;
    _savedHydrated = true;
    await _storage.write(key: _savedLoginKey, value: login);
    await _storage.write(key: _savedPasswordKey, value: password);
  }

  Future<({String? login, String? password})> readSavedCredentials() async {
    if (!_savedHydrated) {
      _cachedSavedLogin = await _storage.read(key: _savedLoginKey);
      _cachedSavedPassword = await _storage.read(key: _savedPasswordKey);
      _savedHydrated = true;
    }
    return (login: _cachedSavedLogin, password: _cachedSavedPassword);
  }

  Future<void> updateToken({
    required String token,
    required DateTime expiresAt,
  }) async {
    _cachedToken = token;
    _cachedExpiresAt = expiresAt.toUtc();
    _memoryHydrated = true;
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(
      key: _tokenExpKey,
      value: expiresAt.toUtc().toIso8601String(),
    );
  }

  /// Сбрасывает токен сессии и оставляет логин с паролем для повторного входа.
  Future<void> clearSession() async {
    _cachedToken = null;
    _cachedUsername = null;
    _cachedRole = null;
    _cachedFullName = null;
    _cachedExpiresAt = null;
    _memoryHydrated = true;
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _usernameKey);
    await _storage.delete(key: _tokenExpKey);
    await _storage.delete(key: _roleKey);
    await _storage.delete(key: _fullNameKey);
  }

  Future<void> clear() async {
    _cachedSavedLogin = null;
    _cachedSavedPassword = null;
    _savedHydrated = true;
    await clearSession();
    await _storage.delete(key: _savedLoginKey);
    await _storage.delete(key: _savedPasswordKey);
  }
}
