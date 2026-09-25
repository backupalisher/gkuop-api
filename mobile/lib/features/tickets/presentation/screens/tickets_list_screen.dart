import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../core/database/app_database.dart';
import '../../../../core/di/providers.dart';
import '../../../../core/sync/sync_engine.dart';

final _searchProvider = StateProvider<String>((ref) => '');

final ticketsStreamProvider = StreamProvider.autoDispose<List<Ticket>>((ref) {
  final auth = ref.watch(authControllerProvider);
  final user = auth.user;
  if (user == null) return const Stream.empty();
  final search = ref.watch(_searchProvider);
  return ref
      .watch(ticketsRepositoryProvider)
      .watchTickets(username: user.username, search: search);
});

class TicketsListScreen extends ConsumerWidget {
  const TicketsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ticketsAsync = ref.watch(ticketsStreamProvider);
    final auth = ref.watch(authControllerProvider);
    final dateFmt = DateFormat('dd.MM.yyyy, HH:mm');

    return Scaffold(
      appBar: AppBar(
        title: const Text('Заявки'),
        actions: [
          IconButton(
            tooltip: 'Синхронизация',
            onPressed: () => context.push('/sync'),
            icon: const Icon(Icons.sync),
          ),
          IconButton(
            tooltip: 'Выйти',
            onPressed: () => ref.read(authControllerProvider.notifier).logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Column(
        children: [
          const _SyncBanner(),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 8, 16, 8),
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Поиск по номеру, инвентарному, комплектующему…',
              ),
              onChanged: (v) => ref.read(_searchProvider.notifier).state = v,
            ),
          ),
          Expanded(
            child: ticketsAsync.when(
              data: (items) {
                if (items.isEmpty) {
                  return const Center(
                    child: Text(
                      'Нет заявок в локальной базе.\nВыполните синхронизацию.',
                    ),
                  );
                }
                return RefreshIndicator(
                  onRefresh: () async {
                    final u = auth.user?.username;
                    if (u == null) return;
                    await ref
                        .read(syncEngineProvider)
                        .sync(username: u, reason: SyncReason.manual);
                  },
                  child: ListView.separated(
                    itemCount: items.length,
                    separatorBuilder: (_, __) => const Divider(height: 1),
                    itemBuilder: (context, index) {
                      final t = items[index];
                      final pending = t.syncStatus != SyncStatuses.synced;
                      return ListTile(
                        title: Text('#${t.ticketNumber}'),
                        subtitle: Text(
                          [
                            t.status ?? '—',
                            if (t.component != null && t.component!.isNotEmpty)
                              t.component!,
                            if (t.officeAbbreviated != null)
                              t.officeAbbreviated!
                            else if (t.office != null)
                              t.office!,
                            if (t.lastUpdatedDate != null)
                              dateFmt.format(t.lastUpdatedDate!.toLocal()),
                          ].join(' · '),
                        ),
                        trailing: pending
                            ? const Icon(Icons.cloud_upload_outlined, size: 18)
                            : null,
                        onTap: () => context.push('/tickets/${t.ticketNumber}'),
                      );
                    },
                  ),
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Ошибка: $e')),
            ),
          ),
        ],
      ),
    );
  }
}

class _SyncBanner extends ConsumerWidget {
  const _SyncBanner();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final scheme = Theme.of(context).colorScheme;
    return Material(
      color: scheme.surfaceContainerHighest,
      child: const Padding(
        padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        child: Row(
          children: [
            Icon(Icons.info_outline, size: 16),
            SizedBox(width: 8),
            Expanded(
              child: Text(
                'Данные из локальной базы. Изменения отправятся при появлении сети.',
                style: TextStyle(fontSize: 12),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
