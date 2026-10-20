import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/router/app_router.dart';
import 'app/theme/app_theme.dart';
import 'app/theme/theme_controller.dart';
import 'core/database/app_database.dart';
import 'core/di/providers.dart';
import 'core/sync/sync_engine.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final db = await AppDatabase.open();

  runApp(
    ProviderScope(
      overrides: [appDatabaseProvider.overrideWithValue(db)],
      child: const GkuopApp(),
    ),
  );
}

class GkuopApp extends ConsumerStatefulWidget {
  const GkuopApp({super.key});

  @override
  ConsumerState<GkuopApp> createState() => _GkuopAppState();
}

class _GkuopAppState extends ConsumerState<GkuopApp> with WidgetsBindingObserver {
  Timer? _syncTimer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _syncTimer = Timer.periodic(const Duration(seconds: 45), (_) {
      _syncIfLoggedIn(SyncReason.background);
    });
  }

  @override
  void dispose() {
    _syncTimer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      ref.read(authControllerProvider.notifier).refreshIfExpiring();
      _syncIfLoggedIn(SyncReason.appResume);
    }
  }

  void _syncIfLoggedIn(SyncReason reason) {
    final user = ref.read(authControllerProvider).user;
    if (user == null || !ref.read(authControllerProvider).isAuthenticated) {
      return;
    }
    ref.read(syncEngineProvider).sync(username: user.username, reason: reason);
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(goRouterProvider);
    final themeMode = ref.watch(themeControllerProvider);
    return MaterialApp.router(
      title: 'ГКУ ОП Заявки',
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: themeMode,
      routerConfig: router,
      debugShowCheckedModeBanner: false,
    );
  }
}
