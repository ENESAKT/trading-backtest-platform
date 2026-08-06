/// İzleme Listesi Ekranı
///
/// Kullanıcının takip ettiği sembollerin anlık fiyat, değişim ve
/// veri kalite rozetleriyle gösterildiği mobil-öncelikli ana ekran.
library;

import 'dart:async';

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/data_quality_badge.dart';
import '../widgets/price_change_chip.dart';
import 'price_alert_screen.dart';
import 'symbol_360_screen.dart';

class WatchlistScreen extends StatefulWidget {
  final ApiService api;
  const WatchlistScreen({super.key, required this.api});

  @override
  State<WatchlistScreen> createState() => _WatchlistScreenState();
}

class _WatchlistScreenState extends State<WatchlistScreen> {
  List<SymbolSnapshot> _items = [];
  bool _loading = true;
  String? _error;
  Timer? _refreshTimer;

  @override
  void initState() {
    super.initState();
    _load();
    _refreshTimer = Timer.periodic(const Duration(seconds: 30), (_) => _load());
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() { _loading = true; _error = null; });
    try {
      final items = await widget.api.getWatchlist();
      setState(() { _items = items; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Bu özelliği kullanmak için giriş yapmalısınız.'
            : 'Veri yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası: $e'; });
    }
  }

  Future<void> _addSymbol() async {
    final ctrl = TextEditingController();
    final symbol = await showDialog<String>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Sembol Ekle'),
        content: TextField(
          controller: ctrl,
          textCapitalization: TextCapitalization.characters,
          decoration: const InputDecoration(
            labelText: 'Sembol (örn. THYAO)',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('İptal')),
          FilledButton(
            onPressed: () => Navigator.pop(ctx, ctrl.text.trim().toUpperCase()),
            child: const Text('Ekle'),
          ),
        ],
      ),
    );
    if (symbol == null || symbol.isEmpty) return;
    try {
      await widget.api.addToWatchlist(symbol, 'BIST');
      _load();
    } on ApiException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Eklenemedi: ${e.message}')),
        );
      }
    }
  }

  Future<void> _removeSymbol(String symbol) async {
    try {
      await widget.api.removeFromWatchlist(symbol);
      setState(() => _items.removeWhere((s) => s.symbol == symbol));
    } on ApiException catch (_) {
      _load();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('İzleme Listesi'),
        actions: [
          IconButton(
            icon: const Icon(Icons.notifications_outlined),
            tooltip: 'Fiyat Alarmları',
            onPressed: () => Navigator.push(
              context,
              MaterialPageRoute(builder: (_) => PriceAlertScreen(api: widget.api)),
            ),
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Yenile',
            onPressed: _load,
          ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _addSymbol,
        tooltip: 'Sembol Ekle',
        child: const Icon(Icons.add),
      ),
    );
  }

  Widget _buildBody() {
    if (_loading && _items.isEmpty) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_error != null && _items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.warning_amber_rounded, size: 48, color: Colors.orange),
              const SizedBox(height: 12),
              Text(_error!, textAlign: TextAlign.center),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
            ],
          ),
        ),
      );
    }
    if (_items.isEmpty) {
      return const Center(
        child: Text(
          'İzleme listeniz boş.\n+ butonuna basarak sembol ekleyin.',
          textAlign: TextAlign.center,
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        itemCount: _items.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (ctx, i) {
          final s = _items[i];
          return Dismissible(
            key: ValueKey(s.symbol),
            direction: DismissDirection.endToStart,
            background: Container(
              color: Colors.red,
              alignment: Alignment.centerRight,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              child: const Icon(Icons.delete, color: Colors.white),
            ),
            onDismissed: (_) => _removeSymbol(s.symbol),
            child: _WatchlistTile(
              snapshot: s,
              onTap: () => Navigator.push(
                ctx,
                MaterialPageRoute(
                  builder: (_) => Symbol360Screen(
                    api: widget.api,
                    symbol: s.symbol,
                    market: s.market,
                  ),
                ),
              ),
            ),
          );
        },
      ),
    );
  }
}

class _WatchlistTile extends StatelessWidget {
  final SymbolSnapshot snapshot;
  final VoidCallback onTap;
  const _WatchlistTile({required this.snapshot, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: CircleAvatar(
        backgroundColor: theme.colorScheme.primaryContainer,
        child: Text(
          snapshot.symbol.substring(0, snapshot.symbol.length.clamp(0, 2)),
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: theme.colorScheme.onPrimaryContainer,
          ),
        ),
      ),
      title: Row(children: [
        Text(snapshot.symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(width: 6),
        DataQualityBadge(truth: snapshot.dataTruth),
      ]),
      subtitle: Text(
        snapshot.name ?? snapshot.market,
        style: theme.textTheme.bodySmall,
        maxLines: 1,
        overflow: TextOverflow.ellipsis,
      ),
      trailing: snapshot.lastPrice != null
          ? Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  '₺${snapshot.lastPrice!.toStringAsFixed(2)}',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                const SizedBox(height: 2),
                PriceChangeChip(changePct: snapshot.changePct1d),
              ],
            )
          : const Text('—', style: TextStyle(color: Colors.grey)),
      onTap: onTap,
    );
  }
}
