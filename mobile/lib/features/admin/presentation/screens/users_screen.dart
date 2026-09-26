import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/providers.dart';
import '../../../../core/errors/failures.dart';
import '../../data/admin_repository.dart';

final _usersProvider = FutureProvider.autoDispose<List<AdminUserSummary>>((
  ref,
) async {
  return ref.watch(adminRepositoryProvider).listUsers();
});

class UsersScreen extends ConsumerWidget {
  const UsersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(_usersProvider);
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Пользователи'),
        actions: [
          IconButton(
            tooltip: 'Обновить',
            onPressed: () => ref.invalidate(_usersProvider),
            icon: const Icon(Icons.refresh),
          ),
        ],
      ),
      body: async.when(
        data: (users) {
          if (users.isEmpty) {
            return const Center(child: Text('Нет пользователей'));
          }
          return ListView.separated(
            padding: const EdgeInsets.all(16),
            itemCount: users.length,
            separatorBuilder: (_, __) => const SizedBox(height: 8),
            itemBuilder: (context, index) {
              final u = users[index];
              return Card(
                child: ListTile(
                  leading: CircleAvatar(
                    backgroundColor: scheme.primaryContainer,
                    foregroundColor: scheme.onPrimaryContainer,
                    child: Text(
                      (() {
                        final label = (u.fullName ?? u.username).trim();
                        return label.isNotEmpty
                            ? label[0].toUpperCase()
                            : '?';
                      })(),
                    ),
                  ),
                  title: Text(
                    u.fullName?.isNotEmpty == true ? u.fullName! : u.username,
                    style: const TextStyle(fontWeight: FontWeight.w600),
                  ),
                  subtitle: Text(
                    [
                      u.username,
                      u.role,
                      if (u.email != null && u.email!.isNotEmpty) u.email!,
                      if (!u.isActive) 'неактивен',
                    ].join(' · '),
                  ),
                  trailing: u.role == 'admin'
                      ? Chip(
                          label: const Text('admin'),
                          visualDensity: VisualDensity.compact,
                          backgroundColor: scheme.primaryContainer,
                        )
                      : null,
                ),
              );
            },
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) {
          final msg = e is AppFailure ? e.message : e.toString();
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(msg, textAlign: TextAlign.center),
                  const SizedBox(height: 12),
                  FilledButton(
                    onPressed: () => ref.invalidate(_usersProvider),
                    child: const Text('Повторить'),
                  ),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
