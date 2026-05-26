/// Screener kontrat modelleri.
///
/// Backend ScreenerRunRequest / ScreenerRunResponse ile hizalıdır (Bölüm 18.14).
library;

import 'data_truth.dart';

class ScreenerFilterRule {
  final String field;
  final String operator; // 'gt' | 'gte' | 'lt' | 'lte' | 'eq' | 'neq' | 'in' | 'not_in'
  final dynamic value;

  const ScreenerFilterRule({
    required this.field,
    required this.operator,
    required this.value,
  });

  Map<String, dynamic> toJson() => {
        'field':    field,
        'operator': operator,
        'value':    value,
      };
}

class ScreenerSort {
  final String field;
  final String direction; // 'asc' | 'desc'

  const ScreenerSort({required this.field, this.direction = 'desc'});

  Map<String, dynamic> toJson() => {'field': field, 'direction': direction};
}

class ScreenerRunRequest {
  final String market;
  final List<String> universe;
  final List<ScreenerFilterRule> filters;
  final List<String> columns;
  final ScreenerSort? sort;
  final int limit;
  final DateTime? snapshotTime;

  const ScreenerRunRequest({
    this.market = 'BIST',
    this.universe = const [],
    this.filters = const [],
    this.columns = const [],
    this.sort,
    this.limit = 50,
    this.snapshotTime,
  });

  Map<String, dynamic> toJson() => {
        'market':        market,
        'universe':      universe,
        'filters':       filters.map((f) => f.toJson()).toList(),
        'columns':       columns,
        if (sort != null) 'sort': sort!.toJson(),
        'limit':         limit,
        if (snapshotTime != null) 'snapshot_time': snapshotTime!.toIso8601String(),
      };
}

class ScreenerRow {
  final String symbol;
  final String? name;
  final String market;
  final String? sector;
  final double? lastPrice;
  final double? changePct1d;
  final double? volume;
  final double? marketCap;
  final String qualityBadge;
  final Map<String, dynamic> columns;

  const ScreenerRow({
    required this.symbol,
    this.name,
    required this.market,
    this.sector,
    this.lastPrice,
    this.changePct1d,
    this.volume,
    this.marketCap,
    this.qualityBadge = 'unknown',
    this.columns = const {},
  });

  factory ScreenerRow.fromJson(Map<String, dynamic> j) => ScreenerRow(
        symbol:       j['symbol'] as String,
        name:         j['name']   as String?,
        market:       j['market'] as String,
        sector:       j['sector'] as String?,
        lastPrice:    (j['last_price']    as num?)?.toDouble(),
        changePct1d:  (j['change_pct_1d'] as num?)?.toDouble(),
        volume:       (j['volume']        as num?)?.toDouble(),
        marketCap:    (j['market_cap']    as num?)?.toDouble(),
        qualityBadge: j['quality_badge'] as String? ?? 'unknown',
        columns:      (j['columns'] as Map<String, dynamic>?) ?? {},
      );
}

class ScreenerRunResponse {
  final String runId;
  final DateTime createdAt;
  final String filtersHash;
  final String dataSnapshotHash;
  final String market;
  final int totalCount;
  final List<ScreenerRow> rows;
  final DataTruth? dataTruth;
  final List<String> warnings;

  const ScreenerRunResponse({
    required this.runId,
    required this.createdAt,
    required this.filtersHash,
    required this.dataSnapshotHash,
    required this.market,
    required this.totalCount,
    required this.rows,
    this.dataTruth,
    this.warnings = const [],
  });

  factory ScreenerRunResponse.fromJson(Map<String, dynamic> j) =>
      ScreenerRunResponse(
        runId:             j['run_id']              as String,
        createdAt:         DateTime.parse(j['created_at'] as String),
        filtersHash:       j['filters_hash']        as String,
        dataSnapshotHash:  j['data_snapshot_hash']  as String,
        market:            j['market']              as String,
        totalCount:        j['total_count']         as int,
        rows: (j['rows'] as List<dynamic>)
            .map((e) => ScreenerRow.fromJson(e as Map<String, dynamic>))
            .toList(),
        dataTruth: j['data_truth'] != null
            ? DataTruth.fromJson(j['data_truth'] as Map<String, dynamic>)
            : null,
        warnings: (j['warnings'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );
}
