import 'package:dio/dio.dart';
import 'package:logger/logger.dart';

import '../constants/api_constants.dart';

/// Dio HTTP client configuration and setup
class ApiClient {
  static final Logger _logger = Logger();

  /// Create configured Dio instance
  static Dio createDio() {
    final dio = Dio(BaseOptions(
      baseUrl: ApiConstants.baseUrl,
      connectTimeout: const Duration(milliseconds: ApiConstants.connectTimeout),
      receiveTimeout: const Duration(milliseconds: ApiConstants.receiveTimeout),
      sendTimeout: const Duration(milliseconds: ApiConstants.sendTimeout),
      headers: ApiConstants.defaultHeaders,
    ));

    // Add logging interceptor in debug mode
    dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (obj) => _logger.d(obj),
    ));

    // Add error handling interceptor
    dio.interceptors.add(ErrorInterceptor());

    // Add retry interceptor for failed requests
    dio.interceptors.add(RetryInterceptor(
      dio: dio,
      retries: 3,
      retryDelays: const [
        Duration(seconds: 1),
        Duration(seconds: 2),
        Duration(seconds: 3),
      ],
    ));

    return dio;
  }
}

/// Error handling interceptor
class ErrorInterceptor extends Interceptor {
  static final Logger _logger = Logger();

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    _logger.e('API Error: ${err.message}', error: err);

    // Transform DioException to custom exception
    final customError = _transformError(err);
    handler.next(customError);
  }

  DioException _transformError(DioException error) {
    String message;

    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        message = 'Connection timeout. Please check your internet connection.';
        break;
      case DioExceptionType.connectionError:
        message = 'Connection error. Please check your internet connection.';
        break;
      case DioExceptionType.badResponse:
        message = _getErrorMessage(error.response?.statusCode);
        break;
      case DioExceptionType.cancel:
        message = 'Request was cancelled.';
        break;
      default:
        message = 'An unexpected error occurred.';
    }

    return DioException(
      requestOptions: error.requestOptions,
      error: message,
      type: error.type,
      response: error.response,
    );
  }

  String _getErrorMessage(int? statusCode) {
    switch (statusCode) {
      case 400:
        return 'Bad request. Please check your input.';
      case 401:
        return 'Unauthorized. Please check your credentials.';
      case 403:
        return 'Forbidden. You don\'t have permission to access this resource.';
      case 404:
        return 'Resource not found.';
      case 429:
        return 'Too many requests. Please try again later.';
      case 500:
        return 'Internal server error. Please try again later.';
      case 502:
        return 'Bad gateway. Please try again later.';
      case 503:
        return 'Service unavailable. Please try again later.';
      default:
        return 'An error occurred. Please try again.';
    }
  }
}

/// Retry interceptor for handling transient failures
class RetryInterceptor extends Interceptor {
  final Dio dio;
  final int retries;
  final List<Duration> retryDelays;

  RetryInterceptor({
    required this.dio,
    required this.retries,
    required this.retryDelays,
  });

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final extra = err.requestOptions.extra;
    final retryCount = extra['retry_count'] ?? 0;

    if (retryCount < retries && _shouldRetry(err)) {
      // Add delay before retry
      if (retryCount < retryDelays.length) {
        await Future.delayed(retryDelays[retryCount]);
      }

      // Update retry count
      err.requestOptions.extra['retry_count'] = retryCount + 1;

      try {
        // Retry the request
        final response = await dio.fetch(err.requestOptions);
        handler.resolve(response);
        return;
      } catch (e) {
        // If retry fails, continue with original error
      }
    }

    handler.next(err);
  }

  bool _shouldRetry(DioException error) {
    // Retry on network errors and 5xx server errors
    return error.type == DioExceptionType.connectionTimeout ||
        error.type == DioExceptionType.connectionError ||
        error.type == DioExceptionType.receiveTimeout ||
        (error.response?.statusCode != null &&
            error.response!.statusCode! >= 500);
  }
}