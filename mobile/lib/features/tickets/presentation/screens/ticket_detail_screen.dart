import 'dart:io';

import 'package:cached_network_image/cached_network_image.dart';
import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:open_filex/open_filex.dart';

import '../../../../app/theme/app_colors.dart';
import '../../../../core/database/app_database.dart';
import '../../../../core/di/providers.dart';
import '../../../../core/errors/failures.dart';
import '../../../../shared/widgets/component_pill.dart';
import '../../../../shared/widgets/status_badge.dart';

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

final attachmentsProvider =
    StreamProvider.autoDispose.family<List<TicketAttachment>, String>((
      ref,
      ticketNumber,
    ) {
      final user = ref.watch(authControllerProvider).user;
      if (user == null) return const Stream.empty();
      return ref.watch(ticketsRepositoryProvider).watchAttachments(
            username: user.username,
            ticketNumber: ticketNumber,
          );
    });

class TicketDetailScreen extends ConsumerStatefulWidget {
  const TicketDetailScreen({super.key, required this.ticketNumber});

  final String ticketNumber;

  @override
  ConsumerState<TicketDetailScreen> createState() => _TicketDetailScreenState();
}

class _TicketDetailScreenState extends ConsumerState<TicketDetailScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _loadRemoteAttachments());
  }

  Future<void> _loadRemoteAttachments() async {
    final user = ref.read(authControllerProvider).user;
    if (user == null) return;
    try {
      await ref.read(ticketsRepositoryProvider).refreshAttachmentsFromServer(
            username: user.username,
            ticketNumber: widget.ticketNumber,
          );
    } catch (_) {
      // Оффлайн — показываем только локальные
    }
  }

  @override
  Widget build(BuildContext context) {
    final async = ref.watch(ticketProvider(widget.ticketNumber));
    final auth = ref.watch(authControllerProvider);
    final canEdit = auth.user?.hasPermission('edit_tickets') ?? false;
    final canComplete = auth.user?.hasPermission('complete_tickets') ?? false;
    final canComment = auth.user?.hasPermission('add_comments') ?? false;
    final canUpload = auth.user?.hasPermission('upload_images') ?? false;
    final canDeleteImg = auth.user?.hasPermission('delete_images') ?? false;
    final dateFmt = DateFormat('dd.MM.yyyy, HH:mm');
    final scheme = Theme.of(context).colorScheme;

    return Scaffold(
      appBar: AppBar(title: Text('Заявка #${widget.ticketNumber}')),
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
                  color: scheme.primaryContainer.withValues(alpha: 0.35),
                  child: const ListTile(
                    leading: Icon(Icons.cloud_upload_outlined),
                    title: Text('Ожидает отправки'),
                    dense: true,
                  ),
                ),
              const SizedBox(height: 4),
              Row(
                children: [
                  Expanded(
                    child: Text(
                      '#${t.ticketNumber}',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFF1976D2),
                      ),
                    ),
                  ),
                  StatusBadge(status: t.status),
                ],
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.fromLTRB(14, 12, 14, 4),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _tile(context, 'Комплектующее', t.component, pill: true),
                      _tile(context, 'Инвентарный номер', t.inventoryNumber),
                      _tile(context, 'Оборудование', t.printerModel),
                      _tile(context, 'Офис', t.office),
                      _tile(context, 'Кабинет', t.cabinet),
                      _tile(context, 'Требуется', t.requiredAction),
                      _tile(context, 'Причина', t.cause),
                      _tile(context, 'Описание', t.faultDescription),
                      _tile(context, 'Работы', t.workDone),
                      _tile(context, 'Тех. вывод', t.techConclusion),
                      _tile(context, 'Примечание', t.currentNote),
                      _tile(
                        context,
                        'Обновлено',
                        t.lastUpdatedDate != null
                            ? dateFmt.format(t.lastUpdatedDate!.toLocal())
                            : null,
                      ),
                      if (t.completedAt != null)
                        _tile(
                          context,
                          'Выполнено',
                          dateFmt.format(t.completedAt!.toLocal()),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              _AttachmentsSection(
                ticketNumber: widget.ticketNumber,
                canUpload: canUpload,
                canDelete: canDeleteImg,
              ),
              const SizedBox(height: 16),
              if (canComplete && t.status != 'Выполнено')
                FilledButton(
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.success,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(vertical: 14),
                  ),
                  onPressed: () async {
                    await ref.read(ticketsRepositoryProvider).completeTicket(
                          username: auth.user!.username,
                          ticketNumber: widget.ticketNumber,
                        );
                    ref.invalidate(ticketProvider(widget.ticketNumber));
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
                  child: const Text('✓ Выполнено'),
                ),
              if (canComment) ...[
                const SizedBox(height: 10),
                OutlinedButton(
                  onPressed: () =>
                      _addComment(context, ref, auth.user!.username),
                  child: const Text('Добавить комментарий'),
                ),
              ],
              if (canEdit) ...[
                const SizedBox(height: 10),
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

  Widget _tile(
    BuildContext context,
    String label,
    String? value, {
    bool pill = false,
  }) {
    if (value == null || value.trim().isEmpty) return const SizedBox.shrink();
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: TextStyle(
              fontSize: 12,
              color: muted,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 4),
          if (pill) ComponentPill(text: value) else Text(value),
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
      await ref.read(ticketsRepositoryProvider).addComment(
            username: username,
            ticketNumber: widget.ticketNumber,
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
      await ref.read(ticketsRepositoryProvider).updateTicketFields(
            username: username,
            ticketNumber: widget.ticketNumber,
            fields: {'current_note': ctrl.text.trim()},
          );
      ref.invalidate(ticketProvider(widget.ticketNumber));
    }
  }
}

class _AttachmentsSection extends ConsumerWidget {
  const _AttachmentsSection({
    required this.ticketNumber,
    required this.canUpload,
    required this.canDelete,
  });

  final String ticketNumber;
  final bool canUpload;
  final bool canDelete;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final async = ref.watch(attachmentsProvider(ticketNumber));
    final scheme = Theme.of(context).colorScheme;
    final config = ref.watch(appConfigProvider);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              children: [
                const Expanded(
                  child: Text(
                    'Файлы',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
                  ),
                ),
                IconButton(
                  tooltip: 'Обновить список',
                  onPressed: () async {
                    final user = ref.read(authControllerProvider).user;
                    if (user == null) return;
                    try {
                      await ref
                          .read(ticketsRepositoryProvider)
                          .refreshAttachmentsFromServer(
                            username: user.username,
                            ticketNumber: ticketNumber,
                          );
                    } catch (e) {
                      if (context.mounted) {
                        final msg = e is AppFailure ? e.message : '$e';
                        ScaffoldMessenger.of(
                          context,
                        ).showSnackBar(SnackBar(content: Text(msg)));
                      }
                    }
                  },
                  icon: const Icon(Icons.refresh, size: 20),
                ),
                if (canUpload)
                  IconButton(
                    tooltip: 'Прикрепить',
                    onPressed: () => _showAttachSheet(context, ref),
                    icon: const Icon(Icons.add_a_photo_outlined),
                  ),
              ],
            ),
            if (canUpload)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: OutlinedButton.icon(
                  onPressed: () => _showAttachSheet(context, ref),
                  icon: const Icon(Icons.cloud_upload_outlined, size: 18),
                  label: const Text('Загрузить файлы'),
                ),
              ),
            async.when(
              data: (items) {
                if (items.isEmpty) {
                  return Text(
                    'Нет прикреплённых файлов',
                    style: TextStyle(
                      color: scheme.onSurfaceVariant,
                      fontSize: 13,
                    ),
                  );
                }
                return FutureBuilder<String?>(
                  future: ref.read(credentialsStoreProvider).readToken(),
                  builder: (context, tokenSnap) {
                    final token = tokenSnap.data;
                    return GridView.builder(
                      shrinkWrap: true,
                      physics: const NeverScrollableScrollPhysics(),
                      itemCount: items.length,
                      gridDelegate:
                          const SliverGridDelegateWithFixedCrossAxisCount(
                            crossAxisCount: 3,
                            mainAxisSpacing: 8,
                            crossAxisSpacing: 8,
                            childAspectRatio: 0.85,
                          ),
                      itemBuilder: (context, index) {
                        final a = items[index];
                        return _AttachmentTile(
                          attachment: a,
                          baseUrl: config.apiBaseUrl,
                          authToken: token,
                          canDelete: canDelete,
                          onOpen: () => _openAttachment(context, ref, a),
                          onDelete: () => _delete(context, ref, a),
                        );
                      },
                    );
                  },
                );
              },
              loading: () => const Padding(
                padding: EdgeInsets.all(12),
                child: Center(child: CircularProgressIndicator(strokeWidth: 2)),
              ),
              error: (e, _) => Text('$e'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _showAttachSheet(BuildContext context, WidgetRef ref) async {
    final choice = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.photo_camera_outlined),
              title: const Text('Камера'),
              onTap: () => Navigator.pop(ctx, 'camera'),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library_outlined),
              title: const Text('Галерея'),
              onTap: () => Navigator.pop(ctx, 'gallery'),
            ),
            ListTile(
              leading: const Icon(Icons.attach_file),
              title: const Text('Файл'),
              onTap: () => Navigator.pop(ctx, 'file'),
            ),
          ],
        ),
      ),
    );
    if (choice == null || !context.mounted) return;
    await _pickAndSave(context, ref, choice);
  }

  Future<void> _pickAndSave(
    BuildContext context,
    WidgetRef ref,
    String source,
  ) async {
    final user = ref.read(authControllerProvider).user;
    if (user == null) return;

    final paths = <({String path, String? name, String? mime})>[];

    if (source == 'camera' || source == 'gallery') {
      final picker = ImagePicker();
      if (source == 'camera') {
        final shot = await picker.pickImage(
          source: ImageSource.camera,
          imageQuality: 85,
          maxWidth: 2400,
        );
        if (shot != null) {
          paths.add((path: shot.path, name: shot.name, mime: shot.mimeType));
        }
      } else {
        final photos = await picker.pickMultiImage(
          imageQuality: 85,
          maxWidth: 2400,
        );
        for (final p in photos) {
          paths.add((path: p.path, name: p.name, mime: p.mimeType));
        }
      }
    } else {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.custom,
        allowedExtensions: const [
          'jpg',
          'jpeg',
          'png',
          'gif',
          'heic',
          'pdf',
          'docx',
          'xlsx',
          'txt',
        ],
      );
      if (result != null) {
        for (final f in result.files) {
          if (f.path != null) {
            paths.add((path: f.path!, name: f.name, mime: null));
          }
        }
      }
    }

    if (paths.isEmpty || !context.mounted) return;

    final messenger = ScaffoldMessenger.of(context);
    var okCount = 0;
    for (final item in paths) {
      try {
        await ref.read(ticketsRepositoryProvider).addAttachment(
              username: user.username,
              ticketNumber: ticketNumber,
              sourcePath: item.path,
              originalFilename: item.name,
              mimeType: item.mime,
            );
        okCount++;
      } catch (e) {
        messenger.showSnackBar(SnackBar(content: Text('Ошибка: $e')));
      }
    }
    if (okCount > 0) {
      messenger.showSnackBar(
        SnackBar(
          content: Text(
            'Сохранено локально: $okCount. Отправка при синхронизации.',
          ),
        ),
      );
    }
  }

  Future<void> _openAttachment(
    BuildContext context,
    WidgetRef ref,
    TicketAttachment a,
  ) async {
    final messenger = ScaffoldMessenger.of(context);
    final config = ref.read(appConfigProvider);
    final isImage = _isImageAttachment(a);

    try {
      final local = a.localFilePath;
      if (local != null && await File(local).exists()) {
        if (!context.mounted) return;
        if (isImage) {
          await Navigator.of(context).push(
            MaterialPageRoute<void>(
              builder: (_) => _ImagePreviewScreen(
                filePath: local,
                title: a.originalFilename ?? 'Фото',
              ),
            ),
          );
        } else {
          await OpenFilex.open(local);
        }
        return;
      }

      // Для изображений сразу открываем сетевой просмотр (без обязательного скачивания).
      if (isImage && a.serverId != null) {
        final token = await ref.read(credentialsStoreProvider).readToken();
        final thumbOrDl =
            a.downloadUrl ?? '/api/images/${a.serverId}/download';
        final url = thumbOrDl.startsWith('http')
            ? thumbOrDl
            : '${config.apiBaseUrl}$thumbOrDl';
        if (!context.mounted) return;
        await Navigator.of(context).push(
          MaterialPageRoute<void>(
            builder: (_) => _ImagePreviewScreen(
              networkUrl: url,
              authToken: token,
              title: a.originalFilename ?? 'Фото',
            ),
          ),
        );
        // Параллельно кэшируем на диск для оффлайна.
        final user = ref.read(authControllerProvider).user;
        if (user != null) {
          // ignore: unawaited_futures
          ref.read(ticketsRepositoryProvider).ensureAttachmentLocalFile(
                username: user.username,
                localId: a.localId,
              );
        }
        return;
      }

      // Документы: скачиваем, затем открываем.
      final user = ref.read(authControllerProvider).user;
      if (user == null) {
        throw StateError('Нет сессии');
      }
      final path = await ref
          .read(ticketsRepositoryProvider)
          .ensureAttachmentLocalFile(
            username: user.username,
            localId: a.localId,
          );
      if (!context.mounted) return;
      await OpenFilex.open(path);
    } catch (e) {
      final msg = e is AppFailure ? e.message : e.toString();
      if (context.mounted) {
        messenger.showSnackBar(SnackBar(content: Text(msg)));
      }
    }
  }

  Future<void> _delete(
    BuildContext context,
    WidgetRef ref,
    TicketAttachment a,
  ) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Удаление файла'),
        content: Text('Удалить «${a.originalFilename ?? 'файл'}»?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Удалить'),
          ),
        ],
      ),
    );
    if (ok != true) return;
    final user = ref.read(authControllerProvider).user;
    if (user == null) return;
    await ref.read(ticketsRepositoryProvider).deleteAttachment(
          username: user.username,
          localId: a.localId,
        );
  }
}

