/// Screener (Tarayıcı) Ekranı
///
/// Kullanıcı filtre kurallarını seçer, backend'e gönderir ve sonuçları listeler.
/// Her sonuç Symbol360 ekranına gidebilir.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/data_quality_badge.dart';
import '../widgets/price_change_chip.dart';
import 'symbol_360_screen.dart';

// Hazır preset'ler
const _presets = [
  _Preset('Güçlü AL Sinyali', [
    {'field': 'technical_rating', 'op': 'eq', 'value': 'strong_buy'},
  ]),
  _Preset('Yüksek Hacim', [
    {'field': 'volume', 'op': 'gt', 'value': 1000000},
  ]),
  _Preset('52 Hafta Zirvesi Yakını', [
    {'field': 'pct_from_52w_high', 'op': 'lt', 'value': 5},
  ]),
  _Preset('Düşük F/K (< 10)', [
    {'field': 'pe_ratio', 'op': 'lt', 'value': 10},
    {'field': 'pe_ratio', 'op': 'gt', 'value': 0},
  ]),
];

class _Preset {
  final String name;
  final List<Map<String, dynamic>> filters;
  const _Preset(this.name, this.filters);
}

class ScreenerScreen extends StatefulWidget {
  final ApiService api;
  const ScreenerScreen({super.key, required this.api});

  @override
  State<ScreenerScreen> createState() => _ScreenerScreenState();
}

class _ScreenerScreenState extends State<ScreenerScreen> {
  List<SymbolSnapshot> _results  = [];
  bool   _loading  = false;
  String? _error;
  int    _selected = -1; // seçili preset indeksi (-1 = hiçbiri)

  Future<void> _runPreset(int idx) async {
    if (idx < 0 || idx >= _presets.length) return;
    setState(() { _loading = true; _error = null; _selected = idx; });
    try {
      final preset = _presets[idx];
      final rules  = preset.filters.map((f) => ScreenerFilterRule(
        field:    f['field'] as String,
        operator: f['op']   as String,
        value:    f['value'],
      )).toList();
      final req  = ScreenerRunRequest(filters: rules, market: 'BIST', limit: 50);
      final resp = await widget.api.runScreener(req);
      setState(() {
        _results = resp.rows.map((r) => SymbolSnapshot(
          symbol: r.symbol,
          market: r.market,
          name: r.name,
          lastPrice: r.lastPrice,
          changePct1d: r.changePct1d,
        )).toList();
        _loading = false;
      });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Tarayıcıyı kullanmak için giriş yapın.'
            : 'Tarayıcı çalıştırılamadı (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Hisse Tarayıcı'),
        actions: [
          if (_results.isNotEmpty)
            Padding(
              padding: const EdgeInsets.only(right: 12),
              child: Center(
                child: Text('${_results.length} sonuç',
                  style: const TextStyle(fontSize: 13, color: Colors.grey)),
              ),
            ),
        ],
      ),
      body: Column(children: [
        // Preset seçim çipi sırası
        _PresetChipRow(
          presets:  _presets,
          selected: _selected,
          onTap:    _runPreset,
        ),
        const Divider(height: 1),
        Expanded(child: _buildBody()),
      ]),
      bottomNavigationBar: Container(
        color: Colors.amber.withOpacity(0.08),
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        child: const Text(
          '⚠️ Tarayıcı sonuçları yatırım tavsiyesi değildir.',
          style: TextStyle(fontSize: 11, color: Colors.grey),
          textAlign: TextAlign.center,
        ),
      ),
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
      ]),
    ));
    if (_results.isEmpty) return Center(
      child: Text(
        _selected < 0
            ? 'Bir preset seçerek taramayı başlatın.'
            : 'Bu kriterlere uyan sembol bulunamadı.',
        textAlign: TextAlign.center,
        style: const TextStyle(color: Colors.grey),
      ),
    );

    return ListView.separated(
      itemCount: _results.length,
      separatorBuilder: (_, __) => const Divider(height: 1),
      itemBuilder: (ctx, i) {
        final s = _results[i];
        return ListTile(
          contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
          leading: CircleAvatar(
            backgroundColor: Theme.of(context).colorScheme.primaryContainer,
            child: Text(
              s.symbol.substring(0, s.symbol.length.clamp(0, 2)),
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
          title: Row(children: [
            Text(s.symbol, style: const TextStyle(fontWeight: FontWeight.bold)),
            const SizedBox(width: 6),
            DataQualityBadge(truth: s.dataTruth),
          ]),
          subtitle: Text(s.name ?? s.market,
            maxLines: 1, overflow: TextOverflow.ellipsis,
            style: const TextStyle(fontSize: 12)),
          trailing: s.lastPrice != null
              ? Column(mainAxisAlignment: MainAxisAlignment.center, crossAxisAlignment: CrossAxisAlignment.end, children: [
                  Text('₺${s.lastPrice!.toStringAsFixed(2)}',
                    style: const TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 2),
                  PriceChangeChip(changePct: s.changePct1d),
                ])
              : const Text('—', style: TextStyle(color: Colors.grey)),
          onTap: () => Navigator.push(ctx, MaterialPageRoute(
            builder: (_) => Symbol360Screen(
              api: widget.api,
              symbol: s.symbol,
              market: s.market,
            ),
          )),
        );
      },
    );
  }
}

class _PresetChipRow extends StatelessWidget {
  final List<_Preset> presets;
  final int selected;
  final void Function(int) onTap;
  const _PresetChipRow({required this.presets, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        itemCount: presets.length,
        separatorBuilder: (_, __) => const SizedBox(width: 8),
        itemBuilder: (_, i) => FilterChip(
          label: Text(presets[i].name, style: const TextStyle(fontSize: 12)),
          selected: selected == i,
          onSelected: (_) => onTap(i),
          visualDensity: VisualDensity.compact,
        ),
      ),
    );
  }
}
