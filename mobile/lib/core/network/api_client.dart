import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:uuid/uuid.dart';

import '../../app/config/app_config.dart';
import '../errors/failures.dart';
import '../security/secure_credentials_store.dart';

typedef OnUnauthorized = Future<void> Function();

class ApiClient {
  ApiClient({
    required AppConfig config,
    required SecureCredentialsStore credentials,
    OnUnauthorized? onUnauthorized,
  }) : _credentials = credentials,
       _onUnauthorized = onUnauthorized {
    final baseOptions = BaseOptions(
      baseUrl: config.apiBaseUrl,
      connectTimeout: const Duration(seconds: 20),
      receiveTimeout: const Duration(seconds: 60),
      sendTimeout: const Duration(seconds: 120),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    );
    _dio = Dio(baseOptions);
    // Отдельный клиент без очереди: повтор и refresh из onError
    // не должны ждать тот же QueuedInterceptor.
    _plain = Dio(baseOptions);

    // QueuedInterceptorsWrapper обязателен для async onRequest —
    // иначе Authorization может не успеть попасть в заголовок.
    _dio.interceptors.add(
      QueuedInterceptorsWrapper(
        onRequest: (options, handler) async {
          options.headers['X-Request-Id'] = const Uuid().v4();
          try {
            final token = await _credentials.readToken();
            if (token != null && token.isNotEmpty) {
              options.headers['Authorization'] = 'Bearer $token';
            } else {
              options.headers.remove('Authorization');
            }
          } catch (_) {
            // Не блокируем запрос из‑за сбоя storage
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          if (error.response?.statusCode != 401 || _skipAuthRecovery(error)) {
            handler.next(error);
            return;
          }

          error.requestOptions.extra['auth_retried'] = true;
          final header =
              error.requestOptions.headers['Authorization']?.toString() ?? '';
          final missingToken =
              !header.startsWith('Bearer ') || header.trim() == 'Bearer';

          if (missingToken) {
            final token = await _credentials.readToken();
            if (token != null && token.isNotEmpty) {
              try {
                final response = await _sendWithToken(
                  error.requestOptions,
                  token,
                );
                handler.resolve(response);
                return;
              } on DioException catch (retryError) {
                if (retryError.response?.statusCode != 401) {
                  handler.next(retryError);
                  return;
                }
              }
            }
          }

          final refreshed = await _refreshAccessToken();
          if (refreshed != null) {
            try {
              final response = await _sendWithToken(
                error.requestOptions,
                refreshed,
              );
              handler.resolve(response);
              return;
            } on DioException catch (retryError) {
              handler.next(retryError);
              await _notifyUnauthorized();
              return;
            }
          }

          await _notifyUnauthorized();
          handler.next(error);
        },
      ),
    );

    if (kDebugMode && !config.isProduction) {
      _dio.interceptors.add(
        LogInterceptor(
          requestBody: false,
          responseBody: false,
          requestHeader: false,
          responseHeader: false,
          logPrint: (obj) {
            final text = obj.toString();
            if (text.toLowerCase().contains('authorization') ||
                text.toLowerCase().contains('password') ||
                text.toLowerCase().contains('token')) {
              return;
            }
            // ignore: avoid_print
            print(text);
          },
        ),
      );
    }
  }

  late final Dio _dio;
  late final Dio _plain;
  final SecureCredentialsStore _credentials;
  final OnUnauthorized? _onUnauthorized;

  bool _skipAuthRecovery(DioException error) {
    final extra = error.requestOptions.extra;
    if (extra['auth_retried'] == true || extra['skip_auth_recovery'] == true) {
      return true;
    }
    final path = error.requestOptions.uri.path;
    return path.endsWith('/api/auth/login') ||
        path.endsWith('/api/auth/login-new') ||
        path.endsWith('/api/auth/refresh');
  }

  Future<Response<dynamic>> _sendWithToken(
    RequestOptions request,
    String token,
  ) {
    request.headers['Authorization'] = 'Bearer $token';
    return _plain.fetch(request);
  }

  Future<String?> _refreshAccessToken() async {
    final current = await _credentials.readToken();
    if (current == null || current.isEmpty) return null;
    try {
      final response = await _plain.post<dynamic>(
        '/api/auth/refresh',
        options: Options(
          headers: {'Authorization': 'Bearer $current'},
        ),
      );
      final data = response.data;
      if (data is Map && data['token'] is String) {
        final token = data['token'] as String;
        if (token.isEmpty) return null;
        await _credentials.updateToken(
          token: token,
          expiresAt: DateTime.now().toUtc().add(const Duration(hours: 24)),
        );
        return token;
      }
    } on DioException {
      return null;
    }
    return null;
  }

  Future<void> _notifyUnauthorized() async {
    final cb = _onUnauthorized;
    if (cb == null) return;
    try {
      await cb();
    } catch (_) {}
  }

  Dio get raw => _dio;

  Future<Map<String, dynamic>> authHeaders([
    Map<String, dynamic>? extra,
  ]) async {
    final headers = <String, dynamic>{...?extra};
    final token = await _credentials.readToken();
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<Response<T>> get<T>(
    String path, {
    Map<String, dynamic>? queryParameters,
    Options? options,
  }) {
    return _guard(
      () =>
          _dio.get<T>(path, queryParameters: queryParameters, options: options),
    );
  }

  /// Скачивание бинарного файла (изображения, дампы и т.п.).
  Future<List<int>> getBytes(String path) async {
    final response = await _guard(
      () => _dio.get<List<int>>(
        path,
        options: Options(
          responseType: ResponseType.bytes,
          headers: {
            Headers.acceptHeader: '*/*',
            Headers.contentTypeHeader: null,
          },
        ),
      ),
    );
    final data = response.data;
    if (data == null) {
      throw const ServerFailure('Пустой ответ при скачивании файла');
    }
    return data;
  }

  Future<Response<T>> put<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? headers,
    Options? options,
  }) {
    final opts = (options ?? Options()).copyWith(
      headers: {...?options?.headers, ...?headers},
    );
    return _guard(() => _dio.put<T>(path, data: data, options: opts));
  }

