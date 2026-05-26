/// Sembol 360 Ekranı
///
/// Fiyat başlığı, teknik özet, temel istatistikler ve veri kalitesi rozetini
/// tek sayfada gösterir. Sekmeli yapı ile daha fazla detay açılabilir.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/data_quality_badge.dart';
import '../widgets/price_change_chip.dart';
import '../widgets/technical_rating_card.dart';

class Symbol360Screen extends StatefulWidget {
  final ApiService api;
  final String symbol;
  final String market;

  const Symbol360Screen({
    super.key,
    required this.api,
    required this.symbol,
    required this.market,
  });

  @override
  State<Symbol360Screen> createState() => _Symbol360ScreenState();
}

class _Symbol360ScreenState extends State<Symbol360Screen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs;

  SymbolSnapshot? _snapshot;
  TechnicalSummary? _technical;
  bool _loadingSnapshot = true;
  bool _loadingTechnical = true;
  String? _snapshotError;
  String? _technicalError;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 3, vsync: this);
    _loadSnapshot();
    _loadTechnical();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _loadSnapshot() async {
    setState(() { _loadingSnapshot = true; _snapshotError = null; });
    try {
      final s = await widget.api.getSymbolSnapshot(widget.symbol, widget.market);
      setState(() { _snapshot = s; _loadingSnapshot = false; });
    } on ApiException catch (e) {
      setState(() { _loadingSnapshot = false; _snapshotError = 'Sembol verisi yüklenemedi (${e.statusCode})'; });
    } catch (e) {
      setState(() { _loadingSnapshot = false; _snapshotError = 'Bağlantı hatası'; });
    }
  }

  Future<void> _loadTechnical() async {
    setState(() { _loadingTechnical = true; _technicalError = null; });
    try {
      final t = await widget.api.getTechnicalSummary(
        symbol: widget.symbol,
        market: widget.market,
      );
      setState(() { _technical = t; _loadingTechnical = false; });
    } on ApiException catch (e) {
      setState(() { _loadingTechnical = false; _technicalError = 'Teknik veri yüklenemedi (${e.statusCode})'; });
    } catch (e) {
      setState(() { _loadingTechnical = false; _technicalError = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.symbol),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () { _loadSnapshot(); _loadTechnical(); },
          ),
        ],
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(text: 'Genel'),
            Tab(text: 'Teknik'),
            Tab(text: 'Veri'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: [
          _OverviewTab(
            snapshot: _snapshot,
            loading: _loadingSnapshot,
            error: _snapshotError,
          ),
          _TechnicalTab(
            summary: _technical,
            loading: _loadingTechnical,
            error: _technicalError,
          ),
          _DataQualityTab(snapshot: _snapshot, technical: _technical),
        ],
      ),
    );
  }
}

// ─── Genel Bakış Sekmesi ──────────────────────────────────────────────────────

