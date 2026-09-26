import 'dart:io';

import 'package:drift/drift.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:uuid/uuid.dart';

import '../../../../core/database/app_database.dart';
import '../../../../core/network/api_client.dart';
import '../../../../core/sync/sync_engine.dart';

class TicketsRepository {
  TicketsRepository({
    required AppDatabase db,
    required SyncEngine syncEngine,
    required ApiClient api,
  }) : _db = db,
       _sync = syncEngine,
       _api = api;

  final AppDatabase _db;
  final SyncEngine _sync;
  final ApiClient _api;
  final _uuid = const Uuid();

  Stream<List<Ticket>> watchTickets({
    required String username,
    bool archived = false,
    bool tasksOnly = false,
    String? search,
  }) {
    return _db.watchTicketsForAccount(
      username,
      archived: archived,
      tasksOnly: tasksOnly,
      search: search,
    );
  }

  Future<Ticket?> getTicket(String username, String ticketNumber) {
    return _db.getTicketByNumber(username, ticketNumber);
  }

  Stream<List<TicketAttachment>> watchAttachments({
    required String username,
    required String ticketNumber,
  }) {
    return _db.watchAttachments(username, ticketNumber);
  }

  /// Подтягивает список файлов с сервера в локальную БД (для просмотра).
  Future<int> refreshAttachmentsFromServer({
    required String username,
    required String ticketNumber,
  }) async {
    final response = await _api.get('/api/tickets/$ticketNumber/images');
    final body = response.data;
    if (body is! Map) return 0;
    final images = (body['images'] as List?) ?? [];
    var count = 0;
    await _db.transaction(() async {
      for (final raw in images) {
        if (raw is! Map) continue;
        final data = Map<String, dynamic>.from(raw);
        final serverId = (data['id'] as num?)?.toInt();
        if (serverId == null) continue;
        if (data['is_deleted'] == true) continue;
        final localId = serverId.toString();
        final existing =
            await (_db.select(_db.ticketAttachments)..where(
                  (t) =>
                      t.accountUsername.equals(username) &
                      t.localId.equals(localId),
                ))
                .getSingleOrNull();
        // Не затираем pending локальные загрузки
        if (existing != null &&
            existing.syncStatus == SyncStatuses.pendingCreate) {
          continue;
        }
        await _db
            .into(_db.ticketAttachments)
            .insertOnConflictUpdate(
              TicketAttachmentsCompanion(
                localId: Value(localId),
                serverId: Value(serverId),
                ticketNumber: Value(ticketNumber),
                originalFilename: Value(
                  data['original_filename'] as String?,
                ),
                mimeType: Value(data['mime_type'] as String?),
                fileSize: Value((data['file_size'] as num?)?.toInt()),
                downloadUrl: Value(
                  data['download_url'] as String? ??
                      '/api/images/$serverId/download',
                ),
                thumbnailUrl: Value(
                  data['thumbnail_url'] as String? ??
                      '/api/images/$serverId/thumbnail',
                ),
                isDeleted: const Value(false),
                uploadedAt: Value(
                  data['uploaded_at'] != null
                      ? DateTime.tryParse(
                          data['uploaded_at'].toString(),
                        )?.toUtc()
                      : null,
                ),
                accountUsername: Value(username),
                syncStatus: const Value(SyncStatuses.synced),
                localUpdatedAt: Value(DateTime.now().toUtc()),
                localFilePath: existing?.localFilePath != null
                    ? Value(existing!.localFilePath)
                    : const Value.absent(),
              ),
            );
        count++;
      }
      if (count > 0) {
        final ticket = await _db.getTicketByNumber(username, ticketNumber);
        if (ticket != null) {
          await (_db.update(
            _db.tickets,
          )..where((t) => t.localId.equals(ticket.localId))).write(
            const TicketsCompanion(hasFiles: Value(true)),
          );
        }
      }
    });
    return count;
  }

  /// Скачивает файл на диск (если ещё нет локальной копии) и возвращает путь.
  Future<String> ensureAttachmentLocalFile({
    required String username,
    required String localId,
  }) async {
    final row =
        await (_db.select(_db.ticketAttachments)..where(
              (t) =>
                  t.accountUsername.equals(username) &
                  t.localId.equals(localId),
            ))
            .getSingleOrNull();
    if (row == null) {
      throw StateError('Вложение не найдено');
    }
    final existing = row.localFilePath;
    if (existing != null && await File(existing).exists()) {
      return existing;
    }
    final serverId = row.serverId;
    if (serverId == null) {
      throw StateError('Файл ещё не отправлен на сервер');
    }

    final url = row.downloadUrl ?? '/api/images/$serverId/download';
    final path = url.startsWith('http')
        ? Uri.parse(url).path
        : (url.startsWith('/') ? url : '/$url');
    final bytes = await _api.getBytes(path);

    final docs = await getApplicationDocumentsDirectory();
    final attachDir = Directory(
      p.join(docs.path, 'attachments', username, row.ticketNumber),
    );
    if (!await attachDir.exists()) {
      await attachDir.create(recursive: true);
    }
    final name = row.originalFilename ?? 'file_$serverId';
    final dest = p.join(attachDir.path, '${serverId}_$name');
    await File(dest).writeAsBytes(bytes, flush: true);

    await (_db.update(
      _db.ticketAttachments,
    )..where((t) => t.localId.equals(localId))).write(
      TicketAttachmentsCompanion(localFilePath: Value(dest)),
    );
    return dest;
  }