  Future<Response<T>> post<T>(
    String path, {
    Object? data,
    Map<String, dynamic>? headers,
    Options? options,
  }) {
    final mergedHeaders = <String, dynamic>{...?options?.headers, ...?headers};
    // FormData сам выставляет multipart + boundary — не оставляем application/json.
    if (data is FormData) {
      mergedHeaders.remove(Headers.contentTypeHeader);
      mergedHeaders.remove('Content-Type');
    }
    final opts = (options ?? Options()).copyWith(
      headers: mergedHeaders,
      contentType: data is FormData ? null : options?.contentType,
    );
    return _guard(() => _dio.post<T>(path, data: data, options: opts));
  }

  Future<Response<T>> delete<T>(
    String path, {
    Map<String, dynamic>? headers,
    Options? options,
  }) {
    final opts = (options ?? Options()).copyWith(
      headers: {...?options?.headers, ...?headers},
    );
    return _guard(() => _dio.delete<T>(path, options: opts));
  }

  Future<Response<T>> _guard<T>(Future<Response<T>> Function() run) async {
    try {
      return await run();
    } on DioException catch (e) {
      throw mapDioException(e);
    }
  }

  static AppFailure mapDioException(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;
    String? serverMessage;
    if (data is Map) {
      serverMessage = (data['message'] ?? data['error'])?.toString();
    }

    if (e.type == DioExceptionType.connectionError ||
        e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout) {
      return NetworkFailure(serverMessage ?? 'Нет связи с сервером');
    }

    switch (status) {
      case 401:
        return AuthenticationFailure(serverMessage ?? 'Требуется авторизация');
      case 403:
        return AuthorizationFailure(serverMessage ?? 'Недостаточно прав');
      case 404:
        return ValidationFailure(serverMessage ?? 'Не найдено');
      case 409:
        Map<String, dynamic>? payload;
        if (data is Map<String, dynamic>) payload = data;
        return ConflictFailure(payload, serverMessage ?? 'Конфликт изменений');
      case 422:
      case 400:
        return ValidationFailure(serverMessage ?? 'Некорректные данные');
      case 429:
        return ServerFailure(serverMessage ?? 'Слишком много запросов');
      default:
        if (status != null && status >= 500) {
          return ServerFailure(serverMessage ?? 'Ошибка сервера');
        }
        return UnknownFailure(serverMessage ?? 'Неизвестная ошибка сети');
    }
  }
}
