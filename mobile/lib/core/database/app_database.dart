import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

part 'app_database.g.dart';

/// Статусы синхронизации сущности.
class SyncStatuses {
  static const synced = 'synced';
  static const pendingCreate = 'pendingCreate';
  static const pendingUpdate = 'pendingUpdate';
  static const pendingDelete = 'pendingDelete';
  static const syncing = 'syncing';
  static const conflict = 'conflict';
  static const failed = 'failed';
}

class Tickets extends Table {
  TextColumn get localId => text()();
  TextColumn get ticketNumber => text()();
  TextColumn get subject => text().nullable()();
  TextColumn get inventoryNumber => text().nullable()();
  TextColumn get printerModel => text().nullable()();
  TextColumn get office => text().nullable()();
  TextColumn get officeAbbreviated => text().nullable()();
  TextColumn get cabinet => text().nullable()();
  TextColumn get component => text().nullable()();
  TextColumn get status => text().nullable()();
  TextColumn get priority => text().nullable()();
  TextColumn get assignedTo => text().nullable()();
  TextColumn get authorName => text().nullable()();
  TextColumn get department => text().nullable()();
  TextColumn get currentNote => text().nullable()();
  TextColumn get requiredAction => text().nullable()();
  TextColumn get cause => text().nullable()();
  TextColumn get faultDescription => text().nullable()();
  TextColumn get workDone => text().nullable()();
  TextColumn get techConclusion => text().nullable()();
  TextColumn get soglasovanoLine => text().nullable()();
  BoolColumn get isArchived => boolean().withDefault(const Constant(false))();
  BoolColumn get isTask => boolean().withDefault(const Constant(false))();
  BoolColumn get hasFiles => boolean().withDefault(const Constant(false))();
  BoolColumn get hasComments => boolean().withDefault(const Constant(false))();
  DateTimeColumn get firstReceivedDate => dateTime().nullable()();
  DateTimeColumn get lastUpdatedDate => dateTime().nullable()();
  DateTimeColumn get completedAt => dateTime().nullable()();
  TextColumn get completedBy => text().nullable()();
  TextColumn get lastStatus => text().nullable()();
  TextColumn get accountUsername => text()();
  TextColumn get syncStatus =>
      text().withDefault(const Constant(SyncStatuses.synced))();
  DateTimeColumn get lastSyncedAt => dateTime().nullable()();
  TextColumn get conflictServerJson => text().nullable()();
  DateTimeColumn get localUpdatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {localId};
}

class UserComments extends Table {
  TextColumn get localId => text()();
  IntColumn get serverId => integer().nullable()();
  TextColumn get ticketNumber => text()();
  TextColumn get authorUsername => text().nullable()();
  TextColumn get authorName => text().nullable()();
  TextColumn get commentText => text()();
  DateTimeColumn get createdAt => dateTime().nullable()();
  TextColumn get accountUsername => text()();
  TextColumn get syncStatus =>
      text().withDefault(const Constant(SyncStatuses.synced))();
  DateTimeColumn get localUpdatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {localId};
}

class TicketAttachments extends Table {
  TextColumn get localId => text()();
  IntColumn get serverId => integer().nullable()();
  TextColumn get ticketNumber => text()();
  TextColumn get originalFilename => text().nullable()();
  TextColumn get mimeType => text().nullable()();
  IntColumn get fileSize => integer().nullable()();
  TextColumn get localFilePath => text().nullable()();
  TextColumn get downloadUrl => text().nullable()();
  TextColumn get thumbnailUrl => text().nullable()();
  BoolColumn get isDeleted => boolean().withDefault(const Constant(false))();
  DateTimeColumn get uploadedAt => dateTime().nullable()();
  TextColumn get accountUsername => text()();
  TextColumn get syncStatus =>
      text().withDefault(const Constant(SyncStatuses.synced))();
  DateTimeColumn get localUpdatedAt => dateTime()();

  @override
  Set<Column> get primaryKey => {localId};
}

class SyncOutbox extends Table {
  TextColumn get id => text()();
  TextColumn get operationId => text()();
  TextColumn get entityType => text()();
  TextColumn get entityLocalId => text()();
  TextColumn get entityServerId => text().nullable()();
  TextColumn get operation => text()();
  TextColumn get payloadJson => text()();
  DateTimeColumn get createdAt => dateTime()();
  IntColumn get retryCount => integer().withDefault(const Constant(0))();
  DateTimeColumn get nextRetryAt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  TextColumn get status => text().withDefault(const Constant('pending'))();
  TextColumn get accountUsername => text()();
  TextColumn get dependsOnOperationId => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncMetadata extends Table {
  TextColumn get accountUsername => text()();
  TextColumn get syncCursor => text().nullable()();
  DateTimeColumn get lastSuccessfulSync => dateTime().nullable()();
  DateTimeColumn get lastSyncAttempt => dateTime().nullable()();
  TextColumn get lastError => text().nullable()();
  IntColumn get pendingOperationsCount =>
      integer().withDefault(const Constant(0))();
  IntColumn get conflictsCount => integer().withDefault(const Constant(0))();

  @override
  Set<Column> get primaryKey => {accountUsername};
}

class LocalPermissions extends Table {
  TextColumn get accountUsername => text()();
  TextColumn get code => text()();

  @override
  Set<Column> get primaryKey => {accountUsername, code};
}

@DriftDatabase(
  tables: [
    Tickets,
    UserComments,
    TicketAttachments,
    SyncOutbox,
    SyncMetadata,
    LocalPermissions,
  ],
)
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  @override
  int get schemaVersion => 1;

  static Future<AppDatabase> open() async {
    final dir = await getApplicationDocumentsDirectory();
    final file = File(p.join(dir.path, 'gkuop_offline.sqlite'));
    return AppDatabase(NativeDatabase.createInBackground(file));
  }

  Stream<List<Ticket>> watchTicketsForAccount(
    String username, {
    bool archived = false,
    String? search,
  }) {
    final q = select(tickets)
      ..where(
        (t) =>
            t.accountUsername.equals(username) &
            t.isArchived.equals(archived) &
            t.syncStatus.isNotValue(SyncStatuses.pendingDelete),
      );
    if (search != null && search.trim().isNotEmpty) {
      final s = '%${search.trim()}%';
      q.where(
        (t) =>
            t.ticketNumber.like(s) |
            t.inventoryNumber.like(s) |
            t.component.like(s) |
            t.office.like(s) |
            t.status.like(s),
      );
    }
    q.orderBy([(t) => OrderingTerm.desc(t.lastUpdatedDate)]);
    return q.watch();
  }

  Future<Ticket?> getTicketByNumber(String username, String ticketNumber) {
    return (select(tickets)..where(
          (t) =>
              t.accountUsername.equals(username) &
              t.ticketNumber.equals(ticketNumber),
        ))
        .getSingleOrNull();
  }
}
