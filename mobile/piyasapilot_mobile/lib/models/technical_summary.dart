/// TechnicalSummary — teknik analiz özeti.
///
/// Backend TechnicalSummary Pydantic modeli ile hizalıdır (Bölüm 18.14).
library;

import 'data_truth.dart';

enum TechnicalRating {
  strongBuy,
  buy,
  neutral,
  sell,
  strongSell,
  unknown;

  static TechnicalRating fromJson(String? v) => switch (v) {
        'strong_buy'  => strongBuy,
        'buy'         => buy,
        'neutral'     => neutral,
        'sell'        => sell,
        'strong_sell' => strongSell,
        _             => unknown,
      };

  /// Kullanıcıya gösterilecek Türkçe etiket
  String get label => switch (this) {
        strongBuy  => 'Güçlü Al',
        buy        => 'Al',
        neutral    => 'Nötr',
        sell       => 'Sat',
        strongSell => 'Güçlü Sat',
        unknown    => '—',
      };
}

class OscillatorEntry {
  final String name;
  final double? value;
  final String signal; // 'buy' | 'sell' | 'neutral' | 'unknown'
  final double? thresholdLow;
  final double? thresholdHigh;
  final String description;

  const OscillatorEntry({
    required this.name,
    this.value,
    this.signal = 'unknown',
    this.thresholdLow,
    this.thresholdHigh,
    this.description = '',
  });

  factory OscillatorEntry.fromJson(Map<String, dynamic> j) => OscillatorEntry(
        name:           j['name'] as String,
        value:          (j['value'] as num?)?.toDouble(),
        signal:         j['signal'] as String? ?? 'unknown',
        thresholdLow:   (j['threshold_low']  as num?)?.toDouble(),
        thresholdHigh:  (j['threshold_high'] as num?)?.toDouble(),
        description:    j['description'] as String? ?? '',
      );
}

class MovingAverageEntry {
  final String name;
  final int period;
  final String maType; // 'ema' | 'sma' | 'wma' | 'vwma' | 'hull' | 'ichimoku'
  final double? value;
  final String signal;  // 'above' | 'below' | 'unknown'
  final double? distancePct;

  const MovingAverageEntry({
    required this.name,
    required this.period,
    this.maType = 'ema',
    this.value,
    this.signal = 'unknown',
    this.distancePct,
  });

  factory MovingAverageEntry.fromJson(Map<String, dynamic> j) => MovingAverageEntry(
        name:        j['name']    as String,
        period:      j['period']  as int,
        maType:      j['ma_type'] as String? ?? 'ema',
        value:       (j['value']        as num?)?.toDouble(),
        signal:      j['signal']        as String? ?? 'unknown',
        distancePct: (j['distance_pct'] as num?)?.toDouble(),
      );
}

class PivotLevels {
  final String method; // 'classic' | 'fibonacci' | 'camarilla' | 'woodie' | 'demark'
  final String period;
  final double? r3, r2, r1, pp, s1, s2, s3;

  const PivotLevels({
    required this.method,
    this.period = '1d',
    this.r3, this.r2, this.r1, this.pp,
    this.s1, this.s2, this.s3,
  });

  factory PivotLevels.fromJson(Map<String, dynamic> j) => PivotLevels(
        method: j['method'] as String,
        period: j['period'] as String? ?? '1d',
        r3: (j['r3'] as num?)?.toDouble(),
        r2: (j['r2'] as num?)?.toDouble(),
        r1: (j['r1'] as num?)?.toDouble(),
        pp: (j['pp'] as num?)?.toDouble(),
        s1: (j['s1'] as num?)?.toDouble(),
        s2: (j['s2'] as num?)?.toDouble(),
        s3: (j['s3'] as num?)?.toDouble(),
      );
}

class TechnicalSummary {
  final String symbol;
  final String market;
  final String timeframe;

  final TechnicalRating overallRating;
  final TechnicalRating oscillatorRating;
  final TechnicalRating movingAverageRating;

  final List<OscillatorEntry> oscillators;
  final List<MovingAverageEntry> movingAverages;
  final List<PivotLevels> pivotLevels;

  final int warmupBarsUsed;
  final String calculationVersion;
  final DataTruth? dataTruth;
  final DateTime? calculatedAt;

  final List<String> warnings;

  const TechnicalSummary({
    required this.symbol,
    required this.market,
    required this.timeframe,
    this.overallRating = TechnicalRating.unknown,
    this.oscillatorRating = TechnicalRating.unknown,
    this.movingAverageRating = TechnicalRating.unknown,
    this.oscillators = const [],
    this.movingAverages = const [],
    this.pivotLevels = const [],
    this.warmupBarsUsed = 0,
    this.calculationVersion = '1.0',
    this.dataTruth,
    this.calculatedAt,
    this.warnings = const [],
  });

  factory TechnicalSummary.fromJson(Map<String, dynamic> j) => TechnicalSummary(
        symbol:    j['symbol']    as String,
        market:    j['market']    as String,
        timeframe: j['timeframe'] as String,
        overallRating:        TechnicalRating.fromJson(j['overall_rating']         as String?),
        oscillatorRating:     TechnicalRating.fromJson(j['oscillator_rating']      as String?),
        movingAverageRating:  TechnicalRating.fromJson(j['moving_average_rating']  as String?),
        oscillators: (j['oscillators'] as List<dynamic>?)
                ?.map((e) => OscillatorEntry.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        movingAverages: (j['moving_averages'] as List<dynamic>?)
                ?.map((e) => MovingAverageEntry.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        pivotLevels: (j['pivot_levels'] as List<dynamic>?)
                ?.map((e) => PivotLevels.fromJson(e as Map<String, dynamic>))
                .toList() ??
            [],
        warmupBarsUsed:    j['warmup_bars_used']    as int? ?? 0,
        calculationVersion: j['calculation_version'] as String? ?? '1.0',
        dataTruth: j['data_truth'] != null
            ? DataTruth.fromJson(j['data_truth'] as Map<String, dynamic>)
            : null,
        calculatedAt: j['calculated_at'] != null
            ? DateTime.tryParse(j['calculated_at'] as String)
            : null,
        warnings: (j['warnings'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );
}
