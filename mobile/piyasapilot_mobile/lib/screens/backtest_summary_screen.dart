/// Backtest Özet Ekranı
///
/// Tamamlanmış backtest sonucunu gösterir: varsayımlar kartı (BacktestAssumptions),
/// temel metrikler ve risk kartları. Plan kapılı özellikler kilit ikonuyla işaretlenir.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';

class BacktestSummaryScreen extends StatelessWidget {
  final Map<String, dynamic> result;

  const BacktestSummaryScreen({super.key, required this.result});

  @override
  Widget build(BuildContext context) {
    final assumptions = result['assumptions'] as Map<String, dynamic>?;
    final metrics     = result['metrics']     as Map<String, dynamic>?;
    final riskCards   = result['risk_cards']  as List<dynamic>?;
    final runId       = result['run_id']      as String? ?? '—';
    final symbol      = result['symbol']      as String? ?? '—';

    return Scaffold(
      appBar: AppBar(
        title: Text('Backtest — $symbol'),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined),
            tooltip: 'Paylaş',
            onPressed: () => _shareResult(context, runId),
          ),
        ],
      ),
      body: ListView(padding: const EdgeInsets.all(12), children: [
        // Varsayımlar Kartı (zorunlu — kartsız rapor geçersiz)
        if (assumptions != null)
          _AssumptionsCard(assumptions: assumptions)
        else
          Container(
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.red.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.red.withOpacity(0.3)),
            ),
            child: const Row(children: [
              Icon(Icons.warning_amber, color: Colors.red),
              SizedBox(width: 8),
              Expanded(child: Text(
                'Varsayımlar kartı eksik — bu rapor geçersiz sayılır.',
                style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold),
              )),
            ]),
          ),
        const SizedBox(height: 12),

        // Temel metrikler
        if (metrics != null) _MetricsCard(metrics: metrics),

        // Risk kartları
        if (riskCards != null && riskCards.isNotEmpty) ...[
          const SizedBox(height: 12),
          const Text('RİSK KARTI', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
          const SizedBox(height: 8),
          ...riskCards.map((rc) => _RiskChip(card: rc as Map<String, dynamic>)),
        ],

        const SizedBox(height: 16),
        // Disclaimer
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: Colors.amber.withOpacity(0.08),
            borderRadius: BorderRadius.circular(8),
          ),
          child: const Text(
            '⚠️ Backtest geçmiş veriye dayanır; gelecek performansı garanti etmez. '
            'Komisyon, slippage ve likidite varsayımlar kısmında belirtilmiştir.',
            style: TextStyle(fontSize: 11, color: Colors.grey),
          ),
        ),
        const SizedBox(height: 24),
      ]),
    );
  }

  void _shareResult(BuildContext context, String runId) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('Paylaşım linki oluşturuldu: /shared/$runId')),
    );
  }
}

class _AssumptionsCard extends StatelessWidget {
  final Map<String, dynamic> assumptions;
  const _AssumptionsCard({required this.assumptions});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Row(children: [
            Icon(Icons.settings_outlined, size: 16),
            SizedBox(width: 6),
            Text('VARSAYIMLAR', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
          ]),
          const Divider(height: 16),
          _row('Başlangıç Sermayesi', '₺${assumptions['initial_capital'] ?? '—'}'),
          _row('Komisyon Oranı',      '%${assumptions['commission_bps'] ?? '—'} (bps)'),
          _row('Slippage Modeli',     '${assumptions['slippage_model'] ?? '—'}'),
          _row('Veri Kaynağı',        '${assumptions['data_source'] ?? '—'}'),
          _row('Timeframe',           '${assumptions['timeframe'] ?? '—'}'),
          if (assumptions['is_data_real'] == false)
            Container(
              margin: const EdgeInsets.only(top: 8),
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.deepOrange.withOpacity(0.1),
                borderRadius: BorderRadius.circular(6),
              ),
              child: const Text(
                '⚠️ Gerçek piyasa verisi kullanılmadı — sonuçlar simülasyondur.',
                style: TextStyle(fontSize: 11, color: Colors.deepOrange),
              ),
            ),
        ]),
      ),
    );
  }

  Widget _row(String label, String value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 3),
    child: Row(children: [
      SizedBox(width: 140, child: Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey))),
      Text(value, style: const TextStyle(fontWeight: FontWeight.w500, fontSize: 13)),
    ]),
  );
}

class _MetricsCard extends StatelessWidget {
  final Map<String, dynamic> metrics;
  const _MetricsCard({required this.metrics});

  @override
  Widget build(BuildContext context) {
    final totalReturn = (metrics['total_return_pct'] as num?)?.toDouble() ?? 0;
    final sharpe      = (metrics['sharpe_ratio']     as num?)?.toDouble();
    final maxDD       = (metrics['max_drawdown_pct'] as num?)?.toDouble();
    final winRate     = (metrics['win_rate_pct']     as num?)?.toDouble();
    final numTrades   = metrics['num_trades'] as int?;
    final returnColor = totalReturn >= 0 ? Colors.green : Colors.red;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(children: [
          Text(
            '${totalReturn >= 0 ? "+" : ""}${totalReturn.toStringAsFixed(2)}%',
            style: TextStyle(fontSize: 32, fontWeight: FontWeight.bold, color: returnColor),
          ),
          const Text('Toplam Getiri', style: TextStyle(fontSize: 12, color: Colors.grey)),
          const Divider(height: 20),
          Row(children: [
            _Stat('Sharpe', sharpe != null ? sharpe.toStringAsFixed(2) : '—'),
            _Stat('Max DD', maxDD  != null ? '${maxDD.toStringAsFixed(1)}%' : '—', color: Colors.red),
            _Stat('Win %', winRate != null ? '${winRate.toStringAsFixed(1)}%' : '—'),
            _Stat('İşlem', numTrades?.toString() ?? '—'),
          ]),
        ]),
      ),
    );
  }
}

class _Stat extends StatelessWidget {
  final String label;
  final String value;
  final Color? color;
  const _Stat(this.label, this.value, {this.color});

  @override
  Widget build(BuildContext context) => Expanded(child: Column(children: [
    Text(label, style: const TextStyle(fontSize: 11, color: Colors.grey)),
    const SizedBox(height: 2),
    Text(value, style: TextStyle(fontWeight: FontWeight.bold, color: color, fontSize: 14)),
  ]));
}

class _RiskChip extends StatelessWidget {
  final Map<String, dynamic> card;
  const _RiskChip({required this.card});

  @override
  Widget build(BuildContext context) {
    final level   = card['level']   as String? ?? 'info';
    final title   = card['title']   as String? ?? '';
    final warning = card['warning'] as String? ?? '';
    final color   = switch (level) {
      'danger'  => Colors.red,
      'warning' => Colors.orange,
      _         => Colors.blue,
    };
    return Container(
      margin: const EdgeInsets.only(bottom: 6),
      padding: const EdgeInsets.all(10),
      decoration: BoxDecoration(
        color: color.withOpacity(0.08),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.25)),
      ),
      child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Icon(_iconForLevel(level), color: color, size: 16),
        const SizedBox(width: 8),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          if (title.isNotEmpty)
            Text(title, style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, color: color)),
          if (warning.isNotEmpty)
            Text(warning, style: const TextStyle(fontSize: 12)),
        ])),
      ]),
    );
  }

  IconData _iconForLevel(String level) => switch (level) {
        'danger'  => Icons.error_outline,
        'warning' => Icons.warning_amber,
        _         => Icons.info_outline,
      };
}
