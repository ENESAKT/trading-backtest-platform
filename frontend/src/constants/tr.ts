// All Turkish UI string constants — single source of truth for localization.

export const TR = {
  // ── Navigation ──────────────────────────────────────────────────────────────
  APP_NAME: 'PiyasaPilot',
  CHART: 'Grafik',
  PORTFOLIO: 'Portföy',
  STRATEGY: 'Strateji',
  SCREENER: 'Tarama',

  // ── Connection Status ────────────────────────────────────────────────────────
  LIVE: 'CANLI',
  DELAYED: 'GECİKMELİ',
  OFFLINE: 'BAĞLANTI YOK',
  CONNECTING: 'BAĞLANIYOR',

  // ── Sidebar ──────────────────────────────────────────────────────────────────
  BIST30: 'BIST 30',
  BIST100: 'BIST 100',
  US_MARKETS: 'ABD Piyasaları',
  CRYPTO: 'Kripto',
  FX_COMMODITY: 'Döviz / Emtia',
  SEARCH_PLACEHOLDER: 'Sembol ara...',

  // ── Chart Controls ───────────────────────────────────────────────────────────
  LAST_UPDATE: 'Son Güncelleme',
  SECONDS_AGO: 'sn önce',
  MINUTES_AGO: 'dk önce',
  FULLSCREEN: 'Tam Ekran',
  EXIT_FULLSCREEN: 'Tam Ekrandan Çık',
  CHART_TYPE: 'Grafik Tipi',
  CANDLE: 'Mum',
  LINE: 'Çizgi',
  BAR: 'Bar',
  TIMEFRAME: 'Zaman Dilimi',
  INDICATORS: 'Göstergeler',
  VOLUME: 'Hacim',

  // ── Timeframe Labels ─────────────────────────────────────────────────────────
  TF_1M: '1D',
  TF_5M: '5D',
  TF_15M: '15D',
  TF_30M: '30D',
  TF_1H: '1S',
  TF_4H: '4S',
  TF_1D: '1G',
  TF_1W: '1H',

  // ── Indicator Names ──────────────────────────────────────────────────────────
  IND_RSI: 'RSI',
  IND_MACD: 'MACD',
  IND_BB: 'Bollinger Bantları',
  IND_EMA: 'EMA',
  IND_VWAP: 'VWAP',
  IND_STOCH: 'Stokastik',

  // ── Portfolio ────────────────────────────────────────────────────────────────
  TOTAL_VALUE: 'Toplam Değer',
  TOTAL_PNL: 'Toplam K/Z',
  CASH: 'Nakit',
  OPEN_POSITIONS: 'Açık Pozisyon',
  POSITIONS: 'Pozisyonlar',
  SYMBOL: 'Sembol',
  QUANTITY: 'Miktar',
  AVG_COST: 'Ort. Maliyet',
  CURRENT_PRICE: 'Güncel Fiyat',
  PNL: 'K/Z',
  PNL_PCT: 'K/Z %',
  CLOSE_POSITION: 'Kapat',
  BUY: 'AL',
  SELL: 'SAT',
  TRADE_FORM: 'İşlem Formu',
  TRADE_HISTORY: 'İşlem Geçmişi',
  DATE: 'Tarih',
  TYPE: 'Tür',
  PRICE: 'Fiyat',
  TOTAL: 'Toplam',
  EXECUTE: 'Uygula',
  PORTFOLIO_ALLOCATION: 'Portföy Dağılımı',
  MARKET_PRICE: 'Piyasa fiyatı',
  NO_POSITIONS: 'Açık pozisyon yok',
  NO_TRADES: 'İşlem geçmişi boş',

  // ── Strategy ─────────────────────────────────────────────────────────────────
  STRATEGY_TREND: 'Trend Takip',
  STRATEGY_MEAN: 'Ortalamaya Dönüş',
  STRATEGY_BREAKOUT: 'Kırılım',
  RETURN: 'Getiri',
  SHARPE: 'Sharpe',
  MAX_DRAWDOWN: 'Maks. Çöküş',
  WIN_RATE: 'Kazanma Oranı',
  TOTAL_TRADES: 'Toplam İşlem',
  PROFIT_FACTOR: 'Kâr Faktörü',
  SIGNALS: 'Sinyaller',
  EQUITY_CURVE: 'Özkaynak Eğrisi',
  RUNNING_BACKTEST: 'Backtest çalışıyor...',
  NO_SIGNALS: 'Henüz sinyal yok',
  SIGNAL_BUY: 'AL',
  SIGNAL_SELL: 'SAT',
  SIGNAL_STRONG_BUY: 'GÜÇLÜ AL',
  SIGNAL_STRONG_SELL: 'GÜÇLÜ SAT',
  SIGNAL_HOLD: 'TUT',
  STRATEGY_DESC_TREND: 'EMA çakışması + RSI momentum tabanlı trend takip stratejisi',
  STRATEGY_DESC_MEAN: 'Bollinger Bandı alt/üst dokunuşlarında ortalamaya dönüş',
  STRATEGY_DESC_BREAKOUT: 'ATR konsolidasyonu sonrası hacimli kırılım tespiti',
  STRATEGY_DONCHIAN: 'Donchian Kırılımı',
  STRATEGY_DESC_DONCHIAN: 'Donchian kanalı üst bandı kırılımında AL, alt bandı kırılımında SAT',
  STRATEGY_MACD: 'MACD Kesişimi',
  STRATEGY_DESC_MACD: 'MACD çizgisi sinyal çizgisini yukarı kesince AL, aşağı kesince SAT',
  STRATEGY_SUPERTREND: 'Supertrend',
  STRATEGY_DESC_SUPERTREND: 'ATR tabanlı trend takip göstergesi; yön dönüşünde işlem',
  STRATEGY_VWAP: 'VWAP Geri Dönüş',
  STRATEGY_DESC_VWAP: "VWAP'dan sapma bölgelerinde ortalamaya dönüş stratejisi",
  STRATEGY_LGBM: 'LightGBM',
  STRATEGY_DESC_LGBM: 'Eğitilmiş model varsa yükseliş olasılığıyla AL/SAT filtresi',
  PAPER_TRADING: 'Sanal İşlemler',
  WALLETS: 'Sanal Cüzdanlar',
  WALLET_HALTED: 'DONDURULDU',
  DAILY_PNL: 'Günlük K/Z',
  EQUITY: 'Özkaynak',
  UNREALIZED_PNL: 'Gerçekleşmemiş K/Z',
  RESET_WALLET: 'Sıfırla',
  NO_WALLETS: 'Henüz sinyal gelmedi — cüzdan oluşturulmadı',
  SIGNAL_FEED: 'Sinyaller',
  SIGNAL_FEED_INFO: 'Tüm semboller · Tüm stratejiler · Her bar kapanışında güncellenir',
  SIGNAL_FEED_EMPTY: 'Henüz sinyal yok',

  // ── Screener ─────────────────────────────────────────────────────────────────
  SCREENER_TITLE: 'Piyasa Tarayıcı',
  FILTER: 'Filtre',
  RSI_OVERSOLD: 'RSI Aşırı Satım (< 30)',
  RSI_OVERBOUGHT: 'RSI Aşırı Alım (> 70)',
  EMA_BULLISH: 'EMA Yükseliş Çakışması',
  BB_LOWER: 'Alt Bollinger Bandı (±1%)',
  HIGH_VOLUME: 'Yüksek Hacim (>%50 ort.)',
  EMA_SIGNAL: 'EMA Sinyali',
  BB_POSITION: 'BB Konumu',
  VOLUME_ALERT: 'Hacim Uyarısı',
  ALERTS: 'Uyarılar',
  CHANGE_PCT: 'Değişim %',
  SCAN: 'Tara',
  SCANNING: 'Taranıyor...',
  NO_RESULTS: 'Filtrelerle eşleşen sembol bulunamadı',
  ALL_FILTERS: 'Tüm Filtreler',
  EMA_UP: 'Yükseliş',
  EMA_DOWN: 'Düşüş',
  EMA_NEUTRAL: 'Nötr',
  BB_LOWER_LABEL: 'Alt Band',
  BB_UPPER_LABEL: 'Üst Band',
  BB_MID_LABEL: 'Orta',
  BB_NORMAL: 'Normal',

  // ── Errors ───────────────────────────────────────────────────────────────────
  DATA_NOT_AVAILABLE: 'Veri mevcut değil',
  CONNECTION_ERROR: 'Bağlantı hatası',
  INSUFFICIENT_CASH: 'Yetersiz nakit',
  INVALID_QUANTITY: 'Geçersiz miktar',
  SYMBOL_NOT_FOUND: 'Sembol bulunamadı',
  INSUFFICIENT_POSITION: 'Yetersiz pozisyon miktarı',
  LOADING: 'Yükleniyor...',
  NO_DATA: 'Veri yok',
  WAITING_DATA: 'Veri bekleniyor...',
  API_ERROR: 'API hatası',

  // ── G7: Multi-chart Sync ──────────────────────────────────────────────────
  SYNC_LOCKS: 'Senkronizasyon',
  SYNC_SYMBOL: 'Sembol',
  SYNC_TIMEFRAME: 'Zaman Dilimi',
  SYNC_RANGE: 'Zaman Aralığı',
  SYNC_CROSSHAIR: 'İmleç',
  SYNC_SCALE: 'Ölçek',

  // ── G8: Chart Templates ───────────────────────────────────────────────────
  TEMPLATES: 'Şablonlar',
  SAVE_TEMPLATE: 'Şablonu Kaydet',
  LOAD_TEMPLATE: 'Şablonu Yükle',
  DEFAULT_TEMPLATE: 'Varsayılan Yap',
  RESET_TEMPLATE: 'Sıfırla',
  EXPORT_CHART: 'Dışa Aktar',
  EXPORT_CSV: 'CSV (OHLCV)',
  EXPORT_PNG: 'PNG (Resim)',
  TEMPLATE_NAME: 'Şablon Adı',

  // ── G9: Event Markers ─────────────────────────────────────────────────────
  EVENTS: 'Olaylar',
  EVENT_ALL: 'Tümü',
  EVENT_HABER: 'Haber',
  EVENT_KAP: 'KAP',
  EVENT_BILANCO: 'Bilanço',
  EVENT_TEMETTU: 'Temettü',
  EVENT_SERMAYE: 'Sermaye',
  EVENT_SOURCE: 'Kaynak',
  EVENT_DATE: 'Tarih',
  EVENT_SAMPLE: 'Örnek olay verisi',
  EVENT_NO_SOURCE: 'Kaynak bağlı değil',
  EVENT_OPEN_FINANCIAL: 'Mali Analizi Aç',

  // ── G10: Advanced Drawing Tools ───────────────────────────────────────────
  DRAWING_FIBONACCI: 'Fibonacci Düzeltme',
  DRAWING_FIBONACCI_EXT: 'Fibonacci Uzantı',
  DRAWING_REGRESSION: 'Regresyon Kanalı',
  DRAWING_RENKO: 'Renko (Yakında)',
  DRAWING_ADVANCED: 'İleri Araçlar',

  // ── General ──────────────────────────────────────────────────────────────────
  YES: 'Evet',
  NO: 'Hayır',
  CANCEL: 'İptal',
  // ── Mali Analiz (Financial Analysis) ──────────────────────────────────────
  FINANCIALS: 'Mali Analiz',
  FIN_SUMMARY: 'Özet',
  FIN_RATIOS: 'Finansal Oranlar',
  FIN_STATEMENTS: 'Mali Tablolar',
  FIN_SEARCH_PLACEHOLDER: 'Sembol ara (örn: THYAO)',
  FIN_SOURCE_CONNECTED: 'Bağlı',
  FIN_SOURCE_MOCK: 'Mock Veri',
  FIN_SOURCE_ERROR: 'Bağlantı Hatası',
  FIN_SOURCE_EMPTY: 'Veri Yok',
  FIN_PERIODS: 'Dönemler',
  FIN_BALANCE_SHEET: 'Bilanço',
  FIN_INCOME_STATEMENT: 'Gelir Tablosu',
  FIN_NO_DATA: 'Veri bulunamadı veya kaynak bağlı değil.',
  FIN_OPEN_CHART: 'Grafikte Aç',
  FIN_ADD_BACKTEST: 'Backtest\'e Ekle',
} as const;

export type TRKey = keyof typeof TR;

// ─── Number & Date Formatters (Turkish Locale) ────────────────────────────────

export function formatNumber(value: number, decimals = 2): string {
  return value.toLocaleString('tr-TR', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export function formatCurrency(value: number, currency = '₺', decimals = 2): string {
  return `${currency}${formatNumber(value, decimals)}`;
}

export function formatPct(value: number, decimals = 2): string {
  const rounded = Number(value.toFixed(decimals));
  if (Object.is(rounded, -0) || rounded === 0) return `${formatNumber(0, decimals)}%`;
  const sign = rounded > 0 ? '+' : '';
  return `${sign}${formatNumber(rounded, decimals)}%`;
}

export function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}

export function formatDateTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString('tr-TR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString('tr-TR', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  });
}

export function formatAgo(seconds: number): string {
  if (seconds < 60) return `${Math.round(seconds)} ${TR.SECONDS_AGO}`;
  return `${Math.round(seconds / 60)} ${TR.MINUTES_AGO}`;
}
