import '../../../../core/network/api_client.dart';
import '../../../../core/security/secure_credentials_store.dart';
import '../../../../core/database/app_database.dart';

class AuthUser {
  const AuthUser({
    required this.username,
    required this.role,
    this.fullName,
    required this.permissions,
    required this.offices,
  });

  final String username;
  final String role;
  final String? fullName;
  final List<String> permissions;
  final List<String> offices;

  bool get isAdmin => role == 'admin';

  bool hasPermission(String code) =>
      isAdmin || permissions.contains(code);
}

class AuthRepository {
  AuthRepository({
    required ApiClient api,
    required SecureCredentialsStore credentials,
    required AppDatabase db,
  }) : _api = api,
       _credentials = credentials,
       _db = db;

  final ApiClient _api;
  final SecureCredentialsStore _credentials;
  final AppDatabase _db;

  Future<AuthUser> login({
    required String username,
    required String password,
  }) async {
    final response = await _api.post(
      '/api/auth/login',
      data: {'username': username, 'password': password},
    );
    final body = response.data as Map<String, dynamic>;
    if (body['status'] != 'ok') {
      throw Exception(body['message'] ?? 'Ошибка входа');
    }
    final token = body['token'] as String;
    final userMap = Map<String, dynamic>.from(body['user'] as Map);
    final permissions =
        (body['permissions'] as List?)?.map((e) => e.toString()).toList() ?? [];
    final officesRaw = body['offices'];
    final offices = <String>[];
    if (officesRaw is List) {
      for (final o in officesRaw) {
        if (o is String) {
          offices.add(o);
        } else if (o is Map && o['office'] != null) {
          offices.add(o['office'].toString());
        }
      }
    }

    final role = userMap['role']?.toString() ?? 'operator';
    final fullName = userMap['full_name'] as String?;
    final uname = userMap['username'] as String;

    await _credentials.saveSession(
      token: token,
      username: uname,
      role: role,
      fullName: fullName,
      expiresAt: DateTime.now().toUtc().add(const Duration(hours: 24)),
    );
    await _credentials.saveSavedCredentials(login: uname, password: password);

    await _db.transaction(() async {
      await (_db.delete(
        _db.localPermissions,
      )..where((p) => p.accountUsername.equals(uname))).go();
      for (final code in permissions) {
        await _db
            .into(_db.localPermissions)
            .insert(
              LocalPermissionsCompanion.insert(
                accountUsername: uname,
                code: code,
              ),
            );
      }
    });

    return AuthUser(
      username: uname,
      role: role,
      fullName: fullName,
      permissions: permissions,
      offices: offices,
    );
  }

  Future<AuthUser?> restoreSession() async {
    final token = await _credentials.readToken();
    final username = await _credentials.readUsername();
    if (token == null || username == null) return null;

    final role = await _credentials.readRole() ?? 'operator';
    final fullName = await _credentials.readFullName();
    final perms = await (_db.select(
      _db.localPermissions,
    )..where((p) => p.accountUsername.equals(username))).get();

    return AuthUser(
      username: username,
      role: role,
      fullName: fullName,
      permissions: perms.map((e) => e.code).toList(),
      offices: const [],
    );
  }

  Future<void> refreshSession() async {
    final response = await _api.post('/api/auth/refresh');
    final body = response.data;
    if (body is! Map || body['status'] != 'ok' || body['token'] is! String) {
      throw Exception('Не удалось обновить сессию');
    }
    await _credentials.updateToken(
      token: body['token'] as String,
      expiresAt: DateTime.now().toUtc().add(const Duration(hours: 24)),
    );
  }

  Future<void> logout({bool clearCredentials = true}) async {
    if (clearCredentials) {
      await _credentials.clearSession();
    }
  }
}
