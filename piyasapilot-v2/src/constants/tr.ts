// All Turkish UI string constants — single source of truth for localization.

export const TR = {
  // ── Navigation ──────────────────────────────────────────────────────────────
  APP_NAME: 'PiyasaPilot',
  CHART: 'Grafik',
  PORTFOLIO: 'Portföy',
  STRATEGY: 'Strateji',
  SCREENER: 'Tarayıcı',

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
  SIGNAL_HOLD: 'TUT',
  STRATEGY_DESC_TREND: 'EMA çakışması + RSI momentum tabanlı trend takip stratejisi',
  STRATEGY_DESC_MEAN: 'Bollinger Bandı alt/üst dokunuşlarında ortalamaya dönüş',
  STRATEGY_DESC_BREAKOUT: 'ATR konsolidasyonu sonrası hacimli kırılım tespiti',

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

  // ── General ──────────────────────────────────────────────────────────────────
  YES: 'Evet',
  NO: 'Hayır',
  CANCEL: 'İptal',
  CONFIRM: 'Onayla',
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
  const sign = value >= 0 ? '+' : '';
  return `${sign}${formatNumber(value, decimals)}%`;
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
