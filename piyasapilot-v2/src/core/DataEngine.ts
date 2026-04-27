import type {
  OHLCV, SymbolInfo, Timeframe, ConnectionStatus,
  DataUpdateEvent, PriceUpdateEvent,
} from '../types.js';
import { WebSocketManager } from './WebSocketManager.js';
import { PollingManager } from './PollingManager.js';
import { DEFAULT_SYMBOL } from '../constants/symbols.js';

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

export class DataEngine extends EventEmitter {
  private wsManager  = new WebSocketManager();
  private pollManager = new PollingManager();

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

  // ─── Crypto path (WebSocket + REST history) ───────────────────────────────

  private async connectCrypto(symbol: string, tf: Timeframe): Promise<void> {
    this.status = 'connecting' as ConnectionStatus;
    this.emit('statusChange', 'connecting');

    try {
      const candles = await this.wsManager.fetchHistorical(symbol, tf);
      this.activeCandles = candles;
      this.lastUpdate = Date.now();
      // Tarihsel veri geldi ama henüz WebSocket tick'i alınmadı.
      // Geo-blok/ağ sorunlarında WS hiç açılmayabilir; o sürede 'live' demek
      // yanıltıcı. İlk gerçek tick gelene kadar 'delayed' olarak yayınla.
      this.status = 'delayed';
      this.emitDataUpdate(candles, 'delayed');
    } catch {
      this.emit('statusChange', 'offline');
    }

    // Subscribe to live tick updates
    this.wsManager.connect(symbol, tf);
    this.wsManager.onKline((candle, isClosed) => {
      this.lastUpdate = Date.now();
      this.status = 'live';

      if (isClosed) {
        // Replace or append
        const idx = this.activeCandles.findIndex(c => c.time === candle.time);
        if (idx >= 0) {
          this.activeCandles[idx] = candle;
        } else {
          this.activeCandles = [...this.activeCandles, candle];
          if (this.activeCandles.length > 1000) {
            this.activeCandles = this.activeCandles.slice(-500);
          }
        }
        this.emitDataUpdate(this.activeCandles, 'live');
      } else {
        // Live tick: emit price update only
        this.priceCache.set(symbol, candle.close);
        const prev = this.activeCandles[this.activeCandles.length - 2]?.close ?? candle.close;
        const changePct = prev !== 0 ? ((candle.close - prev) / prev) * 100 : 0;
        this.emitPriceUpdate(symbol, candle.close, changePct);
      }
    });
  }

  // ─── REST polling path (Yahoo Finance) ───────────────────────────────────

  private connectPolling(symbol: string, tf: Timeframe, assetType: typeof this.activeSymbol.assetType): void {
    this.pollManager.start(symbol, tf, assetType);

    this.pollManager.onData((candles, status) => {
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
    this.wsManager.disconnect();
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
}

// ─── Singleton ───────────────────────────────────────────────────────────────

export const dataEngine = new DataEngine();
