import type { OHLCV, Timeframe, AssetType } from '../types.js';
import { filterAnomalies } from './AnomalyFilter.js';

// Tarihsel/snapshot bar yükleyici — DataEngine ve PollingManager tek noktadan
// ``/api/v2/candles`` (lokal Python backend) çağırır. CLAUDE.md kuralı 10
// gereği frontend hiçbir yerden ``api.binance.com`` veya ``corsproxy.io``
// gibi dış endpoint'lere doğrudan çıkmaz.

const ENDPOINT = '/api/v2/candles';
const DEFAULT_LIMIT = 500;
const DAILY_HISTORY_LIMIT = 3000;
const DEFAULT_TIMEOUT_MS = 10_000;

interface BackendBar {
  time:             number;
  open:             number;
  high:             number;
  low:              number;
  close:            number;
  volume:           number;
  is_real?:         boolean;
  quality_status?:  string;
  data_coverage_pct?: number;
}

interface BackendCandlesResponse {
  status?:            string;
  message?:           string;
  bars?:              BackendBar[];
  // Yanıt düzeyindeki kalite metadata (bar başına değil, toplu)
  is_real?:           boolean;
  quality_status?:    string;
  data_coverage_pct?: number;
}

export interface LoadOptions {
  limit?: number;
  timeoutMs?: number;
  applyAnomalyFilter?: boolean;
  assetType?: AssetType;  // anomaly filter eşiği için
}

/** ``/api/v2/candles`` çağrısı; OHLCV[] döner, hata durumunda fırlatır. */
export async function loadHistorical(
  symbol: string,
  timeframe: Timeframe,
  opts: LoadOptions = {},
): Promise<OHLCV[]> {
  const limit = opts.limit ?? (timeframe === '1d' ? DAILY_HISTORY_LIMIT : DEFAULT_LIMIT);
  const timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
  const url =
    `${ENDPOINT}` +
    `?symbol=${encodeURIComponent(symbol)}` +
    `&interval=${encodeURIComponent(timeframe)}` +
    `&limit=${limit}`;

  const resp = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) });
  if (!resp.ok) {
    throw new Error(`Bağlantı Hatası: backend HTTP ${resp.status}`);
  }
  const dataSource = resp.headers.get('X-Data-Source') ?? 'unknown';

  const json: BackendCandlesResponse = await resp.json();
  if (json.status === 'error' || !Array.isArray(json.bars)) {
    throw new Error(json.message || 'Bağlantı Hatası: backend boş yanıt');
  }
  if (json.bars.length === 0) {
    throw new Error('Empty OHLCV result');
  }

  const candles: OHLCV[] = json.bars.map(b => ({
    time:   b.time,
    open:   b.open,
    high:   b.high,
    low:    b.low,
    close:  b.close,
    volume: b.volume,
  }));

  // Veri kalitesi metadata'sını event olarak ilet (DataQualityBadge ve diğerleri dinleyebilir)
  const qualityMeta = {
    symbol,
    timeframe,
    source: dataSource,
    is_real:           json.is_real           ?? json.bars[0]?.is_real,
    quality_status:    json.quality_status    ?? json.bars[0]?.quality_status,
    data_coverage_pct: json.data_coverage_pct ?? json.bars[0]?.data_coverage_pct,
  };
  window.dispatchEvent(new CustomEvent('piyasapilot:data-source', {
    detail: qualityMeta,
  }));
  window.dispatchEvent(new CustomEvent('piyasapilot:data-quality', {
    detail: qualityMeta,
  }));

  if (opts.applyAnomalyFilter !== false && opts.assetType) {
    return filterAnomalies(candles, opts.assetType);
  }
  return candles;
}
