import 'package:flutter/material.dart';

import '../../app/theme/app_colors.dart';

class StatusBadge extends StatelessWidget {
  const StatusBadge({super.key, required this.status});

  final String? status;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final colors = _colorsFor(status, isDark);
    final text = (status == null || status!.trim().isEmpty) ? '—' : status!;
    final isCompleted = colors.isCompleted;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
      decoration: BoxDecoration(
        color: colors.bg,
        borderRadius: BorderRadius.circular(999),
      ),
      child: Text(
        isCompleted ? '✓ $text' : text,
        style: TextStyle(
          color: colors.fg,
          fontSize: 12,
          fontWeight: FontWeight.w500,
          height: 1.4,
        ),
      ),
    );
  }

  static _StatusColors _colorsFor(String? status, bool isDark) {
    if (status == null || status.trim().isEmpty) {
      return isDark
          ? const _StatusColors(
              AppColors.statusDefaultBgDark,
              AppColors.statusDefaultTextDark,
            )
          : const _StatusColors(
              AppColors.statusDefaultBg,
              AppColors.statusDefaultText,
            );
    }
    final s = status.toLowerCase();
    if (s.contains('отклон') || s.contains('закрыт')) {
      return isDark
          ? const _StatusColors(
              AppColors.statusRejectedBgDark,
              AppColors.statusRejectedTextDark,
            )
          : const _StatusColors(
              AppColors.statusRejectedBg,
              AppColors.statusRejectedText,
            );
    }
    if (s.contains('комплектующ')) {
      return isDark
          ? const _StatusColors(
              AppColors.statusPartsBgDark,
              AppColors.statusPartsTextDark,
            )
          : const _StatusColors(
              AppColors.statusPartsBg,
              AppColors.statusPartsText,
            );
    }
    if (s.contains('выполн')) {
      return isDark
          ? const _StatusColors(
              AppColors.statusCompletedBgDark,
              AppColors.statusCompletedTextDark,
              isCompleted: true,
            )
          : const _StatusColors(
              AppColors.statusCompletedBg,
              AppColors.statusCompletedText,
              isCompleted: true,
            );
    }
    if (s.contains('соглас') || s.contains('решен')) {
      return isDark
          ? const _StatusColors(
              AppColors.statusApprovedBgDark,
              AppColors.statusApprovedTextDark,
            )
          : const _StatusColors(
              AppColors.statusApprovedBg,
              AppColors.statusApprovedText,
            );
    }
    if (s.contains('работ') || s.contains('готов')) {
      if (s.contains('готов')) {
        return isDark
            ? const _StatusColors(
                AppColors.statusReadyBgDark,
                AppColors.statusReadyTextDark,
              )
            : const _StatusColors(
                AppColors.statusReadyBg,
                AppColors.statusReadyText,
              );
      }
      return isDark
          ? const _StatusColors(
              AppColors.statusWorkBgDark,
              AppColors.statusWorkTextDark,
            )
          : const _StatusColors(
              AppColors.statusWorkBg,
              AppColors.statusWorkText,
            );
    }
    if (s.contains('нов') || s.contains('созд')) {
      return isDark
          ? const _StatusColors(
              AppColors.statusNewBgDark,
              AppColors.statusNewTextDark,
            )
          : const _StatusColors(
              AppColors.statusNewBg,
              AppColors.statusNewText,
            );
    }
    return isDark
        ? const _StatusColors(
            AppColors.statusDefaultBgDark,
            AppColors.statusDefaultTextDark,
          )
        : const _StatusColors(
            AppColors.statusDefaultBg,
            AppColors.statusDefaultText,
          );
  }
}

class _StatusColors {
  const _StatusColors(this.bg, this.fg, {this.isCompleted = false});

  final Color bg;
  final Color fg;
  final bool isCompleted;
}
