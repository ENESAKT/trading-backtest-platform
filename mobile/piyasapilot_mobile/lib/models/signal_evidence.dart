/// SignalEvidence — sinyal kanıt paketi.
///
/// Her sinyal, backtest ve paper trading olayı için üretilmeli.
/// Backend SignalEvidence Pydantic modeli ile hizalıdır (Bölüm 18.14).
library;

import 'data_truth.dart';

enum SignalType {
  buy,
  sell,
  short,
  cover,
  hold;

  static SignalType fromJson(String? v) => switch (v?.toUpperCase()) {
        'BUY'   => buy,
        'SELL'  => sell,
        'SHORT' => short,
        'COVER' => cover,
        'HOLD'  => hold,
        _       => hold,
      };

  String get displayLabel => switch (this) {
        buy   => 'Al',
        sell  => 'Sat',
        short => 'Açığa Sat',
        cover => 'Kapat',
        hold  => 'Tut',
      };
}

class SignalIndicatorSnapshot {
  final String name;
  final double? value;
  final String signal;
  final String note;

  const SignalIndicatorSnapshot({
    required this.name,
    this.value,
    this.signal = '',
    this.note = '',
  });

  factory SignalIndicatorSnapshot.fromJson(Map<String, dynamic> j) =>
      SignalIndicatorSnapshot(
        name:   j['name']   as String,
        value:  (j['value'] as num?)?.toDouble(),
        signal: j['signal'] as String? ?? '',
        note:   j['note']   as String? ?? '',
      );
}

class SignalEvidence {
  final String signalId;
  final String strategyId;
  final String symbol;
  final String market;
  final String timeframe;

  final SignalType signalType;
  final int strength; // 1–10
  final double priceAtSignal;
  final DateTime ts;

  final List<SignalIndicatorSnapshot> indicators;
  final String reason;
  final String ruleTriggered;

  final DataTruth? dataTruth;

  final String disclaimer;
  final List<String> warnings;

  const SignalEvidence({
    required this.signalId,
    required this.strategyId,
    required this.symbol,
    required this.market,
    required this.timeframe,
    required this.signalType,
    this.strength = 5,
    required this.priceAtSignal,
    required this.ts,
    this.indicators = const [],
    this.reason = '',
    this.ruleTriggered = '',
    this.dataTruth,
    this.disclaimer =
        'Bu sinyal yatırım tavsiyesi değildir. Teknik gösterge durumunu özetler.',
    this.warnings = const [],
  });

  factory SignalEvidence.fromJson(Map<String, dynamic> j) => SignalEvidence(
        signalId:       j['signal_id']    as String,
        strategyId:     j['strategy_id']  as String,
        symbol:         j['symbol']       as String,
        market:         j['market']       as String,
        timeframe:      j['timeframe']    as String,
        signalType:     SignalType.fromJson(j['signal_type'] as String?),
        strength:       j['strength']     as int? ?? 5,
        priceAtSignal:  (j['price_at_signal'] as num).toDouble(),
        ts:             DateTime.parse(j['ts'] as String),
        indicators: (j['indicators'] as List<dynamic>?)
                ?.map((e) => SignalIndicatorSnapshot.fromJson(
                    e as Map<String, dynamic>))
                .toList() ??
            [],
        reason:        j['reason']         as String? ?? '',
        ruleTriggered: j['rule_triggered'] as String? ?? '',
        dataTruth: j['data_truth'] != null
            ? DataTruth.fromJson(j['data_truth'] as Map<String, dynamic>)
            : null,
        disclaimer: j['disclaimer'] as String? ??
            'Bu sinyal yatırım tavsiyesi değildir. Teknik gösterge durumunu özetler.',
        warnings: (j['warnings'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );
}
