import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/config/app_config.dart';
import '../database/app_database.dart';
import '../network/api_client.dart';
import '../security/secure_credentials_store.dart';
import '../sync/sync_engine.dart';
import '../../features/auth/data/repositories/auth_repository.dart';
import '../../features/tickets/data/repositories/tickets_repository.dart';

final appConfigProvider = Provider<AppConfig>((ref) {
  return AppConfig.fromEnvironment();
});

final credentialsStoreProvider = Provider<SecureCredentialsStore>((ref) {
  return SecureCredentialsStore();
});

final appDatabaseProvider = Provider<AppDatabase>((ref) {
  throw UnimplementedError('AppDatabase must be overridden in bootstrap');
});

final apiClientProvider = Provider<ApiClient>((ref) {
  final config = ref.watch(appConfigProvider);
  final credentials = ref.watch(credentialsStoreProvider);
  return ApiClient(
    config: config,
    credentials: credentials,
    onUnauthorized: () async {
      // Session invalidated — UI listens via auth state
    },
  );
});

final syncEngineProvider = Provider<SyncEngine>((ref) {
  return SyncEngine(
    db: ref.watch(appDatabaseProvider),
    api: ref.watch(apiClientProvider),
  );
});

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(
    api: ref.watch(apiClientProvider),
    credentials: ref.watch(credentialsStoreProvider),
    db: ref.watch(appDatabaseProvider),
  );
});

final ticketsRepositoryProvider = Provider<TicketsRepository>((ref) {
  return TicketsRepository(
    db: ref.watch(appDatabaseProvider),
    syncEngine: ref.watch(syncEngineProvider),
  );
});

class AuthState {
  const AuthState({
    this.user,
    this.isLoading = false,
    this.error,
    this.needsReauth = false,
  });

  final AuthUser? user;
  final bool isLoading;
  final String? error;
  final bool needsReauth;

  bool get isAuthenticated => user != null && !needsReauth;

  AuthState copyWith({
    AuthUser? user,
    bool? isLoading,
    String? error,
    bool? needsReauth,
    bool clearUser = false,
  }) {
    return AuthState(
      user: clearUser ? null : (user ?? this.user),
      isLoading: isLoading ?? this.isLoading,
      error: error,
      needsReauth: needsReauth ?? this.needsReauth,
    );
  }
}

class AuthController extends StateNotifier<AuthState> {
  AuthController(this._ref) : super(const AuthState(isLoading: true)) {
    _restore();
  }

  final Ref _ref;

  Future<void> _restore() async {
    try {
      final user = await _ref.read(authRepositoryProvider).restoreSession();
      state = AuthState(user: user, isLoading: false);
      if (user != null) {
        // ignore: unawaited_futures
        _ref
            .read(syncEngineProvider)
            .sync(username: user.username, reason: SyncReason.appStart);
      }
    } catch (_) {
      state = const AuthState(isLoading: false);
    }
  }

  Future<void> login(String username, String password) async {
    state = state.copyWith(isLoading: true, error: null);
    try {
      final user = await _ref
          .read(authRepositoryProvider)
          .login(username: username, password: password);
      state = AuthState(user: user);
      await _ref
          .read(syncEngineProvider)
          .sync(username: user.username, reason: SyncReason.appStart);
    } catch (e) {
      state = AuthState(
        isLoading: false,
        error: e.toString().replaceFirst('Exception: ', ''),
      );
    }
  }

  Future<void> logout() async {
    await _ref.read(authRepositoryProvider).logout();
    state = const AuthState();
  }
}

final authControllerProvider = StateNotifierProvider<AuthController, AuthState>(
  (ref) {
    return AuthController(ref);
  },
);
