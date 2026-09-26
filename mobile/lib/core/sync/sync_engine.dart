import 'dart:async';
import 'dart:convert';

import 'package:dio/dio.dart';
import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../database/app_database.dart';
import '../errors/failures.dart';
import '../network/api_client.dart';

enum SyncReason {
  appStart,
  appResume,
  connectivityRestored,
  manual,
  background,
  localMutation,
}

class SyncResult {
  const SyncResult({
    required this.success,
    this.pushed = 0,
    this.pulled = 0,
    this.message,
  });

  final bool success;
  final int pushed;
  final int pulled;
  final String? message;
}

/// Центральный Sync Engine (single-flight).
class SyncEngine {
  SyncEngine({required AppDatabase db, required ApiClient api})
    : _db = db,
      _api = api;

  final AppDatabase _db;
  final ApiClient _api;
  final _uuid = const Uuid();

  bool _running = false;
  Completer<SyncResult>? _inflight;

  Future<SyncResult> sync({
    required String username,
    SyncReason reason = SyncReason.manual,
  }) async {
    if (_running && _inflight != null) {
      return _inflight!.future;
    }
    _running = true;
    _inflight = Completer<SyncResult>();
    try {
      final result = await _run(username);
      _inflight!.complete(result);
      return result;
    } catch (e) {
      final fail = SyncResult(success: false, message: e.toString());
      _inflight!.complete(fail);
      return fail;
    } finally {
      _running = false;
      _inflight = null;
    }
  }

  Future<SyncResult> _run(String username) async {
    await _touchAttempt(username);
    await _compactOutbox(username);

    var pushed = 0;
    var pulled = 0;

    // Health probe
    try {
      await _api.get('/api/health');
    } on AppFailure catch (e) {
      await _setError(username, e.message);
      return SyncResult(success: false, message: e.message);
    }

    // PUSH
    final pending =
        await (_db.select(_db.syncOutbox)
              ..where(
                (o) =>
                    o.accountUsername.equals(username) &
                    o.status.equals('pending'),
              )
              ..orderBy([(o) => OrderingTerm.asc(o.createdAt)]))
            .get();

    for (final op in pending) {
      try {
        await _pushOne(op);
        await (_db.update(_db.syncOutbox)..where((t) => t.id.equals(op.id)))
            .write(const SyncOutboxCompanion(status: Value('completed')));
        pushed++;
      } on ConflictFailure catch (e) {
        await _markConflict(op, e);
      } on AppFailure catch (e) {
        if (e is AuthenticationFailure ||
            e is AuthorizationFailure ||
            e is ValidationFailure) {
          await (_db.update(
            _db.syncOutbox,
          )..where((t) => t.id.equals(op.id))).write(
            SyncOutboxCompanion(
              status: const Value('failed'),
              lastError: Value(e.message),
              retryCount: Value(op.retryCount + 1),
            ),
          );
        } else {
          final delayMin = _backoffMinutes(op.retryCount);
          await (_db.update(
            _db.syncOutbox,
          )..where((t) => t.id.equals(op.id))).write(
            SyncOutboxCompanion(
              retryCount: Value(op.retryCount + 1),
              nextRetryAt: Value(
                DateTime.now().toUtc().add(Duration(minutes: delayMin)),
              ),
              lastError: Value(e.message),
            ),
          );
        }
      }
    }

    // PULL
    try {
      pulled = await _pullChanges(username);
    } on AppFailure catch (e) {
      await _setError(username, e.message);
      return SyncResult(
        success: false,
        pushed: pushed,
        pulled: pulled,
        message: e.message,
      );
    }

    await _db
        .into(_db.syncMetadata)
        .insertOnConflictUpdate(
          SyncMetadataCompanion(
            accountUsername: Value(username),
            lastSuccessfulSync: Value(DateTime.now().toUtc()),
            lastSyncAttempt: Value(DateTime.now().toUtc()),
            lastError: const Value(null),
            pendingOperationsCount: Value(await _countPending(username)),
            conflictsCount: Value(await _countConflicts(username)),
          ),
        );

    return SyncResult(success: true, pushed: pushed, pulled: pulled);
  }