  /// Offline-first update: локально + outbox в одной транзакции.
  Future<void> updateTicketFields({
    required String username,
    required String ticketNumber,
    required Map<String, String?> fields,
  }) async {
    final ticket = await _db.getTicketByNumber(username, ticketNumber);
    if (ticket == null) {
      throw StateError('Заявка не найдена локально');
    }

    final ifMatch = ticket.lastUpdatedDate?.toUtc().toIso8601String();

    await _db.transaction(() async {
      await (_db.update(
        _db.tickets,
      )..where((t) => t.localId.equals(ticket.localId))).write(
        TicketsCompanion(
          inventoryNumber: fields.containsKey('inventory_number')
              ? Value(fields['inventory_number'])
              : const Value.absent(),
          printerModel: fields.containsKey('printer_model')
              ? Value(fields['printer_model'])
              : const Value.absent(),
          office: fields.containsKey('office')
              ? Value(fields['office'])
              : const Value.absent(),
          cabinet: fields.containsKey('cabinet')
              ? Value(fields['cabinet'])
              : const Value.absent(),
          component: fields.containsKey('component')
              ? Value(fields['component'])
              : const Value.absent(),
          status: fields.containsKey('status')
              ? Value(fields['status'])
              : const Value.absent(),
          currentNote: fields.containsKey('current_note')
              ? Value(fields['current_note'])
              : const Value.absent(),
          requiredAction: fields.containsKey('required_action')
              ? Value(fields['required_action'])
              : const Value.absent(),
          cause: fields.containsKey('cause')
              ? Value(fields['cause'])
              : const Value.absent(),
          faultDescription: fields.containsKey('fault_description')
              ? Value(fields['fault_description'])
              : const Value.absent(),
          workDone: fields.containsKey('work_done')
              ? Value(fields['work_done'])
              : const Value.absent(),
          techConclusion: fields.containsKey('tech_conclusion')
              ? Value(fields['tech_conclusion'])
              : const Value.absent(),
          department: fields.containsKey('department')
              ? Value(fields['department'])
              : const Value.absent(),
          syncStatus: const Value(SyncStatuses.pendingUpdate),
          localUpdatedAt: Value(DateTime.now().toUtc()),
        ),
      );

      await _sync.enqueue(
        username: username,
        entityType: 'ticket',
        entityLocalId: ticket.localId,
        entityServerId: ticketNumber,
        operation: 'UPDATE_TICKET',
        payload: {
          'ticket_number': ticketNumber,
          'if_match': ifMatch,
          'fields': fields,
        },
      );
    });

    // Fire-and-forget sync
    // ignore: unawaited_futures
    _sync.sync(username: username, reason: SyncReason.localMutation);
  }

  Future<void> addComment({
    required String username,
    required String ticketNumber,
    required String text,
  }) async {
    final localId = _uuid.v4();
    await _db.transaction(() async {
      await _db
          .into(_db.userComments)
          .insert(
            UserCommentsCompanion.insert(
              localId: localId,
              ticketNumber: ticketNumber,
              authorUsername: Value(username),
              authorName: Value(username),
              commentText: text,
              createdAt: Value(DateTime.now().toUtc()),
              accountUsername: username,
              syncStatus: const Value(SyncStatuses.pendingCreate),
              localUpdatedAt: DateTime.now().toUtc(),
            ),
          );
      await _sync.enqueue(
        username: username,
        entityType: 'user_comment',
        entityLocalId: localId,
        operation: 'ADD_COMMENT',
        payload: {'ticket_number': ticketNumber, 'comment_text': text},
      );
    });
    // ignore: unawaited_futures
    _sync.sync(username: username, reason: SyncReason.localMutation);
  }