class _OverviewTab extends StatelessWidget {
  final SymbolSnapshot? snapshot;
  final bool loading;
  final String? error;
  const _OverviewTab({this.snapshot, required this.loading, this.error});

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) return _ErrorView(message: error!);
    if (snapshot == null) return const SizedBox.shrink();

    final s = snapshot!;
    return ListView(padding: const EdgeInsets.all(16), children: [
      // Fiyat başlığı
      Row(children: [
        Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(
            s.lastPrice != null ? '₺${s.lastPrice!.toStringAsFixed(2)}' : '—',
            style: const TextStyle(fontSize: 28, fontWeight: FontWeight.bold),
          ),
          PriceChangeChip(changePct: s.changePct1d),
        ]),
        const Spacer(),
        DataQualityBadge(truth: s.dataTruth),
      ]),
      const SizedBox(height: 16),
      const Divider(),

      // Temel istatistikler
      _StatRow('52H Zirve', s.high52w != null ? '₺${s.high52w!.toStringAsFixed(2)}' : '—'),
      _StatRow('52H Dip',   s.low52w  != null ? '₺${s.low52w!.toStringAsFixed(2)}'  : '—'),
      _StatRow('Piyasa Değeri', s.marketCap != null ? _formatLarge(s.marketCap!) : '—'),
      _StatRow('F/K Oranı', s.peRatio != null ? s.peRatio!.toStringAsFixed(2) : '—'),
      _StatRow('EPS (TTM)', s.epsTtm  != null ? '₺${s.epsTtm!.toStringAsFixed(2)}' : '—'),
      _StatRow('Temettü Verimi', s.dividendYield != null ? '%${(s.dividendYield! * 100).toStringAsFixed(2)}' : '—'),
      _StatRow('Seans Durumu', _sessionLabel(s.sessionStatus)),

      if (s.warnings.isNotEmpty) ...[
        const SizedBox(height: 12),
        ...s.warnings.map((w) => _WarningChip(w)),
      ],

      const SizedBox(height: 16),
      const Text(
        'Bu veriler yatırım tavsiyesi değildir.',
        style: TextStyle(fontSize: 11, color: Colors.grey),
      ),
    ]);
  }

  static String _formatLarge(double v) {
    if (v >= 1e9) return '${(v / 1e9).toStringAsFixed(1)} Mr';
    if (v >= 1e6) return '${(v / 1e6).toStringAsFixed(1)} Mn';
    return v.toStringAsFixed(0);
  }

  static String _sessionLabel(SessionStatus s) => switch (s) {
        SessionStatus.open   => '🟢 Açık',
        SessionStatus.closed => '🔴 Kapalı',
        SessionStatus.pre    => '🟡 Seans Öncesi',
        SessionStatus.post   => '🟡 Seans Sonrası',
        SessionStatus.unknown => '— Bilinmiyor',
      };
}

// ─── Teknik Sekme ─────────────────────────────────────────────────────────────

class _TechnicalTab extends StatelessWidget {
  final TechnicalSummary? summary;
  final bool loading;
  final String? error;
  const _TechnicalTab({this.summary, required this.loading, this.error});

  @override
  Widget build(BuildContext context) {
    if (loading) return const Center(child: CircularProgressIndicator());
    if (error != null) return _ErrorView(message: error!);
    if (summary == null) return const SizedBox.shrink();

    final s = summary!;
    return ListView(padding: const EdgeInsets.all(16), children: [
      TechnicalRatingCard(
        label: 'Genel',
        rating: s.overallRating,
      ),
      const SizedBox(height: 8),
      Row(children: [
        Expanded(child: TechnicalRatingCard(label: 'Osilatörler', rating: s.oscillatorRating)),
        const SizedBox(width: 8),
        Expanded(child: TechnicalRatingCard(label: 'Ort. Değerler', rating: s.movingAverageRating)),
      ]),
      const SizedBox(height: 16),

      if (s.oscillators.isNotEmpty) ...[
        const Text('OSİLATÖRLER', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
        const SizedBox(height: 8),
        ...s.oscillators.map((o) => _IndicatorRow(
          name: o.name,
          value: o.value?.toStringAsFixed(2) ?? '—',
          signal: o.signal,
        )),
        const SizedBox(height: 12),
      ],

      if (s.movingAverages.isNotEmpty) ...[
        const Text('HAREKETLİ ORTALAMALAR', style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold, letterSpacing: 1)),
        const SizedBox(height: 8),
        ...s.movingAverages.map((m) => _IndicatorRow(
          name: '${m.maType.toUpperCase()} ${m.period}',
          value: m.value?.toStringAsFixed(2) ?? '—',
          signal: m.signal,
          note: m.distancePct != null ? '%${m.distancePct!.toStringAsFixed(1)}' : null,
        )),
      ],

      const SizedBox(height: 16),
      Text(
        'Hesaplama v${s.calculationVersion} · ${s.warmupBarsUsed} ısınma barı kullanıldı.\nBu özet yatırım tavsiyesi değildir.',
        style: const TextStyle(fontSize: 11, color: Colors.grey),
      ),
    ]);
  }
}

// ─── Veri Kalitesi Sekmesi ────────────────────────────────────────────────────

class _DataQualityTab extends StatelessWidget {
  final SymbolSnapshot? snapshot;
  final TechnicalSummary? technical;
  const _DataQualityTab({this.snapshot, this.technical});

