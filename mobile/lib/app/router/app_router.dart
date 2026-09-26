import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/di/providers.dart';
import '../../features/admin/presentation/screens/rebuild_screen.dart';
import '../../features/admin/presentation/screens/users_screen.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/sync_status/presentation/screens/sync_status_screen.dart';
import '../../features/tickets/presentation/screens/ticket_detail_screen.dart';
import '../../features/tickets/presentation/screens/tickets_list_screen.dart';

final goRouterProvider = Provider<GoRouter>((ref) {
  final auth = ref.watch(authControllerProvider);

  return GoRouter(
    initialLocation: '/tickets',
    refreshListenable: _AuthListenable(ref),
    redirect: (context, state) {
      final loggingIn = state.matchedLocation == '/login';
      if (auth.isLoading) return null;
      if (!auth.isAuthenticated && !loggingIn) return '/login';
      if (auth.isAuthenticated && loggingIn) return '/tickets';
      final loc = state.matchedLocation;
      if (loc.startsWith('/admin')) {
        final user = auth.user;
        if (user == null) return '/login';
        if (loc.startsWith('/admin/users') &&
            !user.isAdmin &&
            !user.hasPermission('view_users')) {
          return '/tickets';
        }
        if (loc.startsWith('/admin/rebuild') &&
            !user.hasPermission('rebuild_data')) {
          return '/tickets';
        }
      }
      return null;
    },
    routes: [
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      GoRoute(
        path: '/tickets',
        builder: (context, state) => const TicketsListScreen(),
      ),
      GoRoute(
        path: '/tickets/:number',
        builder: (context, state) =>
            TicketDetailScreen(ticketNumber: state.pathParameters['number']!),
      ),
      GoRoute(
        path: '/sync',
        builder: (context, state) => const SyncStatusScreen(),
      ),
      GoRoute(
        path: '/admin/users',
        builder: (context, state) => const UsersScreen(),
      ),
      GoRoute(
        path: '/admin/rebuild',
        builder: (context, state) => RebuildScreen(
          sinceDate: state.extra is String ? state.extra as String : null,
        ),
      ),
    ],
  );
});

class _AuthListenable extends ChangeNotifier {
  _AuthListenable(this._ref) {
    _ref.listen(authControllerProvider, (_, __) => notifyListeners());
  }

  final Ref _ref;
}
