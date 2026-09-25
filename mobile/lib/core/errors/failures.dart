sealed class AppFailure implements Exception {
  const AppFailure(this.message);
  final String message;

  @override
  String toString() => message;
}

class NetworkFailure extends AppFailure {
  const NetworkFailure([super.message = 'Нет связи с сервером']);
}

class AuthenticationFailure extends AppFailure {
  const AuthenticationFailure([super.message = 'Требуется авторизация']);
}

class AuthorizationFailure extends AppFailure {
  const AuthorizationFailure([super.message = 'Недостаточно прав']);
}

class ValidationFailure extends AppFailure {
  const ValidationFailure([super.message = 'Некорректные данные']);
}

class ConflictFailure extends AppFailure {
  const ConflictFailure(
    this.serverPayload, [
    super.message = 'Конфликт изменений',
  ]);
  final Map<String, dynamic>? serverPayload;
}

class ServerFailure extends AppFailure {
  const ServerFailure([super.message = 'Ошибка сервера']);
}

class StorageFailure extends AppFailure {
  const StorageFailure([super.message = 'Ошибка локального хранилища']);
}

class UnknownFailure extends AppFailure {
  const UnknownFailure([super.message = 'Неизвестная ошибка']);
}