  Future<void> completeTicket({
    required String username,
    required String ticketNumber,
  }) async {
    final ticket = await _db.getTicketByNumber(username, ticketNumber);
    if (ticket == null) return;
    await _db.transaction(() async {
      await (_db.update(
        _db.tickets,
      )..where((t) => t.localId.equals(ticket.localId))).write(
        TicketsCompanion(
          status: const Value('Выполнено'),
          completedAt: Value(DateTime.now().toUtc()),
          syncStatus: const Value(SyncStatuses.pendingUpdate),
          localUpdatedAt: Value(DateTime.now().toUtc()),
        ),
      );
      await _sync.enqueue(
        username: username,
        entityType: 'ticket',
        entityLocalId: ticket.localId,
        operation: 'COMPLETE_TICKET',
        payload: {'ticket_number': ticketNumber},
      );
    });
    // ignore: unawaited_futures
    _sync.sync(username: username, reason: SyncReason.localMutation);
  }

  /// Offline-first: файл копируется в app documents, затем outbox UPLOAD.
  Future<TicketAttachment> addAttachment({
    required String username,
    required String ticketNumber,
    required String sourcePath,
    String? originalFilename,
    String? mimeType,
  }) async {
    final ticket = await _db.getTicketByNumber(username, ticketNumber);
    if (ticket == null) {
      throw StateError('Заявка не найдена локально');
    }

    final source = File(sourcePath);
    if (!await source.exists()) {
      throw StateError('Файл не найден: $sourcePath');
    }

    final localId = _uuid.v4();
    final docs = await getApplicationDocumentsDirectory();
    final attachDir = Directory(
      p.join(docs.path, 'attachments', username, ticketNumber),
    );
    if (!await attachDir.exists()) {
      await attachDir.create(recursive: true);
    }

    final name = originalFilename ?? p.basename(sourcePath);
    final ext = p.extension(name);
    final destPath = p.join(attachDir.path, '$localId$ext');
    await source.copy(destPath);
    final size = await File(destPath).length();
    final now = DateTime.now().toUtc();

    late TicketAttachment row;
    await _db.transaction(() async {
      await _db
          .into(_db.ticketAttachments)
          .insert(
            TicketAttachmentsCompanion.insert(
              localId: localId,
              ticketNumber: ticketNumber,
              originalFilename: Value(name),
              mimeType: Value(mimeType),
              fileSize: Value(size),
              localFilePath: Value(destPath),
              uploadedAt: Value(now),
              accountUsername: username,
              syncStatus: const Value(SyncStatuses.pendingCreate),
              localUpdatedAt: now,
            ),
          );

      await (_db.update(
        _db.tickets,
      )..where((t) => t.localId.equals(ticket.localId))).write(
        TicketsCompanion(
          hasFiles: const Value(true),
          localUpdatedAt: Value(now),
        ),
      );

      await _sync.enqueue(
        username: username,
        entityType: 'ticket_image',
        entityLocalId: localId,
        entityServerId: ticketNumber,
        operation: 'UPLOAD_ATTACHMENT',
        payload: {
          'ticket_number': ticketNumber,
          'local_file_path': destPath,
          'original_filename': name,
          'mime_type': mimeType,
        },
      );

      row = (await (_db.select(
        _db.ticketAttachments,
      )..where((t) => t.localId.equals(localId))).getSingle());
    });

    // ignore: unawaited_futures
    _sync.sync(username: username, reason: SyncReason.localMutation);
    return row;
  }

  Future<void> deleteAttachment({
    required String username,
    required String localId,
  }) async {
    final row =
        await (_db.select(_db.ticketAttachments)
              ..where(
                (t) =>
                    t.accountUsername.equals(username) &
                    t.localId.equals(localId),
              ))
            .getSingleOrNull();
    if (row == null) return;

    await _db.transaction(() async {
      if (row.serverId == null &&
          row.syncStatus == SyncStatuses.pendingCreate) {
        await (_db.delete(
          _db.ticketAttachments,
        )..where((t) => t.localId.equals(localId))).go();
        await (_db.delete(_db.syncOutbox)..where(
              (o) =>
                  o.entityLocalId.equals(localId) &
                  o.operation.equals('UPLOAD_ATTACHMENT') &
                  o.status.equals('pending'),
            ))
            .go();
        final localPath = row.localFilePath;
        if (localPath != null) {
          final f = File(localPath);
          if (await f.exists()) await f.delete();
        }
        return;
      }

      await (_db.update(
        _db.ticketAttachments,
      )..where((t) => t.localId.equals(localId))).write(
        TicketAttachmentsCompanion(
          isDeleted: const Value(true),
          syncStatus: const Value(SyncStatuses.pendingDelete),
          localUpdatedAt: Value(DateTime.now().toUtc()),
        ),
      );
      await _sync.enqueue(
        username: username,
        entityType: 'ticket_image',
        entityLocalId: localId,
        entityServerId: row.serverId?.toString(),
        operation: 'DELETE_ATTACHMENT',
        payload: {
          'ticket_number': row.ticketNumber,
          'server_id': row.serverId,
        },
      );
    });
    // ignore: unawaited_futures
    _sync.sync(username: username, reason: SyncReason.localMutation);
  }
}
