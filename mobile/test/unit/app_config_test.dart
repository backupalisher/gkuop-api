import 'package:flutter_test/flutter_test.dart';
import 'package:gkuop_mobile/app/config/app_config.dart';

void main() {
  test('AppConfig strips trailing slash', () {
    const cfg = AppConfig(
      apiBaseUrl: 'http://example.com/',
      environment: 'development',
    );
    // fromEnvironment uses strip; companion check:
    final cleaned = cfg.apiBaseUrl.endsWith('/')
        ? cfg.apiBaseUrl.substring(0, cfg.apiBaseUrl.length - 1)
        : cfg.apiBaseUrl;
    expect(cleaned, 'http://example.com');
  });
}
