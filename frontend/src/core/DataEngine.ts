import type {
  OHLCV, SymbolInfo, Timeframe, ConnectionStatus,
  DataUpdateEvent, PriceUpdateEvent,
} from '../types.js';
import { PollingManager } from './PollingManager.js';
import { QuoteStream, type QuoteMessage } from './QuoteStream.js';
import { loadHistorical } from './HistoricalLoader.js';
import { DEFAULT_SYMBOL, resolveSymbol } from '../constants/symbols.js';

// ─── Simple EventEmitter ──────────────────────────────────────────────────────

type Listener = (...args: unknown[]) => void;

class EventEmitter {
  private map = new Map<string, Set<Listener>>();

  on(event: string, listener: Listener): () => void {
    if (!this.map.has(event)) this.map.set(event, new Set());
    this.map.get(event)!.add(listener);
    return () => this.map.get(event)?.delete(listener);
  }

  emit(event: string, ...args: unknown[]): void {
    this.map.get(event)?.forEach(l => l(...args));
  }

  off(event: string, listener: Listener): void {
    this.map.get(event)?.delete(listener);
  }
}

// ─── DataEngine ───────────────────────────────────────────────────────────────

const MAX_CANDLES = 1000;
const TRIM_TO = 500;

export class DataEngine extends EventEmitter {
  private quoteStream: QuoteStream | null = null;
  private quoteUnsubscribe: (() => void) | null = null;
  private pollManager = new PollingManager();
  private pollUnsubscribe: (() => void) | null = null;

  private activeSymbol: SymbolInfo = DEFAULT_SYMBOL;
  private activeTimeframe: Timeframe = '1d';

  // Last known candles for the active symbol
  private activeCandles: OHLCV[] = [];
  private lastUpdate = 0;
  private status: ConnectionStatus = 'offline';

  // Price cache for screener / portfolio updates
  private priceCache = new Map<string, number>();

  constructor() {
    super();
  }

  // ─── Symbol / timeframe selection ─────────────────────────────────────────

  async setActiveSymbol(info: SymbolInfo, tf?: Timeframe): Promise<void> {
    this.disconnect();

    this.activeSymbol    = info;
    this.activeTimeframe = tf ?? this.activeTimeframe;
    this.activeCandles   = [];
    this.status          = 'offline';

    this.emit('statusChange', 'offline');

    if (info.assetType === 'crypto') {
      await this.connectCrypto(info.symbol, this.activeTimeframe);
    } else {
      this.connectPolling(info.symbol, this.activeTimeframe, info.assetType);
    }
  }

  setTimeframe(tf: Timeframe): void {
    if (tf === this.activeTimeframe) return;
    this.activeTimeframe = tf;
    // Reconnect with new timeframe
    void this.setActiveSymbol(this.activeSymbol, tf);
  }

  // ─── Crypto path: lokal backend + /ws/quotes fan-out ─────────────────────

  private async connectCrypto(symbol: string, tf: Timeframe): Promise<void> {
    this.status = 'connecting' as ConnectionStatus;
    this.emit('statusChange', 'connecting');

    // 1) Tarihsel snapshot — /api/v2/candles cache-aside.
    try {
      const candles = await loadHistorical(symbol, tf, { assetType: 'crypto' });
      this.activeCandles = candles;
      this.lastUpdate = Date.now();
      // Tarihsel veri var ama backend worker'dan henüz live tick alınmadı;
      // ilk QuoteStream mesajı gelene kadar 'delayed' kalsın.
      this.status = 'delayed';
      this.emitDataUpdate(candles, 'delayed');
    } catch {
      this.emit('statusChange', 'offline');
      return;
    }

    // 2) Live update — QuoteStream subscribe.
    this.quoteStream = new QuoteStream({
      symbols: [symbol],
      intervals: [tf],
    });
    this.quoteUnsubscribe = this.quoteStream.onBars(msg => this.handleQuoteMessage(symbol, msg));
    this.quoteStream.connect();
  }

