import type { SymbolInfo } from '../types.js';

// ─── BIST 30 ──────────────────────────────────────────────────────────────────

export const BIST30: SymbolInfo[] = [
  { symbol: 'AKBNK.IS', name: 'Akbank', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'ARCLK.IS', name: 'Arçelik', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'ASELS.IS', name: 'Aselsan', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'BIMAS.IS', name: 'BİM Mağazalar', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'DOHOL.IS', name: 'Doğan Holding', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'EREGL.IS', name: 'Ereğli Demir Çelik', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'FROTO.IS', name: 'Ford Otosan', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'GARAN.IS', name: 'Garanti BBVA', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'HALKB.IS', name: 'Halkbank', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'ISCTR.IS', name: 'İş Bankası C', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'KCHOL.IS', name: 'Koç Holding', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'KOZAL.IS', name: 'Koza Altın', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'KRDMD.IS', name: 'Kardemir D', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'MAVI.IS', name: 'Mavi Giyim', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'PGSUS.IS', name: 'Pegasus', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'SAHOL.IS', name: 'Sabancı Holding', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'SASA.IS', name: 'SASA Polyester', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'SISE.IS', name: 'Şişe Cam', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'TAVHL.IS', name: 'TAV Havalimanları', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'TCELL.IS', name: 'Turkcell', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'THYAO.IS', name: 'Türk Hava Yolları', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'TOASO.IS', name: 'Tofaş Otomobil', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'TTKOM.IS', name: 'Türk Telekom', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'TUPRS.IS', name: 'Tüpraş', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'VAKBN.IS', name: 'Vakıfbank', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'VESTL.IS', name: 'Vestel', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'YKBNK.IS', name: 'Yapı Kredi Bankası', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'PETKM.IS', name: 'Petkim', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'EKGYO.IS', name: 'Emlak Konut GYO', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
  { symbol: 'ENKAI.IS', name: 'Enka İnşaat', assetType: 'equity', group: 'BIST 30', currency: 'TRY' },
];

// ─── BIST 100 (additional members beyond BIST 30) ────────────────────────────

// Not: BIST 100 üyeliği BIST tarafından her dönem revize edilir; bu liste
// 2025 dönemine yakın temsili kümeyi yansıtır. Tam doğrulama (yfinance ile
// her sembolün gerçekten veri döndüğü) Sprint 2.7'de live data path geçince
// otomatik yapılacak. Şimdilik dublike/yanlış sembol temizliği yapıldı:
// - TUPRS/VESTL kaldırıldı (BIST30'da zaten var)
// - SMARTP.IS → SMRTG.IS (gerçek BIST sembolü Smartiks Yazılım için)
// - TURSG.IS adı düzeltildi: "Turkcell Superonline" → "Türk Sigorta"
export const BIST100_EXTRA: SymbolInfo[] = [
  { symbol: 'AEFES.IS', name: 'Anadolu Efes', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AGHOL.IS', name: 'AG Anadolu Grubu', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AKCNS.IS', name: 'Akçansa Çimento', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AKFGY.IS', name: 'Akfen GYO', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AKGRT.IS', name: 'Aksigorta', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AKSA.IS', name: 'Aksa Akrilik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AKSEN.IS', name: 'Aksa Enerji', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ALARK.IS', name: 'Alarko Holding', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ALBRK.IS', name: 'Albaraka Türk', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ASUZU.IS', name: 'Anadolu Isuzu', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'AYGAZ.IS', name: 'Aygaz', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'BAGFS.IS', name: 'Bagfaş', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'BERA.IS', name: 'Bera Holding', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'BRISA.IS', name: 'Brisa', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'BRYAT.IS', name: 'Borusan Yatırım', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'CCOLA.IS', name: 'Coca-Cola İçecek', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'CIMSA.IS', name: 'Çimsa', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'CLEBI.IS', name: 'Çelebi Hava Servisi', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'DOAS.IS', name: 'Doğuş Otomotiv', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ECILC.IS', name: 'Eczacıbaşı İlaç', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'EGEEN.IS', name: 'Ege Endüstri', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ENJSA.IS', name: 'Enerjisa Enerji', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'GENIL.IS', name: 'Gen İlaç', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'GOODY.IS', name: 'Goodyear', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'GUBRF.IS', name: 'Gübre Fabrikaları', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'HEKTS.IS', name: 'Hektaş', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'IPEKE.IS', name: 'İpek Doğal Enerji', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ISDMR.IS', name: 'İskenderun Demir Çelik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ISMEN.IS', name: 'İş Yatırım', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'IZMDC.IS', name: 'İzmir Demir Çelik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'KARSN.IS', name: 'Karsan Otomotiv', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'KONTR.IS', name: 'Kontrolmatik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'KORDS.IS', name: 'Kordsa', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'KOZAA.IS', name: 'Koza Madencilik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'LOGO.IS', name: 'Logo Yazılım', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'MGROS.IS', name: 'Migros', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'MPARK.IS', name: 'MLP Sağlık (Medikal Park)', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'NETAS.IS', name: 'Netaş Telekom', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'NUHCM.IS', name: 'Nuh Çimento', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ODAS.IS', name: 'Odaş Elektrik', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'OTKAR.IS', name: 'Otokar', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'OYAKC.IS', name: 'Oyak Çimento', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'POLHO.IS', name: 'Polisan Holding', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'SDTTR.IS', name: 'SDT Uzay Savunma', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'SELEC.IS', name: 'Selçuk Ecza', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'SKBNK.IS', name: 'Şekerbank', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'SMRTG.IS', name: 'Smartiks Yazılım', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'SOKM.IS', name: 'Şok Marketler', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'TKFEN.IS', name: 'Tekfen Holding', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'TSKB.IS', name: 'TSKB', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'TTRAK.IS', name: 'Türk Traktör', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'TUKAS.IS', name: 'Tukaş Gıda', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'TURSG.IS', name: 'Türk Sigorta', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ULKER.IS', name: 'Ülker Bisküvi', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'YATAS.IS', name: 'Yataş Yatak', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'YEOTK.IS', name: 'Yeo Teknoloji', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
  { symbol: 'ZOREN.IS', name: 'Zorlu Enerji', assetType: 'equity', group: 'BIST 100', currency: 'TRY' },
];

// ─── US Markets (S&P 500 / NASDAQ top 20) ────────────────────────────────────

export const US_SYMBOLS: SymbolInfo[] = [
  { symbol: 'AAPL', name: 'Apple Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'MSFT', name: 'Microsoft Corp.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'NVDA', name: 'NVIDIA Corp.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'GOOGL', name: 'Alphabet Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'AMZN', name: 'Amazon.com Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'META', name: 'Meta Platforms', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'TSLA', name: 'Tesla Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'AVGO', name: 'Broadcom Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'BRK-B', name: 'Berkshire Hathaway B', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'COST', name: 'Costco Wholesale', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'NFLX', name: 'Netflix Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'AMD', name: 'Advanced Micro Devices', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'PEP', name: 'PepsiCo Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'QCOM', name: 'Qualcomm Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'ADBE', name: 'Adobe Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'INTC', name: 'Intel Corp.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'CRM', name: 'Salesforce Inc.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'ORCL', name: 'Oracle Corp.', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'CSCO', name: 'Cisco Systems', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
  { symbol: 'SPY', name: 'S&P 500 ETF', assetType: 'equity', group: 'ABD Piyasaları', currency: 'USD' },
];

// ─── Crypto (Binance pairs) ───────────────────────────────────────────────────

export const CRYPTO_SYMBOLS: SymbolInfo[] = [
  { symbol: 'BTCUSDT', name: 'Bitcoin / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'ETHUSDT', name: 'Ethereum / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'SOLUSDT', name: 'Solana / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'BNBUSDT', name: 'BNB / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'XRPUSDT', name: 'XRP / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'AVAXUSDT', name: 'Avalanche / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'DOTUSDT', name: 'Polkadot / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'ADAUSDT', name: 'Cardano / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'DOGEUSDT', name: 'Dogecoin / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
  { symbol: 'MATICUSDT', name: 'Polygon / USDT', assetType: 'crypto', group: 'Kripto', currency: 'USDT' },
];

// ─── FX & Commodity ───────────────────────────────────────────────────────────

export const FX_COMMODITY_SYMBOLS: SymbolInfo[] = [
  { symbol: 'USDTRY=X', name: 'USD / TRY', assetType: 'fx', group: 'Döviz / Emtia', currency: 'TRY' },
  { symbol: 'EURTRY=X', name: 'EUR / TRY', assetType: 'fx', group: 'Döviz / Emtia', currency: 'TRY' },
  { symbol: 'EURUSD=X', name: 'EUR / USD', assetType: 'fx', group: 'Döviz / Emtia', currency: 'USD' },
  { symbol: 'GBPUSD=X', name: 'GBP / USD', assetType: 'fx', group: 'Döviz / Emtia', currency: 'USD' },
  { symbol: 'GC=F', name: 'Altın (Spot)', assetType: 'commodity', group: 'Döviz / Emtia', currency: 'USD' },
  { symbol: 'SI=F', name: 'Gümüş (Spot)', assetType: 'commodity', group: 'Döviz / Emtia', currency: 'USD' },
  { symbol: 'CL=F', name: 'Ham Petrol (WTI)', assetType: 'commodity', group: 'Döviz / Emtia', currency: 'USD' },
  { symbol: 'BZ=F', name: 'Ham Petrol (Brent)', assetType: 'commodity', group: 'Döviz / Emtia', currency: 'USD' },
];

// ─── Flat lookup map ──────────────────────────────────────────────────────────

export const ALL_SYMBOLS: SymbolInfo[] = [
  ...BIST30,
  ...BIST100_EXTRA,
  ...US_SYMBOLS,
  ...CRYPTO_SYMBOLS,
  ...FX_COMMODITY_SYMBOLS,
];

export const SYMBOL_MAP = new Map<string, SymbolInfo>(
  ALL_SYMBOLS.map(s => [s.symbol, s])
);

export function resolveSymbol(symbol: string): SymbolInfo | undefined {
  return SYMBOL_MAP.get(symbol);
}

// ─── Default symbol on startup ────────────────────────────────────────────────

export const DEFAULT_SYMBOL: SymbolInfo = CRYPTO_SYMBOLS[0]!; // BTCUSDT
