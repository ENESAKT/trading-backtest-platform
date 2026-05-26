/// Auth Token Deposu
///
/// JWT token'ı cihazda (SharedPreferences) kalıcı saklar.
/// AuthStore tüm giriş/çıkış token işlemlerinin tek noktasıdır.
library;

import 'package:shared_preferences/shared_preferences.dart';

class AuthStore {
  static const _keyToken    = 'auth_token';
  static const _keyBaseUrl  = 'api_base_url';

  /// Token'ı kaydet.
  static Future<void> saveToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyToken, token);
  }

  /// Kayıtlı token'ı getir. Yoksa null döner.
  static Future<String?> loadToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyToken);
  }

  /// Token'ı sil (çıkış).
  static Future<void> clearToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_keyToken);
  }

  /// Giriş yapılmış mı?
  static Future<bool> isLoggedIn() async {
    final t = await loadToken();
    return t != null && t.isNotEmpty;
  }

  /// Base URL kaydet (ortam değiştirme için).
  static Future<void> saveBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_keyBaseUrl, url);
  }

  /// Base URL getir.
  static Future<String> loadBaseUrl({String defaultUrl = 'https://piyasapilot.com'}) async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_keyBaseUrl) ?? defaultUrl;
  }
}
