import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/providers.dart';
import '../../../../core/errors/failures.dart';
import '../../data/admin_repository.dart';

class RebuildScreen extends ConsumerStatefulWidget {
  const RebuildScreen({super.key, this.sinceDate});

  final String? sinceDate;

  @override
  ConsumerState<RebuildScreen> createState() => _RebuildScreenState();
}

class _RebuildScreenState extends ConsumerState<RebuildScreen> {
  RebuildStatus? _status;
  String? _error;
  bool _started = false;
  Timer? _timer;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) => _start());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _start() async {
    try {
      await ref
          .read(adminRepositoryProvider)
          .startRebuild(sinceDate: widget.sinceDate);
      setState(() => _started = true);
      _poll();
      _timer = Timer.periodic(const Duration(seconds: 2), (_) => _poll());
    } catch (e) {
      setState(() {
        _error = e is AppFailure ? e.message : e.toString();
      });
    }
  }

  Future<void> _poll() async {
    try {
      final status = await ref.read(adminRepositoryProvider).rebuildStatus();
      if (!mounted) return;
      setState(() => _status = status);
      if (!status.running &&
          (status.status == 'done' ||
              status.status == 'error' ||
              status.status == 'idle')) {
        _timer?.cancel();
      }
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e is AppFailure ? e.message : e.toString();
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final status = _status;
    return Scaffold(
      appBar: AppBar(title: const Text('Обновление данных')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (widget.sinceDate != null)
              Text(
                'С даты: ${widget.sinceDate}',
                style: Theme.of(context).textTheme.bodyMedium,
              ),
            const SizedBox(height: 16),
            if (_error != null)
              Text(
                _error!,
                style: TextStyle(color: Theme.of(context).colorScheme.error),
              )
            else if (!_started)
              const Center(child: CircularProgressIndicator())
            else ...[
              LinearProgressIndicator(
                value: status?.running == true ? status!.progress : 1,
              ),
              const SizedBox(height: 16),
              Text(
                status?.message ?? 'Ожидание…',
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 8),
              Text(
                'Обработано: ${status?.processed ?? 0} / ${status?.total ?? 0}'
                '${(status?.errors ?? 0) > 0 ? ' · ошибок: ${status!.errors}' : ''}',
              ),
              const SizedBox(height: 8),
              Text('Статус: ${status?.status ?? '—'}'),
            ],
            const Spacer(),
            if (status != null && !status.running)
              FilledButton(
                onPressed: () => Navigator.of(context).pop(),
                child: const Text('Готово'),
              ),
          ],
        ),
      ),
    );
  }
}
