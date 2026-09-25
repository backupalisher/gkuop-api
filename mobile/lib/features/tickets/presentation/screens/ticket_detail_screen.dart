import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';

import '../../../../core/di/providers.dart';
import '../../../../core/database/app_database.dart';

final ticketProvider = FutureProvider.autoDispose.family<Ticket?, String>((
  ref,
  ticketNumber,
) {
  final user = ref.watch(authControllerProvider).user;
  if (user == null) return Future.value(null);
  return ref
      .watch(ticketsRepositoryProvider)
      .getTicket(user.username, ticketNumber);
});

class TicketDetailScreen extends ConsumerWidget {
  const TicketDetailScreen({super.key, required this.ticketNumber});

  final String ticketNumber;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(ticketProvider(ticketNumber));
    final auth = ref.watch(authControllerProvider);
    final canEdit = auth.user?.hasPermission('edit_tickets') ?? false;
    final canComplete = auth.user?.hasPermission('complete_tickets') ?? false;
    final canComment = auth.user?.hasPermission('add_comments') ?? false;
    final dateFmt = DateFormat('dd.MM.yyyy, HH:mm');

    return Scaffold(
      appBar: AppBar(title: Text('Заявка #$ticketNumber')),
      body: async.when(
        data: (t) {
          if (t == null) {
            return const Center(child: Text('Заявка не найдена локально'));
          }
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              if (t.syncStatus != SyncStatuses.synced)
                Card(
                  color: Theme.of(context).colorScheme.secondaryContainer,
                  child: const ListTile(
                    leading: Icon(Icons.cloud_upload_outlined),
                    title: Text('Ожидает отправки'),
                  ),
                ),
              _tile('Статус', t.status),
              _tile('Комплектующее', t.component),
              _tile('Инвентарный номер', t.inventoryNumber),
              _tile('Оборудование', t.printerModel),
              _tile('Офис', t.office),
              _tile('Кабинет', t.cabinet),
              _tile('Требуется', t.requiredAction),
              _tile('Причина', t.cause),
              _tile('Описание', t.faultDescription),
              _tile('Работы', t.workDone),
              _tile('Тех. вывод', t.techConclusion),
              _tile(
                'Обновлено',
                t.lastUpdatedDate != null
                    ? dateFmt.format(t.lastUpdatedDate!.toLocal())
                    : null,
              ),
              const SizedBox(height: 16),
              if (canComplete && t.status != 'Выполнено')
                FilledButton(
                  onPressed: () async {
                    await ref
                        .read(ticketsRepositoryProvider)
                        .completeTicket(
                          username: auth.user!.username,
                          ticketNumber: ticketNumber,
                        );
                    ref.invalidate(ticketProvider(ticketNumber));
                    if (context.mounted) {
                      ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(
                          content: Text(
                            'Отмечено локально. Отправится при синхронизации.',
                          ),
                        ),
                      );
                    }
                  },
                  child: const Text('Выполнено'),
                ),
              if (canComment) ...[
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () =>
                      _addComment(context, ref, auth.user!.username),
                  child: const Text('Добавить комментарий'),
                ),
              ],
              if (canEdit) ...[
                const SizedBox(height: 12),
                OutlinedButton(
                  onPressed: () =>
                      _editNote(context, ref, t, auth.user!.username),
                  child: const Text('Изменить примечание'),
                ),
              ],
            ],
          );
        },
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
      ),
    );
  }

  Widget _tile(String label, String? value) {
    if (value == null || value.trim().isEmpty) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey)),
          const SizedBox(height: 2),
          Text(value),
        ],
      ),
    );
  }

  Future<void> _addComment(
    BuildContext context,
    WidgetRef ref,
    String username,
  ) async {
    final ctrl = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Комментарий'),
        content: TextField(
          controller: ctrl,
          maxLines: 4,
          decoration: const InputDecoration(hintText: 'Текст комментария'),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
    if (ok == true && ctrl.text.trim().isNotEmpty) {
      await ref
          .read(ticketsRepositoryProvider)
          .addComment(
            username: username,
            ticketNumber: ticketNumber,
            text: ctrl.text.trim(),
          );
      if (context.mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Комментарий сохранён локально')),
        );
      }
    }
  }

  Future<void> _editNote(
    BuildContext context,
    WidgetRef ref,
    Ticket ticket,
    String username,
  ) async {
    final ctrl = TextEditingController(text: ticket.currentNote ?? '');
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Примечание'),
        content: TextField(controller: ctrl, maxLines: 4),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
    if (ok == true) {
      await ref
          .read(ticketsRepositoryProvider)
          .updateTicketFields(
            username: username,
            ticketNumber: ticketNumber,
            fields: {'current_note': ctrl.text.trim()},
          );
      ref.invalidate(ticketProvider(ticketNumber));
    }
  }
}
