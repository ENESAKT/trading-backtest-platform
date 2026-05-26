/// SymbolSnapshot — sembol anlık durum kartı.
///
/// İzleme listesi ve Sembol 360 başlığı için kullanılır.
/// Backend SymbolSnapshot Pydantic modeli ile hizalıdır (Bölüm 18.14).
library;

import 'data_truth.dart';

enum SessionStatus {
  open,
  closed,
  pre,
  post,
  unknown;

  static SessionStatus fromJson(String? v) => switch (v) {
        'open'   => open,
        'closed' => closed,
        'pre'    => pre,
        'post'   => post,
        _        => unknown,
      };
}

class SymbolSnapshot {
  final String symbol;
  final String market;
  final String? name;
  final String? sector;
  final String instrumentType;

  final double? lastPrice;
  final double? prevClose;
  final double? changePct1d;
  final double? high52w;
  final double? low52w;

  final SessionStatus sessionStatus;
  final DateTime? lastBarTs;

  final DataTruth? dataTruth;

  final double? peRatio;
  final double? pbRatio;
  final double? marketCap;
  final double? epsTtm;
  final double? dividendYield;

  final List<String> warnings;

  const SymbolSnapshot({
    required this.symbol,
    required this.market,
    this.name,
    this.sector,
    this.instrumentType = 'stock',
    this.lastPrice,
    this.prevClose,
    this.changePct1d,
    this.high52w,
    this.low52w,
    this.sessionStatus = SessionStatus.unknown,
    this.lastBarTs,
    this.dataTruth,
    this.peRatio,
    this.pbRatio,
    this.marketCap,
    this.epsTtm,
    this.dividendYield,
    this.warnings = const [],
  });

  factory SymbolSnapshot.fromJson(Map<String, dynamic> j) => SymbolSnapshot(
        symbol:         j['symbol'] as String,
        market:         j['market'] as String,
        name:           j['name'] as String?,
        sector:         j['sector'] as String?,
        instrumentType: j['instrument_type'] as String? ?? 'stock',
        lastPrice:      (j['last_price'] as num?)?.toDouble(),
        prevClose:      (j['prev_close'] as num?)?.toDouble(),
        changePct1d:    (j['change_pct_1d'] as num?)?.toDouble(),
        high52w:        (j['high_52w'] as num?)?.toDouble(),
        low52w:         (j['low_52w'] as num?)?.toDouble(),
        sessionStatus:  SessionStatus.fromJson(j['session_status'] as String?),
        lastBarTs:      j['last_bar_ts'] != null
            ? DateTime.tryParse(j['last_bar_ts'] as String)
            : null,
        dataTruth: j['data_truth'] != null
            ? DataTruth.fromJson(j['data_truth'] as Map<String, dynamic>)
            : null,
        peRatio:       (j['pe_ratio']       as num?)?.toDouble(),
        pbRatio:       (j['pb_ratio']       as num?)?.toDouble(),
        marketCap:     (j['market_cap']     as num?)?.toDouble(),
        epsTtm:        (j['eps_ttm']        as num?)?.toDouble(),
        dividendYield: (j['dividend_yield'] as num?)?.toDouble(),
        warnings: (j['warnings'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );
}
