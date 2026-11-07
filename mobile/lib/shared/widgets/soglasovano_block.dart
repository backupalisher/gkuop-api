import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';

class SoglasovanoRow {
  const SoglasovanoRow({
    required this.number,
    required this.title,
    required this.status,
  });

  final String number;
  final String title;
  final String status;
}

List<SoglasovanoRow> parseSoglasovanieRows(String? value) {
  if (value == null || value.trim().isEmpty) return const [];
  final text = value
      .replaceAll(RegExp(r'<\s*br\s*/?\s*>', caseSensitive: false), '\n')
      .replaceAll(RegExp(r'</\s*(div|p|li|tr)\s*>', caseSensitive: false), '\n')
      .replaceAll('\u00a0', ' ')
      .replaceAll('\r\n', '\n')
      .replaceAll('\r', '\n');

  final linePattern = RegExp(
    r'^(\d+)\s*(?:[-–—]|\s+)\s*(.*?)\s*(?:[-–—=])\s*(СОГЛАСОВАНО.*)$',
    caseSensitive: false,
  );
  final fromLines = <SoglasovanoRow>[];
  for (final raw in text.split('\n')) {
    final line = raw.trim();
    if (line.isEmpty) continue;
    final statusMatches = RegExp(
      'СОГЛАСОВАНО',
      caseSensitive: false,
    ).allMatches(line);
    if (statusMatches.length != 1) continue;
    final match = linePattern.firstMatch(line);
    if (match == null) continue;
    fromLines.add(
      SoglasovanoRow(
        number: match.group(1)!,
        title: match.group(2)!.replaceAll(RegExp(r'\s+'), ' ').trim(),
        status: match.group(3)!.trim(),
      ),
    );
  }
  if (fromLines.isNotEmpty) return fromLines;

  final structured = RegExp(
    r'(?<!\d)(\d+)\s*(?:[-–—]|\s{2,})\s*(.*?)\s*(?:[-–—=])\s*(СОГЛАСОВАНО)',
    caseSensitive: false,
  ).allMatches(text);
  if (structured.isNotEmpty) {
    return structured
        .map(
          (m) => SoglasovanoRow(
            number: m.group(1)!,
            title: m.group(2)!.replaceAll(RegExp(r'\s+'), ' ').trim(),
            status: m.group(3)!.trim(),
          ),
        )
        .where((r) => r.title.isNotEmpty)
        .toList();
  }

  return text
      .split('\n')
      .map((l) => l.trim())
      .where((l) => l.isNotEmpty)
      .map((line) {
        final match = linePattern.firstMatch(line);
        if (match == null) {
          return SoglasovanoRow(number: '', title: line, status: '');
        }
        return SoglasovanoRow(
          number: match.group(1)!,
          title: match.group(2)!.trim(),
          status: match.group(3)!.trim(),
        );
      })
      .toList();
}

/// Убирает слово «СОГЛАСОВАНО» и хвостовые разделители из текста согласования.
String stripSoglasovanoWord(String value) {
  return value
      .replaceAll(
        RegExp(
          r'\s*[-–—=]?\s*СОГЛАСОВАНО(?=$|[\s,.;:!?\n])',
          caseSensitive: false,
        ),
        '',
      )
      .replaceAll(
        RegExp(r'СОГЛАСОВАНО', caseSensitive: false),
        '',
      )
      .replaceAll(RegExp(r'[ \t]+'), ' ')
      .replaceAll(RegExp(r' *\n *'), '\n')
      .replaceAll(RegExp(r'\s*[-–—=]\s*$'), '')
      .trim();
}

/// Блок согласованных деталей (как таблица «Согласование» на вебе).
class SoglasovanoBlock extends StatelessWidget {
  const SoglasovanoBlock({super.key, required this.value, this.compact = false});

  final String value;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final rows = parseSoglasovanieRows(value);
    if (rows.isEmpty) {
      return Text(
        stripSoglasovanoWord(value),
        textAlign: compact ? TextAlign.right : TextAlign.left,
        style: const TextStyle(fontSize: 13),
      );
    }

    final hasStructured =
        rows.any((r) => r.number.isNotEmpty || r.title.isNotEmpty);
    if (!hasStructured) {
      return Text(
        stripSoglasovanoWord(value),
        textAlign: compact ? TextAlign.right : TextAlign.left,
        style: const TextStyle(fontSize: 13),
      );
    }

    return Column(
      crossAxisAlignment:
          compact ? CrossAxisAlignment.end : CrossAxisAlignment.stretch,
      children: [
        for (final row in rows)
          Padding(
            padding: const EdgeInsets.only(bottom: 4),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
              decoration: BoxDecoration(
                color: AppColors.primaryBg,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                // «СОГЛАСОВАНО» не показываем — только номер и название.
                [
                  if (row.number.isNotEmpty) row.number,
                  row.title,
                ].where((s) => s.trim().isNotEmpty).join('  '),
                textAlign: compact ? TextAlign.right : TextAlign.left,
                style: const TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: AppColors.primary,
                ),
              ),
            ),
          ),
      ],
    );
  }
}
