/* PiyasaPilot — mock data */

const WATCHLIST = [
  { sym: 'ARCLK', name: 'Arçelik', px: 111.90, chg: -0.36, fav: true },
  { sym: 'AKBNK', name: 'Akbank',  px: 73.20,  chg: -0.68, fav: true },
  { sym: 'ASELS', name: 'Aselsan', px: 145.30, chg: 0.00,  fav: true },
  { sym: 'VAKBN', name: 'Vakıfbank', px: 31.66, chg: 1.02, fav: true, active: true },
  { sym: 'BRYAT', name: 'Borusan Yatırım', px: 84.50, chg: 0.00, fav: true },
  { sym: 'THYAO', name: 'Türk Hava Yolları', px: 312.40, chg: 2.14, fav: true },
  { sym: 'GARAN', name: 'Garanti BBVA', px: 119.80, chg: 0.84, fav: true },
];

const TICKER = [
  { sym: 'BIST 100', px: '10,847.32', chg: '+1.24%', dir: 'up' },
  { sym: 'BIST 30', px: '11,932.18', chg: '+0.92%', dir: 'up' },
  { sym: 'USDTRY', px: '34.218', chg: '+0.08%', dir: 'up' },
  { sym: 'EURTRY', px: '37.142', chg: '-0.12%', dir: 'down' },
  { sym: 'GBPTRY', px: '43.880', chg: '+0.21%', dir: 'up' },
  { sym: 'XAU/USD', px: '2,418.50', chg: '-0.34%', dir: 'down' },
  { sym: 'BRENT', px: '78.42', chg: '+1.18%', dir: 'up' },
  { sym: 'BTC', px: '67,142', chg: '+2.41%', dir: 'up' },
  { sym: 'ETH', px: '2,329.46', chg: '+1.83%', dir: 'up' },
  { sym: 'VIX', px: '14.82', chg: '-2.10%', dir: 'down' },
  { sym: 'DXY', px: '102.84', chg: '+0.04%', dir: 'up' },
  { sym: 'TLREF', px: '49.84', chg: '0.00%', dir: 'flat' },
];

const NAV_TABS = [
  { id: 'grafik',    label: 'Grafik',    code: 'F1', shortcut: '1' },
  { id: 'portfoy',   label: 'Portföy',   code: 'F2', shortcut: '2' },
  { id: 'strateji',  label: 'Strateji',  code: 'F3', shortcut: '3' },
  { id: 'tarayici',  label: 'Tarayıcı',  code: 'F4', shortcut: '4' },
  { id: 'sinyaller', label: 'Sinyaller', code: 'F5', shortcut: '5' },
  { id: 'egitim',    label: 'Eğitimler', code: 'F6', shortcut: '6' },
  { id: 'mali',      label: 'Mali Analiz', code: 'F7', shortcut: '7' },
];

// generate candle series — pseudo-random walk
function genCandles(n, start, vol) {
  const out = [];
  let p = start;
  for (let i = 0; i < n; i++) {
    const drift = (Math.sin(i * 0.13) + Math.cos(i * 0.07)) * vol * 0.3;
    const noise = (Math.random() - 0.5) * vol;
    const open = p;
    const close = Math.max(0.1, p + drift + noise);
    const high = Math.max(open, close) + Math.random() * vol * 0.4;
    const low = Math.min(open, close) - Math.random() * vol * 0.4;
    const volume = Math.abs(Math.sin(i * 0.2)) * 1000000 + Math.random() * 500000;
    out.push({ open, close, high, low, volume, i });
    p = close;
  }
  return out;
}

const CANDLES_VAKBN = genCandles(140, 28, 1.2);
const CANDLES_AKBNK = genCandles(140, 70, 2.4);
const CANDLES_ARCLK = genCandles(140, 115, 4.5);
const CANDLES_ASELS = genCandles(140, 130, 8);

// equity curve — declining (overfit test)
function genEquity(n) {
  const out = [];
  let v = 10000;
  for (let i = 0; i < n; i++) {
    if (i < 20) v += (Math.random() - 0.3) * 200;
    else v -= (Math.random() * 250 + 50);
    out.push(Math.max(0, v));
  }
  return out;
}
const EQUITY = genEquity(120);

function genDrawdown(eq) {
  let peak = eq[0];
  return eq.map(v => {
    peak = Math.max(peak, v);
    return peak === 0 ? 0 : (v - peak) / peak * 100;
  });
}
const DRAWDOWN = genDrawdown(EQUITY);

