import 'package:flutter_test/flutter_test.dart';
import 'package:gkuop_mobile/core/errors/failures.dart';
import 'package:gkuop_mobile/core/network/api_client.dart';
import 'package:dio/dio.dart';

void main() {
  group('ApiClient.mapDioException', () {
    test('maps timeout to NetworkFailure', () {
      final failure = ApiClient.mapDioException(
        DioException(
          requestOptions: RequestOptions(path: '/'),
          type: DioExceptionType.connectionTimeout,
        ),
      );
      expect(failure, isA<NetworkFailure>());
    });

    test('maps 401 to AuthenticationFailure', () {
      final failure = ApiClient.mapDioException(
        DioException(
          requestOptions: RequestOptions(path: '/'),
          response: Response(
            requestOptions: RequestOptions(path: '/'),
            statusCode: 401,
          ),
          type: DioExceptionType.badResponse,
        ),
      );
      expect(failure, isA<AuthenticationFailure>());
    });

    test('maps 409 to ConflictFailure', () {
      final failure = ApiClient.mapDioException(
        DioException(
          requestOptions: RequestOptions(path: '/'),
          response: Response(
            requestOptions: RequestOptions(path: '/'),
            statusCode: 409,
            data: {'code': 'VERSION_CONFLICT'},
          ),
          type: DioExceptionType.badResponse,
        ),
      );
      expect(failure, isA<ConflictFailure>());
    });
  });
}
