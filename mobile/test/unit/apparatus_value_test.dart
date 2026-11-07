import 'package:flutter_test/flutter_test.dart';
import 'package:gkuop_mobile/shared/widgets/apparatus_value.dart';

void main() {
  test('предпочитает equipment_label над моделью со слэшем', () {
    final parts = resolveApparatusFields(
      equipmentLabel: 'Lexmark MX310dn - 701544LM0GNMV7 - 110134003682',
      printerModel: 'Lexmark MX310dn/MX410dn',
      serialNumber: '701544LM0GNMV7',
      inventoryNumber: '110134003682',
    );
    expect(parts.model, 'Lexmark MX310dn');
    expect(parts.serial, '701544LM0GNMV7');
    expect(parts.inventory, '110134003682');
  });

  test('не дублирует серийный из printer_model и поля serial', () {
    final parts = resolveApparatusFields(
      printerModel: 'Xerox WorkCenter 3325 - 3220058807 - 110134000717',
      serialNumber: '3220058807',
      inventoryNumber: '110134000717',
    );
    expect(parts.model, 'Xerox WorkCenter 3325');
    expect(parts.serial, '3220058807');
    expect(parts.inventory, '110134000717');
  });

  test('не показывает серийный дважды, если он совпадает с инвентарным', () {
    final parts = resolveApparatusFields(
      printerModel: 'Xerox WorkCenter 3325',
      serialNumber: '3220058807',
      inventoryNumber: '3220058807',
    );
    expect(parts.model, 'Xerox WorkCenter 3325');
    // Один идентификатор — как inventory (длинный числовой) или serial, не оба.
    final shown = [parts.serial, parts.inventory].whereType<String>().toList();
    expect(shown.length, 1);
    expect(shown.single, '3220058807');
  });

  test('обрезает ModelA/ModelB без label', () {
    final parts = resolveApparatusFields(
      printerModel: 'Lexmark MX310dn/MX410dn',
      serialNumber: '701544LM0GNMV7',
      inventoryNumber: '110134003682',
    );
    expect(parts.model, 'Lexmark MX310dn');
    expect(parts.serial, '701544LM0GNMV7');
    expect(parts.inventory, '110134003682');
  });
}