const WALLETS = [
  { name: 'sma_crossover',       cash: 342.15,    pl: -9657.85,  plPct: -96.58, today: 0,    state: 'live' },
  { name: 'macd_divergence',     cash: 163.52,    pl: -9836.48,  plPct: -98.36, today: 0,    state: 'live' },
  { name: 'rsi_reversion',       cash: 6558.08,   pl: -3441.92,  plPct: -34.42, today: 0,    state: 'paused' },
  { name: 'donchian_breakout',   cash: 96.50,     pl: -9903.50,  plPct: -99.03, today: 0,    state: 'live' },
  { name: 'bollinger_reversion', cash: 1849.73,   pl: -8150.27,  plPct: -81.50, today: 0,    state: 'live' },
  { name: 'mean_reversion_vwap', cash: 5901.62,   pl: -4098.38,  plPct: -40.98, today: 0,    state: 'paused' },
  { name: 'atr_trend',           cash: 12480.40,  pl: 2480.40,   plPct: 24.80,  today: 142,  state: 'live' },
  { name: 'pivot_breakout',      cash: 8920.10,   pl: -1079.90,  plPct: -10.80, today: -42,  state: 'live' },
];

const TRADES = [
  { date: '05.05.2026 15:30', strat: 'macd_divergence',    sym: 'XRPUSDT', side: 'AL',  px: 1.4099,  qty: 12.8882,  pl: null },
  { date: '05.05.2026 15:30', strat: 'donchian_breakout',  sym: 'XRPUSDT', side: 'AL',  px: 1.4099,  qty: 7.6061,   pl: null },
  { date: '05.05.2026 14:18', strat: 'sma_crossover',      sym: 'BTCUSDT', side: 'SAT', px: 67142.0, qty: 0.0148,   pl: -284.40 },
  { date: '05.05.2026 13:42', strat: 'rsi_reversion',      sym: 'AKBNK',   side: 'AL',  px: 73.18,   qty: 145,      pl: null },
  { date: '05.05.2026 12:09', strat: 'atr_trend',          sym: 'VAKBN',   side: 'AL',  px: 31.42,   qty: 320,      pl: null },
  { date: '05.05.2026 11:50', strat: 'bollinger_reversion',sym: 'ETHUSDT', side: 'SAT', px: 2329.46, qty: 0.85,     pl: 142.30 },
  { date: '05.05.2026 11:33', strat: 'macd_divergence',    sym: 'THYAO',   side: 'AL',  px: 312.40,  qty: 30,       pl: null },
  { date: '05.05.2026 10:12', strat: 'pivot_breakout',     sym: 'ARCLK',   side: 'SAT', px: 112.40,  qty: 80,       pl: -42.00 },
  { date: '05.05.2026 09:48', strat: 'donchian_breakout',  sym: 'ASELS',   side: 'AL',  px: 144.85,  qty: 60,       pl: null },
  { date: '04.05.2026 17:40', strat: 'sma_crossover',      sym: 'GARAN',   side: 'SAT', px: 119.20,  qty: 100,      pl: 84.00 },
];

const SIGNALS = [
  { sym: 'SOLUSDT',  px: 84.2680,    strat: 'donchian_breakout', side: 'AL', tf: '15m', t: '17:14:58', strength: 5, note: 'BUY @ 84.26' },
  { sym: 'DOGEUSDT', px: 0.189270,   strat: 'donchian_breakout', side: 'AL', tf: '15m', t: '17:14:58', strength: 4, note: 'BUY @ 0.19' },
  { sym: 'DOTUSDT',  px: 1.2180,     strat: 'sma_crossover',     side: 'AL', tf: '15m', t: '17:14:58', strength: 5, note: 'BUY @ 1.22' },
  { sym: 'AVAXUSDT', px: 9.1100,     strat: 'sma_crossover',     side: 'AL', tf: '15m', t: '17:14:58', strength: 3, note: 'BUY @ 9.11' },
  { sym: 'ETHUSDT',  px: 2329.46,    strat: 'donchian_breakout', side: 'AL', tf: '15m', t: '17:14:58', strength: 5, note: 'BUY @ 2329.46' },
  { sym: 'BTCUSDT',  px: 78856.80,   strat: 'donchian_breakout', side: 'AL', tf: '15m', t: '17:14:58', strength: 5, note: 'BUY @ 78856.80' },
  { sym: 'LINKUSDT', px: 11.42,      strat: 'rsi_reversion',     side: 'SAT',tf: '1h',  t: '17:12:14', strength: 4, note: 'SELL @ 11.42 — RSI 78' },
  { sym: 'AKBNK',    px: 73.20,      strat: 'macd_divergence',   side: 'AL', tf: '1d',  t: '17:08:02', strength: 4, note: 'BUY @ 73.20' },
  { sym: 'VAKBN',    px: 31.66,      strat: 'atr_trend',         side: 'AL', tf: '4h',  t: '16:55:30', strength: 5, note: 'BUY @ 31.66 — ATR breakout' },
  { sym: 'THYAO',    px: 312.40,     strat: 'pivot_breakout',    side: 'AL', tf: '1h',  t: '16:48:11', strength: 3, note: 'BUY @ 312.40' },
  { sym: 'GARAN',    px: 119.20,     strat: 'bollinger_reversion', side: 'SAT', tf: '15m', t: '16:42:00', strength: 4, note: 'SELL @ 119.20' },
  { sym: 'ARCLK',    px: 111.90,     strat: 'sma_crossover',     side: 'SAT',tf: '1d',  t: '16:30:44', strength: 3, note: 'SELL @ 111.90' },
];

