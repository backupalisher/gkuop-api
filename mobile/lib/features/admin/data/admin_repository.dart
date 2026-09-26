import 'dart:io';
import 'dart:typed_data';

import 'package:dio/dio.dart';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';

import '../../../core/network/api_client.dart';

class AdminUserSummary {
  const AdminUserSummary({
    required this.username,
    required this.role,
    this.fullName,
    this.email,
    required this.isActive,
  });

  final String username;
  final String role;
  final String? fullName;
  final String? email;
  final bool isActive;

  factory AdminUserSummary.fromJson(Map<String, dynamic> json) {
    return AdminUserSummary(
      username: json['username']?.toString() ?? '',
      role: json['role']?.toString() ?? 'operator',
      fullName: json['full_name'] as String?,
      email: json['email'] as String?,
      isActive: json['is_active'] != false,
    );
  }
}

class RebuildStatus {
  const RebuildStatus({
    required this.running,
    required this.status,
    this.message,
    this.total = 0,
    this.processed = 0,
    this.errors = 0,
    this.skipped = 0,
    this.sinceDate,
  });

  final bool running;
  final String status;
  final String? message;
  final int total;
  final int processed;
  final int errors;
  final int skipped;
  final String? sinceDate;

  factory RebuildStatus.fromJson(Map<String, dynamic> json) {
    return RebuildStatus(
      running: json['running'] == true,
      status: json['status']?.toString() ?? 'idle',
      message: json['message']?.toString(),
      total: (json['total'] as num?)?.toInt() ?? 0,
      processed: (json['processed'] as num?)?.toInt() ?? 0,
      errors: (json['errors'] as num?)?.toInt() ?? 0,
      skipped: (json['skipped'] as num?)?.toInt() ?? 0,
      sinceDate: json['since_date']?.toString(),
    );
  }

  double get progress {
    if (total <= 0) return running ? 0.05 : 0;
    return (processed / total).clamp(0.0, 1.0);
  }
}

class AdminRepository {
  AdminRepository({required ApiClient api}) : _api = api;

  final ApiClient _api;

  Future<List<AdminUserSummary>> listUsers() async {
    final response = await _api.get('/api/auth/users');
    final body = response.data as Map<String, dynamic>;
    final users = (body['users'] as List?) ?? [];
    return users
        .whereType<Map>()
        .map((e) => AdminUserSummary.fromJson(Map<String, dynamic>.from(e)))
        .toList();
  }

  Future<void> startRebuild({String? sinceDate}) async {
    final headers = await _api.authHeaders();
    await _api.post(
      '/api/rebuild/start',
      data: {
        if (sinceDate != null && sinceDate.isNotEmpty) 'since_date': sinceDate,
      },
      headers: headers,
    );
  }

  Future<RebuildStatus> rebuildStatus() async {
    final headers = await _api.authHeaders();
    final response = await _api.get(
      '/api/rebuild/status',
      options: Options(headers: headers),
    );
    return RebuildStatus.fromJson(
      Map<String, dynamic>.from(response.data as Map),
    );
  }

  Future<File> exportDatabaseDump() async {
    final response = await _api.get(
      '/api/admin/db/export',
      options: Options(responseType: ResponseType.bytes),
    );
    final bytes = response.data;
    if (bytes is! List<int> && bytes is! Uint8List) {
      throw StateError('Пустой ответ при выгрузке БД');
    }
    final data = bytes is Uint8List ? bytes : Uint8List.fromList(bytes as List<int>);
    final dir = await getTemporaryDirectory();
    final disposition = response.headers.value('content-disposition');
    var filename = 'gkuop_backup.dump';
    if (disposition != null) {
      final match = RegExp(r'filename="?([^"]+)"?').firstMatch(disposition);
      if (match != null) filename = match.group(1)!;
    }
    final file = File(p.join(dir.path, filename));
    await file.writeAsBytes(data, flush: true);
    return file;
  }

  Future<void> importDatabaseDump(String filePath) async {
    final form = FormData.fromMap({
      'file': await MultipartFile.fromFile(
        filePath,
        filename: p.basename(filePath),
      ),
    });
    await _api.post(
      '/api/admin/db/import',
      data: form,
      options: Options(
        sendTimeout: const Duration(minutes: 10),
        receiveTimeout: const Duration(minutes: 10),
      ),
    );
  }
}
