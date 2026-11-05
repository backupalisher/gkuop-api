import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/database/app_database.dart';
import '../../../../core/di/providers.dart';
import '../../../../core/sync/sync_engine.dart';
import '../../../../shared/widgets/app_header_menu.dart';
import '../../../../shared/widgets/component_pill.dart';
import '../../../../shared/widgets/status_badge.dart';

enum TicketsTab { active, tasks, archived }

final _searchProvider = StateProvider<String>((ref) => '');
final _tabProvider = StateProvider<TicketsTab>((ref) => TicketsTab.active);
final _officeProvider = StateProvider<String?>((ref) => null);

final ticketsStreamProvider = StreamProvider.autoDispose<List<Ticket>>((ref) {
  final auth = ref.watch(authControllerProvider);
  final user = auth.user;
  if (user == null) return const Stream.empty();
  final search = ref.watch(_searchProvider);
  final tab = ref.watch(_tabProvider);
  final office = ref.watch(_officeProvider);
  return ref.watch(ticketsRepositoryProvider).watchTickets(
        username: user.username,
        archived: tab == TicketsTab.archived,
        tasksOnly: tab == TicketsTab.tasks,
        search: search,
        office: office,
      );
});

final _officesProvider = StreamProvider.autoDispose<List<({String office, String label})>>((
  ref,
) {
  final auth = ref.watch(authControllerProvider);
  final user = auth.user;
  if (user == null) return const Stream.empty();
  final db = ref.watch(appDatabaseProvider);
  return (db.select(db.tickets)..where(
        (t) => t.accountUsername.equals(user.username),
      ))
      .watch()
      .map((rows) {
        final labels = <String, String>{};
        for (final ticket in rows) {
          final office = ticket.office?.trim();
          if (office == null || office.isEmpty) continue;
          final abbreviated = ticket.officeAbbreviated?.trim();
          labels[office] = (abbreviated != null && abbreviated.isNotEmpty)
              ? abbreviated
              : office;
        }
        final items = labels.entries
            .map((entry) => (office: entry.key, label: entry.value))
            .toList();
        items.sort((a, b) => a.label.compareTo(b.label));
        return items;
      });
});

