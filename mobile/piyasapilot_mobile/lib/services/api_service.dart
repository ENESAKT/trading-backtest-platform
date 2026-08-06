/// PiyasaPilot API Servisi
///
/// Backend REST API ile iletişim kurar.
/// Tüm isteklere Bearer token ekler; hata durumlarını standart ApiException'a çevirir.
library;

import 'dart:async';
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/models.dart';
import 'auth_store.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  const ApiException(this.statusCode, this.message);
  @override
  String toString() => 'ApiException($statusCode): $message';
}

class ApiService {
  final String baseUrl;
  final String? authToken;
  final http.Client _client;
  static const _timeout = Duration(seconds: 30);

  ApiService({
    required this.baseUrl,
    this.authToken,
    http.Client? client,
  }) : _client = client ?? http.Client();

  Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        if (authToken != null) 'Authorization': 'Bearer $authToken',
      };

  Uri _uri(String path, [Map<String, String>? params]) {
    final uri = Uri.parse('$baseUrl$path');
    return params != null ? uri.replace(queryParameters: params) : uri;
  }

  Future<dynamic> _get(String path, [Map<String, String>? params]) async {
    final res = await _client.get(_uri(path, params), headers: _headers).timeout(_timeout);
    return _parse(res);
  }

  Future<dynamic> _post(String path, Map<String, dynamic> body) async {
    final res = await _client.post(
      _uri(path),
      headers: _headers,
      body: jsonEncode(body),
    ).timeout(_timeout);
    return _parse(res);
  }

  Future<dynamic> _delete(String path) async {
    final res = await _client.delete(_uri(path), headers: _headers).timeout(_timeout);
    return _parse(res);
  }

  dynamic _parse(http.Response res) {
    if (res.statusCode >= 200 && res.statusCode < 300) {
      if (res.body.isEmpty) return null;
      final decoded = jsonDecode(res.body);
      if (decoded is Map<String, dynamic> && decoded.containsKey('ok')) {
        return decoded['data'];
      }
      return decoded;
    }
    String msg = 'HTTP ${res.statusCode}';
    try {
      final j = jsonDecode(res.body) as Map<String, dynamic>;
      final detail = j['detail'];
      if (detail is Map) {
        msg = (detail['tr'] ?? detail['en'] ?? msg) as String;
      } else if (detail is String) {
        msg = detail;
      }
    } catch (_) {}
    throw ApiException(res.statusCode, msg);
  }

  // ─── Auth ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final data = await _post('/api/auth/mobile/login', {
      'email': email,
      'password': password,
    });
    return data as Map<String, dynamic>;
  }

  Future<String?> refreshToken() async {
    final refresh = await AuthStore.loadRefreshToken();
    if (refresh == null) return null;
    try {
      final data = await _post('/api/auth/mobile/refresh', {'refresh_token': refresh}) as Map<String, dynamic>;
      final newToken = data['access_token'] as String?;
      if (newToken != null) await AuthStore.saveToken(newToken);
      return newToken;
    } catch (_) {
      return null;
    }
  }

  Future<Map<String, dynamic>> getMe() async {
    final data = await _get('/api/auth/me');
    return data as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> getLimits() async {
    final data = await _get('/api/auth/me/limits');
    return data as Map<String, dynamic>;
  }

  // ─── Semboller ───────────────────────────────────────────────────────────

  Future<List<SymbolSnapshot>> getWatchlist() async {
    final data = await _get('/api/watchlist');
    final list = data as List<dynamic>;
    return list.map((e) => SymbolSnapshot.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<SymbolSnapshot> getSymbolSnapshot(String symbol, String market) async {
    final data = await _get('/api/symbols/$symbol/snapshot', {'market': market});
    return SymbolSnapshot.fromJson(data as Map<String, dynamic>);
  }

  // ─── Teknik Analiz ────────────────────────────────────────────────────────

  Future<TechnicalSummary> getTechnicalSummary({
    required String symbol,
    required String market,
    String timeframe = '1d',
  }) async {
    final data = await _get('/api/technical/summary', {
      'symbol': symbol,
      'market': market,
      'timeframe': timeframe,
    });
    return TechnicalSummary.fromJson(data as Map<String, dynamic>);
  }

  // ─── Screener ─────────────────────────────────────────────────────────────

  Future<ScreenerRunResponse> runScreener(ScreenerRunRequest req) async {
    final data = await _post('/api/screener/run', req.toJson());
    return ScreenerRunResponse.fromJson(data as Map<String, dynamic>);
  }

  // ─── Sinyaller ────────────────────────────────────────────────────────────

  Future<List<SignalEvidence>> getSignals({
    String? symbol,
    String? market,
    int limit = 20,
  }) async {
    final params = <String, String>{'limit': '$limit'};
    if (symbol != null) params['symbol'] = symbol;
    if (market != null) params['market'] = market;
    final data = await _get('/api/signals', params);
    final list = data as List<dynamic>;
    return list.map((e) => SignalEvidence.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ─── Paper Trading ────────────────────────────────────────────────────────

  Future<PaperPortfolioSummary> getPaperPortfolio(String strategyId) async {
    final data = await _get('/api/paper/portfolio/$strategyId');
    return PaperPortfolioSummary.fromJson(data as Map<String, dynamic>);
  }

  Future<List<PaperOrder>> getPaperOrders(String strategyId, {int limit = 50}) async {
    final data = await _get(
      '/api/paper/orders/$strategyId',
      {'limit': '$limit'},
    );
    final list = data as List<dynamic>;
    return list.map((e) => PaperOrder.fromJson(e as Map<String, dynamic>)).toList();
  }

  // ─── Watchlist CRUD ───────────────────────────────────────────────────────

  Future<void> addToWatchlist(String symbol, String market) async {
    await _post('/api/watchlist/add', {'symbol': symbol, 'market': market});
  }

  Future<void> removeFromWatchlist(String symbol) async {
    await _delete('/api/watchlist/$symbol');
  }

  // ─── Fiyat Alarmları ──────────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getAlerts() async {
    final data = await _get('/api/alerts/price');
    final map  = data as Map<String, dynamic>;
    final list = (map['alerts'] as List<dynamic>?) ?? [];
    return list.cast<Map<String, dynamic>>();
  }

  Future<Map<String, dynamic>> createAlert({
    required String symbol,
    required double target,
    required String direction,
    String note = '',
  }) async {
    final data = await _post('/api/alerts/price', {
      'symbol': symbol,
      'target': target,
      'direction': direction,
      'note': note,
    });
    return data as Map<String, dynamic>;
  }

  Future<void> deleteAlert(int alertId) async {
    await _delete('/api/alerts/price/$alertId');
  }

  // ─── Haberler ─────────────────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getNews({String? symbol, int limit = 20}) async {
    final params = <String, String>{'limit': '$limit'};
    if (symbol != null) params['symbol'] = symbol;
    final data = await _get('/api/news', params);
    final map  = data as Map<String, dynamic>;
    final list = (map['news'] as List<dynamic>?) ?? [];
    return list.cast<Map<String, dynamic>>();
  }

  // ─── Grafik Verisi ────────────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getCandles(
    String symbol, {
    String interval = '1d',
    int limit = 90,
  }) async {
    final data = await _get('/api/v2/candles', {
      'symbol': symbol,
      'interval': interval,
      'limit': '$limit',
    });
    if (data is Map<String, dynamic>) {
      final bars = (data['bars'] as List<dynamic>?) ?? [];
      return bars.cast<Map<String, dynamic>>();
    }
    if (data is List<dynamic>) return data.cast<Map<String, dynamic>>();
    return [];
  }

  // ─── Backtest Raporları ───────────────────────────────────────────────────

  Future<List<Map<String, dynamic>>> getBacktestReports({int limit = 50}) async {
    final data = await _get('/api/backtest/reports', {'limit': '$limit'});
    final map  = data as Map<String, dynamic>;
    final list = (map['reports'] as List<dynamic>?) ?? [];
    return list.cast<Map<String, dynamic>>();
  }

  // ─── Health ───────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getHealth() async {
    final data = await _get('/api/health');
    return data as Map<String, dynamic>;
  }
}
