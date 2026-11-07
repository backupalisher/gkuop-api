import 'package:flutter/material.dart';

import '../../core/database/app_database.dart';

/// Разобранные поля аппарата для единого отображения в списке и карточке.
class ApparatusParts {
  const ApparatusParts({
    this.model,
    this.serial,
    this.inventory,
  });

  final String? model;
  final String? serial;
  final String? inventory;

  bool get isEmpty =>
      (model == null || model!.isEmpty) &&
      (serial == null || serial!.isEmpty) &&
      (inventory == null || inventory!.isEmpty);
}

final _emptyInventory = {'', '-', '—', '*'};

String? _clean(String? value) {
  final v = value?.trim();
  if (v == null || v.isEmpty) return null;
  return v;
}

String? _cleanInventory(String? value) {
  final v = _clean(value);
  if (v == null) return null;
  if (_emptyInventory.contains(v)) return null;
  return v;
}

String _digits(String value) => value.replaceAll(RegExp(r'\D'), '');

bool _sameIdentifier(String? a, String? b) {
  if (a == null || b == null) return false;
  final left = a.trim();
  final right = b.trim();
  if (left.isEmpty || right.isEmpty) return false;
  if (left.toUpperCase() == right.toUpperCase()) return true;
  final ld = _digits(left);
  final rd = _digits(right);
  if (ld.isNotEmpty && rd.isNotEmpty && ld == rd) return true;
  return false;
}

/// Убирает варианты «ModelA/ModelB», если это похоже на альтернативы модели.
String? _normalizeModel(String? model) {
  final v = _clean(model);
  if (v == null) return null;
  if (!v.contains('/')) return v;
  // «Lexmark MX310dn/MX410dn» → берём первый вариант до «/»
  // (полный корректный label приходит из equipment_label).
  final first = v.split('/').first.trim();
  return first.isEmpty ? v : first;
}

List<String> _splitEquipmentLabel(String label) {
  return label
      .split(RegExp(r'\s[-–—]\s'))
      .map((p) => p.trim())
      .where((p) => p.isNotEmpty)
      .toList();
}

void _applyLabelParts(
  List<String> parts, {
  required void Function(String) setModel,
  required String? Function() getSerial,
  required void Function(String?) setSerial,
  required String? Function() getInventory,
  required void Function(String?) setInventory,
}) {
  if (parts.length >= 2) {
    setModel(parts[0]);
    final labelSerial = parts[1];
    final labelInv = parts.length >= 3 ? _cleanInventory(parts[2]) : null;
    final serial = getSerial();
    final inventory = getInventory();
    if (serial == null || serial.isEmpty) {
      setSerial(labelSerial);
    } else if (_sameIdentifier(serial, labelSerial)) {
      setSerial(labelSerial);
    }
    if (inventory == null || inventory.isEmpty) {
      if (labelInv != null) setInventory(labelInv);
    } else if (labelInv != null && _sameIdentifier(inventory, labelInv)) {
      setInventory(labelInv);
    }
  } else if (parts.length == 1) {
    setModel(parts[0]);
  }
}