class TicketsListScreen extends ConsumerWidget {
  const TicketsListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final ticketsAsync = ref.watch(ticketsStreamProvider);
    final auth = ref.watch(authControllerProvider);
    final tab = ref.watch(_tabProvider);
    final dateFmt = DateFormat('dd.MM.yyyy, HH:mm');
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text.rich(
          TextSpan(
            children: [
              TextSpan(
                text: 'ГКУ ОП ',
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: scheme.onSurface,
                  fontSize: 18,
                ),
              ),
              const TextSpan(
                text: 'Заявки',
                style: TextStyle(
                  fontWeight: FontWeight.w700,
                  color: AppColors.primary,
                  fontSize: 18,
                ),
              ),
            ],
          ),
        ),
        actions: [
          if (auth.user != null)
            Padding(
              padding: const EdgeInsets.only(right: 4),
              child: Center(
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      width: 8,
                      height: 8,
                      decoration: const BoxDecoration(
                        color: AppColors.success,
                        shape: BoxShape.circle,
                      ),
                    ),
                    const SizedBox(width: 6),
                    Text(
                      auth.user!.username,
                      style: TextStyle(
                        fontSize: 13,
                        color: scheme.onSurfaceVariant,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          const AppHeaderMenuButton(),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: Row(
              children: [
                _TabChip(
                  label: 'Активные',
                  icon: Icons.description_outlined,
                  selected: tab == TicketsTab.active,
                  onTap: () =>
                      ref.read(_tabProvider.notifier).state = TicketsTab.active,
                ),
                const SizedBox(width: 8),
                _TabChip(
                  label: 'Задачи',
                  icon: Icons.checklist_outlined,
                  selected: tab == TicketsTab.tasks,
                  onTap: () =>
                      ref.read(_tabProvider.notifier).state = TicketsTab.tasks,
                ),
                const SizedBox(width: 8),
                _TabChip(
                  label: 'Архив',
                  icon: Icons.folder_outlined,
                  selected: tab == TicketsTab.archived,
                  onTap: () => ref.read(_tabProvider.notifier).state =
                      TicketsTab.archived,
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
            child: _OfficeFilter(),
          ),
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
            child: TextField(
              decoration: const InputDecoration(
                hintText:
                    'Поиск: № заявки, серийный, инв. номер, тема…',
                suffixIcon: Icon(Icons.search, size: 20),
              ),
              onChanged: (v) => ref.read(_searchProvider.notifier).state = v,
            ),
          ),
          Expanded(
            child: ticketsAsync.when(
              data: (items) {
                if (items.isEmpty) {
                  return Center(
                    child: Text(
                      'Нет заявок в локальной базе.\nВыполните синхронизацию.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: scheme.onSurfaceVariant),
                    ),
                  );
                }
                return RefreshIndicator(
                  color: AppColors.primary,
                  onRefresh: () async {
                    final u = auth.user?.username;
                    if (u == null) return;
                    await ref
                        .read(syncEngineProvider)
                        .sync(username: u, reason: SyncReason.manual);
                  },
                  child: ListView.separated(
                    padding: const EdgeInsets.fromLTRB(12, 0, 12, 16),
                    itemCount: items.length + 1,
                    separatorBuilder: (_, __) => const SizedBox(height: 10),
                    itemBuilder: (context, index) {
                      if (index == 0) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 4, top: 4),
                          child: Text(
                            'Найдено заявок: ${items.length}',
                            style: TextStyle(
                              fontSize: 13,
                              color: scheme.onSurfaceVariant,
                            ),
                          ),
                        );
                      }
                      final t = items[index - 1];
                      return _TicketCard(
                        ticket: t,
                        dateFmt: dateFmt,
                        onTap: () =>
                            context.push('/tickets/${t.ticketNumber}'),
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

class _TicketCard extends StatelessWidget {
  const _TicketCard({
    required this.ticket,
    required this.dateFmt,
    required this.onTap,
  });

  final Ticket ticket;
  final DateFormat dateFmt;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final pending = ticket.syncStatus != SyncStatuses.synced;
    final office = ticket.officeAbbreviated ?? ticket.office;
    final cabinet = ticket.cabinet;
    final officeCabinet = (office != null && office.isNotEmpty)
        ? (cabinet != null && cabinet.isNotEmpty ? '$office / $cabinet' : office)
        : (cabinet ?? '');
    final requiredAction = ticket.requiredAction?.trim();
    final component = ticket.component?.trim();
    final hasRequired =
        requiredAction != null &&
        requiredAction.isNotEmpty &&
        requiredAction != '—';
    final hasComponent =
        component != null && component.isNotEmpty && component != '—';

    return Material(
      color: scheme.surface,
      borderRadius: BorderRadius.circular(10),
      elevation: 1,
      shadowColor: Colors.black.withValues(alpha: 0.08),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: onTap,
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: scheme.outlineVariant),
          ),
          padding: const EdgeInsets.fromLTRB(14, 12, 14, 10),
          child: Column(
            children: [
              _CardRow(
                label: '№ заявки',
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    if (ticket.isTask)
                      const Padding(
                        padding: EdgeInsets.only(right: 6),
                        child: Text('🔵', style: TextStyle(fontSize: 12)),
                      ),
                    Flexible(
                      child: Text(
                        '#${ticket.ticketNumber}',
                        style: const TextStyle(
                          color: Color(0xFF1976D2),
                          fontWeight: FontWeight.w700,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    if (ticket.hasFiles)
                      const Padding(
                        padding: EdgeInsets.only(left: 4),
                        child: Text('📎', style: TextStyle(fontSize: 13)),
                      ),
                    if (ticket.hasComments)
                      const Padding(
                        padding: EdgeInsets.only(left: 4),
                        child: Text('💬', style: TextStyle(fontSize: 12)),
                      ),
                    if (pending)
                      Padding(
                        padding: const EdgeInsets.only(left: 6),
                        child: Icon(
                          Icons.cloud_upload_outlined,
                          size: 14,
                          color: scheme.onSurfaceVariant,
                        ),
                      ),
                  ],
                ),
              ),
              _CardRow(
                label: 'Статус',
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    StatusBadge(status: ticket.status),
                    if (ticket.status != null &&
                        ticket.status!.toLowerCase().contains('выполн') &&
                        ticket.completedAt != null)
                      Padding(
                        padding: const EdgeInsets.only(top: 2),
                        child: Text(
                          dateFmt.format(ticket.completedAt!.toLocal()),
                          style: TextStyle(
                            fontSize: 11,
                            color: scheme.onSurfaceVariant,
                          ),
                        ),
                      ),
                  ],
                ),
              ),
              if ((ticket.equipmentLabel != null &&
                      ticket.equipmentLabel!.trim().isNotEmpty) ||
                  (ticket.inventoryNumber != null &&
                      ticket.inventoryNumber!.trim().isNotEmpty))
                _CardRow(
                  label: ticket.equipmentLabel != null &&
                          ticket.equipmentLabel!.trim().isNotEmpty
                      ? 'Аппарат'
                      : 'Инв. номер',
                  child: Text(
                    (ticket.equipmentLabel != null &&
                            ticket.equipmentLabel!.trim().isNotEmpty)
                        ? ticket.equipmentLabel!
                        : ticket.inventoryNumber!,
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
              if (hasRequired)
                _CardRow(
                  label: 'Требуется',
                  child: Text(
                    requiredAction,
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
              if (hasComponent)
                _CardRow(
                  label: 'Комплектующее',
                  child: ComponentPill(text: component),
                ),
              if (officeCabinet.isNotEmpty)
                _CardRow(
                  label: 'Кабинет',
                  child: Text(
                    officeCabinet,
                    textAlign: TextAlign.right,
                    style: const TextStyle(fontSize: 14),
                  ),
                ),
              if (ticket.lastUpdatedDate != null)
                _CardRow(
                  label: 'Обновлено',
                  child: Text(
                    dateFmt.format(ticket.lastUpdatedDate!.toLocal()),
                    textAlign: TextAlign.right,
                    style: TextStyle(
                      fontSize: 13,
                      color: scheme.onSurfaceVariant,
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _CardRow extends StatelessWidget {
  const _CardRow({required this.label, required this.child});

  final String label;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label.toUpperCase(),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.w500,
                color: muted,
                letterSpacing: 0.2,
              ),
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Align(alignment: Alignment.centerRight, child: child),
          ),
        ],
      ),
    );
  }
}

class _TabChip extends StatelessWidget {
  const _TabChip({
    required this.label,
    required this.selected,
    required this.onTap,
    this.icon,
  });

  final String label;
  final bool selected;
  final VoidCallback onTap;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Expanded(
      child: Material(
        color: selected ? const Color(0xFF2F80ED) : scheme.surface,
        borderRadius: BorderRadius.circular(10),
        child: InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(10),
          child: Container(
            alignment: Alignment.center,
            padding: const EdgeInsets.symmetric(vertical: 10),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(10),
              border: Border.all(
                color: selected ? const Color(0xFF2F80ED) : scheme.outline,
              ),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                if (icon != null) ...[
                  Icon(
                    icon,
                    size: 16,
                    color: selected ? Colors.white : scheme.onSurfaceVariant,
                  ),
                  const SizedBox(width: 4),
                ],
                Flexible(
                  child: Text(
                    label,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: selected ? Colors.white : scheme.onSurface,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _OfficeFilter extends ConsumerWidget {
  const _OfficeFilter();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final offices = ref.watch(_officesProvider).valueOrNull ?? const [];
    final selected = ref.watch(_officeProvider);
    final scheme = Theme.of(context).colorScheme;
    String selectedLabel = 'Все адреса';
    if (selected != null) {
      selectedLabel = selected;
      for (final item in offices) {
        if (item.office == selected) {
          selectedLabel = item.label;
          break;
        }
      }
    }

    // Единый Material-вид на Android и iOS: нативный DropdownButtonFormField
    // на iOS выглядит иначе (стрелка/меню/поле).
    return Material(
      color: Colors.transparent,
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _pickOffice(
          context: context,
          ref: ref,
          offices: offices,
          selected: selected,
        ),
        child: InputDecorator(
          isEmpty: false,
          decoration: const InputDecoration(
            labelText: 'Адрес',
            isDense: true,
            suffixIcon: Icon(Icons.arrow_drop_down, size: 24),
          ),
          child: Text(
            selectedLabel,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              fontSize: 14,
              color: scheme.onSurface,
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _pickOffice({
    required BuildContext context,
    required WidgetRef ref,
    required List<({String office, String label})> offices,
    required String? selected,
  }) async {
    final scheme = Theme.of(context).colorScheme;
    final picked = await showModalBottomSheet<Object>(
      context: context,
      showDragHandle: true,
      isScrollControlled: true,
      builder: (ctx) {
        final maxHeight = MediaQuery.sizeOf(ctx).height * 0.6;
        return SafeArea(
          child: SizedBox(
            height: maxHeight,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
                  child: Text(
                    'Адрес',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: scheme.onSurface,
                    ),
                  ),
                ),
                Expanded(
                  child: ListView.builder(
                    itemCount: offices.length + 1,
                    itemBuilder: (context, index) {
                      if (index == 0) {
                        final isSelected = selected == null;
                        return ListTile(
                          title: const Text('Все адреса'),
                          trailing: isSelected
                              ? Icon(Icons.check, color: scheme.primary)
                              : null,
                          selected: isSelected,
                          onTap: () => Navigator.pop(ctx, _OfficeFilterClear.instance),
                        );
                      }
                      final item = offices[index - 1];
                      final isSelected = item.office == selected;
                      return ListTile(
                        title: Text(
                          item.label,
                          maxLines: 2,
                          overflow: TextOverflow.ellipsis,
                        ),
                        trailing: isSelected
                            ? Icon(Icons.check, color: scheme.primary)
                            : null,
                        selected: isSelected,
                        onTap: () => Navigator.pop(ctx, item.office),
                      );
                    },
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );

    if (picked == null) return;
    if (picked is _OfficeFilterClear) {
      ref.read(_officeProvider.notifier).state = null;
      return;
    }
    if (picked is String) {
      ref.read(_officeProvider.notifier).state = picked;
    }
  }
}

/// Sentinel: отличить «Все адреса» от закрытия sheet без выбора (null).
class _OfficeFilterClear {
  const _OfficeFilterClear._();
  static const instance = _OfficeFilterClear._();
}
