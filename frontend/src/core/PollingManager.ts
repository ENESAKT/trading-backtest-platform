import type { OHLCV, AssetType, Timeframe, CacheEntry, ConnectionStatus } from '../types.js';
import { filterAnomalies } from './AnomalyFilter.js';

// Frontend artık corsproxy.io + Yahoo Finance'a doğrudan çıkmıyor; tüm OHLCV
// çağrıları lokal Python backend'in v2 endpoint'i üzerinden geçiyor.
const LOCAL_CANDLES_ENDPOINT = '/api/v2/candles';
const CANDLES_LIMIT = 500;
const POLL_INTERVAL_EQUITY = 15_000;  // ms
const POLL_INTERVAL_CRYPTO  = 10_000;
const RATE_LIMIT_PER_SEC = 2;
const TOKEN_REFILL_MS = Math.floor(1000 / RATE_LIMIT_PER_SEC);
const MAX_QUEUE_SIZE = 50;
const MAX_RETRY = 3;

interface BackendCandlesResponse {
  status?: string;
  message?: string;
  bars?: Array<{
    time: number;
    open: number;
    high: number;
    low: number;
    close: number;
    volume: number;
  }>;
}

type PollListener = (candles: OHLCV[], status: ConnectionStatus) => void;

// ─── Rate limiter (token bucket) ─────────────────────────────────────────────

class RateLimiter {
  private tokens = RATE_LIMIT_PER_SEC;
  private lastRefill = Date.now();

  canRequest(): boolean {
    this.refill();
    if (this.tokens >= 1) {
      this.tokens--;
      return true;
    }
    return false;
  }

  private refill(): void {
    const now = Date.now();
    const elapsed = now - this.lastRefill;
    const newTokens = Math.floor(elapsed / TOKEN_REFILL_MS);
    if (newTokens > 0) {
      this.tokens = Math.min(RATE_LIMIT_PER_SEC, this.tokens + newTokens);
      this.lastRefill = now;
    }
  }
}

// ─── PollingManager ───────────────────────────────────────────────────────────

export class PollingManager {
  private cache = new Map<string, CacheEntry>();
  private listeners: Set<PollListener> = new Set();
  private rateLimiter = new RateLimiter();
  private requestQueue: Array<() => Promise<void>> = [];
  private queueProcessing = false;
  private pollTimer: ReturnType<typeof setInterval> | null = null;
  private retryCount = 0;
  private destroyed = false;

  // ─── Listener management ────────────────────────────────────────────────

