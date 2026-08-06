/// Backtest Rapor Listesi Ekranı
///
/// Backend /api/backtest/reports endpoint'inden tamamlanmış backtest raporlarını listeler.
library;

import 'package:flutter/material.dart';

import '../services/api_service.dart';
import 'backtest_summary_screen.dart';

class BacktestListScreen extends StatefulWidget {
  final ApiService api;
  const BacktestListScreen({super.key, required this.api});

  @override
  State<BacktestListScreen> createState() => _BacktestListScreenState();
}

class _BacktestListScreenState extends State<BacktestListScreen> {
  List<Map<String, dynamic>> _reports = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final list = await widget.api.getBacktestReports();
      setState(() { _reports = list; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Backtest raporlarını görmek için giriş yapın.'
            : 'Raporlar yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Backtest Raporları'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _load)],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.warning_amber, size: 40, color: Colors.orange),
          const SizedBox(height: 8),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
        ]),
      ));
    }
    if (_reports.isEmpty) {
      return const Center(
        child: Text(
          'Henüz backtest raporu yok.\nWeb arayüzünden backtest çalıştırın.',
          textAlign: TextAlign.center,
          style: TextStyle(color: Colors.grey),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        itemCount: _reports.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (ctx, i) {
          final r         = _reports[i];
          final symbol    = r['symbol'] as String? ?? '—';
          final createdAt = r['created_at'] as String? ?? '';
          final metrics   = r['metrics'] as Map<String, dynamic>? ?? {};
          final totalRet  = (metrics['total_return_pct'] as num?)?.toDouble();
          final retColor  = (totalRet ?? 0) >= 0 ? Colors.green : Colors.red;

          return ListTile(
            leading: CircleAvatar(
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                symbol.substring(0, symbol.length.clamp(0, 2)),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: Theme.of(context).colorScheme.onPrimaryContainer,
                ),
              ),
            ),
            title: Text(symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
            subtitle: Text(
              createdAt.length >= 10 ? createdAt.substring(0, 10) : createdAt,
              style: const TextStyle(fontSize: 12, color: Colors.grey),
            ),
            trailing: totalRet != null
                ? Text(
                    '${totalRet >= 0 ? "+" : ""}${totalRet.toStringAsFixed(1)}%',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      color: retColor,
                      fontSize: 15,
                    ),
                  )
                : const Text('—', style: TextStyle(color: Colors.grey)),
            onTap: () => Navigator.push(
              ctx,
              MaterialPageRoute(
                builder: (_) => BacktestSummaryScreen(result: r),
              ),
            ),
          );
        },
      ),
    );
  }
}