const ARTICLES = [
  { id: 1, title: 'ADX / ADXR — Yön Hareketi',           cat: 'İndikatörler', level: 'orta',       active: true,
    tags: ['trend', 'yön', 'güç', 'filtre', 'adx'], src: 'yüksek' },
  { id: 2, title: 'Aktif vs Pasif Yatırım',              cat: 'Psikoloji & Disiplin', level: 'başlangıç' },
  { id: 3, title: 'Algoritmik Trade Nedir?',             cat: 'Sistem & Backtest', level: 'başlangıç' },
  { id: 4, title: 'ATR — Ortalama Gerçek Aralık',        cat: 'İndikatörler', level: 'orta' },
  { id: 5, title: 'Backtest Nasıl Yapılır?',             cat: 'Sistem & Backtest', level: 'orta' },
  { id: 6, title: 'Backtest Tuzakları: Overfit, Lookahead, Data Bias', cat: 'Sistem & Backtest', level: 'ileri' },
  { id: 7, title: 'Bayrak ve Flama',                     cat: 'Formasyonlar', level: 'orta' },
  { id: 8, title: 'Bollinger Bandı',                     cat: 'İndikatörler', level: 'başlangıç' },
  { id: 9, title: 'CCI — Emtia Kanal Endeksi',           cat: 'İndikatörler', level: 'orta' },
  { id: 10, title: 'Çift Tepe / Çift Dip',                cat: 'Formasyonlar', level: 'orta' },
  { id: 11, title: 'Donchian Channel',                    cat: 'İndikatörler', level: 'orta' },
  { id: 12, title: 'EMA vs SMA',                          cat: 'İndikatörler', level: 'başlangıç' },
  { id: 13, title: 'Fibonacci Düzeltmesi',                cat: 'Formasyonlar', level: 'orta' },
  { id: 14, title: 'Heikin-Ashi Mumları',                 cat: 'İndikatörler', level: 'orta' },
  { id: 15, title: 'Ichimoku Kinko Hyo',                  cat: 'İndikatörler', level: 'ileri' },
  { id: 16, title: 'Kayıp Aversiyonu — Risk Yönetimi',    cat: 'Psikoloji & Disiplin', level: 'orta' },
  { id: 17, title: 'Kelebek (Butterfly) Formasyonu',      cat: 'Formasyonlar', level: 'ileri' },
  { id: 18, title: 'MACD',                                cat: 'İndikatörler', level: 'başlangıç' },
  { id: 19, title: 'Monte Carlo Simülasyonu',             cat: 'Sistem & Backtest', level: 'ileri' },
  { id: 20, title: 'Omuz Baş Omuz',                       cat: 'Formasyonlar', level: 'orta' },
];

