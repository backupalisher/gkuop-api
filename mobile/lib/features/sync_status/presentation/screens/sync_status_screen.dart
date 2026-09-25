import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/di/providers.dart';
import '../../../../core/sync/sync_engine.dart';

class SyncStatusScreen extends ConsumerStatefulWidget {
  const SyncStatusScreen({super.key});

  @override
  ConsumerState<SyncStatusScreen> createState() => _SyncStatusScreenState();
}

class _SyncStatusScreenState extends ConsumerState<SyncStatusScreen> {
  bool _busy = false;
  String? _lastMessage;

  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    final fmt = DateFormat('dd.MM.yyyy HH:mm');
    final db = ref.watch(appDatabaseProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Синхронизация')),
      body: user == null
          ? const Center(child: Text('Нет сессии'))
          : StreamBuilder(
              stream:
                  (db.select(db.syncMetadata)
                        ..where((m) => m.accountUsername.equals(user.username)))
                      .watchSingleOrNull(),
              builder: (context, snap) {
                final meta = snap.data;
                return ListView(
                  padding: const EdgeInsets.all(16),
                  children: [
                    ListTile(
                      title: const Text('Состояние'),
                      subtitle: Text(
                        meta?.lastError != null
                            ? 'Ошибка'
                            : (meta?.lastSuccessfulSync != null
                                  ? 'Синхронизировано'
                                  : 'Ещё не синхронизировано'),
                      ),
                    ),
                    ListTile(
                      title: const Text('Последняя синхронизация'),
                      subtitle: Text(
                        meta?.lastSuccessfulSync != null
                            ? fmt.format(meta!.lastSuccessfulSync!.toLocal())
                            : '—',
                      ),
                    ),
                    ListTile(
                      title: const Text('Ожидают отправки'),
                      subtitle: Text('${meta?.pendingOperationsCount ?? 0}'),
                    ),
                    ListTile(
                      title: const Text('Конфликтов'),
                      subtitle: Text('${meta?.conflictsCount ?? 0}'),
                    ),
                    if (meta?.lastError != null)
                      ListTile(
                        title: const Text('Последняя ошибка'),
                        subtitle: Text(meta!.lastError!),
                      ),
                    if (_lastMessage != null)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 12),
                        child: Text(_lastMessage!),
                      ),
                    FilledButton.icon(
                      onPressed: _busy
                          ? null
                          : () async {
                              setState(() => _busy = true);
                              final result = await ref
                                  .read(syncEngineProvider)
                                  .sync(
                                    username: user.username,
                                    reason: SyncReason.manual,
                                  );
                              setState(() {
                                _busy = false;
                                _lastMessage = result.success
                                    ? 'Готово: отправлено ${result.pushed}, получено ${result.pulled}'
                                    : (result.message ??
                                          'Ошибка синхронизации');
                              });
                            },
                      icon: _busy
                          ? const SizedBox(
                              width: 16,
                              height: 16,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            )
                          : const Icon(Icons.sync),
                      label: const Text('Синхронизировать сейчас'),
                    ),
                  ],
                );
              },
            ),
    );
  }
}