  Future<void> _pushOne(SyncOutboxData op) async {
    final payload = jsonDecode(op.payloadJson) as Map<String, dynamic>? ?? {};
    final headers = <String, dynamic>{'Idempotency-Key': op.operationId};

    switch (op.operation) {
      case 'UPDATE_TICKET':
        final ticketNumber = payload['ticket_number'] as String;
        final base = payload['if_match'] as String?;
        if (base != null) headers['If-Match'] = base;
        final fields = Map<String, dynamic>.from(payload['fields'] as Map);
        await _api.put(
          '/api/tickets/$ticketNumber',
          data: fields,
          headers: headers,
        );
        await (_db.update(
          _db.tickets,
        )..where((t) => t.localId.equals(op.entityLocalId))).write(
          const TicketsCompanion(syncStatus: Value(SyncStatuses.synced)),
        );
        break;
      case 'COMPLETE_TICKET':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/complete',
          headers: headers,
        );
        break;
      case 'UNCOMPLETE_TICKET':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/uncomplete',
          headers: headers,
        );
        break;
      case 'ARCHIVE_TICKET':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/archive',
          headers: headers,
        );
        break;
      case 'RESTORE_TICKET':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/restore',
          headers: headers,
        );
        break;
      case 'ADD_COMMENT':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/comments',
          data: {'comment_text': payload['comment_text']},
          headers: headers,
        );
        await (_db.update(
          _db.userComments,
        )..where((t) => t.localId.equals(op.entityLocalId))).write(
          const UserCommentsCompanion(syncStatus: Value(SyncStatuses.synced)),
        );
        break;
      case 'ADD_TASK':
        await _api.post(
          '/api/tickets/${payload['ticket_number']}/task',
          headers: headers,
        );
        break;
      case 'REMOVE_TASK':
        await _api.delete(
          '/api/tickets/${payload['ticket_number']}/task',
          headers: headers,
        );
        break;
      case 'DELETE_ATTACHMENT':
        final serverId = payload['server_id'];
        if (serverId != null) {
          await _api.delete('/api/images/$serverId', headers: headers);
        }
        await (_db.update(
          _db.ticketAttachments,
        )..where((t) => t.localId.equals(op.entityLocalId))).write(
          const TicketAttachmentsCompanion(
            isDeleted: Value(true),
            syncStatus: Value(SyncStatuses.synced),
          ),
        );
        break;
      case 'UPLOAD_ATTACHMENT':
        final path = payload['local_file_path'] as String?;
        final ticketNumber = payload['ticket_number'] as String;
        if (path == null) {
          throw const ValidationFailure('Нет локального файла для загрузки');
        }
        final filename =
            payload['original_filename'] as String? ?? path.split('/').last;
        final form = FormData.fromMap({
          'files': await MultipartFile.fromFile(path, filename: filename),
        });
        final response = await _api.post(
          '/api/tickets/$ticketNumber/images',
          data: form,
          headers: headers,
          options: Options(
            sendTimeout: const Duration(minutes: 5),
            receiveTimeout: const Duration(minutes: 5),
          ),
        );
        final body = response.data;
        int? serverId;
        if (body is Map) {
          final uploaded = body['uploaded'];
          if (uploaded is List && uploaded.isNotEmpty) {
            final first = uploaded.first;
            if (first is Map && first['id'] != null) {
              serverId = (first['id'] as num).toInt();
            }
          }
          final errors = body['errors'];
          if (serverId == null && errors is List && errors.isNotEmpty) {
            final err = errors.first;
            final msg = err is Map
                ? (err['error']?.toString() ?? 'Ошибка загрузки')
                : 'Ошибка загрузки';
            throw ValidationFailure(msg);
          }
        }
        await (_db.update(
          _db.ticketAttachments,
        )..where((t) => t.localId.equals(op.entityLocalId))).write(
          TicketAttachmentsCompanion(
            serverId: Value(serverId),
            downloadUrl: serverId != null
                ? Value('/api/images/$serverId/download')
                : const Value.absent(),
            thumbnailUrl: serverId != null
                ? Value('/api/images/$serverId/thumbnail')
                : const Value.absent(),
            syncStatus: const Value(SyncStatuses.synced),
            localUpdatedAt: Value(DateTime.now().toUtc()),
          ),
        );
        break;
      default:
        throw ValidationFailure('Неизвестная операция: ${op.operation}');
    }
  }

  Future<int> _pullChanges(String username) async {
    final meta = await (_db.select(
      _db.syncMetadata,
    )..where((m) => m.accountUsername.equals(username))).getSingleOrNull();

    var cursor = meta?.syncCursor;
    var pulled = 0;
    var hasMore = true;
    var guard = 0;

    while (hasMore && guard < 50) {
      guard++;
      final response = await _api.get(
        '/api/sync/changes',
        queryParameters: {if (cursor != null) 'cursor': cursor, 'limit': 100},
      );
      final body = response.data as Map<String, dynamic>;
      final changes = (body['changes'] as List?) ?? [];
      await _db.transaction(() async {
        for (final raw in changes) {
          final change = Map<String, dynamic>.from(raw as Map);
          await _applyChange(username, change);
          pulled++;
        }
      });
      cursor = body['next_cursor'] as String?;
      hasMore = body['has_more'] == true;
      await _db
          .into(_db.syncMetadata)
          .insertOnConflictUpdate(
            SyncMetadataCompanion(
              accountUsername: Value(username),
              syncCursor: Value(cursor),
            ),
          );
      if (changes.isEmpty) break;
    }
    await _db.refreshHasFilesFlags(username);
    return pulled;
  }

  Future<void> _applyChange(
    String username,
    Map<String, dynamic> change,
  ) async {
    final entity = change['entity'] as String?;
    final operation = change['operation'] as String?;
    final data = change['data'] is Map
        ? Map<String, dynamic>.from(change['data'] as Map)
        : null;
    final id = change['id']?.toString();

    if (entity == 'ticket' && operation == 'upsert' && data != null) {
      final ticketNumber = data['ticket_number']?.toString() ?? id!;
      final existing = await _db.getTicketByNumber(username, ticketNumber);
      // Не затираем pendingUpdate локальными правками
      if (existing != null &&
          (existing.syncStatus == SyncStatuses.pendingUpdate ||
              existing.syncStatus == SyncStatuses.conflict)) {
        return;
      }
      final localId = existing?.localId ?? ticketNumber;
      await _db
          .into(_db.tickets)
          .insertOnConflictUpdate(
            TicketsCompanion(
              localId: Value(localId),
              ticketNumber: Value(ticketNumber),
              subject: Value(data['subject'] as String?),
              inventoryNumber: Value(data['inventory_number'] as String?),
              printerModel: Value(data['printer_model'] as String?),
              office: Value(data['office'] as String?),
              officeAbbreviated: Value(data['office_abbreviated'] as String?),
              cabinet: Value(data['cabinet'] as String?),
              component: Value(data['component'] as String?),
              status: Value(data['status'] as String?),
              priority: Value(data['priority'] as String?),
              assignedTo: Value(data['assigned_to'] as String?),
              authorName: Value(data['author_name'] as String?),
              department: Value(data['department'] as String?),
              currentNote: Value(data['current_note'] as String?),
              requiredAction: Value(data['required_action'] as String?),
              cause: Value(data['cause'] as String?),
              faultDescription: Value(data['fault_description'] as String?),
              workDone: Value(data['work_done'] as String?),
              techConclusion: Value(data['tech_conclusion'] as String?),
              soglasovanoLine: Value(data['soglasovano_line'] as String?),
              isArchived: Value(data['is_archived'] == true),
              isTask: data.containsKey('is_task')
                  ? Value(data['is_task'] == true)
                  : const Value.absent(),
              hasFiles: data.containsKey('has_files')
                  ? Value(data['has_files'] == true)
                  : const Value.absent(),
              hasComments: data.containsKey('has_comments')
                  ? Value(data['has_comments'] == true)
                  : const Value.absent(),
              lastUpdatedDate: Value(_parseDt(data['last_updated_date'])),
              firstReceivedDate: Value(_parseDt(data['first_received_date'])),
              completedAt: Value(_parseDt(data['completed_at'])),
              completedBy: Value(data['completed_by'] as String?),
              lastStatus: Value(data['last_status'] as String?),
              accountUsername: Value(username),
              syncStatus: const Value(SyncStatuses.synced),
              lastSyncedAt: Value(DateTime.now().toUtc()),
              localUpdatedAt: Value(DateTime.now().toUtc()),
            ),
          );
    } else if (entity == 'user_comment' &&
        operation == 'upsert' &&
        data != null) {
      final serverId = data['id'] as int?;
      final localId = serverId?.toString() ?? _uuid.v4();
      await _db
          .into(_db.userComments)
          .insertOnConflictUpdate(
            UserCommentsCompanion(
              localId: Value(localId),
              serverId: Value(serverId),
              ticketNumber: Value(data['ticket_number'] as String),
              authorUsername: Value(data['author_username'] as String?),
              authorName: Value(data['author_name'] as String?),
              commentText: Value(data['comment_text'] as String? ?? ''),
              createdAt: Value(_parseDt(data['created_at'])),
              accountUsername: Value(username),
              syncStatus: const Value(SyncStatuses.synced),
              localUpdatedAt: Value(DateTime.now().toUtc()),
            ),
          );
    } else if (entity == 'ticket_image') {
      if (operation == 'delete' && id != null) {
        await (_db.update(_db.ticketAttachments)..where(
              (t) =>
                  t.accountUsername.equals(username) &
                  t.serverId.equals(int.parse(id)),
            ))
            .write(
              const TicketAttachmentsCompanion(
                isDeleted: Value(true),
                syncStatus: Value(SyncStatuses.synced),
              ),
            );
      } else if (operation == 'upsert' && data != null) {
        final serverId = data['id'] as int;
        final ticketNumber = data['ticket_number'] as String;
        final download =
            data['download_url'] as String? ??
            '/api/images/$serverId/download';
        final thumb =
            data['thumbnail_url'] as String? ??
            '/api/images/$serverId/thumbnail';
        await _db
            .into(_db.ticketAttachments)
            .insertOnConflictUpdate(
              TicketAttachmentsCompanion(
                localId: Value(serverId.toString()),
                serverId: Value(serverId),
                ticketNumber: Value(ticketNumber),
                originalFilename: Value(data['original_filename'] as String?),
                mimeType: Value(data['mime_type'] as String?),
                fileSize: Value(data['file_size'] as int?),
                downloadUrl: Value(download),
                thumbnailUrl: Value(thumb),
                isDeleted: const Value(false),
                uploadedAt: Value(_parseDt(data['uploaded_at'])),
                accountUsername: Value(username),
                syncStatus: const Value(SyncStatuses.synced),
                localUpdatedAt: Value(DateTime.now().toUtc()),
              ),
            );
        final ticket = await _db.getTicketByNumber(username, ticketNumber);
        if (ticket != null) {
          await (_db.update(
            _db.tickets,
          )..where((t) => t.localId.equals(ticket.localId))).write(
            const TicketsCompanion(hasFiles: Value(true)),
          );
        }
      }
    } else if (entity == 'ticket_task' && id != null) {
      final ticket = await _db.getTicketByNumber(username, id);
      if (ticket == null) return;
      final isTask = operation != 'delete';
      await (_db.update(_db.tickets)
            ..where((t) => t.localId.equals(ticket.localId)))
          .write(TicketsCompanion(isTask: Value(isTask)));
    }
  }

  Future<void> enqueue({
    required String username,
    required String entityType,
    required String entityLocalId,
    required String operation,
    required Map<String, dynamic> payload,
    String? entityServerId,
    String? dependsOn,
  }) async {
    final operationId = _uuid.v4();
    await _db
        .into(_db.syncOutbox)
        .insert(
          SyncOutboxCompanion.insert(
            id: _uuid.v4(),
            operationId: operationId,
            entityType: entityType,
            entityLocalId: entityLocalId,
            entityServerId: Value(entityServerId),
            operation: operation,
            payloadJson: jsonEncode(payload),
            createdAt: DateTime.now().toUtc(),
            accountUsername: username,
            dependsOnOperationId: Value(dependsOn),
          ),
        );
  }

  Future<void> _compactOutbox(String username) async {
    final pending =
        await (_db.select(_db.syncOutbox)..where(
              (o) =>
                  o.accountUsername.equals(username) &
                  o.status.equals('pending'),
            ))
            .get();
    final byEntity = <String, List<SyncOutboxData>>{};
    for (final op in pending) {
      if (op.operation != 'UPDATE_TICKET') continue;
      byEntity.putIfAbsent(op.entityLocalId, () => []).add(op);
    }
    for (final entry in byEntity.entries) {
      if (entry.value.length < 2) continue;
      entry.value.sort((a, b) => a.createdAt.compareTo(b.createdAt));
      final last = entry.value.last;
      for (final old in entry.value.sublist(0, entry.value.length - 1)) {
        await (_db.delete(
          _db.syncOutbox,
        )..where((t) => t.id.equals(old.id))).go();
      }
      // keep last
      assert(last.id.isNotEmpty);
    }
  }

  Future<void> _markConflict(SyncOutboxData op, ConflictFailure e) async {
    await (_db.update(_db.syncOutbox)..where((t) => t.id.equals(op.id))).write(
      SyncOutboxCompanion(
        status: const Value('failed'),
        lastError: Value(e.message),
      ),
    );
    await (_db.update(
      _db.tickets,
    )..where((t) => t.localId.equals(op.entityLocalId))).write(
      TicketsCompanion(
        syncStatus: const Value(SyncStatuses.conflict),
        conflictServerJson: Value(jsonEncode(e.serverPayload ?? {})),
      ),
    );
  }

  int _backoffMinutes(int retryCount) {
    const steps = [1, 2, 5, 15, 30, 60];
    final idx = retryCount.clamp(0, steps.length - 1);
    return steps[idx];
  }

  Future<void> _touchAttempt(String username) async {
    await _db
        .into(_db.syncMetadata)
        .insertOnConflictUpdate(
          SyncMetadataCompanion(
            accountUsername: Value(username),
            lastSyncAttempt: Value(DateTime.now().toUtc()),
          ),
        );
  }

  Future<void> _setError(String username, String message) async {
    await _db
        .into(_db.syncMetadata)
        .insertOnConflictUpdate(
          SyncMetadataCompanion(
            accountUsername: Value(username),
            lastError: Value(message),
            lastSyncAttempt: Value(DateTime.now().toUtc()),
          ),
        );
  }

  Future<int> _countPending(String username) async {
    final rows =
        await (_db.select(_db.syncOutbox)..where(
              (o) =>
                  o.accountUsername.equals(username) &
                  o.status.equals('pending'),
            ))
            .get();
    return rows.length;
  }

  Future<int> _countConflicts(String username) async {
    final rows =
        await (_db.select(_db.tickets)..where(
              (t) =>
                  t.accountUsername.equals(username) &
                  t.syncStatus.equals(SyncStatuses.conflict),
            ))
            .get();
    return rows.length;
  }

  DateTime? _parseDt(dynamic value) {
    if (value == null) return null;
    if (value is DateTime) return value.toUtc();
    return DateTime.tryParse(value.toString())?.toUtc();
  }
}
