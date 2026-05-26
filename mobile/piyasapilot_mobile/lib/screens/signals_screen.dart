/// Sinyaller Ekranı
///
/// Sinyal motoru tarafından üretilen sinyalleri kanıt paketiyle gösterir.
/// Her sinyal için disclaimer ve veri kalitesi rozeti zorunludur.
library;

import 'package:flutter/material.dart';

import '../models/models.dart';
import '../services/api_service.dart';
import '../widgets/data_quality_badge.dart';

class SignalsScreen extends StatefulWidget {
  final ApiService api;
  final String? filterSymbol;
  const SignalsScreen({super.key, required this.api, this.filterSymbol});

  @override
  State<SignalsScreen> createState() => _SignalsScreenState();
}

class _SignalsScreenState extends State<SignalsScreen> {
  List<SignalEvidence> _signals = [];
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
      final list = await widget.api.getSignals(symbol: widget.filterSymbol);
      setState(() { _signals = list; _loading = false; });
    } on ApiException catch (e) {
      setState(() {
        _loading = false;
        _error = e.statusCode == 401
            ? 'Sinyal verilerini görmek için giriş yapmalısınız.'
            : 'Sinyaller yüklenemedi (${e.statusCode})';
      });
    } catch (e) {
      setState(() { _loading = false; _error = 'Bağlantı hatası'; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.filterSymbol != null
            ? '${widget.filterSymbol} Sinyalleri'
            : 'Sinyaller'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _buildBody(),
      bottomNavigationBar: _DisclaimerBar(),
    );
  }

  Widget _buildBody() {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) {
      return Center(child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const Icon(Icons.info_outline, size: 40, color: Colors.orange),
          const SizedBox(height: 8),
          Text(_error!, textAlign: TextAlign.center),
          const SizedBox(height: 16),
          ElevatedButton(onPressed: _load, child: const Text('Tekrar Dene')),
        ]),
      ));
    }
    if (_signals.isEmpty) {
      return const Center(child: Text('Şu an aktif sinyal bulunmuyor.'));
    }
    return ListView.builder(
      itemCount: _signals.length,
      itemBuilder: (ctx, i) => _SignalCard(signal: _signals[i]),
    );
  }
}

class _SignalCard extends StatelessWidget {
  final SignalEvidence signal;
  const _SignalCard({required this.signal});

  Color _typeColor() => switch (signal.signalType) {
        SignalType.buy   => Colors.green,
        SignalType.sell  => Colors.red,
        SignalType.short => Colors.deepOrange,
        SignalType.cover => Colors.blue,
        SignalType.hold  => Colors.grey,
      };

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          // Başlık satırı
          Row(children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: _typeColor(),
                borderRadius: BorderRadius.circular(4),
              ),
              child: Text(
                signal.signalType.displayLabel,
                style: const TextStyle(color: Colors.white, fontWeight: FontWeight.bold, fontSize: 12),
              ),
            ),
            const SizedBox(width: 8),
            Text(signal.symbol, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
            const SizedBox(width: 4),
            Text(signal.market, style: const TextStyle(color: Colors.grey, fontSize: 12)),
            const Spacer(),
            DataQualityBadge(truth: signal.dataTruth),
          ]),
          const SizedBox(height: 8),

          // Fiyat ve güç
          Row(children: [
            Text(
              '₺${signal.priceAtSignal.toStringAsFixed(2)}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(width: 12),
            _StrengthBar(strength: signal.strength),
          ]),
          const SizedBox(height: 6),

          // Sebep
          if (signal.reason.isNotEmpty)
            Text(signal.reason, style: const TextStyle(fontSize: 13)),

          // Göstergeler
          if (signal.indicators.isNotEmpty) ...[
            const SizedBox(height: 8),
            Wrap(spacing: 6, runSpacing: 4, children: signal.indicators.map((ind) =>
              Chip(
                label: Text('${ind.name}: ${ind.value?.toStringAsFixed(2) ?? "—"}',
                  style: const TextStyle(fontSize: 11)),
                padding: EdgeInsets.zero,
                visualDensity: VisualDensity.compact,
              ),
            ).toList()),
          ],

          // Uyarılar
          if (signal.warnings.isNotEmpty) ...[
            const SizedBox(height: 6),
            ...signal.warnings.map((w) => Text('⚠️ $w',
              style: const TextStyle(fontSize: 11, color: Colors.orange))),
          ],

          // Disclaimer
          const SizedBox(height: 8),
          Text(
            signal.disclaimer,
            style: const TextStyle(fontSize: 10, color: Colors.grey, fontStyle: FontStyle.italic),
          ),

          // Zaman
          const SizedBox(height: 4),
          Text(
            signal.ts.toLocal().toString().substring(0, 16),
            style: const TextStyle(fontSize: 11, color: Colors.grey),
          ),
        ]),
      ),
    );
  }
}

class _StrengthBar extends StatelessWidget {
  final int strength; // 1–10
  const _StrengthBar({required this.strength});

  @override
  Widget build(BuildContext context) {
    return Row(mainAxisSize: MainAxisSize.min, children: [
      const Text('Güç:', style: TextStyle(fontSize: 12, color: Colors.grey)),
      const SizedBox(width: 4),
      ...List.generate(10, (i) => Container(
        width: 6, height: 12, margin: const EdgeInsets.only(right: 1),
        decoration: BoxDecoration(
          color: i < strength ? Colors.amber : Colors.grey.withOpacity(0.2),
          borderRadius: BorderRadius.circular(2),
        ),
      )),
      const SizedBox(width: 4),
      Text('$strength/10', style: const TextStyle(fontSize: 11)),
    ]);
  }
}

class _DisclaimerBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.amber.withOpacity(0.1),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      child: const Text(
        '⚠️ Bu sinyaller yatırım tavsiyesi değildir. Geçmiş performans gelecek sonuçları garanti etmez.',
        style: TextStyle(fontSize: 11, color: Colors.grey),
        textAlign: TextAlign.center,
      ),
    );
  }
}
