import 'package:flutter/material.dart';

/// Pill для комплектующего — как `.component-pill` в веб-CSS.
class ComponentPill extends StatelessWidget {
  const ComponentPill({super.key, required this.text});

  final String text;

  @override
  Widget build(BuildContext context) {
    return Container(
      constraints: const BoxConstraints(maxWidth: 260),
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF2EC),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: const Color(0x38E95420)),
      ),
      child: Text(
        text,
        textAlign: TextAlign.right,
        style: const TextStyle(
          color: Color(0xFFB34CB3),
          fontSize: 12,
          fontWeight: FontWeight.w600,
          height: 1.25,
        ),
      ),
    );
  }
}
