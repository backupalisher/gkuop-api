import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:open_filex/open_filex.dart';

import '../../app/theme/app_colors.dart';
import '../../app/theme/theme_controller.dart';
import '../../core/di/providers.dart';
import '../../features/auth/data/repositories/auth_repository.dart';

/// Гамбургер-меню как в веб-шапке: синхронизация, тема, админ-пункты, выход.
class AppHeaderMenuButton extends ConsumerWidget {
  const AppHeaderMenuButton({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final auth = ref.watch(authControllerProvider);
    final user = auth.user;
    final themeMode = ref.watch(themeControllerProvider);
    final themeCtrl = ref.read(themeControllerProvider.notifier);

    return PopupMenuButton<_MenuAction>(
      tooltip: 'Меню',
      icon: const Icon(Icons.menu),
      onSelected: (action) => _onSelected(context, ref, action, user),
      itemBuilder: (context) {
        final items = <PopupMenuEntry<_MenuAction>>[
          PopupMenuItem(
            value: _MenuAction.sync,
            child: const ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.sync, size: 20),
              title: Text('Синхронизация'),
            ),
          ),
          PopupMenuItem(
            value: _MenuAction.theme,
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(
                themeMode == ThemeMode.dark
                    ? Icons.dark_mode
                    : themeMode == ThemeMode.light
                    ? Icons.light_mode
                    : Icons.brightness_auto,
                size: 20,
              ),
              title: Text('Тема: ${themeCtrl.label}'),
            ),
          ),
        ];

        if (user != null &&
            (user.isAdmin || user.hasPermission('view_users'))) {
          items.add(const PopupMenuDivider());
          items.add(
            const PopupMenuItem(
              value: _MenuAction.users,
              child: ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.people_outline, size: 20),
                title: Text('Пользователи'),
              ),
            ),
          );
        }

        if (user != null && user.hasPermission('rebuild_data')) {
          items.add(
            const PopupMenuItem(
              value: _MenuAction.rebuild,
              child: ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.refresh, size: 20),
                title: Text('Обновить данные'),
              ),
            ),
          );
          items.add(
            const PopupMenuItem(
              value: _MenuAction.rebuildFromDate,
              child: ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.date_range, size: 20),
                title: Text('Обновить данные с…'),
              ),
            ),
          );
        }

        if (user != null && user.isAdmin) {
          items.add(
            const PopupMenuItem(
              value: _MenuAction.exportDb,
              child: ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.download_outlined, size: 20),
                title: Text('Выгрузить БД'),
              ),
            ),
          );
          items.add(
            const PopupMenuItem(
              value: _MenuAction.importDb,
              child: ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.upload_file_outlined, size: 20),
                title: Text('Загрузить БД'),
              ),
            ),
          );
        }

        items.add(const PopupMenuDivider());
        items.add(
          const PopupMenuItem(
            value: _MenuAction.logout,
            child: ListTile(
              dense: true,
              contentPadding: EdgeInsets.zero,
              leading: Icon(Icons.logout, size: 20, color: AppColors.error),
              title: Text('Выйти', style: TextStyle(color: AppColors.error)),
            ),
          ),
        );
        return items;
      },
    );
  }

  Future<void> _onSelected(
    BuildContext context,
    WidgetRef ref,
    _MenuAction action,
    AuthUser? user,
  ) async {
    switch (action) {
      case _MenuAction.sync:
        context.push('/sync');
      case _MenuAction.theme:
        await ref.read(themeControllerProvider.notifier).cycle();
      case _MenuAction.users:
        context.push('/admin/users');
      case _MenuAction.rebuild:
        await _confirmRebuild(context, ref, sinceDate: null);
      case _MenuAction.rebuildFromDate:
        final date = await _pickDate(context);
        if (date != null && context.mounted) {
          await _confirmRebuild(context, ref, sinceDate: date);
        }
      case _MenuAction.exportDb:
        await _exportDb(context, ref);
      case _MenuAction.importDb:
        await _importDb(context, ref);
      case _MenuAction.logout:
        await ref.read(authControllerProvider.notifier).logout();
    }
  }

  Future<String?> _pickDate(BuildContext context) async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      initialDate: now,
      firstDate: DateTime(2020),
      lastDate: now,
      helpText: 'Дата начала обновления',
      cancelText: 'Отмена',
      confirmText: 'Обновить',
    );
    if (picked == null) return null;
    final y = picked.year.toString().padLeft(4, '0');
    final m = picked.month.toString().padLeft(2, '0');
    final d = picked.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  Future<void> _confirmRebuild(
    BuildContext context,
    WidgetRef ref, {
    required String? sinceDate,
  }) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Обновить данные'),
        content: Text(
          sinceDate == null
              ? 'Запустить полную перестройку данных с сервера почты?'
              : 'Обновить данные начиная с $sinceDate?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Запустить'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;
    context.push('/admin/rebuild', extra: sinceDate);
  }

  Future<void> _exportDb(BuildContext context, WidgetRef ref) async {
    final messenger = ScaffoldMessenger.of(context);
    messenger.showSnackBar(
      const SnackBar(content: Text('Выгрузка дампа БД…')),
    );
    try {
      final file = await ref.read(adminRepositoryProvider).exportDatabaseDump();
      messenger.hideCurrentSnackBar();
      await OpenFilex.open(file.path);
      messenger.showSnackBar(
        SnackBar(content: Text('Дамп сохранён: ${file.path}')),
      );
    } catch (e) {
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(content: Text('Ошибка выгрузки: $e')),
      );
    }
  }

  Future<void> _importDb(BuildContext context, WidgetRef ref) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Загрузить БД'),
        content: const Text(
          'Текущая база на сервере будет заменена дампом. Продолжить?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Выбрать файл'),
          ),
        ],
      ),
    );
    if (ok != true || !context.mounted) return;

    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: const ['dump'],
    );
    final path = result?.files.single.path;
    if (path == null || !context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    messenger.showSnackBar(
      const SnackBar(content: Text('Загрузка дампа…')),
    );
    try {
      await ref.read(adminRepositoryProvider).importDatabaseDump(path);
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        const SnackBar(content: Text('Дамп загружен. Запустите синхронизацию.')),
      );
    } catch (e) {
      messenger.hideCurrentSnackBar();
      messenger.showSnackBar(
        SnackBar(content: Text('Ошибка загрузки: $e')),
      );
    }
  }
}

enum _MenuAction {
  sync,
  theme,
  users,
  rebuild,
  rebuildFromDate,
  exportDb,
  importDb,
  logout,
}
