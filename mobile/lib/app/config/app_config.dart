/// Конфигурация окружения через --dart-define.
class AppConfig {
  const AppConfig({required this.apiBaseUrl, required this.environment});

  final String apiBaseUrl;
  final String environment;

  bool get isProduction => environment == 'production';
  bool get isDevelopment => environment == 'development';

  static AppConfig fromEnvironment() {
    const base = String.fromEnvironment(
      'API_BASE_URL',
      defaultValue: 'https://gkuop.part4.info',
    );
    const env = String.fromEnvironment(
      'ENVIRONMENT',
      defaultValue: 'development',
    );
    return AppConfig(
      apiBaseUrl: base.endsWith('/')
          ? base.substring(0, base.length - 1)
          : base,
      environment: env,
    );
  }
}
