import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gkuop_mobile/shared/widgets/soglasovano_block.dart';

void main() {
  testWidgets('не показывает слово СОГЛАСОВАНО', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: SoglasovanoBlock(
            value: '27 - Ролик отделения ADF в сборе - СОГЛАСОВАНО',
          ),
        ),
      ),
    );

    expect(find.textContaining('СОГЛАСОВАНО'), findsNothing);
    expect(find.textContaining('Ролик отделения ADF в сборе'), findsOneWidget);
    expect(find.textContaining('27'), findsOneWidget);
  });

  test('stripSoglasovanoWord убирает статус и разделитель', () {
    expect(
      stripSoglasovanoWord('27 - Ролик - СОГЛАСОВАНО'),
      '27 - Ролик',
    );
  });
}