bool _isImageAttachment(TicketAttachment a) {
  final mime = a.mimeType?.toLowerCase() ?? '';
  final name = a.originalFilename?.toLowerCase() ?? '';
  return mime.startsWith('image/') ||
      name.endsWith('.jpg') ||
      name.endsWith('.jpeg') ||
      name.endsWith('.png') ||
      name.endsWith('.gif') ||
      name.endsWith('.heic') ||
      name.endsWith('.webp');
}

class _AttachmentTile extends StatelessWidget {
  const _AttachmentTile({
    required this.attachment,
    required this.baseUrl,
    required this.authToken,
    required this.canDelete,
    required this.onOpen,
    required this.onDelete,
  });

  final TicketAttachment attachment;
  final String baseUrl;
  final String? authToken;
  final bool canDelete;
  final VoidCallback onOpen;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    final pending = attachment.syncStatus != SyncStatuses.synced;
    final scheme = Theme.of(context).colorScheme;
    final local = attachment.localFilePath;
    final hasLocal = local != null && File(local).existsSync();
    final isImage = _isImageAttachment(attachment);

    Widget preview;
    if (isImage && hasLocal) {
      preview = Image.file(File(local), fit: BoxFit.cover);
    } else if (isImage && attachment.serverId != null) {
      final thumbPath =
          attachment.thumbnailUrl ??
          '/api/images/${attachment.serverId}/thumbnail';
      final url = thumbPath.startsWith('http')
          ? thumbPath
          : '$baseUrl$thumbPath';
      preview = CachedNetworkImage(
        imageUrl: url,
        fit: BoxFit.cover,
        httpHeaders: {
          'Accept': 'image/*',
          if (authToken != null) 'Authorization': 'Bearer $authToken',
        },
        placeholder: (_, __) => const Center(
          child: SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(strokeWidth: 2),
          ),
        ),
        errorWidget: (_, __, ___) {
          final dl =
              attachment.downloadUrl ??
              '/api/images/${attachment.serverId}/download';
          final dlUrl = dl.startsWith('http') ? dl : '$baseUrl$dl';
          return CachedNetworkImage(
            imageUrl: dlUrl,
            fit: BoxFit.cover,
            httpHeaders: {
              'Accept': 'image/*',
              if (authToken != null) 'Authorization': 'Bearer $authToken',
            },
            errorWidget: (_, __, ___) => Icon(
              Icons.insert_drive_file_outlined,
              color: scheme.onSurfaceVariant,
            ),
          );
        },
      );
    } else {
      preview = Icon(
        Icons.insert_drive_file_outlined,
        color: scheme.onSurfaceVariant,
        size: 36,
      );
    }

    return Stack(
      children: [
        Positioned.fill(
          child: Material(
            color: scheme.surfaceContainerHighest,
            borderRadius: BorderRadius.circular(8),
            child: InkWell(
              onTap: onOpen,
              borderRadius: BorderRadius.circular(8),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: Column(
                  children: [
                    Expanded(child: preview),
                    Padding(
                      padding: const EdgeInsets.all(4),
                      child: Text(
                        attachment.originalFilename ?? 'файл',
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 10),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
        if (pending)
          Positioned(
            left: 4,
            top: 4,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.warning,
                borderRadius: BorderRadius.circular(4),
              ),
              child: const Text(
                'offline',
                style: TextStyle(fontSize: 9, color: Colors.white),
              ),
            ),
          ),
        if (canDelete)
          Positioned(
            right: 0,
            top: 0,
            child: IconButton(
              visualDensity: VisualDensity.compact,
              iconSize: 18,
              onPressed: onDelete,
              icon: const Icon(Icons.close, color: AppColors.error),
            ),
          ),
      ],
    );
  }
}

class _ImagePreviewScreen extends StatelessWidget {
  const _ImagePreviewScreen({
    required this.title,
    this.filePath,
    this.networkUrl,
    this.authToken,
  });

  final String title;
  final String? filePath;
  final String? networkUrl;
  final String? authToken;

  @override
  Widget build(BuildContext context) {
    Widget image;
    if (filePath != null) {
      image = Image.file(File(filePath!), fit: BoxFit.contain);
    } else if (networkUrl != null) {
      image = CachedNetworkImage(
        imageUrl: networkUrl!,
        fit: BoxFit.contain,
        httpHeaders: {
          'Accept': 'image/*',
          if (authToken != null) 'Authorization': 'Bearer $authToken',
        },
        placeholder: (_, __) => const Center(
          child: CircularProgressIndicator(color: Colors.white),
        ),
        errorWidget: (_, __, ___) => const Center(
          child: Text(
            'Не удалось загрузить изображение',
            style: TextStyle(color: Colors.white70),
          ),
        ),
      );
    } else {
      image = const Center(
        child: Text('Нет данных', style: TextStyle(color: Colors.white70)),
      );
    }

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: Text(title, style: const TextStyle(fontSize: 14)),
      ),
      body: Center(child: InteractiveViewer(child: image)),
    );
  }
}
