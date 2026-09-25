import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../../../core/database/app_database.dart';
import '../../../../core/sync/sync_engine.dart';

class TicketsRepository {
  TicketsRepository({required AppDatabase db, required SyncEngine syncEngine})
    : _db = db,
      _sync = syncEngine;

  final AppDatabase _db;
  final SyncEngine _sync;
  final _uuid = const Uuid();

  Stream<List<Ticket>> watchTickets({
    required String username,
    bool archived = false,
    String? search,
  }) {
    return _db.watchTicketsForAccount(
      username,
      archived: archived,
      search: search,
    );
  }

  Future<Ticket?> getTicket(String username, String ticketNumber) {
    return _db.getTicketByNumber(username, ticketNumber);
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
}