/// Источник истины: `equipment_label` (модель - серийный - инв.), затем поля заявки.
/// Дедупликация серийного/инвентарного, чтобы не показывать дважды.
ApparatusParts resolveApparatus(Ticket ticket) {
  String? model;
  String? serial = _clean(ticket.serialNumber);
  String? inventory = _cleanInventory(ticket.inventoryNumber);

  final label = _clean(ticket.equipmentLabel);
  if (label != null) {
    // Предпочитаем модель из справочной подписи, а не сырой printer_model
    // вида «MX310dn/MX410dn».
    final parts = _splitEquipmentLabel(label);
    _applyLabelParts(
      parts,
      setModel: (m) => model = m,
      getSerial: () => serial,
      setSerial: (s) => serial = s,
      getInventory: () => inventory,
      setInventory: (i) => inventory = i,
    );
  }

  if (model == null || model!.isEmpty) {
    final rawModel = _clean(ticket.printerModel);
    if (rawModel != null) {
      final parts = _splitEquipmentLabel(rawModel);
      // «Model - serial - inv» целиком в printer_model — разбираем, иначе дубли.
      if (parts.length >= 2) {
        _applyLabelParts(
          parts,
          setModel: (m) => model = m,
          getSerial: () => serial,
          setSerial: (s) => serial = s,
          getInventory: () => inventory,
          setInventory: (i) => inventory = i,
        );
      } else {
        model = _normalizeModel(rawModel);
      }
    }
  } else {
    // Модель уже из label — сырой printer_model со слэшем игнорируем.
  }

  // Серийный не должен повторять модель и наоборот.
  if (_sameIdentifier(model, serial)) {
    serial = null;
  }
  if (_sameIdentifier(model, inventory)) {
    inventory = null;
  }

  // Если серийный продублирован в инвентарном (или наоборот) — один раз.
  if (_sameIdentifier(serial, inventory)) {
    final digits = _digits(serial ?? inventory ?? '');
    // Инвентарные обычно длинные числовые; серийные часто с буквами.
    final serialHasLetters = RegExp(
      r'[A-Za-zА-Яа-яЁё]',
    ).hasMatch(serial ?? '');
    if (serialHasLetters) {
      inventory = null;
    } else if (digits.length >= 10) {
      // Похоже на инвентарный — показываем как inventory с bold-хвостом.
      inventory = serial ?? inventory;
      serial = null;
    } else {
      inventory = null;
    }
  }

  // serial дважды в одной строке «A - A»
  final serialValue = serial;
  if (serialValue != null && serialValue.contains(RegExp(r'\s[-–—]\s'))) {
    final bits = _splitEquipmentLabel(serialValue);
    if (bits.length >= 2 && _sameIdentifier(bits[0], bits[1])) {
      serial = bits[0];
    }
  }

  return ApparatusParts(model: model, serial: serial, inventory: inventory);
}

/// Разбор без Drift-модели — для тестов и вызовов с сырыми полями.
ApparatusParts resolveApparatusFields({
  String? equipmentLabel,
  String? printerModel,
  String? serialNumber,
  String? inventoryNumber,
}) {
  return resolveApparatus(
    Ticket(
      localId: 'test',
      ticketNumber: '0',
      status: '',
      isArchived: false,
      isTask: false,
      hasFiles: false,
      hasComments: false,
      accountUsername: 'test',
      syncStatus: 'synced',
      localUpdatedAt: DateTime.fromMillisecondsSinceEpoch(0),
      equipmentLabel: equipmentLabel,
      printerModel: printerModel,
      serialNumber: serialNumber,
      inventoryNumber: inventoryNumber,
    ),
  );
}

/// Виджет строки «Аппарат»:
/// модель;
/// серийный — приглушённый;
/// инвентарный — обычный, последние 5 цифр жирные.
class ApparatusValue extends StatelessWidget {
  const ApparatusValue({
    super.key,
    required this.ticket,
    this.alignEnd = true,
  });

  final Ticket ticket;
  final bool alignEnd;

  @override
  Widget build(BuildContext context) {
    final parts = resolveApparatus(ticket);
    if (parts.isEmpty) return const SizedBox.shrink();

    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    final cross = alignEnd ? CrossAxisAlignment.end : CrossAxisAlignment.start;
    final align = alignEnd ? TextAlign.right : TextAlign.left;

    return Column(
      crossAxisAlignment: cross,
      children: [
        if (parts.model != null && parts.model!.isNotEmpty)
          Text(
            parts.model!,
            textAlign: align,
            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w500),
          ),
        if (parts.serial != null && parts.serial!.isNotEmpty)
          Text(
            parts.serial!,
            textAlign: align,
            style: TextStyle(fontSize: 13, color: muted),
          ),
        if (parts.inventory != null && parts.inventory!.isNotEmpty)
          _InventoryText(value: parts.inventory!, textAlign: align),
      ],
    );
  }
}

class _InventoryText extends StatelessWidget {
  const _InventoryText({required this.value, required this.textAlign});

  final String value;
  final TextAlign textAlign;

  @override
  Widget build(BuildContext context) {
    final onSurface = Theme.of(context).colorScheme.onSurface;
    // Жирными — последние 5 символов строки (обычно цифры инвентарного).
    if (value.length <= 5) {
      return Text(
        value,
        textAlign: textAlign,
        style: TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.w700,
          color: onSurface,
        ),
      );
    }
    final head = value.substring(0, value.length - 5);
    final tail = value.substring(value.length - 5);
    return Text.rich(
      TextSpan(
        children: [
          TextSpan(
            text: head,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w400,
              color: onSurface,
            ),
          ),
          TextSpan(
            text: tail,
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w700,
              color: onSurface,
            ),
          ),
        ],
      ),
      textAlign: textAlign,
    );
  }
}
