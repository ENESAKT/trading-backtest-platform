/// DataTruth — her veri yanıtına eklenen kalite ve soy ağacı bilgisi.
///
/// Backend'deki DataTruth Pydantic modeli ve frontend types.ts ile
/// birebir alan uyumu sağlar (Bölüm 18.14).
library;

enum DataSourceType {
  licensed,
  exchangePublic,
  broker,
  cache,
  importedCsv,
  sample,
  unknown;

  static DataSourceType fromJson(String? v) => switch (v) {
        'licensed'        => licensed,
        'exchange_public' => exchangePublic,
        'broker'          => broker,
        'cache'           => cache,
        'imported_csv'    => importedCsv,
        'sample'          => sample,
        _                 => unknown,
      };
}

enum DataQualityStatus {
  ok,
  warning,
  blocked,
  unknown;

  static DataQualityStatus fromJson(String? v) => switch (v) {
        'ok'      => ok,
        'warning' => warning,
        'blocked' => blocked,
        _         => unknown,
      };
}

class DataTruth {
  final String symbol;
  final String market;
  final String timeframe;

  final String provider;
  final DataSourceType sourceType;

  final bool isReal;
  final bool isLive;
  final bool isDelayed;
  final int delayMinutes;

  final DateTime? fetchedAt;
  final DateTime? firstBarTs;
  final DateTime? lastBarTs;
  final DateTime? lastProviderTs;
  final int stalenessSeconds;

  final DataQualityStatus qualityStatus;
  final double coveragePct;
  final int gapCount;
  final int duplicateCount;
  final int outlierCount;

  final bool adjustedForSplits;
  final bool adjustedForDividends;

  final bool isDerived;
  final String sourceTimeframe;
  final String derivationMethod;

  final String licenseNote;
  final List<String> warnings;

  const DataTruth({
    required this.symbol,
    required this.market,
    required this.timeframe,
    this.provider = 'unknown',
    this.sourceType = DataSourceType.unknown,
    this.isReal = false,
    this.isLive = false,
    this.isDelayed = false,
    this.delayMinutes = 0,
    this.fetchedAt,
    this.firstBarTs,
    this.lastBarTs,
    this.lastProviderTs,
    this.stalenessSeconds = 0,
    this.qualityStatus = DataQualityStatus.unknown,
    this.coveragePct = 0.0,
    this.gapCount = 0,
    this.duplicateCount = 0,
    this.outlierCount = 0,
    this.adjustedForSplits = false,
    this.adjustedForDividends = false,
    this.isDerived = false,
    this.sourceTimeframe = '',
    this.derivationMethod = '',
    this.licenseNote = '',
    this.warnings = const [],
  });

  factory DataTruth.unknown({
    required String symbol,
    required String market,
    required String timeframe,
  }) =>
      DataTruth(
        symbol: symbol,
        market: market,
        timeframe: timeframe,
        qualityStatus: DataQualityStatus.unknown,
        warnings: const ['Veri metadata bilgisi alınamadı. Sonuçlar doğrulanmamıştır.'],
      );

  factory DataTruth.fromJson(Map<String, dynamic> j) => DataTruth(
        symbol:              j['symbol']    as String? ?? '',
        market:              j['market']    as String? ?? '',
        timeframe:           j['timeframe'] as String? ?? '',
        provider:            j['provider']  as String? ?? 'unknown',
        sourceType:          DataSourceType.fromJson(j['source_type'] as String?),
        isReal:              j['is_real']    as bool? ?? false,
        isLive:              j['is_live']    as bool? ?? false,
        isDelayed:           j['is_delayed'] as bool? ?? false,
        delayMinutes:        j['delay_minutes']     as int? ?? 0,
        fetchedAt:           _parseDateTime(j['fetched_at']),
        firstBarTs:          _parseDateTime(j['first_bar_ts']),
        lastBarTs:           _parseDateTime(j['last_bar_ts']),
        lastProviderTs:      _parseDateTime(j['last_provider_ts']),
        stalenessSeconds:    j['staleness_seconds']  as int? ?? 0,
        qualityStatus:       DataQualityStatus.fromJson(j['quality_status'] as String?),
        coveragePct:         (j['coverage_pct'] as num?)?.toDouble() ?? 0.0,
        gapCount:            j['gap_count']       as int? ?? 0,
        duplicateCount:      j['duplicate_count'] as int? ?? 0,
        outlierCount:        j['outlier_count']   as int? ?? 0,
        adjustedForSplits:    j['adjusted_for_splits']    as bool? ?? false,
        adjustedForDividends: j['adjusted_for_dividends'] as bool? ?? false,
        isDerived:           j['is_derived']        as bool? ?? false,
        sourceTimeframe:     j['source_timeframe']  as String? ?? '',
        derivationMethod:    j['derivation_method'] as String? ?? '',
        licenseNote:         j['license_note'] as String? ?? '',
        warnings: (j['warnings'] as List<dynamic>?)
                ?.map((e) => e as String)
                .toList() ??
            [],
      );

  static DateTime? _parseDateTime(dynamic v) =>
      v == null ? null : DateTime.tryParse(v as String);
}