  @override
  Widget build(BuildContext context) {
    final truth = snapshot?.dataTruth ?? technical?.dataTruth;
    if (truth == null) {
      return const Center(child: Text('Veri kalitesi bilgisi mevcut değil.'));
    }
    return ListView(padding: const EdgeInsets.all(16), children: [
      _StatRow('Sağlayıcı', truth.provider),
      _StatRow('Kaynak Tipi', truth.sourceType.name),
      _StatRow('Gerçek Veri', truth.isReal ? 'Evet' : 'Hayır ⚠️'),
      _StatRow('Canlı', truth.isLive ? 'Evet' : 'Hayır'),
      _StatRow('Gecikme', truth.isDelayed ? '${truth.delayMinutes} dk' : 'Yok'),
      _StatRow('Kalite', truth.qualityStatus.name.toUpperCase()),
      _StatRow('Kapsam', '%${truth.coveragePct.toStringAsFixed(1)}'),
      _StatRow('Boşluk Sayısı', '${truth.gapCount}'),
      _StatRow('Yinelenen Bar', '${truth.duplicateCount}'),
      _StatRow('Aykırı Değer', '${truth.outlierCount}'),
      if (truth.isDerived) ...[
        _StatRow('Türetilmiş', 'Evet — kaynak: ${truth.sourceTimeframe}'),
        _StatRow('Türetme Yöntemi', truth.derivationMethod),
      ],
      if (truth.licenseNote.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text(truth.licenseNote, style: const TextStyle(fontSize: 12, color: Colors.grey)),
      ],
      if (truth.warnings.isNotEmpty) ...[
        const SizedBox(height: 12),
        ...truth.warnings.map((w) => _WarningChip(w)),
      ],
    ]);
  }
}

// ─── Paylaşılan widget yardımcıları ──────────────────────────────────────────

class _StatRow extends StatelessWidget {
  final String label;
  final String value;
  const _StatRow(this.label, this.value);

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(children: [
        SizedBox(
          width: 140,
          child: Text(label, style: const TextStyle(color: Colors.grey, fontSize: 13)),
        ),
        Expanded(child: Text(value, style: const TextStyle(fontWeight: FontWeight.w500))),
      ]),
    );
  }
}

class _IndicatorRow extends StatelessWidget {
  final String name;
  final String value;
  final String signal;
  final String? note;
  const _IndicatorRow({required this.name, required this.value, required this.signal, this.note});

  Color _signalColor() => switch (signal) {
        'buy'     => Colors.green,
        'above'   => Colors.green,
        'sell'    => Colors.red,
        'below'   => Colors.red,
        'neutral' => Colors.orange,
        _         => Colors.grey,
      };

  String _signalLabel() => switch (signal) {
        'buy'     => 'AL',
        'above'   => 'ÜSTÜNDE',
        'sell'    => 'SAT',
        'below'   => 'ALTINDA',
        'neutral' => 'NÖTR',
        _         => '—',
      };

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(children: [
        SizedBox(width: 120, child: Text(name, style: const TextStyle(fontSize: 13))),
        SizedBox(width: 60, child: Text(value, textAlign: TextAlign.right, style: const TextStyle(fontFamily: 'monospace'))),
        const SizedBox(width: 8),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
          decoration: BoxDecoration(
            color: _signalColor().withOpacity(0.12),
            borderRadius: BorderRadius.circular(4),
          ),
          child: Text(_signalLabel(), style: TextStyle(fontSize: 11, color: _signalColor(), fontWeight: FontWeight.bold)),
        ),
        if (note != null) ...[
          const SizedBox(width: 6),
          Text(note!, style: const TextStyle(fontSize: 11, color: Colors.grey)),
        ],
      ]),
    );
  }
}

class _WarningChip extends StatelessWidget {
  final String message;
  const _WarningChip(this.message);

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 4),
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: Colors.orange.withOpacity(0.1),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: Colors.orange.withOpacity(0.3)),
      ),
      child: Row(children: [
        const Icon(Icons.warning_amber, size: 14, color: Colors.orange),
        const SizedBox(width: 6),
        Expanded(child: Text(message, style: const TextStyle(fontSize: 12))),
      ]),
    );
  }
}

class _ErrorView extends StatelessWidget {
  final String message;
  const _ErrorView({required this.message});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.error_outline, size: 40, color: Colors.red),
          const SizedBox(height: 8),
          Text(message, textAlign: TextAlign.center),
        ]),
      ),
    );
  }
}
