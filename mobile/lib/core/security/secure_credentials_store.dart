import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Безопасное хранение токена и контекста аккаунта.
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

  Future<void> saveSession({
    required String token,
    required String username,
    DateTime? expiresAt,
  }) async {
    await _storage.write(key: _tokenKey, value: token);
    await _storage.write(key: _usernameKey, value: username);
    if (expiresAt != null) {
      await _storage.write(
        key: _tokenExpKey,
        value: expiresAt.toUtc().toIso8601String(),
      );
    }
  }

  Future<String?> readToken() => _storage.read(key: _tokenKey);

  Future<String?> readUsername() => _storage.read(key: _usernameKey);

  Future<DateTime?> readExpiresAt() async {
    final raw = await _storage.read(key: _tokenExpKey);
    if (raw == null) return null;
    return DateTime.tryParse(raw)?.toUtc();
  }

  Future<void> clear() async {
    await _storage.delete(key: _tokenKey);
    await _storage.delete(key: _usernameKey);
    await _storage.delete(key: _tokenExpKey);
  }
}
