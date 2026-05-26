/// Paper Portföy Ekranı
///
/// Sanal cüzdan durumu, açık pozisyonlar ve son emirleri gösterir.
/// Restart sonrası pozisyon kalıcılığı backend tarafında sağlanır.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';

class PaperPortfolioScreen extends StatefulWidget {
  final ApiService api;
  final String strategyId;
  const PaperPortfolioScreen({
    super.key,
    required this.api,
    required this.strategyId,
  });

  @override
  State<PaperPortfolioScreen> createState() => _PaperPortfolioScreenState();
}

class _PaperPortfolioScreenState extends State<PaperPortfolioScreen> {
  PaperPortfolioSummary? _portfolio;
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
      final p = await widget.api.getPaperPortfolio(widget.strategyId);
      setState(() { _portfolio = p; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Portföy verilerini görmek için giriş yapmalısınız.'
            : 'Portföy yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Paper Portföy'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: _PaperDisclaimer(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return Center(child: Padding(
      padding: const EdgeInsets.all(24),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        const Icon(Icons.warning_amber, size: 40, color: Colors.orange),
        const SizedBox(height: 8),
        Text(_error!, textAlign: TextAlign.center),
        const SizedBox(height: 16),
        ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
      ]),
    ));
    if (_portfolio == null) return const SizedBox.shrink();

    final p = _portfolio!;
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView(children: [
        // Donduruldu uyarısı
        if (p.isHalted)
          Container(
            color: Colors.red.withOpacity(0.1),
            padding: const EdgeInsets.all(12),
            child: const Row(children: [
              Icon(Icons.lock, color: Colors.red),
              SizedBox(width: 8),
              Expanded(child: Text(
                'Strateji günlük zarar limiti nedeniyle donduruldu.',
                style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
              )),
            ]),
          ),

        // Özet kartı
        _SummaryCard(portfolio: p),

        // Açık pozisyonlar
        if (p.positions.isNotEmpty) ...[
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text('AÇIK POZİSYONLAR',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
          ),
          ...p.positions.map((pos) => _PositionTile(position: pos)),
        ] else
          const Padding(
            padding: EdgeInsets.all(24),
            child: Text('Açık pozisyon yok.', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey)),
          ),

        // Son emirler
        if (p.openOrders.isNotEmpty) ...[
          const Padding(
            padding: EdgeInsets.fromLTRB(16, 16, 16, 8),
            child: Text('BEKLEYEN EMİRLER',
              style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
          ),
          ...p.openOrders.map((o) => _OrderTile(order: o)),
        ],

        const SizedBox(height: 24),
      ]),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  final PaperPortfolioSummary portfolio;
  const _SummaryCard({required this.portfolio});

  @override
  Widget build(BuildContext context) {
    final p = portfolio;
    final pnlColor = p.unrealizedPnl >= 0 ? Colors.green : Colors.red;
    final dailyColor = p.dailyPnl >= 0 ? Colors.green : Colors.red;

    return Card(
      margin: const EdgeInsets.all(12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(children: [
          // Toplam sermaye
          Text(
            '₺${p.totalEquity.toStringAsFixed(2)}',
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
          Text('Toplam Sermaye', style: TextStyle(color: Colors.grey[600], fontSize: 13)),
          const Divider(height: 24),

          // İstatistikler grid
          Row(children: [
            _StatCell('Nakit', '₺${p.cash.toStringAsFixed(2)}'),
            _StatCell('Pozisyon Değeri', '₺${p.positionsValue.toStringAsFixed(2)}'),
          ]),
          const SizedBox(height: 8),
          Row(children: [
            _StatCell('Gerçekleşmemiş K/Z',
              '${p.unrealizedPnl >= 0 ? "+" : ""}₺${p.unrealizedPnl.toStringAsFixed(2)}',
              color: pnlColor,
            ),
            _StatCell('Günlük K/Z',
              '${p.dailyPnl >= 0 ? "+" : ""}₺${p.dailyPnl.toStringAsFixed(2)} (%${p.dailyPnlPct.toStringAsFixed(2)})',
              color: dailyColor,
            ),
          ]),
        ]),
      ),
    );
  }
}

class _StatCell extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;
  const _StatCell(this.label, this.value, {this.color});

  @override
  Widget build(BuildContext context) {
    return Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
      const SizedBox(height: 2),
      Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14)),
    ]));
  }
}

class _PositionTile extends StatelessWidget {
  final PaperPosition position;
  const _PositionTile({required this.position});

  @override
  Widget build(BuildContext context) {
    final pnl = position.unrealizedPnl ?? 0;
    final pnlColor = pnl >= 0 ? Colors.green : Colors.red;

    return ListTile(
      dense: true,
      leading: Container(
        width: 36, height: 36,
        decoration: BoxDecoration(
          color: position.side == 'long' ? Colors.green.withOpacity(0.15) : Colors.red.withOpacity(0.15),
          borderRadius: BorderRadius.circular(6),
        ),
        child: Center(child: Text(
          position.side == 'long' ? 'L' : 'S',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            color: position.side == 'long' ? Colors.green : Colors.red,
          ),
        )),
      ),
      title: Text(position.symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
      subtitle: Text('${position.quantity.toStringAsFixed(2)} lot @ ₺${position.entryPrice.toStringAsFixed(2)}'),
      trailing: Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
        if (position.currentPrice != null)
          Text('₺${position.currentPrice!.toStringAsFixed(2)}',
            style: const TextStyle(fontWeight: FontWeight.bold)),
        Text(
          '${pnl >= 0 ? "+" : ""}₺${pnl.toStringAsFixed(2)}',
          style: TextStyle(color: pnlColor, fontSize: 12),
        ),
      ]),
    );
  }
}

class _OrderTile extends StatelessWidget {
  final PaperOrder order;
  const _OrderTile({required this.order});

  @override
  Widget build(BuildContext context) {
    return ListTile(
      dense: true,
      title: Text('${order.symbol} — ${order.side.name.toUpperCase()}'),
      subtitle: Text('${order.quantity} lot · ${order.orderType.name}'),
      trailing: Text(order.status.name.toUpperCase(),
        style: TextStyle(
          fontSize: 11,
          color: order.status == PaperOrderStatus.filled ? Colors.green : Colors.orange,
          fontWeight: FontWeight.bold,
        )),
    );
  }
}

class _PaperDisclaimer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.blue.withOpacity(0.08),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      child: const Text(
        '📋 SANAL AL/SAT — Bu ekrandaki tüm işlemler simülasyondur. Gerçek emir verilmez, gerçek para kullanılmaz.',
        style: TextStyle(fontSize: 11, color: Colors.blueGrey),
        textAlign: TextAlign.center,
      ),
    );
  }
}
