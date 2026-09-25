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
    _dio = Dio(
      BaseOptions(
        baseUrl: config.apiBaseUrl,
        connectTimeout: const Duration(seconds: 20),
        receiveTimeout: const Duration(seconds: 60),
        sendTimeout: const Duration(seconds: 120),
        headers: {
          'Accept': 'application/json',
          'Content-Type': 'application/json',
        },
      ),
    );

    _dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) async {
          options.headers['X-Request-Id'] = const Uuid().v4();
          final token = await _credentials.readToken();
          if (token != null && token.isNotEmpty) {
            options.headers['Authorization'] = 'Bearer $token';
          }
          handler.next(options);
        },
        onError: (error, handler) async {
          final status = error.response?.statusCode;
          if (status == 401 && _onUnauthorized != null) {
            await _onUnauthorized();
          }
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
  final SecureCredentialsStore _credentials;
  final OnUnauthorized? _onUnauthorized;

  Dio get raw => _dio;

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
    final opts = (options ?? Options()).copyWith(
      headers: {...?options?.headers, ...?headers},
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
