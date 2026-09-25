// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'app_database.dart';

// ignore_for_file: type=lint
class $TicketsTable extends Tickets with TableInfo<$TicketsTable, Ticket> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TicketsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localIdMeta = const VerificationMeta(
    'localId',
  );
  @override
  late final GeneratedColumn<String> localId = GeneratedColumn<String>(
    'local_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _ticketNumberMeta = const VerificationMeta(
    'ticketNumber',
  );
  @override
  late final GeneratedColumn<String> ticketNumber = GeneratedColumn<String>(
    'ticket_number',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _subjectMeta = const VerificationMeta(
    'subject',
  );
  @override
  late final GeneratedColumn<String> subject = GeneratedColumn<String>(
    'subject',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _inventoryNumberMeta = const VerificationMeta(
    'inventoryNumber',
  );
  @override
  late final GeneratedColumn<String> inventoryNumber = GeneratedColumn<String>(
    'inventory_number',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _printerModelMeta = const VerificationMeta(
    'printerModel',
  );
  @override
  late final GeneratedColumn<String> printerModel = GeneratedColumn<String>(
    'printer_model',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _officeMeta = const VerificationMeta('office');
  @override
  late final GeneratedColumn<String> office = GeneratedColumn<String>(
    'office',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _officeAbbreviatedMeta = const VerificationMeta(
    'officeAbbreviated',
  );
  @override
  late final GeneratedColumn<String> officeAbbreviated =
      GeneratedColumn<String>(
        'office_abbreviated',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _cabinetMeta = const VerificationMeta(
    'cabinet',
  );
  @override
  late final GeneratedColumn<String> cabinet = GeneratedColumn<String>(
    'cabinet',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _componentMeta = const VerificationMeta(
    'component',
  );
  @override
  late final GeneratedColumn<String> component = GeneratedColumn<String>(
    'component',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _priorityMeta = const VerificationMeta(
    'priority',
  );
  @override
  late final GeneratedColumn<String> priority = GeneratedColumn<String>(
    'priority',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _assignedToMeta = const VerificationMeta(
    'assignedTo',
  );
  @override
  late final GeneratedColumn<String> assignedTo = GeneratedColumn<String>(
    'assigned_to',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _authorNameMeta = const VerificationMeta(
    'authorName',
  );
  @override
  late final GeneratedColumn<String> authorName = GeneratedColumn<String>(
    'author_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _departmentMeta = const VerificationMeta(
    'department',
  );
  @override
  late final GeneratedColumn<String> department = GeneratedColumn<String>(
    'department',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _currentNoteMeta = const VerificationMeta(
    'currentNote',
  );
  @override
  late final GeneratedColumn<String> currentNote = GeneratedColumn<String>(
    'current_note',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _requiredActionMeta = const VerificationMeta(
    'requiredAction',
  );
  @override
  late final GeneratedColumn<String> requiredAction = GeneratedColumn<String>(
    'required_action',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _causeMeta = const VerificationMeta('cause');
  @override
  late final GeneratedColumn<String> cause = GeneratedColumn<String>(
    'cause',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _faultDescriptionMeta = const VerificationMeta(
    'faultDescription',
  );
  @override
  late final GeneratedColumn<String> faultDescription = GeneratedColumn<String>(
    'fault_description',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _workDoneMeta = const VerificationMeta(
    'workDone',
  );
  @override
  late final GeneratedColumn<String> workDone = GeneratedColumn<String>(
    'work_done',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _techConclusionMeta = const VerificationMeta(
    'techConclusion',
  );
  @override
  late final GeneratedColumn<String> techConclusion = GeneratedColumn<String>(
    'tech_conclusion',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _soglasovanoLineMeta = const VerificationMeta(
    'soglasovanoLine',
  );
  @override
  late final GeneratedColumn<String> soglasovanoLine = GeneratedColumn<String>(
    'soglasovano_line',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isArchivedMeta = const VerificationMeta(
    'isArchived',
  );
  @override
  late final GeneratedColumn<bool> isArchived = GeneratedColumn<bool>(
    'is_archived',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_archived" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _isTaskMeta = const VerificationMeta('isTask');
  @override
  late final GeneratedColumn<bool> isTask = GeneratedColumn<bool>(
    'is_task',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_task" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _hasFilesMeta = const VerificationMeta(
    'hasFiles',
  );
  @override
  late final GeneratedColumn<bool> hasFiles = GeneratedColumn<bool>(
    'has_files',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("has_files" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _hasCommentsMeta = const VerificationMeta(
    'hasComments',
  );
  @override
  late final GeneratedColumn<bool> hasComments = GeneratedColumn<bool>(
    'has_comments',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("has_comments" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _firstReceivedDateMeta = const VerificationMeta(
    'firstReceivedDate',
  );
  @override
  late final GeneratedColumn<DateTime> firstReceivedDate =
      GeneratedColumn<DateTime>(
        'first_received_date',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _lastUpdatedDateMeta = const VerificationMeta(
    'lastUpdatedDate',
  );
  @override
  late final GeneratedColumn<DateTime> lastUpdatedDate =
      GeneratedColumn<DateTime>(
        'last_updated_date',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _completedAtMeta = const VerificationMeta(
    'completedAt',
  );
  @override
  late final GeneratedColumn<DateTime> completedAt = GeneratedColumn<DateTime>(
    'completed_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _completedByMeta = const VerificationMeta(
    'completedBy',
  );
  @override
  late final GeneratedColumn<String> completedBy = GeneratedColumn<String>(
    'completed_by',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _lastStatusMeta = const VerificationMeta(
    'lastStatus',
  );
  @override
  late final GeneratedColumn<String> lastStatus = GeneratedColumn<String>(
    'last_status',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(SyncStatuses.synced),
  );
  static const VerificationMeta _lastSyncedAtMeta = const VerificationMeta(
    'lastSyncedAt',
  );
  @override
  late final GeneratedColumn<DateTime> lastSyncedAt = GeneratedColumn<DateTime>(
    'last_synced_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _conflictServerJsonMeta =
      const VerificationMeta('conflictServerJson');
  @override
  late final GeneratedColumn<String> conflictServerJson =
      GeneratedColumn<String>(
        'conflict_server_json',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _localUpdatedAtMeta = const VerificationMeta(
    'localUpdatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> localUpdatedAt =
      GeneratedColumn<DateTime>(
        'local_updated_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  @override
  List<GeneratedColumn> get $columns => [
    localId,
    ticketNumber,
    subject,
    inventoryNumber,
    printerModel,
    office,
    officeAbbreviated,
    cabinet,
    component,
    status,
    priority,
    assignedTo,
    authorName,
    department,
    currentNote,
    requiredAction,
    cause,
    faultDescription,
    workDone,
    techConclusion,
    soglasovanoLine,
    isArchived,
    isTask,
    hasFiles,
    hasComments,
    firstReceivedDate,
    lastUpdatedDate,
    completedAt,
    completedBy,
    lastStatus,
    accountUsername,
    syncStatus,
    lastSyncedAt,
    conflictServerJson,
    localUpdatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'tickets';
  @override
  VerificationContext validateIntegrity(
    Insertable<Ticket> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_id')) {
      context.handle(
        _localIdMeta,
        localId.isAcceptableOrUnknown(data['local_id']!, _localIdMeta),
      );
    } else if (isInserting) {
      context.missing(_localIdMeta);
    }
    if (data.containsKey('ticket_number')) {
      context.handle(
        _ticketNumberMeta,
        ticketNumber.isAcceptableOrUnknown(
          data['ticket_number']!,
          _ticketNumberMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_ticketNumberMeta);
    }
    if (data.containsKey('subject')) {
      context.handle(
        _subjectMeta,
        subject.isAcceptableOrUnknown(data['subject']!, _subjectMeta),
      );
    }
    if (data.containsKey('inventory_number')) {
      context.handle(
        _inventoryNumberMeta,
        inventoryNumber.isAcceptableOrUnknown(
          data['inventory_number']!,
          _inventoryNumberMeta,
        ),
      );
    }
    if (data.containsKey('printer_model')) {
      context.handle(
        _printerModelMeta,
        printerModel.isAcceptableOrUnknown(
          data['printer_model']!,
          _printerModelMeta,
        ),
      );
    }
    if (data.containsKey('office')) {
      context.handle(
        _officeMeta,
        office.isAcceptableOrUnknown(data['office']!, _officeMeta),
      );
    }
    if (data.containsKey('office_abbreviated')) {
      context.handle(
        _officeAbbreviatedMeta,
        officeAbbreviated.isAcceptableOrUnknown(
          data['office_abbreviated']!,
          _officeAbbreviatedMeta,
        ),
      );
    }
    if (data.containsKey('cabinet')) {
      context.handle(
        _cabinetMeta,
        cabinet.isAcceptableOrUnknown(data['cabinet']!, _cabinetMeta),
      );
    }
    if (data.containsKey('component')) {
      context.handle(
        _componentMeta,
        component.isAcceptableOrUnknown(data['component']!, _componentMeta),
      );
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('priority')) {
      context.handle(
        _priorityMeta,
        priority.isAcceptableOrUnknown(data['priority']!, _priorityMeta),
      );
    }
    if (data.containsKey('assigned_to')) {
      context.handle(
        _assignedToMeta,
        assignedTo.isAcceptableOrUnknown(data['assigned_to']!, _assignedToMeta),
      );
    }
    if (data.containsKey('author_name')) {
      context.handle(
        _authorNameMeta,
        authorName.isAcceptableOrUnknown(data['author_name']!, _authorNameMeta),
      );
    }
    if (data.containsKey('department')) {
      context.handle(
        _departmentMeta,
        department.isAcceptableOrUnknown(data['department']!, _departmentMeta),
      );
    }
    if (data.containsKey('current_note')) {
      context.handle(
        _currentNoteMeta,
        currentNote.isAcceptableOrUnknown(
          data['current_note']!,
          _currentNoteMeta,
        ),
      );
    }
    if (data.containsKey('required_action')) {
      context.handle(
        _requiredActionMeta,
        requiredAction.isAcceptableOrUnknown(
          data['required_action']!,
          _requiredActionMeta,
        ),
      );
    }
    if (data.containsKey('cause')) {
      context.handle(
        _causeMeta,
        cause.isAcceptableOrUnknown(data['cause']!, _causeMeta),
      );
    }
    if (data.containsKey('fault_description')) {
      context.handle(
        _faultDescriptionMeta,
        faultDescription.isAcceptableOrUnknown(
          data['fault_description']!,
          _faultDescriptionMeta,
        ),
      );
    }
    if (data.containsKey('work_done')) {
      context.handle(
        _workDoneMeta,
        workDone.isAcceptableOrUnknown(data['work_done']!, _workDoneMeta),
      );
    }
    if (data.containsKey('tech_conclusion')) {
      context.handle(
        _techConclusionMeta,
        techConclusion.isAcceptableOrUnknown(
          data['tech_conclusion']!,
          _techConclusionMeta,
        ),
      );
    }
    if (data.containsKey('soglasovano_line')) {
      context.handle(
        _soglasovanoLineMeta,
        soglasovanoLine.isAcceptableOrUnknown(
          data['soglasovano_line']!,
          _soglasovanoLineMeta,
        ),
      );
    }
    if (data.containsKey('is_archived')) {
      context.handle(
        _isArchivedMeta,
        isArchived.isAcceptableOrUnknown(data['is_archived']!, _isArchivedMeta),
      );
    }
    if (data.containsKey('is_task')) {
      context.handle(
        _isTaskMeta,
        isTask.isAcceptableOrUnknown(data['is_task']!, _isTaskMeta),
      );
    }
    if (data.containsKey('has_files')) {
      context.handle(
        _hasFilesMeta,
        hasFiles.isAcceptableOrUnknown(data['has_files']!, _hasFilesMeta),
      );
    }
    if (data.containsKey('has_comments')) {
      context.handle(
        _hasCommentsMeta,
        hasComments.isAcceptableOrUnknown(
          data['has_comments']!,
          _hasCommentsMeta,
        ),
      );
    }
    if (data.containsKey('first_received_date')) {
      context.handle(
        _firstReceivedDateMeta,
        firstReceivedDate.isAcceptableOrUnknown(
          data['first_received_date']!,
          _firstReceivedDateMeta,
        ),
      );
    }
    if (data.containsKey('last_updated_date')) {
      context.handle(
        _lastUpdatedDateMeta,
        lastUpdatedDate.isAcceptableOrUnknown(
          data['last_updated_date']!,
          _lastUpdatedDateMeta,
        ),
      );
    }
    if (data.containsKey('completed_at')) {
      context.handle(
        _completedAtMeta,
        completedAt.isAcceptableOrUnknown(
          data['completed_at']!,
          _completedAtMeta,
        ),
      );
    }
    if (data.containsKey('completed_by')) {
      context.handle(
        _completedByMeta,
        completedBy.isAcceptableOrUnknown(
          data['completed_by']!,
          _completedByMeta,
        ),
      );
    }
    if (data.containsKey('last_status')) {
      context.handle(
        _lastStatusMeta,
        lastStatus.isAcceptableOrUnknown(data['last_status']!, _lastStatusMeta),
      );
    }
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    }
    if (data.containsKey('last_synced_at')) {
      context.handle(
        _lastSyncedAtMeta,
        lastSyncedAt.isAcceptableOrUnknown(
          data['last_synced_at']!,
          _lastSyncedAtMeta,
        ),
      );
    }
    if (data.containsKey('conflict_server_json')) {
      context.handle(
        _conflictServerJsonMeta,
        conflictServerJson.isAcceptableOrUnknown(
          data['conflict_server_json']!,
          _conflictServerJsonMeta,
        ),
      );
    }
    if (data.containsKey('local_updated_at')) {
      context.handle(
        _localUpdatedAtMeta,
        localUpdatedAt.isAcceptableOrUnknown(
          data['local_updated_at']!,
          _localUpdatedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_localUpdatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {localId};
  @override
  Ticket map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Ticket(
      localId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_id'],
      )!,
      ticketNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}ticket_number'],
      )!,
      subject: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}subject'],
      ),
      inventoryNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}inventory_number'],
      ),
      printerModel: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}printer_model'],
      ),
      office: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}office'],
      ),
      officeAbbreviated: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}office_abbreviated'],
      ),
      cabinet: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}cabinet'],
      ),
      component: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}component'],
      ),
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      ),
      priority: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}priority'],
      ),
      assignedTo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}assigned_to'],
      ),
      authorName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}author_name'],
      ),
      department: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}department'],
      ),
      currentNote: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}current_note'],
      ),
      requiredAction: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}required_action'],
      ),
      cause: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}cause'],
      ),
      faultDescription: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}fault_description'],
      ),
      workDone: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}work_done'],
      ),
      techConclusion: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tech_conclusion'],
      ),
      soglasovanoLine: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}soglasovano_line'],
      ),
      isArchived: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_archived'],
      )!,
      isTask: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_task'],
      )!,
      hasFiles: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}has_files'],
      )!,
      hasComments: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}has_comments'],
      )!,
      firstReceivedDate: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}first_received_date'],
      ),
      lastUpdatedDate: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_updated_date'],
      ),
      completedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}completed_at'],
      ),
      completedBy: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}completed_by'],
      ),
      lastStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_status'],
      ),
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
      lastSyncedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_synced_at'],
      ),
      conflictServerJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}conflict_server_json'],
      ),
      localUpdatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}local_updated_at'],
      )!,
    );
  }

  @override
  $TicketsTable createAlias(String alias) {
    return $TicketsTable(attachedDatabase, alias);
  }
}

