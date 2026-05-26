/// İzleme Listesi Ekranı
///
/// Kullanıcının takip ettiği sembollerin anlık fiyat, değişim ve
/// veri kalite rozetleriyle gösterildiği mobil-öncelikli ana ekran.
/// Masaüstü terminalin kopyası değil; hızlı izleme odaklıdır.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/data_quality_badge.dart';
import '../widgets/price_change_chip.dart';

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

  @override
  void initState() {
    super.initState();
    _load();
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

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('İzleme Listesi'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Yenile',
            onPressed: _load,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
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
        child: Text('İzleme listeniz boş.\nSembol eklemek için + butonunu kullanın.', textAlign: TextAlign.center),
      );
    }
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.separated(
        itemCount: _items.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (ctx, i) => _WatchlistTile(snapshot: _items[i]),
      ),
    );
  }
}

class _WatchlistTile extends StatelessWidget {
  final SymbolSnapshot snapshot;
  const _WatchlistTile({required this.snapshot});

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
      onTap: () {
        // Symbol 360 ekranına git
      },
    );
  }
}