const COMPANIES = [
  { sym: 'AKBNK', name: 'Akbank T.A.Ş.' },
  { sym: 'ARCLK', name: 'Arçelik A.Ş.' },
  { sym: 'ASELS', name: 'Aselsan Elektronik Sanayi ve Ticaret A.Ş.' },
  { sym: 'BIMAS', name: 'BİM Birleşik Mağazalar A.Ş.' },
  { sym: 'EREGL', name: 'Ereğli Demir ve Çelik Fabrikaları T.A.Ş.' },
  { sym: 'GARAN', name: 'Türkiye Garanti Bankası A.Ş.' },
  { sym: 'ISCTR', name: 'Türkiye İş Bankası A.Ş.' },
  { sym: 'KCHOL', name: 'Koç Holding A.Ş.' },
  { sym: 'SAHOL', name: 'Hacı Ömer Sabancı Holding A.Ş.' },
  { sym: 'THYAO', name: 'Türk Hava Yolları A.O.', active: true },
  { sym: 'TUPRS', name: 'Tüpraş Türkiye Petrol Rafinerileri A.Ş.' },
  { sym: 'VAKBN', name: 'Türkiye Vakıflar Bankası T.A.O.' },
];

// THYAO mock fundamentals
const THYAO_FIN = {
  marketCap: '486.4B',
  shares: '1.38B',
  freeFloat: '49.12%',
  peRatio: 4.82,
  pbRatio: 1.14,
  evEbitda: 5.21,
  divYield: 0.00,
  beta: 1.34,
  rev: { '2025': 18420, '2024': 14982, '2023': 11240, '2022': 9840, '2021': 6420 }, // M USD
  ebitda: { '2025': 4980, '2024': 3812, '2023': 2640, '2022': 2120, '2021': 1080 },
  netIncome: { '2025': 2840, '2024': 2104, '2023': 1820, '2022': 1480, '2021': 290 },
  margin: { '2025': 27.0, '2024': 25.4, '2023': 23.5, '2022': 21.5, '2021': 16.8 },
};

const SCANNER_PRESETS = [
  { id: 'rsi_oversold',   label: 'RSI Aşırı Satım', expr: 'RSI(14) < 30', count: 8 },
  { id: 'rsi_overbought', label: 'RSI Aşırı Alım',  expr: 'RSI(14) > 70', count: 12 },
  { id: 'ema_breakout',   label: 'EMA Yükseliş Çakışması', expr: 'C > EMA(50) AND EMA(50) > EMA(200)', count: 24 },
  { id: 'bb_lower',       label: 'Alt Bollinger Bandı', expr: 'C ≤ BB_LOWER(20,2)', count: 6 },
  { id: 'high_vol',       label: 'Yüksek Hacim', expr: 'V > AVG(V, 50) × 2', count: 18 },
];

const SCANNER_RESULTS = [
  { sym: 'AKBNK', name: 'Akbank',         px: 73.20,  chg: -0.68, vol: '142.4M', rsi: 28.4, atr: 1.84, score: 92, sig: 'STRONG_BUY' },
  { sym: 'GARAN', name: 'Garanti BBVA',   px: 119.80, chg: 0.84,  vol: '198.2M', rsi: 31.2, atr: 2.42, score: 88, sig: 'BUY' },
  { sym: 'ISCTR', name: 'İş Bankası',     px: 18.42,  chg: -1.20, vol: '88.6M',  rsi: 26.8, atr: 0.42, score: 85, sig: 'STRONG_BUY' },
  { sym: 'YKBNK', name: 'Yapı Kredi',     px: 32.18,  chg: 0.40,  vol: '124.0M', rsi: 29.1, atr: 0.81, score: 82, sig: 'BUY' },
  { sym: 'HALKB', name: 'Halkbank',       px: 18.80,  chg: -0.42, vol: '64.2M',  rsi: 27.5, atr: 0.48, score: 80, sig: 'STRONG_BUY' },
  { sym: 'VAKBN', name: 'Vakıfbank',      px: 31.66,  chg: 1.02,  vol: '72.8M',  rsi: 32.8, atr: 0.74, score: 76, sig: 'BUY' },
  { sym: 'KRDMD', name: 'Kardemir',       px: 24.40,  chg: -2.10, vol: '42.1M',  rsi: 29.4, atr: 0.62, score: 72, sig: 'BUY' },
  { sym: 'EREGL', name: 'Ereğli Demir',   px: 38.60,  chg: -0.84, vol: '56.4M',  rsi: 30.1, atr: 0.92, score: 70, sig: 'BUY' },
];

Object.assign(window, {
  WATCHLIST, TICKER, NAV_TABS,
  CANDLES_VAKBN, CANDLES_AKBNK, CANDLES_ARCLK, CANDLES_ASELS,
  EQUITY, DRAWDOWN, WALLETS, TRADES, SIGNALS,
  ARTICLES, COMPANIES, THYAO_FIN, SCANNER_PRESETS, SCANNER_RESULTS,
});