class Ticket extends DataClass implements Insertable<Ticket> {
  final String localId;
  final String ticketNumber;
  final String? subject;
  final String? inventoryNumber;
  final String? printerModel;
  final String? office;
  final String? officeAbbreviated;
  final String? cabinet;
  final String? component;
  final String? status;
  final String? priority;
  final String? assignedTo;
  final String? authorName;
  final String? department;
  final String? currentNote;
  final String? requiredAction;
  final String? cause;
  final String? faultDescription;
  final String? workDone;
  final String? techConclusion;
  final String? soglasovanoLine;
  final bool isArchived;
  final bool isTask;
  final bool hasFiles;
  final bool hasComments;
  final DateTime? firstReceivedDate;
  final DateTime? lastUpdatedDate;
  final DateTime? completedAt;
  final String? completedBy;
  final String? lastStatus;
  final String accountUsername;
  final String syncStatus;
  final DateTime? lastSyncedAt;
  final String? conflictServerJson;
  final DateTime localUpdatedAt;
  const Ticket({
    required this.localId,
    required this.ticketNumber,
    this.subject,
    this.inventoryNumber,
    this.printerModel,
    this.office,
    this.officeAbbreviated,
    this.cabinet,
    this.component,
    this.status,
    this.priority,
    this.assignedTo,
    this.authorName,
    this.department,
    this.currentNote,
    this.requiredAction,
    this.cause,
    this.faultDescription,
    this.workDone,
    this.techConclusion,
    this.soglasovanoLine,
    required this.isArchived,
    required this.isTask,
    required this.hasFiles,
    required this.hasComments,
    this.firstReceivedDate,
    this.lastUpdatedDate,
    this.completedAt,
    this.completedBy,
    this.lastStatus,
    required this.accountUsername,
    required this.syncStatus,
    this.lastSyncedAt,
    this.conflictServerJson,
    required this.localUpdatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_id'] = Variable<String>(localId);
    map['ticket_number'] = Variable<String>(ticketNumber);
    if (!nullToAbsent || subject != null) {
      map['subject'] = Variable<String>(subject);
    }
    if (!nullToAbsent || inventoryNumber != null) {
      map['inventory_number'] = Variable<String>(inventoryNumber);
    }
    if (!nullToAbsent || printerModel != null) {
      map['printer_model'] = Variable<String>(printerModel);
    }
    if (!nullToAbsent || office != null) {
      map['office'] = Variable<String>(office);
    }
    if (!nullToAbsent || officeAbbreviated != null) {
      map['office_abbreviated'] = Variable<String>(officeAbbreviated);
    }
    if (!nullToAbsent || cabinet != null) {
      map['cabinet'] = Variable<String>(cabinet);
    }
    if (!nullToAbsent || component != null) {
      map['component'] = Variable<String>(component);
    }
    if (!nullToAbsent || status != null) {
      map['status'] = Variable<String>(status);
    }
    if (!nullToAbsent || priority != null) {
      map['priority'] = Variable<String>(priority);
    }
    if (!nullToAbsent || assignedTo != null) {
      map['assigned_to'] = Variable<String>(assignedTo);
    }
    if (!nullToAbsent || authorName != null) {
      map['author_name'] = Variable<String>(authorName);
    }
    if (!nullToAbsent || department != null) {
      map['department'] = Variable<String>(department);
    }
    if (!nullToAbsent || currentNote != null) {
      map['current_note'] = Variable<String>(currentNote);
    }
    if (!nullToAbsent || requiredAction != null) {
      map['required_action'] = Variable<String>(requiredAction);
    }
    if (!nullToAbsent || cause != null) {
      map['cause'] = Variable<String>(cause);
    }
    if (!nullToAbsent || faultDescription != null) {
      map['fault_description'] = Variable<String>(faultDescription);
    }
    if (!nullToAbsent || workDone != null) {
      map['work_done'] = Variable<String>(workDone);
    }
    if (!nullToAbsent || techConclusion != null) {
      map['tech_conclusion'] = Variable<String>(techConclusion);
    }
    if (!nullToAbsent || soglasovanoLine != null) {
      map['soglasovano_line'] = Variable<String>(soglasovanoLine);
    }
    map['is_archived'] = Variable<bool>(isArchived);
    map['is_task'] = Variable<bool>(isTask);
    map['has_files'] = Variable<bool>(hasFiles);
    map['has_comments'] = Variable<bool>(hasComments);
    if (!nullToAbsent || firstReceivedDate != null) {
      map['first_received_date'] = Variable<DateTime>(firstReceivedDate);
    }
    if (!nullToAbsent || lastUpdatedDate != null) {
      map['last_updated_date'] = Variable<DateTime>(lastUpdatedDate);
    }
    if (!nullToAbsent || completedAt != null) {
      map['completed_at'] = Variable<DateTime>(completedAt);
    }
    if (!nullToAbsent || completedBy != null) {
      map['completed_by'] = Variable<String>(completedBy);
    }
    if (!nullToAbsent || lastStatus != null) {
      map['last_status'] = Variable<String>(lastStatus);
    }
    map['account_username'] = Variable<String>(accountUsername);
    map['sync_status'] = Variable<String>(syncStatus);
    if (!nullToAbsent || lastSyncedAt != null) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt);
    }
    if (!nullToAbsent || conflictServerJson != null) {
      map['conflict_server_json'] = Variable<String>(conflictServerJson);
    }
    map['local_updated_at'] = Variable<DateTime>(localUpdatedAt);
    return map;
  }

  TicketsCompanion toCompanion(bool nullToAbsent) {
    return TicketsCompanion(
      localId: Value(localId),
      ticketNumber: Value(ticketNumber),
      subject: subject == null && nullToAbsent
          ? const Value.absent()
          : Value(subject),
      inventoryNumber: inventoryNumber == null && nullToAbsent
          ? const Value.absent()
          : Value(inventoryNumber),
      printerModel: printerModel == null && nullToAbsent
          ? const Value.absent()
          : Value(printerModel),
      office: office == null && nullToAbsent
          ? const Value.absent()
          : Value(office),
      officeAbbreviated: officeAbbreviated == null && nullToAbsent
          ? const Value.absent()
          : Value(officeAbbreviated),
      cabinet: cabinet == null && nullToAbsent
          ? const Value.absent()
          : Value(cabinet),
      component: component == null && nullToAbsent
          ? const Value.absent()
          : Value(component),
      status: status == null && nullToAbsent
          ? const Value.absent()
          : Value(status),
      priority: priority == null && nullToAbsent
          ? const Value.absent()
          : Value(priority),
      assignedTo: assignedTo == null && nullToAbsent
          ? const Value.absent()
          : Value(assignedTo),
      authorName: authorName == null && nullToAbsent
          ? const Value.absent()
          : Value(authorName),
      department: department == null && nullToAbsent
          ? const Value.absent()
          : Value(department),
      currentNote: currentNote == null && nullToAbsent
          ? const Value.absent()
          : Value(currentNote),
      requiredAction: requiredAction == null && nullToAbsent
          ? const Value.absent()
          : Value(requiredAction),
      cause: cause == null && nullToAbsent
          ? const Value.absent()
          : Value(cause),
      faultDescription: faultDescription == null && nullToAbsent
          ? const Value.absent()
          : Value(faultDescription),
      workDone: workDone == null && nullToAbsent
          ? const Value.absent()
          : Value(workDone),
      techConclusion: techConclusion == null && nullToAbsent
          ? const Value.absent()
          : Value(techConclusion),
      soglasovanoLine: soglasovanoLine == null && nullToAbsent
          ? const Value.absent()
          : Value(soglasovanoLine),
      isArchived: Value(isArchived),
      isTask: Value(isTask),
      hasFiles: Value(hasFiles),
      hasComments: Value(hasComments),
      firstReceivedDate: firstReceivedDate == null && nullToAbsent
          ? const Value.absent()
          : Value(firstReceivedDate),
      lastUpdatedDate: lastUpdatedDate == null && nullToAbsent
          ? const Value.absent()
          : Value(lastUpdatedDate),
      completedAt: completedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(completedAt),
      completedBy: completedBy == null && nullToAbsent
          ? const Value.absent()
          : Value(completedBy),
      lastStatus: lastStatus == null && nullToAbsent
          ? const Value.absent()
          : Value(lastStatus),
      accountUsername: Value(accountUsername),
      syncStatus: Value(syncStatus),
      lastSyncedAt: lastSyncedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSyncedAt),
      conflictServerJson: conflictServerJson == null && nullToAbsent
          ? const Value.absent()
          : Value(conflictServerJson),
      localUpdatedAt: Value(localUpdatedAt),
    );
  }

  factory Ticket.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Ticket(
      localId: serializer.fromJson<String>(json['localId']),
      ticketNumber: serializer.fromJson<String>(json['ticketNumber']),
      subject: serializer.fromJson<String?>(json['subject']),
      inventoryNumber: serializer.fromJson<String?>(json['inventoryNumber']),
      printerModel: serializer.fromJson<String?>(json['printerModel']),
      office: serializer.fromJson<String?>(json['office']),
      officeAbbreviated: serializer.fromJson<String?>(
        json['officeAbbreviated'],
      ),
      cabinet: serializer.fromJson<String?>(json['cabinet']),
      component: serializer.fromJson<String?>(json['component']),
      status: serializer.fromJson<String?>(json['status']),
      priority: serializer.fromJson<String?>(json['priority']),
      assignedTo: serializer.fromJson<String?>(json['assignedTo']),
      authorName: serializer.fromJson<String?>(json['authorName']),
      department: serializer.fromJson<String?>(json['department']),
      currentNote: serializer.fromJson<String?>(json['currentNote']),
      requiredAction: serializer.fromJson<String?>(json['requiredAction']),
      cause: serializer.fromJson<String?>(json['cause']),
      faultDescription: serializer.fromJson<String?>(json['faultDescription']),
      workDone: serializer.fromJson<String?>(json['workDone']),
      techConclusion: serializer.fromJson<String?>(json['techConclusion']),
      soglasovanoLine: serializer.fromJson<String?>(json['soglasovanoLine']),
      isArchived: serializer.fromJson<bool>(json['isArchived']),
      isTask: serializer.fromJson<bool>(json['isTask']),
      hasFiles: serializer.fromJson<bool>(json['hasFiles']),
      hasComments: serializer.fromJson<bool>(json['hasComments']),
      firstReceivedDate: serializer.fromJson<DateTime?>(
        json['firstReceivedDate'],
      ),
      lastUpdatedDate: serializer.fromJson<DateTime?>(json['lastUpdatedDate']),
      completedAt: serializer.fromJson<DateTime?>(json['completedAt']),
      completedBy: serializer.fromJson<String?>(json['completedBy']),
      lastStatus: serializer.fromJson<String?>(json['lastStatus']),
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
      lastSyncedAt: serializer.fromJson<DateTime?>(json['lastSyncedAt']),
      conflictServerJson: serializer.fromJson<String?>(
        json['conflictServerJson'],
      ),
      localUpdatedAt: serializer.fromJson<DateTime>(json['localUpdatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localId': serializer.toJson<String>(localId),
      'ticketNumber': serializer.toJson<String>(ticketNumber),
      'subject': serializer.toJson<String?>(subject),
      'inventoryNumber': serializer.toJson<String?>(inventoryNumber),
      'printerModel': serializer.toJson<String?>(printerModel),
      'office': serializer.toJson<String?>(office),
      'officeAbbreviated': serializer.toJson<String?>(officeAbbreviated),
      'cabinet': serializer.toJson<String?>(cabinet),
      'component': serializer.toJson<String?>(component),
      'status': serializer.toJson<String?>(status),
      'priority': serializer.toJson<String?>(priority),
      'assignedTo': serializer.toJson<String?>(assignedTo),
      'authorName': serializer.toJson<String?>(authorName),
      'department': serializer.toJson<String?>(department),
      'currentNote': serializer.toJson<String?>(currentNote),
      'requiredAction': serializer.toJson<String?>(requiredAction),
      'cause': serializer.toJson<String?>(cause),
      'faultDescription': serializer.toJson<String?>(faultDescription),
      'workDone': serializer.toJson<String?>(workDone),
      'techConclusion': serializer.toJson<String?>(techConclusion),
      'soglasovanoLine': serializer.toJson<String?>(soglasovanoLine),
      'isArchived': serializer.toJson<bool>(isArchived),
      'isTask': serializer.toJson<bool>(isTask),
      'hasFiles': serializer.toJson<bool>(hasFiles),
      'hasComments': serializer.toJson<bool>(hasComments),
      'firstReceivedDate': serializer.toJson<DateTime?>(firstReceivedDate),
      'lastUpdatedDate': serializer.toJson<DateTime?>(lastUpdatedDate),
      'completedAt': serializer.toJson<DateTime?>(completedAt),
      'completedBy': serializer.toJson<String?>(completedBy),
      'lastStatus': serializer.toJson<String?>(lastStatus),
      'accountUsername': serializer.toJson<String>(accountUsername),
      'syncStatus': serializer.toJson<String>(syncStatus),
      'lastSyncedAt': serializer.toJson<DateTime?>(lastSyncedAt),
      'conflictServerJson': serializer.toJson<String?>(conflictServerJson),
      'localUpdatedAt': serializer.toJson<DateTime>(localUpdatedAt),
    };
  }

  Ticket copyWith({
    String? localId,
    String? ticketNumber,
    Value<String?> subject = const Value.absent(),
    Value<String?> inventoryNumber = const Value.absent(),
    Value<String?> printerModel = const Value.absent(),
    Value<String?> office = const Value.absent(),
    Value<String?> officeAbbreviated = const Value.absent(),
    Value<String?> cabinet = const Value.absent(),
    Value<String?> component = const Value.absent(),
    Value<String?> status = const Value.absent(),
    Value<String?> priority = const Value.absent(),
    Value<String?> assignedTo = const Value.absent(),
    Value<String?> authorName = const Value.absent(),
    Value<String?> department = const Value.absent(),
    Value<String?> currentNote = const Value.absent(),
    Value<String?> requiredAction = const Value.absent(),
    Value<String?> cause = const Value.absent(),
    Value<String?> faultDescription = const Value.absent(),
    Value<String?> workDone = const Value.absent(),
    Value<String?> techConclusion = const Value.absent(),
    Value<String?> soglasovanoLine = const Value.absent(),
    bool? isArchived,
    bool? isTask,
    bool? hasFiles,
    bool? hasComments,
    Value<DateTime?> firstReceivedDate = const Value.absent(),
    Value<DateTime?> lastUpdatedDate = const Value.absent(),
    Value<DateTime?> completedAt = const Value.absent(),
    Value<String?> completedBy = const Value.absent(),
    Value<String?> lastStatus = const Value.absent(),
    String? accountUsername,
    String? syncStatus,
    Value<DateTime?> lastSyncedAt = const Value.absent(),
    Value<String?> conflictServerJson = const Value.absent(),
    DateTime? localUpdatedAt,
  }) => Ticket(
    localId: localId ?? this.localId,
    ticketNumber: ticketNumber ?? this.ticketNumber,
    subject: subject.present ? subject.value : this.subject,
    inventoryNumber: inventoryNumber.present
        ? inventoryNumber.value
        : this.inventoryNumber,
    printerModel: printerModel.present ? printerModel.value : this.printerModel,
    office: office.present ? office.value : this.office,
    officeAbbreviated: officeAbbreviated.present
        ? officeAbbreviated.value
        : this.officeAbbreviated,
    cabinet: cabinet.present ? cabinet.value : this.cabinet,
    component: component.present ? component.value : this.component,
    status: status.present ? status.value : this.status,
    priority: priority.present ? priority.value : this.priority,
    assignedTo: assignedTo.present ? assignedTo.value : this.assignedTo,
    authorName: authorName.present ? authorName.value : this.authorName,
    department: department.present ? department.value : this.department,
    currentNote: currentNote.present ? currentNote.value : this.currentNote,
    requiredAction: requiredAction.present
        ? requiredAction.value
        : this.requiredAction,
    cause: cause.present ? cause.value : this.cause,
    faultDescription: faultDescription.present
        ? faultDescription.value
        : this.faultDescription,
    workDone: workDone.present ? workDone.value : this.workDone,
    techConclusion: techConclusion.present
        ? techConclusion.value
        : this.techConclusion,
    soglasovanoLine: soglasovanoLine.present
        ? soglasovanoLine.value
        : this.soglasovanoLine,
    isArchived: isArchived ?? this.isArchived,
    isTask: isTask ?? this.isTask,
    hasFiles: hasFiles ?? this.hasFiles,
    hasComments: hasComments ?? this.hasComments,
    firstReceivedDate: firstReceivedDate.present
        ? firstReceivedDate.value
        : this.firstReceivedDate,
    lastUpdatedDate: lastUpdatedDate.present
        ? lastUpdatedDate.value
        : this.lastUpdatedDate,
    completedAt: completedAt.present ? completedAt.value : this.completedAt,
    completedBy: completedBy.present ? completedBy.value : this.completedBy,
    lastStatus: lastStatus.present ? lastStatus.value : this.lastStatus,
    accountUsername: accountUsername ?? this.accountUsername,
    syncStatus: syncStatus ?? this.syncStatus,
    lastSyncedAt: lastSyncedAt.present ? lastSyncedAt.value : this.lastSyncedAt,
    conflictServerJson: conflictServerJson.present
        ? conflictServerJson.value
        : this.conflictServerJson,
    localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
  );
  Ticket copyWithCompanion(TicketsCompanion data) {
    return Ticket(
      localId: data.localId.present ? data.localId.value : this.localId,
      ticketNumber: data.ticketNumber.present
          ? data.ticketNumber.value
          : this.ticketNumber,
      subject: data.subject.present ? data.subject.value : this.subject,
      inventoryNumber: data.inventoryNumber.present
          ? data.inventoryNumber.value
          : this.inventoryNumber,
      printerModel: data.printerModel.present
          ? data.printerModel.value
          : this.printerModel,
      office: data.office.present ? data.office.value : this.office,
      officeAbbreviated: data.officeAbbreviated.present
          ? data.officeAbbreviated.value
          : this.officeAbbreviated,
      cabinet: data.cabinet.present ? data.cabinet.value : this.cabinet,
      component: data.component.present ? data.component.value : this.component,
      status: data.status.present ? data.status.value : this.status,
      priority: data.priority.present ? data.priority.value : this.priority,
      assignedTo: data.assignedTo.present
          ? data.assignedTo.value
          : this.assignedTo,
      authorName: data.authorName.present
          ? data.authorName.value
          : this.authorName,
      department: data.department.present
          ? data.department.value
          : this.department,
      currentNote: data.currentNote.present
          ? data.currentNote.value
          : this.currentNote,
      requiredAction: data.requiredAction.present
          ? data.requiredAction.value
          : this.requiredAction,
      cause: data.cause.present ? data.cause.value : this.cause,
      faultDescription: data.faultDescription.present
          ? data.faultDescription.value
          : this.faultDescription,
      workDone: data.workDone.present ? data.workDone.value : this.workDone,
      techConclusion: data.techConclusion.present
          ? data.techConclusion.value
          : this.techConclusion,
      soglasovanoLine: data.soglasovanoLine.present
          ? data.soglasovanoLine.value
          : this.soglasovanoLine,
      isArchived: data.isArchived.present
          ? data.isArchived.value
          : this.isArchived,
      isTask: data.isTask.present ? data.isTask.value : this.isTask,
      hasFiles: data.hasFiles.present ? data.hasFiles.value : this.hasFiles,
      hasComments: data.hasComments.present
          ? data.hasComments.value
          : this.hasComments,
      firstReceivedDate: data.firstReceivedDate.present
          ? data.firstReceivedDate.value
          : this.firstReceivedDate,
      lastUpdatedDate: data.lastUpdatedDate.present
          ? data.lastUpdatedDate.value
          : this.lastUpdatedDate,
      completedAt: data.completedAt.present
          ? data.completedAt.value
          : this.completedAt,
      completedBy: data.completedBy.present
          ? data.completedBy.value
          : this.completedBy,
      lastStatus: data.lastStatus.present
          ? data.lastStatus.value
          : this.lastStatus,
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
      lastSyncedAt: data.lastSyncedAt.present
          ? data.lastSyncedAt.value
          : this.lastSyncedAt,
      conflictServerJson: data.conflictServerJson.present
          ? data.conflictServerJson.value
          : this.conflictServerJson,
      localUpdatedAt: data.localUpdatedAt.present
          ? data.localUpdatedAt.value
          : this.localUpdatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Ticket(')
          ..write('localId: $localId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('subject: $subject, ')
          ..write('inventoryNumber: $inventoryNumber, ')
          ..write('printerModel: $printerModel, ')
          ..write('office: $office, ')
          ..write('officeAbbreviated: $officeAbbreviated, ')
          ..write('cabinet: $cabinet, ')
          ..write('component: $component, ')
          ..write('status: $status, ')
          ..write('priority: $priority, ')
          ..write('assignedTo: $assignedTo, ')
          ..write('authorName: $authorName, ')
          ..write('department: $department, ')
          ..write('currentNote: $currentNote, ')
          ..write('requiredAction: $requiredAction, ')
          ..write('cause: $cause, ')
          ..write('faultDescription: $faultDescription, ')
          ..write('workDone: $workDone, ')
          ..write('techConclusion: $techConclusion, ')
          ..write('soglasovanoLine: $soglasovanoLine, ')
          ..write('isArchived: $isArchived, ')
          ..write('isTask: $isTask, ')
          ..write('hasFiles: $hasFiles, ')
          ..write('hasComments: $hasComments, ')
          ..write('firstReceivedDate: $firstReceivedDate, ')
          ..write('lastUpdatedDate: $lastUpdatedDate, ')
          ..write('completedAt: $completedAt, ')
          ..write('completedBy: $completedBy, ')
          ..write('lastStatus: $lastStatus, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('conflictServerJson: $conflictServerJson, ')
          ..write('localUpdatedAt: $localUpdatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    localId,
    ticketNumber,
    subject,
    inventoryNumber,
    printerModel,
    office,
    officeAbbreviated,
    cabinet,
    component,
    status,
    priority,
    assignedTo,
    authorName,
    department,
    currentNote,
    requiredAction,
    cause,
    faultDescription,
    workDone,
    techConclusion,
    soglasovanoLine,
    isArchived,
    isTask,
    hasFiles,
    hasComments,
    firstReceivedDate,
    lastUpdatedDate,
    completedAt,
    completedBy,
    lastStatus,
    accountUsername,
    syncStatus,
    lastSyncedAt,
    conflictServerJson,
    localUpdatedAt,
  ]);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Ticket &&
          other.localId == this.localId &&
          other.ticketNumber == this.ticketNumber &&
          other.subject == this.subject &&
          other.inventoryNumber == this.inventoryNumber &&
          other.printerModel == this.printerModel &&
          other.office == this.office &&
          other.officeAbbreviated == this.officeAbbreviated &&
          other.cabinet == this.cabinet &&
          other.component == this.component &&
          other.status == this.status &&
          other.priority == this.priority &&
          other.assignedTo == this.assignedTo &&
          other.authorName == this.authorName &&
          other.department == this.department &&
          other.currentNote == this.currentNote &&
          other.requiredAction == this.requiredAction &&
          other.cause == this.cause &&
          other.faultDescription == this.faultDescription &&
          other.workDone == this.workDone &&
          other.techConclusion == this.techConclusion &&
          other.soglasovanoLine == this.soglasovanoLine &&
          other.isArchived == this.isArchived &&
          other.isTask == this.isTask &&
          other.hasFiles == this.hasFiles &&
          other.hasComments == this.hasComments &&
          other.firstReceivedDate == this.firstReceivedDate &&
          other.lastUpdatedDate == this.lastUpdatedDate &&
          other.completedAt == this.completedAt &&
          other.completedBy == this.completedBy &&
          other.lastStatus == this.lastStatus &&
          other.accountUsername == this.accountUsername &&
          other.syncStatus == this.syncStatus &&
          other.lastSyncedAt == this.lastSyncedAt &&
          other.conflictServerJson == this.conflictServerJson &&
          other.localUpdatedAt == this.localUpdatedAt);
}

class TicketsCompanion extends UpdateCompanion<Ticket> {
  final Value<String> localId;
  final Value<String> ticketNumber;
  final Value<String?> subject;
  final Value<String?> inventoryNumber;
  final Value<String?> printerModel;
  final Value<String?> office;
  final Value<String?> officeAbbreviated;
  final Value<String?> cabinet;
  final Value<String?> component;
  final Value<String?> status;
  final Value<String?> priority;
  final Value<String?> assignedTo;
  final Value<String?> authorName;
  final Value<String?> department;
  final Value<String?> currentNote;
  final Value<String?> requiredAction;
  final Value<String?> cause;
  final Value<String?> faultDescription;
  final Value<String?> workDone;
  final Value<String?> techConclusion;
  final Value<String?> soglasovanoLine;
  final Value<bool> isArchived;
  final Value<bool> isTask;
  final Value<bool> hasFiles;
  final Value<bool> hasComments;
  final Value<DateTime?> firstReceivedDate;
  final Value<DateTime?> lastUpdatedDate;
  final Value<DateTime?> completedAt;
  final Value<String?> completedBy;
  final Value<String?> lastStatus;
  final Value<String> accountUsername;
  final Value<String> syncStatus;
  final Value<DateTime?> lastSyncedAt;
  final Value<String?> conflictServerJson;
  final Value<DateTime> localUpdatedAt;
  final Value<int> rowid;
  const TicketsCompanion({
    this.localId = const Value.absent(),
    this.ticketNumber = const Value.absent(),
    this.subject = const Value.absent(),
    this.inventoryNumber = const Value.absent(),
    this.printerModel = const Value.absent(),
    this.office = const Value.absent(),
    this.officeAbbreviated = const Value.absent(),
    this.cabinet = const Value.absent(),
    this.component = const Value.absent(),
    this.status = const Value.absent(),
    this.priority = const Value.absent(),
    this.assignedTo = const Value.absent(),
    this.authorName = const Value.absent(),
    this.department = const Value.absent(),
    this.currentNote = const Value.absent(),
    this.requiredAction = const Value.absent(),
    this.cause = const Value.absent(),
    this.faultDescription = const Value.absent(),
    this.workDone = const Value.absent(),
    this.techConclusion = const Value.absent(),
    this.soglasovanoLine = const Value.absent(),
    this.isArchived = const Value.absent(),
    this.isTask = const Value.absent(),
    this.hasFiles = const Value.absent(),
    this.hasComments = const Value.absent(),
    this.firstReceivedDate = const Value.absent(),
    this.lastUpdatedDate = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.completedBy = const Value.absent(),
    this.lastStatus = const Value.absent(),
    this.accountUsername = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.conflictServerJson = const Value.absent(),
    this.localUpdatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  TicketsCompanion.insert({
    required String localId,
    required String ticketNumber,
    this.subject = const Value.absent(),
    this.inventoryNumber = const Value.absent(),
    this.printerModel = const Value.absent(),
    this.office = const Value.absent(),
    this.officeAbbreviated = const Value.absent(),
    this.cabinet = const Value.absent(),
    this.component = const Value.absent(),
    this.status = const Value.absent(),
    this.priority = const Value.absent(),
    this.assignedTo = const Value.absent(),
    this.authorName = const Value.absent(),
    this.department = const Value.absent(),
    this.currentNote = const Value.absent(),
    this.requiredAction = const Value.absent(),
    this.cause = const Value.absent(),
    this.faultDescription = const Value.absent(),
    this.workDone = const Value.absent(),
    this.techConclusion = const Value.absent(),
    this.soglasovanoLine = const Value.absent(),
    this.isArchived = const Value.absent(),
    this.isTask = const Value.absent(),
    this.hasFiles = const Value.absent(),
    this.hasComments = const Value.absent(),
    this.firstReceivedDate = const Value.absent(),
    this.lastUpdatedDate = const Value.absent(),
    this.completedAt = const Value.absent(),
    this.completedBy = const Value.absent(),
    this.lastStatus = const Value.absent(),
    required String accountUsername,
    this.syncStatus = const Value.absent(),
    this.lastSyncedAt = const Value.absent(),
    this.conflictServerJson = const Value.absent(),
    required DateTime localUpdatedAt,
    this.rowid = const Value.absent(),
  }) : localId = Value(localId),
       ticketNumber = Value(ticketNumber),
       accountUsername = Value(accountUsername),
       localUpdatedAt = Value(localUpdatedAt);
  static Insertable<Ticket> custom({
    Expression<String>? localId,
    Expression<String>? ticketNumber,
    Expression<String>? subject,
    Expression<String>? inventoryNumber,
    Expression<String>? printerModel,
    Expression<String>? office,
    Expression<String>? officeAbbreviated,
    Expression<String>? cabinet,
    Expression<String>? component,
    Expression<String>? status,
    Expression<String>? priority,
    Expression<String>? assignedTo,
    Expression<String>? authorName,
    Expression<String>? department,
    Expression<String>? currentNote,
    Expression<String>? requiredAction,
    Expression<String>? cause,
    Expression<String>? faultDescription,
    Expression<String>? workDone,
    Expression<String>? techConclusion,
    Expression<String>? soglasovanoLine,
    Expression<bool>? isArchived,
    Expression<bool>? isTask,
    Expression<bool>? hasFiles,
    Expression<bool>? hasComments,
    Expression<DateTime>? firstReceivedDate,
    Expression<DateTime>? lastUpdatedDate,
    Expression<DateTime>? completedAt,
    Expression<String>? completedBy,
    Expression<String>? lastStatus,
    Expression<String>? accountUsername,
    Expression<String>? syncStatus,
    Expression<DateTime>? lastSyncedAt,
    Expression<String>? conflictServerJson,
    Expression<DateTime>? localUpdatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localId != null) 'local_id': localId,
      if (ticketNumber != null) 'ticket_number': ticketNumber,
      if (subject != null) 'subject': subject,
      if (inventoryNumber != null) 'inventory_number': inventoryNumber,
      if (printerModel != null) 'printer_model': printerModel,
      if (office != null) 'office': office,
      if (officeAbbreviated != null) 'office_abbreviated': officeAbbreviated,
      if (cabinet != null) 'cabinet': cabinet,
      if (component != null) 'component': component,
      if (status != null) 'status': status,
      if (priority != null) 'priority': priority,
      if (assignedTo != null) 'assigned_to': assignedTo,
      if (authorName != null) 'author_name': authorName,
      if (department != null) 'department': department,
      if (currentNote != null) 'current_note': currentNote,
      if (requiredAction != null) 'required_action': requiredAction,
      if (cause != null) 'cause': cause,
      if (faultDescription != null) 'fault_description': faultDescription,
      if (workDone != null) 'work_done': workDone,
      if (techConclusion != null) 'tech_conclusion': techConclusion,
      if (soglasovanoLine != null) 'soglasovano_line': soglasovanoLine,
      if (isArchived != null) 'is_archived': isArchived,
      if (isTask != null) 'is_task': isTask,
      if (hasFiles != null) 'has_files': hasFiles,
      if (hasComments != null) 'has_comments': hasComments,
      if (firstReceivedDate != null) 'first_received_date': firstReceivedDate,
      if (lastUpdatedDate != null) 'last_updated_date': lastUpdatedDate,
      if (completedAt != null) 'completed_at': completedAt,
      if (completedBy != null) 'completed_by': completedBy,
      if (lastStatus != null) 'last_status': lastStatus,
      if (accountUsername != null) 'account_username': accountUsername,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (lastSyncedAt != null) 'last_synced_at': lastSyncedAt,
      if (conflictServerJson != null)
        'conflict_server_json': conflictServerJson,
      if (localUpdatedAt != null) 'local_updated_at': localUpdatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  TicketsCompanion copyWith({
    Value<String>? localId,
    Value<String>? ticketNumber,
    Value<String?>? subject,
    Value<String?>? inventoryNumber,
    Value<String?>? printerModel,
    Value<String?>? office,
    Value<String?>? officeAbbreviated,
    Value<String?>? cabinet,
    Value<String?>? component,
    Value<String?>? status,
    Value<String?>? priority,
    Value<String?>? assignedTo,
    Value<String?>? authorName,
    Value<String?>? department,
    Value<String?>? currentNote,
    Value<String?>? requiredAction,
    Value<String?>? cause,
    Value<String?>? faultDescription,
    Value<String?>? workDone,
    Value<String?>? techConclusion,
    Value<String?>? soglasovanoLine,
    Value<bool>? isArchived,
    Value<bool>? isTask,
    Value<bool>? hasFiles,
    Value<bool>? hasComments,
    Value<DateTime?>? firstReceivedDate,
    Value<DateTime?>? lastUpdatedDate,
    Value<DateTime?>? completedAt,
    Value<String?>? completedBy,
    Value<String?>? lastStatus,
    Value<String>? accountUsername,
    Value<String>? syncStatus,
    Value<DateTime?>? lastSyncedAt,
    Value<String?>? conflictServerJson,
    Value<DateTime>? localUpdatedAt,
    Value<int>? rowid,
  }) {
    return TicketsCompanion(
      localId: localId ?? this.localId,
      ticketNumber: ticketNumber ?? this.ticketNumber,
      subject: subject ?? this.subject,
      inventoryNumber: inventoryNumber ?? this.inventoryNumber,
      printerModel: printerModel ?? this.printerModel,
      office: office ?? this.office,
      officeAbbreviated: officeAbbreviated ?? this.officeAbbreviated,
      cabinet: cabinet ?? this.cabinet,
      component: component ?? this.component,
      status: status ?? this.status,
      priority: priority ?? this.priority,
      assignedTo: assignedTo ?? this.assignedTo,
      authorName: authorName ?? this.authorName,
      department: department ?? this.department,
      currentNote: currentNote ?? this.currentNote,
      requiredAction: requiredAction ?? this.requiredAction,
      cause: cause ?? this.cause,
      faultDescription: faultDescription ?? this.faultDescription,
      workDone: workDone ?? this.workDone,
      techConclusion: techConclusion ?? this.techConclusion,
      soglasovanoLine: soglasovanoLine ?? this.soglasovanoLine,
      isArchived: isArchived ?? this.isArchived,
      isTask: isTask ?? this.isTask,
      hasFiles: hasFiles ?? this.hasFiles,
      hasComments: hasComments ?? this.hasComments,
      firstReceivedDate: firstReceivedDate ?? this.firstReceivedDate,
      lastUpdatedDate: lastUpdatedDate ?? this.lastUpdatedDate,
      completedAt: completedAt ?? this.completedAt,
      completedBy: completedBy ?? this.completedBy,
      lastStatus: lastStatus ?? this.lastStatus,
      accountUsername: accountUsername ?? this.accountUsername,
      syncStatus: syncStatus ?? this.syncStatus,
      lastSyncedAt: lastSyncedAt ?? this.lastSyncedAt,
      conflictServerJson: conflictServerJson ?? this.conflictServerJson,
      localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localId.present) {
      map['local_id'] = Variable<String>(localId.value);
    }
    if (ticketNumber.present) {
      map['ticket_number'] = Variable<String>(ticketNumber.value);
    }
    if (subject.present) {
      map['subject'] = Variable<String>(subject.value);
    }
    if (inventoryNumber.present) {
      map['inventory_number'] = Variable<String>(inventoryNumber.value);
    }
    if (printerModel.present) {
      map['printer_model'] = Variable<String>(printerModel.value);
    }
    if (office.present) {
      map['office'] = Variable<String>(office.value);
    }
    if (officeAbbreviated.present) {
      map['office_abbreviated'] = Variable<String>(officeAbbreviated.value);
    }
    if (cabinet.present) {
      map['cabinet'] = Variable<String>(cabinet.value);
    }
    if (component.present) {
      map['component'] = Variable<String>(component.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (priority.present) {
      map['priority'] = Variable<String>(priority.value);
    }
    if (assignedTo.present) {
      map['assigned_to'] = Variable<String>(assignedTo.value);
    }
    if (authorName.present) {
      map['author_name'] = Variable<String>(authorName.value);
    }
    if (department.present) {
      map['department'] = Variable<String>(department.value);
    }
    if (currentNote.present) {
      map['current_note'] = Variable<String>(currentNote.value);
    }
    if (requiredAction.present) {
      map['required_action'] = Variable<String>(requiredAction.value);
    }
    if (cause.present) {
      map['cause'] = Variable<String>(cause.value);
    }
    if (faultDescription.present) {
      map['fault_description'] = Variable<String>(faultDescription.value);
    }
    if (workDone.present) {
      map['work_done'] = Variable<String>(workDone.value);
    }
    if (techConclusion.present) {
      map['tech_conclusion'] = Variable<String>(techConclusion.value);
    }
    if (soglasovanoLine.present) {
      map['soglasovano_line'] = Variable<String>(soglasovanoLine.value);
    }
    if (isArchived.present) {
      map['is_archived'] = Variable<bool>(isArchived.value);
    }
    if (isTask.present) {
      map['is_task'] = Variable<bool>(isTask.value);
    }
    if (hasFiles.present) {
      map['has_files'] = Variable<bool>(hasFiles.value);
    }
    if (hasComments.present) {
      map['has_comments'] = Variable<bool>(hasComments.value);
    }
    if (firstReceivedDate.present) {
      map['first_received_date'] = Variable<DateTime>(firstReceivedDate.value);
    }
    if (lastUpdatedDate.present) {
      map['last_updated_date'] = Variable<DateTime>(lastUpdatedDate.value);
    }
    if (completedAt.present) {
      map['completed_at'] = Variable<DateTime>(completedAt.value);
    }
    if (completedBy.present) {
      map['completed_by'] = Variable<String>(completedBy.value);
    }
    if (lastStatus.present) {
      map['last_status'] = Variable<String>(lastStatus.value);
    }
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (lastSyncedAt.present) {
      map['last_synced_at'] = Variable<DateTime>(lastSyncedAt.value);
    }
    if (conflictServerJson.present) {
      map['conflict_server_json'] = Variable<String>(conflictServerJson.value);
    }
    if (localUpdatedAt.present) {
      map['local_updated_at'] = Variable<DateTime>(localUpdatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TicketsCompanion(')
          ..write('localId: $localId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('subject: $subject, ')
          ..write('inventoryNumber: $inventoryNumber, ')
          ..write('printerModel: $printerModel, ')
          ..write('office: $office, ')
          ..write('officeAbbreviated: $officeAbbreviated, ')
          ..write('cabinet: $cabinet, ')
          ..write('component: $component, ')
          ..write('status: $status, ')
          ..write('priority: $priority, ')
          ..write('assignedTo: $assignedTo, ')
          ..write('authorName: $authorName, ')
          ..write('department: $department, ')
          ..write('currentNote: $currentNote, ')
          ..write('requiredAction: $requiredAction, ')
          ..write('cause: $cause, ')
          ..write('faultDescription: $faultDescription, ')
          ..write('workDone: $workDone, ')
          ..write('techConclusion: $techConclusion, ')
          ..write('soglasovanoLine: $soglasovanoLine, ')
          ..write('isArchived: $isArchived, ')
          ..write('isTask: $isTask, ')
          ..write('hasFiles: $hasFiles, ')
          ..write('hasComments: $hasComments, ')
          ..write('firstReceivedDate: $firstReceivedDate, ')
          ..write('lastUpdatedDate: $lastUpdatedDate, ')
          ..write('completedAt: $completedAt, ')
          ..write('completedBy: $completedBy, ')
          ..write('lastStatus: $lastStatus, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('lastSyncedAt: $lastSyncedAt, ')
          ..write('conflictServerJson: $conflictServerJson, ')
          ..write('localUpdatedAt: $localUpdatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $UserCommentsTable extends UserComments
    with TableInfo<$UserCommentsTable, UserComment> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $UserCommentsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localIdMeta = const VerificationMeta(
    'localId',
  );
  @override
  late final GeneratedColumn<String> localId = GeneratedColumn<String>(
    'local_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _serverIdMeta = const VerificationMeta(
    'serverId',
  );
  @override
  late final GeneratedColumn<int> serverId = GeneratedColumn<int>(
    'server_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _ticketNumberMeta = const VerificationMeta(
    'ticketNumber',
  );
  @override
  late final GeneratedColumn<String> ticketNumber = GeneratedColumn<String>(
    'ticket_number',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _authorUsernameMeta = const VerificationMeta(
    'authorUsername',
  );
  @override
  late final GeneratedColumn<String> authorUsername = GeneratedColumn<String>(
    'author_username',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _authorNameMeta = const VerificationMeta(
    'authorName',
  );
  @override
  late final GeneratedColumn<String> authorName = GeneratedColumn<String>(
    'author_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _commentTextMeta = const VerificationMeta(
    'commentText',
  );
  @override
  late final GeneratedColumn<String> commentText = GeneratedColumn<String>(
    'comment_text',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(SyncStatuses.synced),
  );
  static const VerificationMeta _localUpdatedAtMeta = const VerificationMeta(
    'localUpdatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> localUpdatedAt =
      GeneratedColumn<DateTime>(
        'local_updated_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  @override
  List<GeneratedColumn> get $columns => [
    localId,
    serverId,
    ticketNumber,
    authorUsername,
    authorName,
    commentText,
    createdAt,
    accountUsername,
    syncStatus,
    localUpdatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'user_comments';
  @override
  VerificationContext validateIntegrity(
    Insertable<UserComment> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_id')) {
      context.handle(
        _localIdMeta,
        localId.isAcceptableOrUnknown(data['local_id']!, _localIdMeta),
      );
    } else if (isInserting) {
      context.missing(_localIdMeta);
    }
    if (data.containsKey('server_id')) {
      context.handle(
        _serverIdMeta,
        serverId.isAcceptableOrUnknown(data['server_id']!, _serverIdMeta),
      );
    }
    if (data.containsKey('ticket_number')) {
      context.handle(
        _ticketNumberMeta,
        ticketNumber.isAcceptableOrUnknown(
          data['ticket_number']!,
          _ticketNumberMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_ticketNumberMeta);
    }
    if (data.containsKey('author_username')) {
      context.handle(
        _authorUsernameMeta,
        authorUsername.isAcceptableOrUnknown(
          data['author_username']!,
          _authorUsernameMeta,
        ),
      );
    }
    if (data.containsKey('author_name')) {
      context.handle(
        _authorNameMeta,
        authorName.isAcceptableOrUnknown(data['author_name']!, _authorNameMeta),
      );
    }
    if (data.containsKey('comment_text')) {
      context.handle(
        _commentTextMeta,
        commentText.isAcceptableOrUnknown(
          data['comment_text']!,
          _commentTextMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_commentTextMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    }
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    }
    if (data.containsKey('local_updated_at')) {
      context.handle(
        _localUpdatedAtMeta,
        localUpdatedAt.isAcceptableOrUnknown(
          data['local_updated_at']!,
          _localUpdatedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_localUpdatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {localId};
  @override
  UserComment map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return UserComment(
      localId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_id'],
      )!,
      serverId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}server_id'],
      ),
      ticketNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}ticket_number'],
      )!,
      authorUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}author_username'],
      ),
      authorName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}author_name'],
      ),
      commentText: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}comment_text'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      ),
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
      localUpdatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}local_updated_at'],
      )!,
    );
  }

  @override
  $UserCommentsTable createAlias(String alias) {
    return $UserCommentsTable(attachedDatabase, alias);
  }
}

class UserComment extends DataClass implements Insertable<UserComment> {
  final String localId;
  final int? serverId;
  final String ticketNumber;
  final String? authorUsername;
  final String? authorName;
  final String commentText;
  final DateTime? createdAt;
  final String accountUsername;
  final String syncStatus;
  final DateTime localUpdatedAt;
  const UserComment({
    required this.localId,
    this.serverId,
    required this.ticketNumber,
    this.authorUsername,
    this.authorName,
    required this.commentText,
    this.createdAt,
    required this.accountUsername,
    required this.syncStatus,
    required this.localUpdatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_id'] = Variable<String>(localId);
    if (!nullToAbsent || serverId != null) {
      map['server_id'] = Variable<int>(serverId);
    }
    map['ticket_number'] = Variable<String>(ticketNumber);
    if (!nullToAbsent || authorUsername != null) {
      map['author_username'] = Variable<String>(authorUsername);
    }
    if (!nullToAbsent || authorName != null) {
      map['author_name'] = Variable<String>(authorName);
    }
    map['comment_text'] = Variable<String>(commentText);
    if (!nullToAbsent || createdAt != null) {
      map['created_at'] = Variable<DateTime>(createdAt);
    }
    map['account_username'] = Variable<String>(accountUsername);
    map['sync_status'] = Variable<String>(syncStatus);
    map['local_updated_at'] = Variable<DateTime>(localUpdatedAt);
    return map;
  }

  UserCommentsCompanion toCompanion(bool nullToAbsent) {
    return UserCommentsCompanion(
      localId: Value(localId),
      serverId: serverId == null && nullToAbsent
          ? const Value.absent()
          : Value(serverId),
      ticketNumber: Value(ticketNumber),
      authorUsername: authorUsername == null && nullToAbsent
          ? const Value.absent()
          : Value(authorUsername),
      authorName: authorName == null && nullToAbsent
          ? const Value.absent()
          : Value(authorName),
      commentText: Value(commentText),
      createdAt: createdAt == null && nullToAbsent
          ? const Value.absent()
          : Value(createdAt),
      accountUsername: Value(accountUsername),
      syncStatus: Value(syncStatus),
      localUpdatedAt: Value(localUpdatedAt),
    );
  }

  factory UserComment.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return UserComment(
      localId: serializer.fromJson<String>(json['localId']),
      serverId: serializer.fromJson<int?>(json['serverId']),
      ticketNumber: serializer.fromJson<String>(json['ticketNumber']),
      authorUsername: serializer.fromJson<String?>(json['authorUsername']),
      authorName: serializer.fromJson<String?>(json['authorName']),
      commentText: serializer.fromJson<String>(json['commentText']),
      createdAt: serializer.fromJson<DateTime?>(json['createdAt']),
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
      localUpdatedAt: serializer.fromJson<DateTime>(json['localUpdatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localId': serializer.toJson<String>(localId),
      'serverId': serializer.toJson<int?>(serverId),
      'ticketNumber': serializer.toJson<String>(ticketNumber),
      'authorUsername': serializer.toJson<String?>(authorUsername),
      'authorName': serializer.toJson<String?>(authorName),
      'commentText': serializer.toJson<String>(commentText),
      'createdAt': serializer.toJson<DateTime?>(createdAt),
      'accountUsername': serializer.toJson<String>(accountUsername),
      'syncStatus': serializer.toJson<String>(syncStatus),
      'localUpdatedAt': serializer.toJson<DateTime>(localUpdatedAt),
    };
  }

  UserComment copyWith({
    String? localId,
    Value<int?> serverId = const Value.absent(),
    String? ticketNumber,
    Value<String?> authorUsername = const Value.absent(),
    Value<String?> authorName = const Value.absent(),
    String? commentText,
    Value<DateTime?> createdAt = const Value.absent(),
    String? accountUsername,
    String? syncStatus,
    DateTime? localUpdatedAt,
  }) => UserComment(
    localId: localId ?? this.localId,
    serverId: serverId.present ? serverId.value : this.serverId,
    ticketNumber: ticketNumber ?? this.ticketNumber,
    authorUsername: authorUsername.present
        ? authorUsername.value
        : this.authorUsername,
    authorName: authorName.present ? authorName.value : this.authorName,
    commentText: commentText ?? this.commentText,
    createdAt: createdAt.present ? createdAt.value : this.createdAt,
    accountUsername: accountUsername ?? this.accountUsername,
    syncStatus: syncStatus ?? this.syncStatus,
    localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
  );
  UserComment copyWithCompanion(UserCommentsCompanion data) {
    return UserComment(
      localId: data.localId.present ? data.localId.value : this.localId,
      serverId: data.serverId.present ? data.serverId.value : this.serverId,
      ticketNumber: data.ticketNumber.present
          ? data.ticketNumber.value
          : this.ticketNumber,
      authorUsername: data.authorUsername.present
          ? data.authorUsername.value
          : this.authorUsername,
      authorName: data.authorName.present
          ? data.authorName.value
          : this.authorName,
      commentText: data.commentText.present
          ? data.commentText.value
          : this.commentText,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
      localUpdatedAt: data.localUpdatedAt.present
          ? data.localUpdatedAt.value
          : this.localUpdatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('UserComment(')
          ..write('localId: $localId, ')
          ..write('serverId: $serverId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('authorUsername: $authorUsername, ')
          ..write('authorName: $authorName, ')
          ..write('commentText: $commentText, ')
          ..write('createdAt: $createdAt, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('localUpdatedAt: $localUpdatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    localId,
    serverId,
    ticketNumber,
    authorUsername,
    authorName,
    commentText,
    createdAt,
    accountUsername,
    syncStatus,
    localUpdatedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is UserComment &&
          other.localId == this.localId &&
          other.serverId == this.serverId &&
          other.ticketNumber == this.ticketNumber &&
          other.authorUsername == this.authorUsername &&
          other.authorName == this.authorName &&
          other.commentText == this.commentText &&
          other.createdAt == this.createdAt &&
          other.accountUsername == this.accountUsername &&
          other.syncStatus == this.syncStatus &&
          other.localUpdatedAt == this.localUpdatedAt);
}

class UserCommentsCompanion extends UpdateCompanion<UserComment> {
  final Value<String> localId;
  final Value<int?> serverId;
  final Value<String> ticketNumber;
  final Value<String?> authorUsername;
  final Value<String?> authorName;
  final Value<String> commentText;
  final Value<DateTime?> createdAt;
  final Value<String> accountUsername;
  final Value<String> syncStatus;
  final Value<DateTime> localUpdatedAt;
  final Value<int> rowid;
  const UserCommentsCompanion({
    this.localId = const Value.absent(),
    this.serverId = const Value.absent(),
    this.ticketNumber = const Value.absent(),
    this.authorUsername = const Value.absent(),
    this.authorName = const Value.absent(),
    this.commentText = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.accountUsername = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.localUpdatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  UserCommentsCompanion.insert({
    required String localId,
    this.serverId = const Value.absent(),
    required String ticketNumber,
    this.authorUsername = const Value.absent(),
    this.authorName = const Value.absent(),
    required String commentText,
    this.createdAt = const Value.absent(),
    required String accountUsername,
    this.syncStatus = const Value.absent(),
    required DateTime localUpdatedAt,
    this.rowid = const Value.absent(),
  }) : localId = Value(localId),
       ticketNumber = Value(ticketNumber),
       commentText = Value(commentText),
       accountUsername = Value(accountUsername),
       localUpdatedAt = Value(localUpdatedAt);
  static Insertable<UserComment> custom({
    Expression<String>? localId,
    Expression<int>? serverId,
    Expression<String>? ticketNumber,
    Expression<String>? authorUsername,
    Expression<String>? authorName,
    Expression<String>? commentText,
    Expression<DateTime>? createdAt,
    Expression<String>? accountUsername,
    Expression<String>? syncStatus,
    Expression<DateTime>? localUpdatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localId != null) 'local_id': localId,
      if (serverId != null) 'server_id': serverId,
      if (ticketNumber != null) 'ticket_number': ticketNumber,
      if (authorUsername != null) 'author_username': authorUsername,
      if (authorName != null) 'author_name': authorName,
      if (commentText != null) 'comment_text': commentText,
      if (createdAt != null) 'created_at': createdAt,
      if (accountUsername != null) 'account_username': accountUsername,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (localUpdatedAt != null) 'local_updated_at': localUpdatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  UserCommentsCompanion copyWith({
    Value<String>? localId,
    Value<int?>? serverId,
    Value<String>? ticketNumber,
    Value<String?>? authorUsername,
    Value<String?>? authorName,
    Value<String>? commentText,
    Value<DateTime?>? createdAt,
    Value<String>? accountUsername,
    Value<String>? syncStatus,
    Value<DateTime>? localUpdatedAt,
    Value<int>? rowid,
  }) {
    return UserCommentsCompanion(
      localId: localId ?? this.localId,
      serverId: serverId ?? this.serverId,
      ticketNumber: ticketNumber ?? this.ticketNumber,
      authorUsername: authorUsername ?? this.authorUsername,
      authorName: authorName ?? this.authorName,
      commentText: commentText ?? this.commentText,
      createdAt: createdAt ?? this.createdAt,
      accountUsername: accountUsername ?? this.accountUsername,
      syncStatus: syncStatus ?? this.syncStatus,
      localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localId.present) {
      map['local_id'] = Variable<String>(localId.value);
    }
    if (serverId.present) {
      map['server_id'] = Variable<int>(serverId.value);
    }
    if (ticketNumber.present) {
      map['ticket_number'] = Variable<String>(ticketNumber.value);
    }
    if (authorUsername.present) {
      map['author_username'] = Variable<String>(authorUsername.value);
    }
    if (authorName.present) {
      map['author_name'] = Variable<String>(authorName.value);
    }
    if (commentText.present) {
      map['comment_text'] = Variable<String>(commentText.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (localUpdatedAt.present) {
      map['local_updated_at'] = Variable<DateTime>(localUpdatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('UserCommentsCompanion(')
          ..write('localId: $localId, ')
          ..write('serverId: $serverId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('authorUsername: $authorUsername, ')
          ..write('authorName: $authorName, ')
          ..write('commentText: $commentText, ')
          ..write('createdAt: $createdAt, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('localUpdatedAt: $localUpdatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $TicketAttachmentsTable extends TicketAttachments
    with TableInfo<$TicketAttachmentsTable, TicketAttachment> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $TicketAttachmentsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _localIdMeta = const VerificationMeta(
    'localId',
  );
  @override
  late final GeneratedColumn<String> localId = GeneratedColumn<String>(
    'local_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _serverIdMeta = const VerificationMeta(
    'serverId',
  );
  @override
  late final GeneratedColumn<int> serverId = GeneratedColumn<int>(
    'server_id',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _ticketNumberMeta = const VerificationMeta(
    'ticketNumber',
  );
  @override
  late final GeneratedColumn<String> ticketNumber = GeneratedColumn<String>(
    'ticket_number',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _originalFilenameMeta = const VerificationMeta(
    'originalFilename',
  );
  @override
  late final GeneratedColumn<String> originalFilename = GeneratedColumn<String>(
    'original_filename',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _mimeTypeMeta = const VerificationMeta(
    'mimeType',
  );
  @override
  late final GeneratedColumn<String> mimeType = GeneratedColumn<String>(
    'mime_type',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _fileSizeMeta = const VerificationMeta(
    'fileSize',
  );
  @override
  late final GeneratedColumn<int> fileSize = GeneratedColumn<int>(
    'file_size',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _localFilePathMeta = const VerificationMeta(
    'localFilePath',
  );
  @override
  late final GeneratedColumn<String> localFilePath = GeneratedColumn<String>(
    'local_file_path',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _downloadUrlMeta = const VerificationMeta(
    'downloadUrl',
  );
  @override
  late final GeneratedColumn<String> downloadUrl = GeneratedColumn<String>(
    'download_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _thumbnailUrlMeta = const VerificationMeta(
    'thumbnailUrl',
  );
  @override
  late final GeneratedColumn<String> thumbnailUrl = GeneratedColumn<String>(
    'thumbnail_url',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _isDeletedMeta = const VerificationMeta(
    'isDeleted',
  );
  @override
  late final GeneratedColumn<bool> isDeleted = GeneratedColumn<bool>(
    'is_deleted',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_deleted" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _uploadedAtMeta = const VerificationMeta(
    'uploadedAt',
  );
  @override
  late final GeneratedColumn<DateTime> uploadedAt = GeneratedColumn<DateTime>(
    'uploaded_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncStatusMeta = const VerificationMeta(
    'syncStatus',
  );
  @override
  late final GeneratedColumn<String> syncStatus = GeneratedColumn<String>(
    'sync_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant(SyncStatuses.synced),
  );
  static const VerificationMeta _localUpdatedAtMeta = const VerificationMeta(
    'localUpdatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> localUpdatedAt =
      GeneratedColumn<DateTime>(
        'local_updated_at',
        aliasedName,
        false,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: true,
      );
  @override
  List<GeneratedColumn> get $columns => [
    localId,
    serverId,
    ticketNumber,
    originalFilename,
    mimeType,
    fileSize,
    localFilePath,
    downloadUrl,
    thumbnailUrl,
    isDeleted,
    uploadedAt,
    accountUsername,
    syncStatus,
    localUpdatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'ticket_attachments';
  @override
  VerificationContext validateIntegrity(
    Insertable<TicketAttachment> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('local_id')) {
      context.handle(
        _localIdMeta,
        localId.isAcceptableOrUnknown(data['local_id']!, _localIdMeta),
      );
    } else if (isInserting) {
      context.missing(_localIdMeta);
    }
    if (data.containsKey('server_id')) {
      context.handle(
        _serverIdMeta,
        serverId.isAcceptableOrUnknown(data['server_id']!, _serverIdMeta),
      );
    }
    if (data.containsKey('ticket_number')) {
      context.handle(
        _ticketNumberMeta,
        ticketNumber.isAcceptableOrUnknown(
          data['ticket_number']!,
          _ticketNumberMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_ticketNumberMeta);
    }
    if (data.containsKey('original_filename')) {
      context.handle(
        _originalFilenameMeta,
        originalFilename.isAcceptableOrUnknown(
          data['original_filename']!,
          _originalFilenameMeta,
        ),
      );
    }
    if (data.containsKey('mime_type')) {
      context.handle(
        _mimeTypeMeta,
        mimeType.isAcceptableOrUnknown(data['mime_type']!, _mimeTypeMeta),
      );
    }
    if (data.containsKey('file_size')) {
      context.handle(
        _fileSizeMeta,
        fileSize.isAcceptableOrUnknown(data['file_size']!, _fileSizeMeta),
      );
    }
    if (data.containsKey('local_file_path')) {
      context.handle(
        _localFilePathMeta,
        localFilePath.isAcceptableOrUnknown(
          data['local_file_path']!,
          _localFilePathMeta,
        ),
      );
    }
    if (data.containsKey('download_url')) {
      context.handle(
        _downloadUrlMeta,
        downloadUrl.isAcceptableOrUnknown(
          data['download_url']!,
          _downloadUrlMeta,
        ),
      );
    }
    if (data.containsKey('thumbnail_url')) {
      context.handle(
        _thumbnailUrlMeta,
        thumbnailUrl.isAcceptableOrUnknown(
          data['thumbnail_url']!,
          _thumbnailUrlMeta,
        ),
      );
    }
    if (data.containsKey('is_deleted')) {
      context.handle(
        _isDeletedMeta,
        isDeleted.isAcceptableOrUnknown(data['is_deleted']!, _isDeletedMeta),
      );
    }
    if (data.containsKey('uploaded_at')) {
      context.handle(
        _uploadedAtMeta,
        uploadedAt.isAcceptableOrUnknown(data['uploaded_at']!, _uploadedAtMeta),
      );
    }
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('sync_status')) {
      context.handle(
        _syncStatusMeta,
        syncStatus.isAcceptableOrUnknown(data['sync_status']!, _syncStatusMeta),
      );
    }
    if (data.containsKey('local_updated_at')) {
      context.handle(
        _localUpdatedAtMeta,
        localUpdatedAt.isAcceptableOrUnknown(
          data['local_updated_at']!,
          _localUpdatedAtMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_localUpdatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {localId};
  @override
  TicketAttachment map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return TicketAttachment(
      localId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_id'],
      )!,
      serverId: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}server_id'],
      ),
      ticketNumber: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}ticket_number'],
      )!,
      originalFilename: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}original_filename'],
      ),
      mimeType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mime_type'],
      ),
      fileSize: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}file_size'],
      ),
      localFilePath: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_file_path'],
      ),
      downloadUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}download_url'],
      ),
      thumbnailUrl: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}thumbnail_url'],
      ),
      isDeleted: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_deleted'],
      )!,
      uploadedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}uploaded_at'],
      ),
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      syncStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_status'],
      )!,
      localUpdatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}local_updated_at'],
      )!,
    );
  }

  @override
  $TicketAttachmentsTable createAlias(String alias) {
    return $TicketAttachmentsTable(attachedDatabase, alias);
  }
}

class TicketAttachment extends DataClass
    implements Insertable<TicketAttachment> {
  final String localId;
  final int? serverId;
  final String ticketNumber;
  final String? originalFilename;
  final String? mimeType;
  final int? fileSize;
  final String? localFilePath;
  final String? downloadUrl;
  final String? thumbnailUrl;
  final bool isDeleted;
  final DateTime? uploadedAt;
  final String accountUsername;
  final String syncStatus;
  final DateTime localUpdatedAt;
  const TicketAttachment({
    required this.localId,
    this.serverId,
    required this.ticketNumber,
    this.originalFilename,
    this.mimeType,
    this.fileSize,
    this.localFilePath,
    this.downloadUrl,
    this.thumbnailUrl,
    required this.isDeleted,
    this.uploadedAt,
    required this.accountUsername,
    required this.syncStatus,
    required this.localUpdatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['local_id'] = Variable<String>(localId);
    if (!nullToAbsent || serverId != null) {
      map['server_id'] = Variable<int>(serverId);
    }
    map['ticket_number'] = Variable<String>(ticketNumber);
    if (!nullToAbsent || originalFilename != null) {
      map['original_filename'] = Variable<String>(originalFilename);
    }
    if (!nullToAbsent || mimeType != null) {
      map['mime_type'] = Variable<String>(mimeType);
    }
    if (!nullToAbsent || fileSize != null) {
      map['file_size'] = Variable<int>(fileSize);
    }
    if (!nullToAbsent || localFilePath != null) {
      map['local_file_path'] = Variable<String>(localFilePath);
    }
    if (!nullToAbsent || downloadUrl != null) {
      map['download_url'] = Variable<String>(downloadUrl);
    }
    if (!nullToAbsent || thumbnailUrl != null) {
      map['thumbnail_url'] = Variable<String>(thumbnailUrl);
    }
    map['is_deleted'] = Variable<bool>(isDeleted);
    if (!nullToAbsent || uploadedAt != null) {
      map['uploaded_at'] = Variable<DateTime>(uploadedAt);
    }
    map['account_username'] = Variable<String>(accountUsername);
    map['sync_status'] = Variable<String>(syncStatus);
    map['local_updated_at'] = Variable<DateTime>(localUpdatedAt);
    return map;
  }

  TicketAttachmentsCompanion toCompanion(bool nullToAbsent) {
    return TicketAttachmentsCompanion(
      localId: Value(localId),
      serverId: serverId == null && nullToAbsent
          ? const Value.absent()
          : Value(serverId),
      ticketNumber: Value(ticketNumber),
      originalFilename: originalFilename == null && nullToAbsent
          ? const Value.absent()
          : Value(originalFilename),
      mimeType: mimeType == null && nullToAbsent
          ? const Value.absent()
          : Value(mimeType),
      fileSize: fileSize == null && nullToAbsent
          ? const Value.absent()
          : Value(fileSize),
      localFilePath: localFilePath == null && nullToAbsent
          ? const Value.absent()
          : Value(localFilePath),
      downloadUrl: downloadUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(downloadUrl),
      thumbnailUrl: thumbnailUrl == null && nullToAbsent
          ? const Value.absent()
          : Value(thumbnailUrl),
      isDeleted: Value(isDeleted),
      uploadedAt: uploadedAt == null && nullToAbsent
          ? const Value.absent()
          : Value(uploadedAt),
      accountUsername: Value(accountUsername),
      syncStatus: Value(syncStatus),
      localUpdatedAt: Value(localUpdatedAt),
    );
  }

  factory TicketAttachment.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return TicketAttachment(
      localId: serializer.fromJson<String>(json['localId']),
      serverId: serializer.fromJson<int?>(json['serverId']),
      ticketNumber: serializer.fromJson<String>(json['ticketNumber']),
      originalFilename: serializer.fromJson<String?>(json['originalFilename']),
      mimeType: serializer.fromJson<String?>(json['mimeType']),
      fileSize: serializer.fromJson<int?>(json['fileSize']),
      localFilePath: serializer.fromJson<String?>(json['localFilePath']),
      downloadUrl: serializer.fromJson<String?>(json['downloadUrl']),
      thumbnailUrl: serializer.fromJson<String?>(json['thumbnailUrl']),
      isDeleted: serializer.fromJson<bool>(json['isDeleted']),
      uploadedAt: serializer.fromJson<DateTime?>(json['uploadedAt']),
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      syncStatus: serializer.fromJson<String>(json['syncStatus']),
      localUpdatedAt: serializer.fromJson<DateTime>(json['localUpdatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'localId': serializer.toJson<String>(localId),
      'serverId': serializer.toJson<int?>(serverId),
      'ticketNumber': serializer.toJson<String>(ticketNumber),
      'originalFilename': serializer.toJson<String?>(originalFilename),
      'mimeType': serializer.toJson<String?>(mimeType),
      'fileSize': serializer.toJson<int?>(fileSize),
      'localFilePath': serializer.toJson<String?>(localFilePath),
      'downloadUrl': serializer.toJson<String?>(downloadUrl),
      'thumbnailUrl': serializer.toJson<String?>(thumbnailUrl),
      'isDeleted': serializer.toJson<bool>(isDeleted),
      'uploadedAt': serializer.toJson<DateTime?>(uploadedAt),
      'accountUsername': serializer.toJson<String>(accountUsername),
      'syncStatus': serializer.toJson<String>(syncStatus),
      'localUpdatedAt': serializer.toJson<DateTime>(localUpdatedAt),
    };
  }

  TicketAttachment copyWith({
    String? localId,
    Value<int?> serverId = const Value.absent(),
    String? ticketNumber,
    Value<String?> originalFilename = const Value.absent(),
    Value<String?> mimeType = const Value.absent(),
    Value<int?> fileSize = const Value.absent(),
    Value<String?> localFilePath = const Value.absent(),
    Value<String?> downloadUrl = const Value.absent(),
    Value<String?> thumbnailUrl = const Value.absent(),
    bool? isDeleted,
    Value<DateTime?> uploadedAt = const Value.absent(),
    String? accountUsername,
    String? syncStatus,
    DateTime? localUpdatedAt,
  }) => TicketAttachment(
    localId: localId ?? this.localId,
    serverId: serverId.present ? serverId.value : this.serverId,
    ticketNumber: ticketNumber ?? this.ticketNumber,
    originalFilename: originalFilename.present
        ? originalFilename.value
        : this.originalFilename,
    mimeType: mimeType.present ? mimeType.value : this.mimeType,
    fileSize: fileSize.present ? fileSize.value : this.fileSize,
    localFilePath: localFilePath.present
        ? localFilePath.value
        : this.localFilePath,
    downloadUrl: downloadUrl.present ? downloadUrl.value : this.downloadUrl,
    thumbnailUrl: thumbnailUrl.present ? thumbnailUrl.value : this.thumbnailUrl,
    isDeleted: isDeleted ?? this.isDeleted,
    uploadedAt: uploadedAt.present ? uploadedAt.value : this.uploadedAt,
    accountUsername: accountUsername ?? this.accountUsername,
    syncStatus: syncStatus ?? this.syncStatus,
    localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
  );
  TicketAttachment copyWithCompanion(TicketAttachmentsCompanion data) {
    return TicketAttachment(
      localId: data.localId.present ? data.localId.value : this.localId,
      serverId: data.serverId.present ? data.serverId.value : this.serverId,
      ticketNumber: data.ticketNumber.present
          ? data.ticketNumber.value
          : this.ticketNumber,
      originalFilename: data.originalFilename.present
          ? data.originalFilename.value
          : this.originalFilename,
      mimeType: data.mimeType.present ? data.mimeType.value : this.mimeType,
      fileSize: data.fileSize.present ? data.fileSize.value : this.fileSize,
      localFilePath: data.localFilePath.present
          ? data.localFilePath.value
          : this.localFilePath,
      downloadUrl: data.downloadUrl.present
          ? data.downloadUrl.value
          : this.downloadUrl,
      thumbnailUrl: data.thumbnailUrl.present
          ? data.thumbnailUrl.value
          : this.thumbnailUrl,
      isDeleted: data.isDeleted.present ? data.isDeleted.value : this.isDeleted,
      uploadedAt: data.uploadedAt.present
          ? data.uploadedAt.value
          : this.uploadedAt,
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      syncStatus: data.syncStatus.present
          ? data.syncStatus.value
          : this.syncStatus,
      localUpdatedAt: data.localUpdatedAt.present
          ? data.localUpdatedAt.value
          : this.localUpdatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('TicketAttachment(')
          ..write('localId: $localId, ')
          ..write('serverId: $serverId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('originalFilename: $originalFilename, ')
          ..write('mimeType: $mimeType, ')
          ..write('fileSize: $fileSize, ')
          ..write('localFilePath: $localFilePath, ')
          ..write('downloadUrl: $downloadUrl, ')
          ..write('thumbnailUrl: $thumbnailUrl, ')
          ..write('isDeleted: $isDeleted, ')
          ..write('uploadedAt: $uploadedAt, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('localUpdatedAt: $localUpdatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    localId,
    serverId,
    ticketNumber,
    originalFilename,
    mimeType,
    fileSize,
    localFilePath,
    downloadUrl,
    thumbnailUrl,
    isDeleted,
    uploadedAt,
    accountUsername,
    syncStatus,
    localUpdatedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is TicketAttachment &&
          other.localId == this.localId &&
          other.serverId == this.serverId &&
          other.ticketNumber == this.ticketNumber &&
          other.originalFilename == this.originalFilename &&
          other.mimeType == this.mimeType &&
          other.fileSize == this.fileSize &&
          other.localFilePath == this.localFilePath &&
          other.downloadUrl == this.downloadUrl &&
          other.thumbnailUrl == this.thumbnailUrl &&
          other.isDeleted == this.isDeleted &&
          other.uploadedAt == this.uploadedAt &&
          other.accountUsername == this.accountUsername &&
          other.syncStatus == this.syncStatus &&
          other.localUpdatedAt == this.localUpdatedAt);
}

class TicketAttachmentsCompanion extends UpdateCompanion<TicketAttachment> {
  final Value<String> localId;
  final Value<int?> serverId;
  final Value<String> ticketNumber;
  final Value<String?> originalFilename;
  final Value<String?> mimeType;
  final Value<int?> fileSize;
  final Value<String?> localFilePath;
  final Value<String?> downloadUrl;
  final Value<String?> thumbnailUrl;
  final Value<bool> isDeleted;
  final Value<DateTime?> uploadedAt;
  final Value<String> accountUsername;
  final Value<String> syncStatus;
  final Value<DateTime> localUpdatedAt;
  final Value<int> rowid;
  const TicketAttachmentsCompanion({
    this.localId = const Value.absent(),
    this.serverId = const Value.absent(),
    this.ticketNumber = const Value.absent(),
    this.originalFilename = const Value.absent(),
    this.mimeType = const Value.absent(),
    this.fileSize = const Value.absent(),
    this.localFilePath = const Value.absent(),
    this.downloadUrl = const Value.absent(),
    this.thumbnailUrl = const Value.absent(),
    this.isDeleted = const Value.absent(),
    this.uploadedAt = const Value.absent(),
    this.accountUsername = const Value.absent(),
    this.syncStatus = const Value.absent(),
    this.localUpdatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  TicketAttachmentsCompanion.insert({
    required String localId,
    this.serverId = const Value.absent(),
    required String ticketNumber,
    this.originalFilename = const Value.absent(),
    this.mimeType = const Value.absent(),
    this.fileSize = const Value.absent(),
    this.localFilePath = const Value.absent(),
    this.downloadUrl = const Value.absent(),
    this.thumbnailUrl = const Value.absent(),
    this.isDeleted = const Value.absent(),
    this.uploadedAt = const Value.absent(),
    required String accountUsername,
    this.syncStatus = const Value.absent(),
    required DateTime localUpdatedAt,
    this.rowid = const Value.absent(),
  }) : localId = Value(localId),
       ticketNumber = Value(ticketNumber),
       accountUsername = Value(accountUsername),
       localUpdatedAt = Value(localUpdatedAt);
  static Insertable<TicketAttachment> custom({
    Expression<String>? localId,
    Expression<int>? serverId,
    Expression<String>? ticketNumber,
    Expression<String>? originalFilename,
    Expression<String>? mimeType,
    Expression<int>? fileSize,
    Expression<String>? localFilePath,
    Expression<String>? downloadUrl,
    Expression<String>? thumbnailUrl,
    Expression<bool>? isDeleted,
    Expression<DateTime>? uploadedAt,
    Expression<String>? accountUsername,
    Expression<String>? syncStatus,
    Expression<DateTime>? localUpdatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (localId != null) 'local_id': localId,
      if (serverId != null) 'server_id': serverId,
      if (ticketNumber != null) 'ticket_number': ticketNumber,
      if (originalFilename != null) 'original_filename': originalFilename,
      if (mimeType != null) 'mime_type': mimeType,
      if (fileSize != null) 'file_size': fileSize,
      if (localFilePath != null) 'local_file_path': localFilePath,
      if (downloadUrl != null) 'download_url': downloadUrl,
      if (thumbnailUrl != null) 'thumbnail_url': thumbnailUrl,
      if (isDeleted != null) 'is_deleted': isDeleted,
      if (uploadedAt != null) 'uploaded_at': uploadedAt,
      if (accountUsername != null) 'account_username': accountUsername,
      if (syncStatus != null) 'sync_status': syncStatus,
      if (localUpdatedAt != null) 'local_updated_at': localUpdatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  TicketAttachmentsCompanion copyWith({
    Value<String>? localId,
    Value<int?>? serverId,
    Value<String>? ticketNumber,
    Value<String?>? originalFilename,
    Value<String?>? mimeType,
    Value<int?>? fileSize,
    Value<String?>? localFilePath,
    Value<String?>? downloadUrl,
    Value<String?>? thumbnailUrl,
    Value<bool>? isDeleted,
    Value<DateTime?>? uploadedAt,
    Value<String>? accountUsername,
    Value<String>? syncStatus,
    Value<DateTime>? localUpdatedAt,
    Value<int>? rowid,
  }) {
    return TicketAttachmentsCompanion(
      localId: localId ?? this.localId,
      serverId: serverId ?? this.serverId,
      ticketNumber: ticketNumber ?? this.ticketNumber,
      originalFilename: originalFilename ?? this.originalFilename,
      mimeType: mimeType ?? this.mimeType,
      fileSize: fileSize ?? this.fileSize,
      localFilePath: localFilePath ?? this.localFilePath,
      downloadUrl: downloadUrl ?? this.downloadUrl,
      thumbnailUrl: thumbnailUrl ?? this.thumbnailUrl,
      isDeleted: isDeleted ?? this.isDeleted,
      uploadedAt: uploadedAt ?? this.uploadedAt,
      accountUsername: accountUsername ?? this.accountUsername,
      syncStatus: syncStatus ?? this.syncStatus,
      localUpdatedAt: localUpdatedAt ?? this.localUpdatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (localId.present) {
      map['local_id'] = Variable<String>(localId.value);
    }
    if (serverId.present) {
      map['server_id'] = Variable<int>(serverId.value);
    }
    if (ticketNumber.present) {
      map['ticket_number'] = Variable<String>(ticketNumber.value);
    }
    if (originalFilename.present) {
      map['original_filename'] = Variable<String>(originalFilename.value);
    }
    if (mimeType.present) {
      map['mime_type'] = Variable<String>(mimeType.value);
    }
    if (fileSize.present) {
      map['file_size'] = Variable<int>(fileSize.value);
    }
    if (localFilePath.present) {
      map['local_file_path'] = Variable<String>(localFilePath.value);
    }
    if (downloadUrl.present) {
      map['download_url'] = Variable<String>(downloadUrl.value);
    }
    if (thumbnailUrl.present) {
      map['thumbnail_url'] = Variable<String>(thumbnailUrl.value);
    }
    if (isDeleted.present) {
      map['is_deleted'] = Variable<bool>(isDeleted.value);
    }
    if (uploadedAt.present) {
      map['uploaded_at'] = Variable<DateTime>(uploadedAt.value);
    }
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (syncStatus.present) {
      map['sync_status'] = Variable<String>(syncStatus.value);
    }
    if (localUpdatedAt.present) {
      map['local_updated_at'] = Variable<DateTime>(localUpdatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('TicketAttachmentsCompanion(')
          ..write('localId: $localId, ')
          ..write('serverId: $serverId, ')
          ..write('ticketNumber: $ticketNumber, ')
          ..write('originalFilename: $originalFilename, ')
          ..write('mimeType: $mimeType, ')
          ..write('fileSize: $fileSize, ')
          ..write('localFilePath: $localFilePath, ')
          ..write('downloadUrl: $downloadUrl, ')
          ..write('thumbnailUrl: $thumbnailUrl, ')
          ..write('isDeleted: $isDeleted, ')
          ..write('uploadedAt: $uploadedAt, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncStatus: $syncStatus, ')
          ..write('localUpdatedAt: $localUpdatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncOutboxTable extends SyncOutbox
    with TableInfo<$SyncOutboxTable, SyncOutboxData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncOutboxTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _operationIdMeta = const VerificationMeta(
    'operationId',
  );
  @override
  late final GeneratedColumn<String> operationId = GeneratedColumn<String>(
    'operation_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityTypeMeta = const VerificationMeta(
    'entityType',
  );
  @override
  late final GeneratedColumn<String> entityType = GeneratedColumn<String>(
    'entity_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityLocalIdMeta = const VerificationMeta(
    'entityLocalId',
  );
  @override
  late final GeneratedColumn<String> entityLocalId = GeneratedColumn<String>(
    'entity_local_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _entityServerIdMeta = const VerificationMeta(
    'entityServerId',
  );
  @override
  late final GeneratedColumn<String> entityServerId = GeneratedColumn<String>(
    'entity_server_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _operationMeta = const VerificationMeta(
    'operation',
  );
  @override
  late final GeneratedColumn<String> operation = GeneratedColumn<String>(
    'operation',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _payloadJsonMeta = const VerificationMeta(
    'payloadJson',
  );
  @override
  late final GeneratedColumn<String> payloadJson = GeneratedColumn<String>(
    'payload_json',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _retryCountMeta = const VerificationMeta(
    'retryCount',
  );
  @override
  late final GeneratedColumn<int> retryCount = GeneratedColumn<int>(
    'retry_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _nextRetryAtMeta = const VerificationMeta(
    'nextRetryAt',
  );
  @override
  late final GeneratedColumn<DateTime> nextRetryAt = GeneratedColumn<DateTime>(
    'next_retry_at',
    aliasedName,
    true,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _statusMeta = const VerificationMeta('status');
  @override
  late final GeneratedColumn<String> status = GeneratedColumn<String>(
    'status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('pending'),
  );
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _dependsOnOperationIdMeta =
      const VerificationMeta('dependsOnOperationId');
  @override
  late final GeneratedColumn<String> dependsOnOperationId =
      GeneratedColumn<String>(
        'depends_on_operation_id',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    operationId,
    entityType,
    entityLocalId,
    entityServerId,
    operation,
    payloadJson,
    createdAt,
    retryCount,
    nextRetryAt,
    lastError,
    status,
    accountUsername,
    dependsOnOperationId,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_outbox';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncOutboxData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('operation_id')) {
      context.handle(
        _operationIdMeta,
        operationId.isAcceptableOrUnknown(
          data['operation_id']!,
          _operationIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_operationIdMeta);
    }
    if (data.containsKey('entity_type')) {
      context.handle(
        _entityTypeMeta,
        entityType.isAcceptableOrUnknown(data['entity_type']!, _entityTypeMeta),
      );
    } else if (isInserting) {
      context.missing(_entityTypeMeta);
    }
    if (data.containsKey('entity_local_id')) {
      context.handle(
        _entityLocalIdMeta,
        entityLocalId.isAcceptableOrUnknown(
          data['entity_local_id']!,
          _entityLocalIdMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_entityLocalIdMeta);
    }
    if (data.containsKey('entity_server_id')) {
      context.handle(
        _entityServerIdMeta,
        entityServerId.isAcceptableOrUnknown(
          data['entity_server_id']!,
          _entityServerIdMeta,
        ),
      );
    }
    if (data.containsKey('operation')) {
      context.handle(
        _operationMeta,
        operation.isAcceptableOrUnknown(data['operation']!, _operationMeta),
      );
    } else if (isInserting) {
      context.missing(_operationMeta);
    }
    if (data.containsKey('payload_json')) {
      context.handle(
        _payloadJsonMeta,
        payloadJson.isAcceptableOrUnknown(
          data['payload_json']!,
          _payloadJsonMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_payloadJsonMeta);
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('retry_count')) {
      context.handle(
        _retryCountMeta,
        retryCount.isAcceptableOrUnknown(data['retry_count']!, _retryCountMeta),
      );
    }
    if (data.containsKey('next_retry_at')) {
      context.handle(
        _nextRetryAtMeta,
        nextRetryAt.isAcceptableOrUnknown(
          data['next_retry_at']!,
          _nextRetryAtMeta,
        ),
      );
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    if (data.containsKey('status')) {
      context.handle(
        _statusMeta,
        status.isAcceptableOrUnknown(data['status']!, _statusMeta),
      );
    }
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('depends_on_operation_id')) {
      context.handle(
        _dependsOnOperationIdMeta,
        dependsOnOperationId.isAcceptableOrUnknown(
          data['depends_on_operation_id']!,
          _dependsOnOperationIdMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  SyncOutboxData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncOutboxData(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      operationId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}operation_id'],
      )!,
      entityType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_type'],
      )!,
      entityLocalId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_local_id'],
      )!,
      entityServerId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}entity_server_id'],
      ),
      operation: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}operation'],
      )!,
      payloadJson: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}payload_json'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      retryCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}retry_count'],
      )!,
      nextRetryAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}next_retry_at'],
      ),
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
      status: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}status'],
      )!,
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      dependsOnOperationId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}depends_on_operation_id'],
      ),
    );
  }

  @override
  $SyncOutboxTable createAlias(String alias) {
    return $SyncOutboxTable(attachedDatabase, alias);
  }
}

class SyncOutboxData extends DataClass implements Insertable<SyncOutboxData> {
  final String id;
  final String operationId;
  final String entityType;
  final String entityLocalId;
  final String? entityServerId;
  final String operation;
  final String payloadJson;
  final DateTime createdAt;
  final int retryCount;
  final DateTime? nextRetryAt;
  final String? lastError;
  final String status;
  final String accountUsername;
  final String? dependsOnOperationId;
  const SyncOutboxData({
    required this.id,
    required this.operationId,
    required this.entityType,
    required this.entityLocalId,
    this.entityServerId,
    required this.operation,
    required this.payloadJson,
    required this.createdAt,
    required this.retryCount,
    this.nextRetryAt,
    this.lastError,
    required this.status,
    required this.accountUsername,
    this.dependsOnOperationId,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['operation_id'] = Variable<String>(operationId);
    map['entity_type'] = Variable<String>(entityType);
    map['entity_local_id'] = Variable<String>(entityLocalId);
    if (!nullToAbsent || entityServerId != null) {
      map['entity_server_id'] = Variable<String>(entityServerId);
    }
    map['operation'] = Variable<String>(operation);
    map['payload_json'] = Variable<String>(payloadJson);
    map['created_at'] = Variable<DateTime>(createdAt);
    map['retry_count'] = Variable<int>(retryCount);
    if (!nullToAbsent || nextRetryAt != null) {
      map['next_retry_at'] = Variable<DateTime>(nextRetryAt);
    }
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    map['status'] = Variable<String>(status);
    map['account_username'] = Variable<String>(accountUsername);
    if (!nullToAbsent || dependsOnOperationId != null) {
      map['depends_on_operation_id'] = Variable<String>(dependsOnOperationId);
    }
    return map;
  }

  SyncOutboxCompanion toCompanion(bool nullToAbsent) {
    return SyncOutboxCompanion(
      id: Value(id),
      operationId: Value(operationId),
      entityType: Value(entityType),
      entityLocalId: Value(entityLocalId),
      entityServerId: entityServerId == null && nullToAbsent
          ? const Value.absent()
          : Value(entityServerId),
      operation: Value(operation),
      payloadJson: Value(payloadJson),
      createdAt: Value(createdAt),
      retryCount: Value(retryCount),
      nextRetryAt: nextRetryAt == null && nullToAbsent
          ? const Value.absent()
          : Value(nextRetryAt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
      status: Value(status),
      accountUsername: Value(accountUsername),
      dependsOnOperationId: dependsOnOperationId == null && nullToAbsent
          ? const Value.absent()
          : Value(dependsOnOperationId),
    );
  }

  factory SyncOutboxData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncOutboxData(
      id: serializer.fromJson<String>(json['id']),
      operationId: serializer.fromJson<String>(json['operationId']),
      entityType: serializer.fromJson<String>(json['entityType']),
      entityLocalId: serializer.fromJson<String>(json['entityLocalId']),
      entityServerId: serializer.fromJson<String?>(json['entityServerId']),
      operation: serializer.fromJson<String>(json['operation']),
      payloadJson: serializer.fromJson<String>(json['payloadJson']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      retryCount: serializer.fromJson<int>(json['retryCount']),
      nextRetryAt: serializer.fromJson<DateTime?>(json['nextRetryAt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
      status: serializer.fromJson<String>(json['status']),
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      dependsOnOperationId: serializer.fromJson<String?>(
        json['dependsOnOperationId'],
      ),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'operationId': serializer.toJson<String>(operationId),
      'entityType': serializer.toJson<String>(entityType),
      'entityLocalId': serializer.toJson<String>(entityLocalId),
      'entityServerId': serializer.toJson<String?>(entityServerId),
      'operation': serializer.toJson<String>(operation),
      'payloadJson': serializer.toJson<String>(payloadJson),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'retryCount': serializer.toJson<int>(retryCount),
      'nextRetryAt': serializer.toJson<DateTime?>(nextRetryAt),
      'lastError': serializer.toJson<String?>(lastError),
      'status': serializer.toJson<String>(status),
      'accountUsername': serializer.toJson<String>(accountUsername),
      'dependsOnOperationId': serializer.toJson<String?>(dependsOnOperationId),
    };
  }

  SyncOutboxData copyWith({
    String? id,
    String? operationId,
    String? entityType,
    String? entityLocalId,
    Value<String?> entityServerId = const Value.absent(),
    String? operation,
    String? payloadJson,
    DateTime? createdAt,
    int? retryCount,
    Value<DateTime?> nextRetryAt = const Value.absent(),
    Value<String?> lastError = const Value.absent(),
    String? status,
    String? accountUsername,
    Value<String?> dependsOnOperationId = const Value.absent(),
  }) => SyncOutboxData(
    id: id ?? this.id,
    operationId: operationId ?? this.operationId,
    entityType: entityType ?? this.entityType,
    entityLocalId: entityLocalId ?? this.entityLocalId,
    entityServerId: entityServerId.present
        ? entityServerId.value
        : this.entityServerId,
    operation: operation ?? this.operation,
    payloadJson: payloadJson ?? this.payloadJson,
    createdAt: createdAt ?? this.createdAt,
    retryCount: retryCount ?? this.retryCount,
    nextRetryAt: nextRetryAt.present ? nextRetryAt.value : this.nextRetryAt,
    lastError: lastError.present ? lastError.value : this.lastError,
    status: status ?? this.status,
    accountUsername: accountUsername ?? this.accountUsername,
    dependsOnOperationId: dependsOnOperationId.present
        ? dependsOnOperationId.value
        : this.dependsOnOperationId,
  );
  SyncOutboxData copyWithCompanion(SyncOutboxCompanion data) {
    return SyncOutboxData(
      id: data.id.present ? data.id.value : this.id,
      operationId: data.operationId.present
          ? data.operationId.value
          : this.operationId,
      entityType: data.entityType.present
          ? data.entityType.value
          : this.entityType,
      entityLocalId: data.entityLocalId.present
          ? data.entityLocalId.value
          : this.entityLocalId,
      entityServerId: data.entityServerId.present
          ? data.entityServerId.value
          : this.entityServerId,
      operation: data.operation.present ? data.operation.value : this.operation,
      payloadJson: data.payloadJson.present
          ? data.payloadJson.value
          : this.payloadJson,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      retryCount: data.retryCount.present
          ? data.retryCount.value
          : this.retryCount,
      nextRetryAt: data.nextRetryAt.present
          ? data.nextRetryAt.value
          : this.nextRetryAt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
      status: data.status.present ? data.status.value : this.status,
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      dependsOnOperationId: data.dependsOnOperationId.present
          ? data.dependsOnOperationId.value
          : this.dependsOnOperationId,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncOutboxData(')
          ..write('id: $id, ')
          ..write('operationId: $operationId, ')
          ..write('entityType: $entityType, ')
          ..write('entityLocalId: $entityLocalId, ')
          ..write('entityServerId: $entityServerId, ')
          ..write('operation: $operation, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('retryCount: $retryCount, ')
          ..write('nextRetryAt: $nextRetryAt, ')
          ..write('lastError: $lastError, ')
          ..write('status: $status, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('dependsOnOperationId: $dependsOnOperationId')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    operationId,
    entityType,
    entityLocalId,
    entityServerId,
    operation,
    payloadJson,
    createdAt,
    retryCount,
    nextRetryAt,
    lastError,
    status,
    accountUsername,
    dependsOnOperationId,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncOutboxData &&
          other.id == this.id &&
          other.operationId == this.operationId &&
          other.entityType == this.entityType &&
          other.entityLocalId == this.entityLocalId &&
          other.entityServerId == this.entityServerId &&
          other.operation == this.operation &&
          other.payloadJson == this.payloadJson &&
          other.createdAt == this.createdAt &&
          other.retryCount == this.retryCount &&
          other.nextRetryAt == this.nextRetryAt &&
          other.lastError == this.lastError &&
          other.status == this.status &&
          other.accountUsername == this.accountUsername &&
          other.dependsOnOperationId == this.dependsOnOperationId);
}

class SyncOutboxCompanion extends UpdateCompanion<SyncOutboxData> {
  final Value<String> id;
  final Value<String> operationId;
  final Value<String> entityType;
  final Value<String> entityLocalId;
  final Value<String?> entityServerId;
  final Value<String> operation;
  final Value<String> payloadJson;
  final Value<DateTime> createdAt;
  final Value<int> retryCount;
  final Value<DateTime?> nextRetryAt;
  final Value<String?> lastError;
  final Value<String> status;
  final Value<String> accountUsername;
  final Value<String?> dependsOnOperationId;
  final Value<int> rowid;
  const SyncOutboxCompanion({
    this.id = const Value.absent(),
    this.operationId = const Value.absent(),
    this.entityType = const Value.absent(),
    this.entityLocalId = const Value.absent(),
    this.entityServerId = const Value.absent(),
    this.operation = const Value.absent(),
    this.payloadJson = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.retryCount = const Value.absent(),
    this.nextRetryAt = const Value.absent(),
    this.lastError = const Value.absent(),
    this.status = const Value.absent(),
    this.accountUsername = const Value.absent(),
    this.dependsOnOperationId = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncOutboxCompanion.insert({
    required String id,
    required String operationId,
    required String entityType,
    required String entityLocalId,
    this.entityServerId = const Value.absent(),
    required String operation,
    required String payloadJson,
    required DateTime createdAt,
    this.retryCount = const Value.absent(),
    this.nextRetryAt = const Value.absent(),
    this.lastError = const Value.absent(),
    this.status = const Value.absent(),
    required String accountUsername,
    this.dependsOnOperationId = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       operationId = Value(operationId),
       entityType = Value(entityType),
       entityLocalId = Value(entityLocalId),
       operation = Value(operation),
       payloadJson = Value(payloadJson),
       createdAt = Value(createdAt),
       accountUsername = Value(accountUsername);
  static Insertable<SyncOutboxData> custom({
    Expression<String>? id,
    Expression<String>? operationId,
    Expression<String>? entityType,
    Expression<String>? entityLocalId,
    Expression<String>? entityServerId,
    Expression<String>? operation,
    Expression<String>? payloadJson,
    Expression<DateTime>? createdAt,
    Expression<int>? retryCount,
    Expression<DateTime>? nextRetryAt,
    Expression<String>? lastError,
    Expression<String>? status,
    Expression<String>? accountUsername,
    Expression<String>? dependsOnOperationId,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (operationId != null) 'operation_id': operationId,
      if (entityType != null) 'entity_type': entityType,
      if (entityLocalId != null) 'entity_local_id': entityLocalId,
      if (entityServerId != null) 'entity_server_id': entityServerId,
      if (operation != null) 'operation': operation,
      if (payloadJson != null) 'payload_json': payloadJson,
      if (createdAt != null) 'created_at': createdAt,
      if (retryCount != null) 'retry_count': retryCount,
      if (nextRetryAt != null) 'next_retry_at': nextRetryAt,
      if (lastError != null) 'last_error': lastError,
      if (status != null) 'status': status,
      if (accountUsername != null) 'account_username': accountUsername,
      if (dependsOnOperationId != null)
        'depends_on_operation_id': dependsOnOperationId,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncOutboxCompanion copyWith({
    Value<String>? id,
    Value<String>? operationId,
    Value<String>? entityType,
    Value<String>? entityLocalId,
    Value<String?>? entityServerId,
    Value<String>? operation,
    Value<String>? payloadJson,
    Value<DateTime>? createdAt,
    Value<int>? retryCount,
    Value<DateTime?>? nextRetryAt,
    Value<String?>? lastError,
    Value<String>? status,
    Value<String>? accountUsername,
    Value<String?>? dependsOnOperationId,
    Value<int>? rowid,
  }) {
    return SyncOutboxCompanion(
      id: id ?? this.id,
      operationId: operationId ?? this.operationId,
      entityType: entityType ?? this.entityType,
      entityLocalId: entityLocalId ?? this.entityLocalId,
      entityServerId: entityServerId ?? this.entityServerId,
      operation: operation ?? this.operation,
      payloadJson: payloadJson ?? this.payloadJson,
      createdAt: createdAt ?? this.createdAt,
      retryCount: retryCount ?? this.retryCount,
      nextRetryAt: nextRetryAt ?? this.nextRetryAt,
      lastError: lastError ?? this.lastError,
      status: status ?? this.status,
      accountUsername: accountUsername ?? this.accountUsername,
      dependsOnOperationId: dependsOnOperationId ?? this.dependsOnOperationId,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (operationId.present) {
      map['operation_id'] = Variable<String>(operationId.value);
    }
    if (entityType.present) {
      map['entity_type'] = Variable<String>(entityType.value);
    }
    if (entityLocalId.present) {
      map['entity_local_id'] = Variable<String>(entityLocalId.value);
    }
    if (entityServerId.present) {
      map['entity_server_id'] = Variable<String>(entityServerId.value);
    }
    if (operation.present) {
      map['operation'] = Variable<String>(operation.value);
    }
    if (payloadJson.present) {
      map['payload_json'] = Variable<String>(payloadJson.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (retryCount.present) {
      map['retry_count'] = Variable<int>(retryCount.value);
    }
    if (nextRetryAt.present) {
      map['next_retry_at'] = Variable<DateTime>(nextRetryAt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    if (status.present) {
      map['status'] = Variable<String>(status.value);
    }
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (dependsOnOperationId.present) {
      map['depends_on_operation_id'] = Variable<String>(
        dependsOnOperationId.value,
      );
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncOutboxCompanion(')
          ..write('id: $id, ')
          ..write('operationId: $operationId, ')
          ..write('entityType: $entityType, ')
          ..write('entityLocalId: $entityLocalId, ')
          ..write('entityServerId: $entityServerId, ')
          ..write('operation: $operation, ')
          ..write('payloadJson: $payloadJson, ')
          ..write('createdAt: $createdAt, ')
          ..write('retryCount: $retryCount, ')
          ..write('nextRetryAt: $nextRetryAt, ')
          ..write('lastError: $lastError, ')
          ..write('status: $status, ')
          ..write('accountUsername: $accountUsername, ')
          ..write('dependsOnOperationId: $dependsOnOperationId, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SyncMetadataTable extends SyncMetadata
    with TableInfo<$SyncMetadataTable, SyncMetadataData> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SyncMetadataTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _syncCursorMeta = const VerificationMeta(
    'syncCursor',
  );
  @override
  late final GeneratedColumn<String> syncCursor = GeneratedColumn<String>(
    'sync_cursor',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _lastSuccessfulSyncMeta =
      const VerificationMeta('lastSuccessfulSync');
  @override
  late final GeneratedColumn<DateTime> lastSuccessfulSync =
      GeneratedColumn<DateTime>(
        'last_successful_sync',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _lastSyncAttemptMeta = const VerificationMeta(
    'lastSyncAttempt',
  );
  @override
  late final GeneratedColumn<DateTime> lastSyncAttempt =
      GeneratedColumn<DateTime>(
        'last_sync_attempt',
        aliasedName,
        true,
        type: DriftSqlType.dateTime,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _pendingOperationsCountMeta =
      const VerificationMeta('pendingOperationsCount');
  @override
  late final GeneratedColumn<int> pendingOperationsCount = GeneratedColumn<int>(
    'pending_operations_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _conflictsCountMeta = const VerificationMeta(
    'conflictsCount',
  );
  @override
  late final GeneratedColumn<int> conflictsCount = GeneratedColumn<int>(
    'conflicts_count',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  @override
  List<GeneratedColumn> get $columns => [
    accountUsername,
    syncCursor,
    lastSuccessfulSync,
    lastSyncAttempt,
    lastError,
    pendingOperationsCount,
    conflictsCount,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'sync_metadata';
  @override
  VerificationContext validateIntegrity(
    Insertable<SyncMetadataData> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('sync_cursor')) {
      context.handle(
        _syncCursorMeta,
        syncCursor.isAcceptableOrUnknown(data['sync_cursor']!, _syncCursorMeta),
      );
    }
    if (data.containsKey('last_successful_sync')) {
      context.handle(
        _lastSuccessfulSyncMeta,
        lastSuccessfulSync.isAcceptableOrUnknown(
          data['last_successful_sync']!,
          _lastSuccessfulSyncMeta,
        ),
      );
    }
    if (data.containsKey('last_sync_attempt')) {
      context.handle(
        _lastSyncAttemptMeta,
        lastSyncAttempt.isAcceptableOrUnknown(
          data['last_sync_attempt']!,
          _lastSyncAttemptMeta,
        ),
      );
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    if (data.containsKey('pending_operations_count')) {
      context.handle(
        _pendingOperationsCountMeta,
        pendingOperationsCount.isAcceptableOrUnknown(
          data['pending_operations_count']!,
          _pendingOperationsCountMeta,
        ),
      );
    }
    if (data.containsKey('conflicts_count')) {
      context.handle(
        _conflictsCountMeta,
        conflictsCount.isAcceptableOrUnknown(
          data['conflicts_count']!,
          _conflictsCountMeta,
        ),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {accountUsername};
  @override
  SyncMetadataData map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return SyncMetadataData(
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      syncCursor: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}sync_cursor'],
      ),
      lastSuccessfulSync: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_successful_sync'],
      ),
      lastSyncAttempt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}last_sync_attempt'],
      ),
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
      pendingOperationsCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}pending_operations_count'],
      )!,
      conflictsCount: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}conflicts_count'],
      )!,
    );
  }

  @override
  $SyncMetadataTable createAlias(String alias) {
    return $SyncMetadataTable(attachedDatabase, alias);
  }
}

class SyncMetadataData extends DataClass
    implements Insertable<SyncMetadataData> {
  final String accountUsername;
  final String? syncCursor;
  final DateTime? lastSuccessfulSync;
  final DateTime? lastSyncAttempt;
  final String? lastError;
  final int pendingOperationsCount;
  final int conflictsCount;
  const SyncMetadataData({
    required this.accountUsername,
    this.syncCursor,
    this.lastSuccessfulSync,
    this.lastSyncAttempt,
    this.lastError,
    required this.pendingOperationsCount,
    required this.conflictsCount,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['account_username'] = Variable<String>(accountUsername);
    if (!nullToAbsent || syncCursor != null) {
      map['sync_cursor'] = Variable<String>(syncCursor);
    }
    if (!nullToAbsent || lastSuccessfulSync != null) {
      map['last_successful_sync'] = Variable<DateTime>(lastSuccessfulSync);
    }
    if (!nullToAbsent || lastSyncAttempt != null) {
      map['last_sync_attempt'] = Variable<DateTime>(lastSyncAttempt);
    }
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    map['pending_operations_count'] = Variable<int>(pendingOperationsCount);
    map['conflicts_count'] = Variable<int>(conflictsCount);
    return map;
  }

  SyncMetadataCompanion toCompanion(bool nullToAbsent) {
    return SyncMetadataCompanion(
      accountUsername: Value(accountUsername),
      syncCursor: syncCursor == null && nullToAbsent
          ? const Value.absent()
          : Value(syncCursor),
      lastSuccessfulSync: lastSuccessfulSync == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSuccessfulSync),
      lastSyncAttempt: lastSyncAttempt == null && nullToAbsent
          ? const Value.absent()
          : Value(lastSyncAttempt),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
      pendingOperationsCount: Value(pendingOperationsCount),
      conflictsCount: Value(conflictsCount),
    );
  }

  factory SyncMetadataData.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return SyncMetadataData(
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      syncCursor: serializer.fromJson<String?>(json['syncCursor']),
      lastSuccessfulSync: serializer.fromJson<DateTime?>(
        json['lastSuccessfulSync'],
      ),
      lastSyncAttempt: serializer.fromJson<DateTime?>(json['lastSyncAttempt']),
      lastError: serializer.fromJson<String?>(json['lastError']),
      pendingOperationsCount: serializer.fromJson<int>(
        json['pendingOperationsCount'],
      ),
      conflictsCount: serializer.fromJson<int>(json['conflictsCount']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'accountUsername': serializer.toJson<String>(accountUsername),
      'syncCursor': serializer.toJson<String?>(syncCursor),
      'lastSuccessfulSync': serializer.toJson<DateTime?>(lastSuccessfulSync),
      'lastSyncAttempt': serializer.toJson<DateTime?>(lastSyncAttempt),
      'lastError': serializer.toJson<String?>(lastError),
      'pendingOperationsCount': serializer.toJson<int>(pendingOperationsCount),
      'conflictsCount': serializer.toJson<int>(conflictsCount),
    };
  }

  SyncMetadataData copyWith({
    String? accountUsername,
    Value<String?> syncCursor = const Value.absent(),
    Value<DateTime?> lastSuccessfulSync = const Value.absent(),
    Value<DateTime?> lastSyncAttempt = const Value.absent(),
    Value<String?> lastError = const Value.absent(),
    int? pendingOperationsCount,
    int? conflictsCount,
  }) => SyncMetadataData(
    accountUsername: accountUsername ?? this.accountUsername,
    syncCursor: syncCursor.present ? syncCursor.value : this.syncCursor,
    lastSuccessfulSync: lastSuccessfulSync.present
        ? lastSuccessfulSync.value
        : this.lastSuccessfulSync,
    lastSyncAttempt: lastSyncAttempt.present
        ? lastSyncAttempt.value
        : this.lastSyncAttempt,
    lastError: lastError.present ? lastError.value : this.lastError,
    pendingOperationsCount:
        pendingOperationsCount ?? this.pendingOperationsCount,
    conflictsCount: conflictsCount ?? this.conflictsCount,
  );
  SyncMetadataData copyWithCompanion(SyncMetadataCompanion data) {
    return SyncMetadataData(
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      syncCursor: data.syncCursor.present
          ? data.syncCursor.value
          : this.syncCursor,
      lastSuccessfulSync: data.lastSuccessfulSync.present
          ? data.lastSuccessfulSync.value
          : this.lastSuccessfulSync,
      lastSyncAttempt: data.lastSyncAttempt.present
          ? data.lastSyncAttempt.value
          : this.lastSyncAttempt,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
      pendingOperationsCount: data.pendingOperationsCount.present
          ? data.pendingOperationsCount.value
          : this.pendingOperationsCount,
      conflictsCount: data.conflictsCount.present
          ? data.conflictsCount.value
          : this.conflictsCount,
    );
  }

  @override
  String toString() {
    return (StringBuffer('SyncMetadataData(')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncCursor: $syncCursor, ')
          ..write('lastSuccessfulSync: $lastSuccessfulSync, ')
          ..write('lastSyncAttempt: $lastSyncAttempt, ')
          ..write('lastError: $lastError, ')
          ..write('pendingOperationsCount: $pendingOperationsCount, ')
          ..write('conflictsCount: $conflictsCount')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    accountUsername,
    syncCursor,
    lastSuccessfulSync,
    lastSyncAttempt,
    lastError,
    pendingOperationsCount,
    conflictsCount,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is SyncMetadataData &&
          other.accountUsername == this.accountUsername &&
          other.syncCursor == this.syncCursor &&
          other.lastSuccessfulSync == this.lastSuccessfulSync &&
          other.lastSyncAttempt == this.lastSyncAttempt &&
          other.lastError == this.lastError &&
          other.pendingOperationsCount == this.pendingOperationsCount &&
          other.conflictsCount == this.conflictsCount);
}

class SyncMetadataCompanion extends UpdateCompanion<SyncMetadataData> {
  final Value<String> accountUsername;
  final Value<String?> syncCursor;
  final Value<DateTime?> lastSuccessfulSync;
  final Value<DateTime?> lastSyncAttempt;
  final Value<String?> lastError;
  final Value<int> pendingOperationsCount;
  final Value<int> conflictsCount;
  final Value<int> rowid;
  const SyncMetadataCompanion({
    this.accountUsername = const Value.absent(),
    this.syncCursor = const Value.absent(),
    this.lastSuccessfulSync = const Value.absent(),
    this.lastSyncAttempt = const Value.absent(),
    this.lastError = const Value.absent(),
    this.pendingOperationsCount = const Value.absent(),
    this.conflictsCount = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SyncMetadataCompanion.insert({
    required String accountUsername,
    this.syncCursor = const Value.absent(),
    this.lastSuccessfulSync = const Value.absent(),
    this.lastSyncAttempt = const Value.absent(),
    this.lastError = const Value.absent(),
    this.pendingOperationsCount = const Value.absent(),
    this.conflictsCount = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : accountUsername = Value(accountUsername);
  static Insertable<SyncMetadataData> custom({
    Expression<String>? accountUsername,
    Expression<String>? syncCursor,
    Expression<DateTime>? lastSuccessfulSync,
    Expression<DateTime>? lastSyncAttempt,
    Expression<String>? lastError,
    Expression<int>? pendingOperationsCount,
    Expression<int>? conflictsCount,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (accountUsername != null) 'account_username': accountUsername,
      if (syncCursor != null) 'sync_cursor': syncCursor,
      if (lastSuccessfulSync != null)
        'last_successful_sync': lastSuccessfulSync,
      if (lastSyncAttempt != null) 'last_sync_attempt': lastSyncAttempt,
      if (lastError != null) 'last_error': lastError,
      if (pendingOperationsCount != null)
        'pending_operations_count': pendingOperationsCount,
      if (conflictsCount != null) 'conflicts_count': conflictsCount,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SyncMetadataCompanion copyWith({
    Value<String>? accountUsername,
    Value<String?>? syncCursor,
    Value<DateTime?>? lastSuccessfulSync,
    Value<DateTime?>? lastSyncAttempt,
    Value<String?>? lastError,
    Value<int>? pendingOperationsCount,
    Value<int>? conflictsCount,
    Value<int>? rowid,
  }) {
    return SyncMetadataCompanion(
      accountUsername: accountUsername ?? this.accountUsername,
      syncCursor: syncCursor ?? this.syncCursor,
      lastSuccessfulSync: lastSuccessfulSync ?? this.lastSuccessfulSync,
      lastSyncAttempt: lastSyncAttempt ?? this.lastSyncAttempt,
      lastError: lastError ?? this.lastError,
      pendingOperationsCount:
          pendingOperationsCount ?? this.pendingOperationsCount,
      conflictsCount: conflictsCount ?? this.conflictsCount,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (syncCursor.present) {
      map['sync_cursor'] = Variable<String>(syncCursor.value);
    }
    if (lastSuccessfulSync.present) {
      map['last_successful_sync'] = Variable<DateTime>(
        lastSuccessfulSync.value,
      );
    }
    if (lastSyncAttempt.present) {
      map['last_sync_attempt'] = Variable<DateTime>(lastSyncAttempt.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    if (pendingOperationsCount.present) {
      map['pending_operations_count'] = Variable<int>(
        pendingOperationsCount.value,
      );
    }
    if (conflictsCount.present) {
      map['conflicts_count'] = Variable<int>(conflictsCount.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SyncMetadataCompanion(')
          ..write('accountUsername: $accountUsername, ')
          ..write('syncCursor: $syncCursor, ')
          ..write('lastSuccessfulSync: $lastSuccessfulSync, ')
          ..write('lastSyncAttempt: $lastSyncAttempt, ')
          ..write('lastError: $lastError, ')
          ..write('pendingOperationsCount: $pendingOperationsCount, ')
          ..write('conflictsCount: $conflictsCount, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $LocalPermissionsTable extends LocalPermissions
    with TableInfo<$LocalPermissionsTable, LocalPermission> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $LocalPermissionsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _accountUsernameMeta = const VerificationMeta(
    'accountUsername',
  );
  @override
  late final GeneratedColumn<String> accountUsername = GeneratedColumn<String>(
    'account_username',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _codeMeta = const VerificationMeta('code');
  @override
  late final GeneratedColumn<String> code = GeneratedColumn<String>(
    'code',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [accountUsername, code];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'local_permissions';
  @override
  VerificationContext validateIntegrity(
    Insertable<LocalPermission> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('account_username')) {
      context.handle(
        _accountUsernameMeta,
        accountUsername.isAcceptableOrUnknown(
          data['account_username']!,
          _accountUsernameMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_accountUsernameMeta);
    }
    if (data.containsKey('code')) {
      context.handle(
        _codeMeta,
        code.isAcceptableOrUnknown(data['code']!, _codeMeta),
      );
    } else if (isInserting) {
      context.missing(_codeMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {accountUsername, code};
  @override
  LocalPermission map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return LocalPermission(
      accountUsername: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}account_username'],
      )!,
      code: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}code'],
      )!,
    );
  }

  @override
  $LocalPermissionsTable createAlias(String alias) {
    return $LocalPermissionsTable(attachedDatabase, alias);
  }
}

class LocalPermission extends DataClass implements Insertable<LocalPermission> {
  final String accountUsername;
  final String code;
  const LocalPermission({required this.accountUsername, required this.code});
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['account_username'] = Variable<String>(accountUsername);
    map['code'] = Variable<String>(code);
    return map;
  }

  LocalPermissionsCompanion toCompanion(bool nullToAbsent) {
    return LocalPermissionsCompanion(
      accountUsername: Value(accountUsername),
      code: Value(code),
    );
  }

  factory LocalPermission.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return LocalPermission(
      accountUsername: serializer.fromJson<String>(json['accountUsername']),
      code: serializer.fromJson<String>(json['code']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'accountUsername': serializer.toJson<String>(accountUsername),
      'code': serializer.toJson<String>(code),
    };
  }

  LocalPermission copyWith({String? accountUsername, String? code}) =>
      LocalPermission(
        accountUsername: accountUsername ?? this.accountUsername,
        code: code ?? this.code,
      );
  LocalPermission copyWithCompanion(LocalPermissionsCompanion data) {
    return LocalPermission(
      accountUsername: data.accountUsername.present
          ? data.accountUsername.value
          : this.accountUsername,
      code: data.code.present ? data.code.value : this.code,
    );
  }

  @override
  String toString() {
    return (StringBuffer('LocalPermission(')
          ..write('accountUsername: $accountUsername, ')
          ..write('code: $code')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(accountUsername, code);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is LocalPermission &&
          other.accountUsername == this.accountUsername &&
          other.code == this.code);
}

class LocalPermissionsCompanion extends UpdateCompanion<LocalPermission> {
  final Value<String> accountUsername;
  final Value<String> code;
  final Value<int> rowid;
  const LocalPermissionsCompanion({
    this.accountUsername = const Value.absent(),
    this.code = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  LocalPermissionsCompanion.insert({
    required String accountUsername,
    required String code,
    this.rowid = const Value.absent(),
  }) : accountUsername = Value(accountUsername),
       code = Value(code);
  static Insertable<LocalPermission> custom({
    Expression<String>? accountUsername,
    Expression<String>? code,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (accountUsername != null) 'account_username': accountUsername,
      if (code != null) 'code': code,
      if (rowid != null) 'rowid': rowid,
    });
  }

  LocalPermissionsCompanion copyWith({
    Value<String>? accountUsername,
    Value<String>? code,
    Value<int>? rowid,
  }) {
    return LocalPermissionsCompanion(
      accountUsername: accountUsername ?? this.accountUsername,
      code: code ?? this.code,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (accountUsername.present) {
      map['account_username'] = Variable<String>(accountUsername.value);
    }
    if (code.present) {
      map['code'] = Variable<String>(code.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('LocalPermissionsCompanion(')
          ..write('accountUsername: $accountUsername, ')
          ..write('code: $code, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $TicketsTable tickets = $TicketsTable(this);
  late final $UserCommentsTable userComments = $UserCommentsTable(this);
  late final $TicketAttachmentsTable ticketAttachments =
      $TicketAttachmentsTable(this);
  late final $SyncOutboxTable syncOutbox = $SyncOutboxTable(this);
  late final $SyncMetadataTable syncMetadata = $SyncMetadataTable(this);
  late final $LocalPermissionsTable localPermissions = $LocalPermissionsTable(
    this,
  );
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    tickets,
    userComments,
    ticketAttachments,
    syncOutbox,
    syncMetadata,
    localPermissions,
  ];
}

typedef $$TicketsTableCreateCompanionBuilder =
    TicketsCompanion Function({
      required String localId,
      required String ticketNumber,
      Value<String?> subject,
      Value<String?> inventoryNumber,
      Value<String?> printerModel,
      Value<String?> office,
      Value<String?> officeAbbreviated,
      Value<String?> cabinet,
      Value<String?> component,
      Value<String?> status,
      Value<String?> priority,
      Value<String?> assignedTo,
      Value<String?> authorName,
      Value<String?> department,
      Value<String?> currentNote,
      Value<String?> requiredAction,
      Value<String?> cause,
      Value<String?> faultDescription,
      Value<String?> workDone,
      Value<String?> techConclusion,
      Value<String?> soglasovanoLine,
      Value<bool> isArchived,
      Value<bool> isTask,
      Value<bool> hasFiles,
      Value<bool> hasComments,
      Value<DateTime?> firstReceivedDate,
      Value<DateTime?> lastUpdatedDate,
      Value<DateTime?> completedAt,
      Value<String?> completedBy,
      Value<String?> lastStatus,
      required String accountUsername,
      Value<String> syncStatus,
      Value<DateTime?> lastSyncedAt,
      Value<String?> conflictServerJson,
      required DateTime localUpdatedAt,
      Value<int> rowid,
    });
typedef $$TicketsTableUpdateCompanionBuilder =
    TicketsCompanion Function({
      Value<String> localId,
      Value<String> ticketNumber,
      Value<String?> subject,
      Value<String?> inventoryNumber,
      Value<String?> printerModel,
      Value<String?> office,
      Value<String?> officeAbbreviated,
      Value<String?> cabinet,
      Value<String?> component,
      Value<String?> status,
      Value<String?> priority,
      Value<String?> assignedTo,
      Value<String?> authorName,
      Value<String?> department,
      Value<String?> currentNote,
      Value<String?> requiredAction,
      Value<String?> cause,
      Value<String?> faultDescription,
      Value<String?> workDone,
      Value<String?> techConclusion,
      Value<String?> soglasovanoLine,
      Value<bool> isArchived,
      Value<bool> isTask,
      Value<bool> hasFiles,
      Value<bool> hasComments,
      Value<DateTime?> firstReceivedDate,
      Value<DateTime?> lastUpdatedDate,
      Value<DateTime?> completedAt,
      Value<String?> completedBy,
      Value<String?> lastStatus,
      Value<String> accountUsername,
      Value<String> syncStatus,
      Value<DateTime?> lastSyncedAt,
      Value<String?> conflictServerJson,
      Value<DateTime> localUpdatedAt,
      Value<int> rowid,
    });

class $$TicketsTableFilterComposer
    extends Composer<_$AppDatabase, $TicketsTable> {
  $$TicketsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get subject => $composableBuilder(
    column: $table.subject,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get inventoryNumber => $composableBuilder(
    column: $table.inventoryNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get printerModel => $composableBuilder(
    column: $table.printerModel,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get office => $composableBuilder(
    column: $table.office,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get officeAbbreviated => $composableBuilder(
    column: $table.officeAbbreviated,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get cabinet => $composableBuilder(
    column: $table.cabinet,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get component => $composableBuilder(
    column: $table.component,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get priority => $composableBuilder(
    column: $table.priority,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get assignedTo => $composableBuilder(
    column: $table.assignedTo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get department => $composableBuilder(
    column: $table.department,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get currentNote => $composableBuilder(
    column: $table.currentNote,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get requiredAction => $composableBuilder(
    column: $table.requiredAction,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get cause => $composableBuilder(
    column: $table.cause,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get faultDescription => $composableBuilder(
    column: $table.faultDescription,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get workDone => $composableBuilder(
    column: $table.workDone,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get techConclusion => $composableBuilder(
    column: $table.techConclusion,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get soglasovanoLine => $composableBuilder(
    column: $table.soglasovanoLine,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isArchived => $composableBuilder(
    column: $table.isArchived,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isTask => $composableBuilder(
    column: $table.isTask,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get hasFiles => $composableBuilder(
    column: $table.hasFiles,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get hasComments => $composableBuilder(
    column: $table.hasComments,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get firstReceivedDate => $composableBuilder(
    column: $table.firstReceivedDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastUpdatedDate => $composableBuilder(
    column: $table.lastUpdatedDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get completedBy => $composableBuilder(
    column: $table.completedBy,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastStatus => $composableBuilder(
    column: $table.lastStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get conflictServerJson => $composableBuilder(
    column: $table.conflictServerJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$TicketsTableOrderingComposer
    extends Composer<_$AppDatabase, $TicketsTable> {
  $$TicketsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get subject => $composableBuilder(
    column: $table.subject,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get inventoryNumber => $composableBuilder(
    column: $table.inventoryNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get printerModel => $composableBuilder(
    column: $table.printerModel,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get office => $composableBuilder(
    column: $table.office,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get officeAbbreviated => $composableBuilder(
    column: $table.officeAbbreviated,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get cabinet => $composableBuilder(
    column: $table.cabinet,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get component => $composableBuilder(
    column: $table.component,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get priority => $composableBuilder(
    column: $table.priority,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get assignedTo => $composableBuilder(
    column: $table.assignedTo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get department => $composableBuilder(
    column: $table.department,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get currentNote => $composableBuilder(
    column: $table.currentNote,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get requiredAction => $composableBuilder(
    column: $table.requiredAction,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get cause => $composableBuilder(
    column: $table.cause,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get faultDescription => $composableBuilder(
    column: $table.faultDescription,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get workDone => $composableBuilder(
    column: $table.workDone,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get techConclusion => $composableBuilder(
    column: $table.techConclusion,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get soglasovanoLine => $composableBuilder(
    column: $table.soglasovanoLine,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isArchived => $composableBuilder(
    column: $table.isArchived,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isTask => $composableBuilder(
    column: $table.isTask,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get hasFiles => $composableBuilder(
    column: $table.hasFiles,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get hasComments => $composableBuilder(
    column: $table.hasComments,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get firstReceivedDate => $composableBuilder(
    column: $table.firstReceivedDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastUpdatedDate => $composableBuilder(
    column: $table.lastUpdatedDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get completedBy => $composableBuilder(
    column: $table.completedBy,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastStatus => $composableBuilder(
    column: $table.lastStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get conflictServerJson => $composableBuilder(
    column: $table.conflictServerJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$TicketsTableAnnotationComposer
    extends Composer<_$AppDatabase, $TicketsTable> {
  $$TicketsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localId =>
      $composableBuilder(column: $table.localId, builder: (column) => column);

  GeneratedColumn<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get subject =>
      $composableBuilder(column: $table.subject, builder: (column) => column);

  GeneratedColumn<String> get inventoryNumber => $composableBuilder(
    column: $table.inventoryNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get printerModel => $composableBuilder(
    column: $table.printerModel,
    builder: (column) => column,
  );

  GeneratedColumn<String> get office =>
      $composableBuilder(column: $table.office, builder: (column) => column);

  GeneratedColumn<String> get officeAbbreviated => $composableBuilder(
    column: $table.officeAbbreviated,
    builder: (column) => column,
  );

  GeneratedColumn<String> get cabinet =>
      $composableBuilder(column: $table.cabinet, builder: (column) => column);

  GeneratedColumn<String> get component =>
      $composableBuilder(column: $table.component, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get priority =>
      $composableBuilder(column: $table.priority, builder: (column) => column);

  GeneratedColumn<String> get assignedTo => $composableBuilder(
    column: $table.assignedTo,
    builder: (column) => column,
  );

  GeneratedColumn<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get department => $composableBuilder(
    column: $table.department,
    builder: (column) => column,
  );

  GeneratedColumn<String> get currentNote => $composableBuilder(
    column: $table.currentNote,
    builder: (column) => column,
  );

  GeneratedColumn<String> get requiredAction => $composableBuilder(
    column: $table.requiredAction,
    builder: (column) => column,
  );

  GeneratedColumn<String> get cause =>
      $composableBuilder(column: $table.cause, builder: (column) => column);

  GeneratedColumn<String> get faultDescription => $composableBuilder(
    column: $table.faultDescription,
    builder: (column) => column,
  );

  GeneratedColumn<String> get workDone =>
      $composableBuilder(column: $table.workDone, builder: (column) => column);

  GeneratedColumn<String> get techConclusion => $composableBuilder(
    column: $table.techConclusion,
    builder: (column) => column,
  );

  GeneratedColumn<String> get soglasovanoLine => $composableBuilder(
    column: $table.soglasovanoLine,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isArchived => $composableBuilder(
    column: $table.isArchived,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isTask =>
      $composableBuilder(column: $table.isTask, builder: (column) => column);

  GeneratedColumn<bool> get hasFiles =>
      $composableBuilder(column: $table.hasFiles, builder: (column) => column);

  GeneratedColumn<bool> get hasComments => $composableBuilder(
    column: $table.hasComments,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get firstReceivedDate => $composableBuilder(
    column: $table.firstReceivedDate,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get lastUpdatedDate => $composableBuilder(
    column: $table.lastUpdatedDate,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get completedAt => $composableBuilder(
    column: $table.completedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get completedBy => $composableBuilder(
    column: $table.completedBy,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastStatus => $composableBuilder(
    column: $table.lastStatus,
    builder: (column) => column,
  );

  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get lastSyncedAt => $composableBuilder(
    column: $table.lastSyncedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get conflictServerJson => $composableBuilder(
    column: $table.conflictServerJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => column,
  );
}

class $$TicketsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $TicketsTable,
          Ticket,
          $$TicketsTableFilterComposer,
          $$TicketsTableOrderingComposer,
          $$TicketsTableAnnotationComposer,
          $$TicketsTableCreateCompanionBuilder,
          $$TicketsTableUpdateCompanionBuilder,
          (Ticket, BaseReferences<_$AppDatabase, $TicketsTable, Ticket>),
          Ticket,
          PrefetchHooks Function()
        > {
  $$TicketsTableTableManager(_$AppDatabase db, $TicketsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TicketsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TicketsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TicketsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> localId = const Value.absent(),
                Value<String> ticketNumber = const Value.absent(),
                Value<String?> subject = const Value.absent(),
                Value<String?> inventoryNumber = const Value.absent(),
                Value<String?> printerModel = const Value.absent(),
                Value<String?> office = const Value.absent(),
                Value<String?> officeAbbreviated = const Value.absent(),
                Value<String?> cabinet = const Value.absent(),
                Value<String?> component = const Value.absent(),
                Value<String?> status = const Value.absent(),
                Value<String?> priority = const Value.absent(),
                Value<String?> assignedTo = const Value.absent(),
                Value<String?> authorName = const Value.absent(),
                Value<String?> department = const Value.absent(),
                Value<String?> currentNote = const Value.absent(),
                Value<String?> requiredAction = const Value.absent(),
                Value<String?> cause = const Value.absent(),
                Value<String?> faultDescription = const Value.absent(),
                Value<String?> workDone = const Value.absent(),
                Value<String?> techConclusion = const Value.absent(),
                Value<String?> soglasovanoLine = const Value.absent(),
                Value<bool> isArchived = const Value.absent(),
                Value<bool> isTask = const Value.absent(),
                Value<bool> hasFiles = const Value.absent(),
                Value<bool> hasComments = const Value.absent(),
                Value<DateTime?> firstReceivedDate = const Value.absent(),
                Value<DateTime?> lastUpdatedDate = const Value.absent(),
                Value<DateTime?> completedAt = const Value.absent(),
                Value<String?> completedBy = const Value.absent(),
                Value<String?> lastStatus = const Value.absent(),
                Value<String> accountUsername = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<DateTime?> lastSyncedAt = const Value.absent(),
                Value<String?> conflictServerJson = const Value.absent(),
                Value<DateTime> localUpdatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => TicketsCompanion(
                localId: localId,
                ticketNumber: ticketNumber,
                subject: subject,
                inventoryNumber: inventoryNumber,
                printerModel: printerModel,
                office: office,
                officeAbbreviated: officeAbbreviated,
                cabinet: cabinet,
                component: component,
                status: status,
                priority: priority,
                assignedTo: assignedTo,
                authorName: authorName,
                department: department,
                currentNote: currentNote,
                requiredAction: requiredAction,
                cause: cause,
                faultDescription: faultDescription,
                workDone: workDone,
                techConclusion: techConclusion,
                soglasovanoLine: soglasovanoLine,
                isArchived: isArchived,
                isTask: isTask,
                hasFiles: hasFiles,
                hasComments: hasComments,
                firstReceivedDate: firstReceivedDate,
                lastUpdatedDate: lastUpdatedDate,
                completedAt: completedAt,
                completedBy: completedBy,
                lastStatus: lastStatus,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                lastSyncedAt: lastSyncedAt,
                conflictServerJson: conflictServerJson,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String localId,
                required String ticketNumber,
                Value<String?> subject = const Value.absent(),
                Value<String?> inventoryNumber = const Value.absent(),
                Value<String?> printerModel = const Value.absent(),
                Value<String?> office = const Value.absent(),
                Value<String?> officeAbbreviated = const Value.absent(),
                Value<String?> cabinet = const Value.absent(),
                Value<String?> component = const Value.absent(),
                Value<String?> status = const Value.absent(),
                Value<String?> priority = const Value.absent(),
                Value<String?> assignedTo = const Value.absent(),
                Value<String?> authorName = const Value.absent(),
                Value<String?> department = const Value.absent(),
                Value<String?> currentNote = const Value.absent(),
                Value<String?> requiredAction = const Value.absent(),
                Value<String?> cause = const Value.absent(),
                Value<String?> faultDescription = const Value.absent(),
                Value<String?> workDone = const Value.absent(),
                Value<String?> techConclusion = const Value.absent(),
                Value<String?> soglasovanoLine = const Value.absent(),
                Value<bool> isArchived = const Value.absent(),
                Value<bool> isTask = const Value.absent(),
                Value<bool> hasFiles = const Value.absent(),
                Value<bool> hasComments = const Value.absent(),
                Value<DateTime?> firstReceivedDate = const Value.absent(),
                Value<DateTime?> lastUpdatedDate = const Value.absent(),
                Value<DateTime?> completedAt = const Value.absent(),
                Value<String?> completedBy = const Value.absent(),
                Value<String?> lastStatus = const Value.absent(),
                required String accountUsername,
                Value<String> syncStatus = const Value.absent(),
                Value<DateTime?> lastSyncedAt = const Value.absent(),
                Value<String?> conflictServerJson = const Value.absent(),
                required DateTime localUpdatedAt,
                Value<int> rowid = const Value.absent(),
              }) => TicketsCompanion.insert(
                localId: localId,
                ticketNumber: ticketNumber,
                subject: subject,
                inventoryNumber: inventoryNumber,
                printerModel: printerModel,
                office: office,
                officeAbbreviated: officeAbbreviated,
                cabinet: cabinet,
                component: component,
                status: status,
                priority: priority,
                assignedTo: assignedTo,
                authorName: authorName,
                department: department,
                currentNote: currentNote,
                requiredAction: requiredAction,
                cause: cause,
                faultDescription: faultDescription,
                workDone: workDone,
                techConclusion: techConclusion,
                soglasovanoLine: soglasovanoLine,
                isArchived: isArchived,
                isTask: isTask,
                hasFiles: hasFiles,
                hasComments: hasComments,
                firstReceivedDate: firstReceivedDate,
                lastUpdatedDate: lastUpdatedDate,
                completedAt: completedAt,
                completedBy: completedBy,
                lastStatus: lastStatus,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                lastSyncedAt: lastSyncedAt,
                conflictServerJson: conflictServerJson,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$TicketsTable, Ticket>(table),
                  BaseReferences<_$AppDatabase, $TicketsTable, Ticket>(
                    db,
                    table,
                    e,
                  ),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$TicketsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $TicketsTable,
      Ticket,
      $$TicketsTableFilterComposer,
      $$TicketsTableOrderingComposer,
      $$TicketsTableAnnotationComposer,
      $$TicketsTableCreateCompanionBuilder,
      $$TicketsTableUpdateCompanionBuilder,
      (Ticket, BaseReferences<_$AppDatabase, $TicketsTable, Ticket>),
      Ticket,
      PrefetchHooks Function()
    >;
typedef $$UserCommentsTableCreateCompanionBuilder =
    UserCommentsCompanion Function({
      required String localId,
      Value<int?> serverId,
      required String ticketNumber,
      Value<String?> authorUsername,
      Value<String?> authorName,
      required String commentText,
      Value<DateTime?> createdAt,
      required String accountUsername,
      Value<String> syncStatus,
      required DateTime localUpdatedAt,
      Value<int> rowid,
    });
typedef $$UserCommentsTableUpdateCompanionBuilder =
    UserCommentsCompanion Function({
      Value<String> localId,
      Value<int?> serverId,
      Value<String> ticketNumber,
      Value<String?> authorUsername,
      Value<String?> authorName,
      Value<String> commentText,
      Value<DateTime?> createdAt,
      Value<String> accountUsername,
      Value<String> syncStatus,
      Value<DateTime> localUpdatedAt,
      Value<int> rowid,
    });

class $$UserCommentsTableFilterComposer
    extends Composer<_$AppDatabase, $UserCommentsTable> {
  $$UserCommentsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get serverId => $composableBuilder(
    column: $table.serverId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get authorUsername => $composableBuilder(
    column: $table.authorUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get commentText => $composableBuilder(
    column: $table.commentText,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$UserCommentsTableOrderingComposer
    extends Composer<_$AppDatabase, $UserCommentsTable> {
  $$UserCommentsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get serverId => $composableBuilder(
    column: $table.serverId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get authorUsername => $composableBuilder(
    column: $table.authorUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get commentText => $composableBuilder(
    column: $table.commentText,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$UserCommentsTableAnnotationComposer
    extends Composer<_$AppDatabase, $UserCommentsTable> {
  $$UserCommentsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localId =>
      $composableBuilder(column: $table.localId, builder: (column) => column);

  GeneratedColumn<int> get serverId =>
      $composableBuilder(column: $table.serverId, builder: (column) => column);

  GeneratedColumn<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get authorUsername => $composableBuilder(
    column: $table.authorUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get authorName => $composableBuilder(
    column: $table.authorName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get commentText => $composableBuilder(
    column: $table.commentText,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => column,
  );
}

class $$UserCommentsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $UserCommentsTable,
          UserComment,
          $$UserCommentsTableFilterComposer,
          $$UserCommentsTableOrderingComposer,
          $$UserCommentsTableAnnotationComposer,
          $$UserCommentsTableCreateCompanionBuilder,
          $$UserCommentsTableUpdateCompanionBuilder,
          (
            UserComment,
            BaseReferences<_$AppDatabase, $UserCommentsTable, UserComment>,
          ),
          UserComment,
          PrefetchHooks Function()
        > {
  $$UserCommentsTableTableManager(_$AppDatabase db, $UserCommentsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$UserCommentsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$UserCommentsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$UserCommentsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> localId = const Value.absent(),
                Value<int?> serverId = const Value.absent(),
                Value<String> ticketNumber = const Value.absent(),
                Value<String?> authorUsername = const Value.absent(),
                Value<String?> authorName = const Value.absent(),
                Value<String> commentText = const Value.absent(),
                Value<DateTime?> createdAt = const Value.absent(),
                Value<String> accountUsername = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<DateTime> localUpdatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => UserCommentsCompanion(
                localId: localId,
                serverId: serverId,
                ticketNumber: ticketNumber,
                authorUsername: authorUsername,
                authorName: authorName,
                commentText: commentText,
                createdAt: createdAt,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String localId,
                Value<int?> serverId = const Value.absent(),
                required String ticketNumber,
                Value<String?> authorUsername = const Value.absent(),
                Value<String?> authorName = const Value.absent(),
                required String commentText,
                Value<DateTime?> createdAt = const Value.absent(),
                required String accountUsername,
                Value<String> syncStatus = const Value.absent(),
                required DateTime localUpdatedAt,
                Value<int> rowid = const Value.absent(),
              }) => UserCommentsCompanion.insert(
                localId: localId,
                serverId: serverId,
                ticketNumber: ticketNumber,
                authorUsername: authorUsername,
                authorName: authorName,
                commentText: commentText,
                createdAt: createdAt,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$UserCommentsTable, UserComment>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $UserCommentsTable,
                    UserComment
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$UserCommentsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $UserCommentsTable,
      UserComment,
      $$UserCommentsTableFilterComposer,
      $$UserCommentsTableOrderingComposer,
      $$UserCommentsTableAnnotationComposer,
      $$UserCommentsTableCreateCompanionBuilder,
      $$UserCommentsTableUpdateCompanionBuilder,
      (
        UserComment,
        BaseReferences<_$AppDatabase, $UserCommentsTable, UserComment>,
      ),
      UserComment,
      PrefetchHooks Function()
    >;
typedef $$TicketAttachmentsTableCreateCompanionBuilder =
    TicketAttachmentsCompanion Function({
      required String localId,
      Value<int?> serverId,
      required String ticketNumber,
      Value<String?> originalFilename,
      Value<String?> mimeType,
      Value<int?> fileSize,
      Value<String?> localFilePath,
      Value<String?> downloadUrl,
      Value<String?> thumbnailUrl,
      Value<bool> isDeleted,
      Value<DateTime?> uploadedAt,
      required String accountUsername,
      Value<String> syncStatus,
      required DateTime localUpdatedAt,
      Value<int> rowid,
    });
typedef $$TicketAttachmentsTableUpdateCompanionBuilder =
    TicketAttachmentsCompanion Function({
      Value<String> localId,
      Value<int?> serverId,
      Value<String> ticketNumber,
      Value<String?> originalFilename,
      Value<String?> mimeType,
      Value<int?> fileSize,
      Value<String?> localFilePath,
      Value<String?> downloadUrl,
      Value<String?> thumbnailUrl,
      Value<bool> isDeleted,
      Value<DateTime?> uploadedAt,
      Value<String> accountUsername,
      Value<String> syncStatus,
      Value<DateTime> localUpdatedAt,
      Value<int> rowid,
    });

class $$TicketAttachmentsTableFilterComposer
    extends Composer<_$AppDatabase, $TicketAttachmentsTable> {
  $$TicketAttachmentsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get serverId => $composableBuilder(
    column: $table.serverId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get originalFilename => $composableBuilder(
    column: $table.originalFilename,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get mimeType => $composableBuilder(
    column: $table.mimeType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get fileSize => $composableBuilder(
    column: $table.fileSize,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get localFilePath => $composableBuilder(
    column: $table.localFilePath,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get downloadUrl => $composableBuilder(
    column: $table.downloadUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get thumbnailUrl => $composableBuilder(
    column: $table.thumbnailUrl,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isDeleted => $composableBuilder(
    column: $table.isDeleted,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get uploadedAt => $composableBuilder(
    column: $table.uploadedAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$TicketAttachmentsTableOrderingComposer
    extends Composer<_$AppDatabase, $TicketAttachmentsTable> {
  $$TicketAttachmentsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get localId => $composableBuilder(
    column: $table.localId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get serverId => $composableBuilder(
    column: $table.serverId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get originalFilename => $composableBuilder(
    column: $table.originalFilename,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get mimeType => $composableBuilder(
    column: $table.mimeType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get fileSize => $composableBuilder(
    column: $table.fileSize,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get localFilePath => $composableBuilder(
    column: $table.localFilePath,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get downloadUrl => $composableBuilder(
    column: $table.downloadUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get thumbnailUrl => $composableBuilder(
    column: $table.thumbnailUrl,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isDeleted => $composableBuilder(
    column: $table.isDeleted,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get uploadedAt => $composableBuilder(
    column: $table.uploadedAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$TicketAttachmentsTableAnnotationComposer
    extends Composer<_$AppDatabase, $TicketAttachmentsTable> {
  $$TicketAttachmentsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get localId =>
      $composableBuilder(column: $table.localId, builder: (column) => column);

  GeneratedColumn<int> get serverId =>
      $composableBuilder(column: $table.serverId, builder: (column) => column);

  GeneratedColumn<String> get ticketNumber => $composableBuilder(
    column: $table.ticketNumber,
    builder: (column) => column,
  );

  GeneratedColumn<String> get originalFilename => $composableBuilder(
    column: $table.originalFilename,
    builder: (column) => column,
  );

  GeneratedColumn<String> get mimeType =>
      $composableBuilder(column: $table.mimeType, builder: (column) => column);

  GeneratedColumn<int> get fileSize =>
      $composableBuilder(column: $table.fileSize, builder: (column) => column);

  GeneratedColumn<String> get localFilePath => $composableBuilder(
    column: $table.localFilePath,
    builder: (column) => column,
  );

  GeneratedColumn<String> get downloadUrl => $composableBuilder(
    column: $table.downloadUrl,
    builder: (column) => column,
  );

  GeneratedColumn<String> get thumbnailUrl => $composableBuilder(
    column: $table.thumbnailUrl,
    builder: (column) => column,
  );

  GeneratedColumn<bool> get isDeleted =>
      $composableBuilder(column: $table.isDeleted, builder: (column) => column);

  GeneratedColumn<DateTime> get uploadedAt => $composableBuilder(
    column: $table.uploadedAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncStatus => $composableBuilder(
    column: $table.syncStatus,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get localUpdatedAt => $composableBuilder(
    column: $table.localUpdatedAt,
    builder: (column) => column,
  );
}

class $$TicketAttachmentsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $TicketAttachmentsTable,
          TicketAttachment,
          $$TicketAttachmentsTableFilterComposer,
          $$TicketAttachmentsTableOrderingComposer,
          $$TicketAttachmentsTableAnnotationComposer,
          $$TicketAttachmentsTableCreateCompanionBuilder,
          $$TicketAttachmentsTableUpdateCompanionBuilder,
          (
            TicketAttachment,
            BaseReferences<
              _$AppDatabase,
              $TicketAttachmentsTable,
              TicketAttachment
            >,
          ),
          TicketAttachment,
          PrefetchHooks Function()
        > {
  $$TicketAttachmentsTableTableManager(
    _$AppDatabase db,
    $TicketAttachmentsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$TicketAttachmentsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$TicketAttachmentsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$TicketAttachmentsTableAnnotationComposer(
                $db: db,
                $table: table,
              ),
          updateCompanionCallback:
              ({
                Value<String> localId = const Value.absent(),
                Value<int?> serverId = const Value.absent(),
                Value<String> ticketNumber = const Value.absent(),
                Value<String?> originalFilename = const Value.absent(),
                Value<String?> mimeType = const Value.absent(),
                Value<int?> fileSize = const Value.absent(),
                Value<String?> localFilePath = const Value.absent(),
                Value<String?> downloadUrl = const Value.absent(),
                Value<String?> thumbnailUrl = const Value.absent(),
                Value<bool> isDeleted = const Value.absent(),
                Value<DateTime?> uploadedAt = const Value.absent(),
                Value<String> accountUsername = const Value.absent(),
                Value<String> syncStatus = const Value.absent(),
                Value<DateTime> localUpdatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => TicketAttachmentsCompanion(
                localId: localId,
                serverId: serverId,
                ticketNumber: ticketNumber,
                originalFilename: originalFilename,
                mimeType: mimeType,
                fileSize: fileSize,
                localFilePath: localFilePath,
                downloadUrl: downloadUrl,
                thumbnailUrl: thumbnailUrl,
                isDeleted: isDeleted,
                uploadedAt: uploadedAt,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String localId,
                Value<int?> serverId = const Value.absent(),
                required String ticketNumber,
                Value<String?> originalFilename = const Value.absent(),
                Value<String?> mimeType = const Value.absent(),
                Value<int?> fileSize = const Value.absent(),
                Value<String?> localFilePath = const Value.absent(),
                Value<String?> downloadUrl = const Value.absent(),
                Value<String?> thumbnailUrl = const Value.absent(),
                Value<bool> isDeleted = const Value.absent(),
                Value<DateTime?> uploadedAt = const Value.absent(),
                required String accountUsername,
                Value<String> syncStatus = const Value.absent(),
                required DateTime localUpdatedAt,
                Value<int> rowid = const Value.absent(),
              }) => TicketAttachmentsCompanion.insert(
                localId: localId,
                serverId: serverId,
                ticketNumber: ticketNumber,
                originalFilename: originalFilename,
                mimeType: mimeType,
                fileSize: fileSize,
                localFilePath: localFilePath,
                downloadUrl: downloadUrl,
                thumbnailUrl: thumbnailUrl,
                isDeleted: isDeleted,
                uploadedAt: uploadedAt,
                accountUsername: accountUsername,
                syncStatus: syncStatus,
                localUpdatedAt: localUpdatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$TicketAttachmentsTable, TicketAttachment>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $TicketAttachmentsTable,
                    TicketAttachment
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$TicketAttachmentsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $TicketAttachmentsTable,
      TicketAttachment,
      $$TicketAttachmentsTableFilterComposer,
      $$TicketAttachmentsTableOrderingComposer,
      $$TicketAttachmentsTableAnnotationComposer,
      $$TicketAttachmentsTableCreateCompanionBuilder,
      $$TicketAttachmentsTableUpdateCompanionBuilder,
      (
        TicketAttachment,
        BaseReferences<
          _$AppDatabase,
          $TicketAttachmentsTable,
          TicketAttachment
        >,
      ),
      TicketAttachment,
      PrefetchHooks Function()
    >;
typedef $$SyncOutboxTableCreateCompanionBuilder =
    SyncOutboxCompanion Function({
      required String id,
      required String operationId,
      required String entityType,
      required String entityLocalId,
      Value<String?> entityServerId,
      required String operation,
      required String payloadJson,
      required DateTime createdAt,
      Value<int> retryCount,
      Value<DateTime?> nextRetryAt,
      Value<String?> lastError,
      Value<String> status,
      required String accountUsername,
      Value<String?> dependsOnOperationId,
      Value<int> rowid,
    });
typedef $$SyncOutboxTableUpdateCompanionBuilder =
    SyncOutboxCompanion Function({
      Value<String> id,
      Value<String> operationId,
      Value<String> entityType,
      Value<String> entityLocalId,
      Value<String?> entityServerId,
      Value<String> operation,
      Value<String> payloadJson,
      Value<DateTime> createdAt,
      Value<int> retryCount,
      Value<DateTime?> nextRetryAt,
      Value<String?> lastError,
      Value<String> status,
      Value<String> accountUsername,
      Value<String?> dependsOnOperationId,
      Value<int> rowid,
    });

class $$SyncOutboxTableFilterComposer
    extends Composer<_$AppDatabase, $SyncOutboxTable> {
  $$SyncOutboxTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get operationId => $composableBuilder(
    column: $table.operationId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityLocalId => $composableBuilder(
    column: $table.entityLocalId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get entityServerId => $composableBuilder(
    column: $table.entityServerId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get nextRetryAt => $composableBuilder(
    column: $table.nextRetryAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get dependsOnOperationId => $composableBuilder(
    column: $table.dependsOnOperationId,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncOutboxTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncOutboxTable> {
  $$SyncOutboxTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get operationId => $composableBuilder(
    column: $table.operationId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityLocalId => $composableBuilder(
    column: $table.entityLocalId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get entityServerId => $composableBuilder(
    column: $table.entityServerId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get operation => $composableBuilder(
    column: $table.operation,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get nextRetryAt => $composableBuilder(
    column: $table.nextRetryAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get status => $composableBuilder(
    column: $table.status,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get dependsOnOperationId => $composableBuilder(
    column: $table.dependsOnOperationId,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncOutboxTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncOutboxTable> {
  $$SyncOutboxTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get operationId => $composableBuilder(
    column: $table.operationId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityType => $composableBuilder(
    column: $table.entityType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityLocalId => $composableBuilder(
    column: $table.entityLocalId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get entityServerId => $composableBuilder(
    column: $table.entityServerId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get operation =>
      $composableBuilder(column: $table.operation, builder: (column) => column);

  GeneratedColumn<String> get payloadJson => $composableBuilder(
    column: $table.payloadJson,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<int> get retryCount => $composableBuilder(
    column: $table.retryCount,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get nextRetryAt => $composableBuilder(
    column: $table.nextRetryAt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);

  GeneratedColumn<String> get status =>
      $composableBuilder(column: $table.status, builder: (column) => column);

  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get dependsOnOperationId => $composableBuilder(
    column: $table.dependsOnOperationId,
    builder: (column) => column,
  );
}

class $$SyncOutboxTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncOutboxTable,
          SyncOutboxData,
          $$SyncOutboxTableFilterComposer,
          $$SyncOutboxTableOrderingComposer,
          $$SyncOutboxTableAnnotationComposer,
          $$SyncOutboxTableCreateCompanionBuilder,
          $$SyncOutboxTableUpdateCompanionBuilder,
          (
            SyncOutboxData,
            BaseReferences<_$AppDatabase, $SyncOutboxTable, SyncOutboxData>,
          ),
          SyncOutboxData,
          PrefetchHooks Function()
        > {
  $$SyncOutboxTableTableManager(_$AppDatabase db, $SyncOutboxTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncOutboxTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncOutboxTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncOutboxTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> operationId = const Value.absent(),
                Value<String> entityType = const Value.absent(),
                Value<String> entityLocalId = const Value.absent(),
                Value<String?> entityServerId = const Value.absent(),
                Value<String> operation = const Value.absent(),
                Value<String> payloadJson = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<int> retryCount = const Value.absent(),
                Value<DateTime?> nextRetryAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<String> status = const Value.absent(),
                Value<String> accountUsername = const Value.absent(),
                Value<String?> dependsOnOperationId = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncOutboxCompanion(
                id: id,
                operationId: operationId,
                entityType: entityType,
                entityLocalId: entityLocalId,
                entityServerId: entityServerId,
                operation: operation,
                payloadJson: payloadJson,
                createdAt: createdAt,
                retryCount: retryCount,
                nextRetryAt: nextRetryAt,
                lastError: lastError,
                status: status,
                accountUsername: accountUsername,
                dependsOnOperationId: dependsOnOperationId,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String operationId,
                required String entityType,
                required String entityLocalId,
                Value<String?> entityServerId = const Value.absent(),
                required String operation,
                required String payloadJson,
                required DateTime createdAt,
                Value<int> retryCount = const Value.absent(),
                Value<DateTime?> nextRetryAt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<String> status = const Value.absent(),
                required String accountUsername,
                Value<String?> dependsOnOperationId = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncOutboxCompanion.insert(
                id: id,
                operationId: operationId,
                entityType: entityType,
                entityLocalId: entityLocalId,
                entityServerId: entityServerId,
                operation: operation,
                payloadJson: payloadJson,
                createdAt: createdAt,
                retryCount: retryCount,
                nextRetryAt: nextRetryAt,
                lastError: lastError,
                status: status,
                accountUsername: accountUsername,
                dependsOnOperationId: dependsOnOperationId,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncOutboxTable, SyncOutboxData>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $SyncOutboxTable,
                    SyncOutboxData
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncOutboxTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncOutboxTable,
      SyncOutboxData,
      $$SyncOutboxTableFilterComposer,
      $$SyncOutboxTableOrderingComposer,
      $$SyncOutboxTableAnnotationComposer,
      $$SyncOutboxTableCreateCompanionBuilder,
      $$SyncOutboxTableUpdateCompanionBuilder,
      (
        SyncOutboxData,
        BaseReferences<_$AppDatabase, $SyncOutboxTable, SyncOutboxData>,
      ),
      SyncOutboxData,
      PrefetchHooks Function()
    >;
typedef $$SyncMetadataTableCreateCompanionBuilder =
    SyncMetadataCompanion Function({
      required String accountUsername,
      Value<String?> syncCursor,
      Value<DateTime?> lastSuccessfulSync,
      Value<DateTime?> lastSyncAttempt,
      Value<String?> lastError,
      Value<int> pendingOperationsCount,
      Value<int> conflictsCount,
      Value<int> rowid,
    });
typedef $$SyncMetadataTableUpdateCompanionBuilder =
    SyncMetadataCompanion Function({
      Value<String> accountUsername,
      Value<String?> syncCursor,
      Value<DateTime?> lastSuccessfulSync,
      Value<DateTime?> lastSyncAttempt,
      Value<String?> lastError,
      Value<int> pendingOperationsCount,
      Value<int> conflictsCount,
      Value<int> rowid,
    });

class $$SyncMetadataTableFilterComposer
    extends Composer<_$AppDatabase, $SyncMetadataTable> {
  $$SyncMetadataTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get syncCursor => $composableBuilder(
    column: $table.syncCursor,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastSuccessfulSync => $composableBuilder(
    column: $table.lastSuccessfulSync,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get lastSyncAttempt => $composableBuilder(
    column: $table.lastSyncAttempt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get pendingOperationsCount => $composableBuilder(
    column: $table.pendingOperationsCount,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get conflictsCount => $composableBuilder(
    column: $table.conflictsCount,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SyncMetadataTableOrderingComposer
    extends Composer<_$AppDatabase, $SyncMetadataTable> {
  $$SyncMetadataTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get syncCursor => $composableBuilder(
    column: $table.syncCursor,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastSuccessfulSync => $composableBuilder(
    column: $table.lastSuccessfulSync,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get lastSyncAttempt => $composableBuilder(
    column: $table.lastSyncAttempt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get pendingOperationsCount => $composableBuilder(
    column: $table.pendingOperationsCount,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get conflictsCount => $composableBuilder(
    column: $table.conflictsCount,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SyncMetadataTableAnnotationComposer
    extends Composer<_$AppDatabase, $SyncMetadataTable> {
  $$SyncMetadataTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get syncCursor => $composableBuilder(
    column: $table.syncCursor,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get lastSuccessfulSync => $composableBuilder(
    column: $table.lastSuccessfulSync,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get lastSyncAttempt => $composableBuilder(
    column: $table.lastSyncAttempt,
    builder: (column) => column,
  );

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);

  GeneratedColumn<int> get pendingOperationsCount => $composableBuilder(
    column: $table.pendingOperationsCount,
    builder: (column) => column,
  );

  GeneratedColumn<int> get conflictsCount => $composableBuilder(
    column: $table.conflictsCount,
    builder: (column) => column,
  );
}

class $$SyncMetadataTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SyncMetadataTable,
          SyncMetadataData,
          $$SyncMetadataTableFilterComposer,
          $$SyncMetadataTableOrderingComposer,
          $$SyncMetadataTableAnnotationComposer,
          $$SyncMetadataTableCreateCompanionBuilder,
          $$SyncMetadataTableUpdateCompanionBuilder,
          (
            SyncMetadataData,
            BaseReferences<_$AppDatabase, $SyncMetadataTable, SyncMetadataData>,
          ),
          SyncMetadataData,
          PrefetchHooks Function()
        > {
  $$SyncMetadataTableTableManager(_$AppDatabase db, $SyncMetadataTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SyncMetadataTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SyncMetadataTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SyncMetadataTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> accountUsername = const Value.absent(),
                Value<String?> syncCursor = const Value.absent(),
                Value<DateTime?> lastSuccessfulSync = const Value.absent(),
                Value<DateTime?> lastSyncAttempt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<int> pendingOperationsCount = const Value.absent(),
                Value<int> conflictsCount = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncMetadataCompanion(
                accountUsername: accountUsername,
                syncCursor: syncCursor,
                lastSuccessfulSync: lastSuccessfulSync,
                lastSyncAttempt: lastSyncAttempt,
                lastError: lastError,
                pendingOperationsCount: pendingOperationsCount,
                conflictsCount: conflictsCount,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String accountUsername,
                Value<String?> syncCursor = const Value.absent(),
                Value<DateTime?> lastSuccessfulSync = const Value.absent(),
                Value<DateTime?> lastSyncAttempt = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<int> pendingOperationsCount = const Value.absent(),
                Value<int> conflictsCount = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SyncMetadataCompanion.insert(
                accountUsername: accountUsername,
                syncCursor: syncCursor,
                lastSuccessfulSync: lastSuccessfulSync,
                lastSyncAttempt: lastSyncAttempt,
                lastError: lastError,
                pendingOperationsCount: pendingOperationsCount,
                conflictsCount: conflictsCount,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$SyncMetadataTable, SyncMetadataData>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $SyncMetadataTable,
                    SyncMetadataData
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SyncMetadataTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SyncMetadataTable,
      SyncMetadataData,
      $$SyncMetadataTableFilterComposer,
      $$SyncMetadataTableOrderingComposer,
      $$SyncMetadataTableAnnotationComposer,
      $$SyncMetadataTableCreateCompanionBuilder,
      $$SyncMetadataTableUpdateCompanionBuilder,
      (
        SyncMetadataData,
        BaseReferences<_$AppDatabase, $SyncMetadataTable, SyncMetadataData>,
      ),
      SyncMetadataData,
      PrefetchHooks Function()
    >;
typedef $$LocalPermissionsTableCreateCompanionBuilder =
    LocalPermissionsCompanion Function({
      required String accountUsername,
      required String code,
      Value<int> rowid,
    });
typedef $$LocalPermissionsTableUpdateCompanionBuilder =
    LocalPermissionsCompanion Function({
      Value<String> accountUsername,
      Value<String> code,
      Value<int> rowid,
    });

class $$LocalPermissionsTableFilterComposer
    extends Composer<_$AppDatabase, $LocalPermissionsTable> {
  $$LocalPermissionsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get code => $composableBuilder(
    column: $table.code,
    builder: (column) => ColumnFilters(column),
  );
}

class $$LocalPermissionsTableOrderingComposer
    extends Composer<_$AppDatabase, $LocalPermissionsTable> {
  $$LocalPermissionsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get code => $composableBuilder(
    column: $table.code,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$LocalPermissionsTableAnnotationComposer
    extends Composer<_$AppDatabase, $LocalPermissionsTable> {
  $$LocalPermissionsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get accountUsername => $composableBuilder(
    column: $table.accountUsername,
    builder: (column) => column,
  );

  GeneratedColumn<String> get code =>
      $composableBuilder(column: $table.code, builder: (column) => column);
}

class $$LocalPermissionsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $LocalPermissionsTable,
          LocalPermission,
          $$LocalPermissionsTableFilterComposer,
          $$LocalPermissionsTableOrderingComposer,
          $$LocalPermissionsTableAnnotationComposer,
          $$LocalPermissionsTableCreateCompanionBuilder,
          $$LocalPermissionsTableUpdateCompanionBuilder,
          (
            LocalPermission,
            BaseReferences<
              _$AppDatabase,
              $LocalPermissionsTable,
              LocalPermission
            >,
          ),
          LocalPermission,
          PrefetchHooks Function()
        > {
  $$LocalPermissionsTableTableManager(
    _$AppDatabase db,
    $LocalPermissionsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$LocalPermissionsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$LocalPermissionsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$LocalPermissionsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> accountUsername = const Value.absent(),
                Value<String> code = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => LocalPermissionsCompanion(
                accountUsername: accountUsername,
                code: code,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String accountUsername,
                required String code,
                Value<int> rowid = const Value.absent(),
              }) => LocalPermissionsCompanion.insert(
                accountUsername: accountUsername,
                code: code,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map(
                (e) => (
                  e.readTable<$LocalPermissionsTable, LocalPermission>(table),
                  BaseReferences<
                    _$AppDatabase,
                    $LocalPermissionsTable,
                    LocalPermission
                  >(db, table, e),
                ),
              )
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$LocalPermissionsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $LocalPermissionsTable,
      LocalPermission,
      $$LocalPermissionsTableFilterComposer,
      $$LocalPermissionsTableOrderingComposer,
      $$LocalPermissionsTableAnnotationComposer,
      $$LocalPermissionsTableCreateCompanionBuilder,
      $$LocalPermissionsTableUpdateCompanionBuilder,
      (
        LocalPermission,
        BaseReferences<_$AppDatabase, $LocalPermissionsTable, LocalPermission>,
      ),
      LocalPermission,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$TicketsTableTableManager get tickets =>
      $$TicketsTableTableManager(_db, _db.tickets);
  $$UserCommentsTableTableManager get userComments =>
      $$UserCommentsTableTableManager(_db, _db.userComments);
  $$TicketAttachmentsTableTableManager get ticketAttachments =>
      $$TicketAttachmentsTableTableManager(_db, _db.ticketAttachments);
  $$SyncOutboxTableTableManager get syncOutbox =>
      $$SyncOutboxTableTableManager(_db, _db.syncOutbox);
  $$SyncMetadataTableTableManager get syncMetadata =>
      $$SyncMetadataTableTableManager(_db, _db.syncMetadata);
  $$LocalPermissionsTableTableManager get localPermissions =>
      $$LocalPermissionsTableTableManager(_db, _db.localPermissions);
}
