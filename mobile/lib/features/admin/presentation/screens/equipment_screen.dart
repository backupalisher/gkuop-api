import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../../core/di/providers.dart';
import '../../../../core/errors/failures.dart';
import '../../data/admin_repository.dart';

class EquipmentScreen extends ConsumerStatefulWidget {
  const EquipmentScreen({super.key});

  @override
  ConsumerState<EquipmentScreen> createState() => _EquipmentScreenState();
}

class _EquipmentScreenState extends ConsumerState<EquipmentScreen> {
  final _searchCtrl = TextEditingController();
  List<EquipmentItem> _items = const [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final items = await ref.read(adminRepositoryProvider).listEquipment(
            search: _searchCtrl.text.trim(),
          );
      if (!mounted) return;
      setState(() {
        _items = items;
        _loading = false;
      });
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _error = error.toString();
        _loading = false;
      });
    }
  }

  Future<void> _openForm([EquipmentItem? item]) async {
    final saved = await showDialog<bool>(
      context: context,
      builder: (context) => _EquipmentDialog(item: item),
    );
    if (saved == true) {
      await _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Аппараты')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _openForm(),
        icon: const Icon(Icons.add),
        label: const Text('Добавить'),
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 8),
            child: TextField(
              controller: _searchCtrl,
              decoration: const InputDecoration(
                hintText: 'Модель, серийный или инвентарный номер',
                prefixIcon: Icon(Icons.search),
              ),
              onSubmitted: (_) => _load(),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _error != null
                    ? Center(child: Text(_error!))
                    : _items.isEmpty
                    ? const Center(child: Text('Аппараты не найдены'))
                    : RefreshIndicator(
                        onRefresh: _load,
                        child: ListView.separated(
                          padding: const EdgeInsets.fromLTRB(12, 0, 12, 88),
                          itemCount: _items.length,
                          separatorBuilder: (_, __) => const Divider(height: 1),
                          itemBuilder: (context, index) {
                            final item = _items[index];
                            return ListTile(
                              title: Text(item.label),
                              subtitle: Text(item.model),
                              onTap: () => _openForm(item),
                            );
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }
}

class _EquipmentDialog extends ConsumerStatefulWidget {
  const _EquipmentDialog({this.item});

  final EquipmentItem? item;

  @override
  ConsumerState<_EquipmentDialog> createState() => _EquipmentDialogState();
}

class _EquipmentDialogState extends ConsumerState<_EquipmentDialog> {
  late final TextEditingController _model;
  late final TextEditingController _serial;
  late final TextEditingController _inventory;
  bool _saving = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _model = TextEditingController(text: widget.item?.model ?? '');
    _serial = TextEditingController(text: widget.item?.serialNumber ?? '');
    _inventory = TextEditingController(text: widget.item?.inventoryNumber ?? '');
  }

  @override
  void dispose() {
    _model.dispose();
    _serial.dispose();
    _inventory.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    setState(() {
      _saving = true;
      _error = null;
    });
    try {
      await ref.read(adminRepositoryProvider).saveEquipment(
            id: widget.item?.id,
            model: _model.text.trim(),
            serialNumber: _serial.text.trim(),
            inventoryNumber: _inventory.text.trim(),
          );
      if (mounted) Navigator.of(context).pop(true);
    } on AppFailure catch (error) {
      setState(() {
        _error = error.message;
        _saving = false;
      });
    } catch (error) {
      setState(() {
        _error = error.toString();
        _saving = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final editing = widget.item != null;
    return AlertDialog(
      title: Text(editing ? 'Изменить аппарат' : 'Новый аппарат'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: _model,
              decoration: const InputDecoration(labelText: 'Модель'),
            ),
            TextField(
              controller: _serial,
              decoration: const InputDecoration(labelText: 'Серийный номер'),
            ),
            TextField(
              controller: _inventory,
              decoration: const InputDecoration(
                labelText: 'Инвентарный номер',
                helperText: 'Необязательно, от 4 цифр',
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(top: 8),
                child: Text(
                  _error!,
                  style: TextStyle(color: Theme.of(context).colorScheme.error),
                ),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: _saving ? null : () => Navigator.of(context).pop(false),
          child: const Text('Отмена'),
        ),
        FilledButton(
          onPressed: _saving ? null : _save,
          child: Text(editing ? 'Сохранить' : 'Добавить'),
        ),
      ],
    );
  }
}
