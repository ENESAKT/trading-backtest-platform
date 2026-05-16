import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiClient {
  ApiClient({
    Dio? dio,
    FlutterSecureStorage? storage,
    String? baseUrl,
  })  : _storage = storage ?? const FlutterSecureStorage(),
        _dio = dio ??
            Dio(BaseOptions(
              baseUrl: baseUrl ??
                  const String.fromEnvironment(
                    'API_BASE_URL',
                    defaultValue: 'http://10.0.2.2:8000',
                  ),
              connectTimeout: const Duration(seconds: 10),
              receiveTimeout: const Duration(seconds: 20),
            )) {
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'access_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
    ));
  }

  final Dio _dio;
  final FlutterSecureStorage _storage;

  Future<Map<String, dynamic>> mobileLogin({
    required String email,
    required String password,
    String? totpCode,
  }) async {
    final response = await _dio.post<Map<String, dynamic>>(
      '/api/auth/mobile/login',
      data: {
        'email': email,
        'password': password,
        if (totpCode != null) 'totp_code': totpCode,
        'device_name': 'Flutter Mobile',
      },
    );
    final data = (response.data?['data'] ?? {}) as Map<String, dynamic>;
    await _storage.write(key: 'access_token', value: data['access_token'] as String?);
    await _storage.write(key: 'refresh_token', value: data['refresh_token'] as String?);
    return data;
  }

  Future<Response<dynamic>> get(String path, {Map<String, dynamic>? query}) {
    return _dio.get(path, queryParameters: query);
  }
}