  private handleQuoteMessage(activeSymbol: string, msg: QuoteMessage): void {
    if (msg.symbol !== activeSymbol.toUpperCase() || msg.interval !== this.activeTimeframe) {
      return;
    }
    this.lastUpdate = Date.now();
    this.status = 'live';

    for (const bar of msg.bars) {
      const idx = this.activeCandles.findIndex(c => c.time === bar.time);
      if (idx >= 0) {
        this.activeCandles[idx] = bar;
      } else {
        this.activeCandles = [...this.activeCandles, bar];
        if (this.activeCandles.length > MAX_CANDLES) {
          this.activeCandles = this.activeCandles.slice(-TRIM_TO);
        }
      }
    }

    const last = msg.bars[msg.bars.length - 1]!;
    this.priceCache.set(activeSymbol, last.close);
    const prev = this.activeCandles[this.activeCandles.length - 2]?.close ?? last.close;
    const changePct = prev !== 0 ? ((last.close - prev) / prev) * 100 : 0;
    this.emitPriceUpdate(activeSymbol, last.close, changePct);
    this.emitDataUpdate(this.activeCandles, 'live');
  }

  // ─── REST polling path (BIST / FX / Commodity / US) ──────────────────────

  private connectPolling(symbol: string, tf: Timeframe, assetType: typeof this.activeSymbol.assetType): void {
    if (this.pollUnsubscribe) {
      this.pollUnsubscribe();
      this.pollUnsubscribe = null;
    }
    
    this.pollManager.start(symbol, tf, assetType);

    this.pollUnsubscribe = this.pollManager.onData((candles, status) => {
      this.lastUpdate = Date.now();
      this.status = status;

      if (candles.length > 0) {
        this.activeCandles = candles;
        const last = candles[candles.length - 1]!;
        this.priceCache.set(symbol, last.close);

        const prev = candles[candles.length - 2]?.close ?? last.close;
        const changePct = prev !== 0 ? ((last.close - prev) / prev) * 100 : 0;
        this.emitPriceUpdate(symbol, last.close, changePct);
        this.emitDataUpdate(candles, status);
      } else {
        this.emit('statusChange', status);
      }
    });
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  private disconnect(): void {
    if (this.quoteUnsubscribe) {
      this.quoteUnsubscribe();
      this.quoteUnsubscribe = null;
    }
    if (this.quoteStream) {
      this.quoteStream.disconnect();
      this.quoteStream = null;
    }
    if (this.pollUnsubscribe) {
      this.pollUnsubscribe();
      this.pollUnsubscribe = null;
    }
    this.pollManager.stop();
  }

  // ─── Emitters ────────────────────────────────────────────────────────────

  private emitDataUpdate(candles: OHLCV[], status: ConnectionStatus): void {
    const event: DataUpdateEvent = {
      symbol: this.activeSymbol.symbol,
      candles,
      status,
      lastUpdate: this.lastUpdate,
    };
    this.emit('dataUpdate', event);
    this.emit('statusChange', status);
  }

  private emitPriceUpdate(symbol: string, price: number, changePct: number): void {
    const event: PriceUpdateEvent = {
      symbol,
      price,
      changePct,
      timestamp: Math.floor(Date.now() / 1000),
    };
    this.emit('priceUpdate', event);
  }

  // ─── Typed event subscriptions ───────────────────────────────────────────

  onDataUpdate(listener: (evt: DataUpdateEvent) => void): () => void {
    return this.on('dataUpdate', listener as Listener);
  }

  onPriceUpdate(listener: (evt: PriceUpdateEvent) => void): () => void {
    return this.on('priceUpdate', listener as Listener);
  }

  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    return this.on('statusChange', listener as Listener);
  }

  // ─── Accessors ───────────────────────────────────────────────────────────

  getActiveCandles(): OHLCV[] { return this.activeCandles; }
  getActiveSymbol(): SymbolInfo { return this.activeSymbol; }
  getActiveTimeframe(): Timeframe { return this.activeTimeframe; }
  getStatus(): ConnectionStatus { return this.status; }
  getLastUpdate(): number { return this.lastUpdate; }
  getPriceCache(): Map<string, number> { return this.priceCache; }

  // Returns all cached OHLCV data across all symbols (for screener)
  getAllCached(): Map<string, OHLCV[]> {
    const result = new Map<string, OHLCV[]>();
    for (const [key, entry] of this.pollManager.getAllCached()) {
      const symbol = key.split(':')[0]!;
      result.set(symbol, entry.data);
    }
    return result;
  }

  getSymbolInfo(symbol: string): SymbolInfo | undefined {
    return resolveSymbol(symbol);
  }
}

// ─── Singleton ───────────────────────────────────────────────────────────────

export const dataEngine = new DataEngine();