  onData(listener: PollListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // ─── Start / stop ────────────────────────────────────────────────────────

  start(symbol: string, timeframe: Timeframe, assetType: AssetType): void {
    this.stop();
    this.retryCount = 0;
    this.destroyed = false;

    const interval = assetType === 'crypto' ? POLL_INTERVAL_CRYPTO : POLL_INTERVAL_EQUITY;

    // Immediate first fetch
    this.enqueueRequest(() => this.fetchAndUpdate(symbol, timeframe, assetType));

    this.pollTimer = setInterval(() => {
      this.enqueueRequest(() => this.fetchAndUpdate(symbol, timeframe, assetType));
    }, interval);
  }

  stop(): void {
    this.destroyed = true;
    if (this.pollTimer !== null) {
      clearInterval(this.pollTimer);
      this.pollTimer = null;
    }
    this.requestQueue = [];
  }

  // ─── Cache ───────────────────────────────────────────────────────────────

  private cacheKey(symbol: string, tf: Timeframe): string {
    return `${symbol}:${tf}`;
  }

  private getCached(symbol: string, tf: Timeframe): OHLCV[] | null {
    const key = this.cacheKey(symbol, tf);
    const entry = this.cache.get(key);
    if (!entry) return null;

    const ttl = (tf === '1m' ? POLL_INTERVAL_CRYPTO : POLL_INTERVAL_EQUITY) - 3_000;
    if (Date.now() - entry.timestamp > ttl) return null;

    return entry.data;
  }

  private setCache(symbol: string, tf: Timeframe, data: OHLCV[]): void {
    this.cache.set(this.cacheKey(symbol, tf), {
      data,
      timestamp: Date.now(),
      symbol,
      timeframe: tf,
    });
  }

  getCachedData(symbol: string, tf: Timeframe): OHLCV[] | null {
    return this.cache.get(this.cacheKey(symbol, tf))?.data ?? null;
  }

  getAllCached(): Map<string, CacheEntry> {
    return this.cache;
  }

  // ─── Request queue ───────────────────────────────────────────────────────

  private enqueueRequest(fn: () => Promise<void>): void {
    if (this.requestQueue.length >= MAX_QUEUE_SIZE) {
      this.requestQueue.shift(); // drop oldest
    }
    this.requestQueue.push(fn);
    if (!this.queueProcessing) {
      void this.processQueue();
    }
  }

  private async processQueue(): Promise<void> {
    this.queueProcessing = true;
    while (this.requestQueue.length > 0) {
      if (!this.rateLimiter.canRequest()) {
        await this.sleep(TOKEN_REFILL_MS);
        continue;
      }
      const task = this.requestQueue.shift()!;
      await task();
    }
    this.queueProcessing = false;
  }

  // ─── Fetch logic ─────────────────────────────────────────────────────────

  private async fetchAndUpdate(
    symbol: string,
    tf: Timeframe,
    assetType: AssetType
  ): Promise<void> {
    if (this.destroyed) return;

    const cached = this.getCached(symbol, tf);
    if (cached) {
      this.emit(cached, 'delayed');
      return;
    }

    try {
      const candles = await this.fetchWithRetry(symbol, tf, assetType);
      this.retryCount = 0;
      this.setCache(symbol, tf, candles);
      this.emit(candles, 'live');
    } catch (err: any) {
      if (err?.isNoData) {
        this.emit([], 'no_data' as any);
        return;
      }
      this.retryCount++;
      if (this.retryCount >= MAX_RETRY) {
        this.emit([], 'offline');
      }
    }
  }

  private async fetchWithRetry(
    symbol: string,
    tf: Timeframe,
    assetType: AssetType,
    attempt = 0
  ): Promise<OHLCV[]> {
    try {
      return await this.fetchYahooFinance(symbol, tf, assetType);
    } catch (err) {
      if (attempt < MAX_RETRY - 1) {
        await this.sleep(1000 * 2 ** attempt);
        return this.fetchWithRetry(symbol, tf, assetType, attempt + 1);
      }
      throw err;
    }
  }

  private async fetchYahooFinance(
    symbol: string,
    tf: Timeframe,
    assetType: AssetType
  ): Promise<OHLCV[]> {
    const url =
      `${LOCAL_CANDLES_ENDPOINT}` +
      `?symbol=${encodeURIComponent(symbol)}` +
      `&interval=${encodeURIComponent(tf)}` +
      `&limit=${CANDLES_LIMIT}`;

    const resp = await fetch(url, { signal: AbortSignal.timeout(10_000) });
    if (!resp.ok) throw new Error(`backend HTTP ${resp.status}`);

    const json: BackendCandlesResponse = await resp.json();

    if (json.status === 'error' || !Array.isArray(json.bars)) {
      throw new Error(json.message || 'Bağlantı Hatası: backend boş yanıt');
    }

    if (json.bars.length === 0) {
      const noDataErr = new Error('NO_DATA_FOR_SYMBOL');
      (noDataErr as any).isNoData = true;
      throw noDataErr;
    }

    const candles: OHLCV[] = json.bars.map(b => ({
      time:   b.time,
      open:   b.open,
      high:   b.high,
      low:    b.low,
      close:  b.close,
      volume: b.volume,
    }));

    return filterAnomalies(candles, assetType);
  }

  // ─── Emit ────────────────────────────────────────────────────────────────

  private emit(candles: OHLCV[], status: ConnectionStatus): void {
    if (this.destroyed) return;
    this.listeners.forEach(l => l(candles, status));
  }

  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }
}
