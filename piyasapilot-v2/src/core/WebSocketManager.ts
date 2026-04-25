import type { OHLCV, Timeframe } from '../types.js';
import { filterAnomalies } from './AnomalyFilter.js';

// ─── Binance WS kline message shape ──────────────────────────────────────────

interface BinanceKlineMsg {
  e: 'kline';
  E: number;
  s: string;
  k: {
    t: number;   // kline open time (ms)
    T: number;   // kline close time (ms)
    s: string;
    i: string;   // interval
    o: string; c: string; h: string; l: string;
    v: string;   // base asset volume
    x: boolean;  // is closed
  };
}

// ─── Timeframe → Binance interval mapping ────────────────────────────────────

const TF_TO_BINANCE: Record<Timeframe, string> = {
  '1m':  '1m',
  '5m':  '5m',
  '15m': '15m',
  '30m': '30m',
  '1h':  '1h',
  '4h':  '4h',
  '1d':  '1d',
  '1w':  '1w',
};

const BINANCE_WS_BASE = 'wss://stream.binance.com:9443/ws';
const BINANCE_REST_BASE = 'https://api.binance.com/api/v3/klines';
const HEARTBEAT_INTERVAL_MS = 30_000;
const MAX_BACKOFF_MS = 30_000;
const MAX_QUEUE = 200;
const KLINES_LIMIT = 500;

type KlineListener = (candle: OHLCV, isClosed: boolean) => void;

// ─── WebSocketManager ─────────────────────────────────────────────────────────

export class WebSocketManager {
  private ws: WebSocket | null = null;
  private symbol = '';
  private timeframe: Timeframe = '1d';
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private messageQueue: BinanceKlineMsg[] = [];
  private listeners: Set<KlineListener> = new Set();
  private destroyed = false;
  private candles: OHLCV[] = [];

  // ─── Listener management ──────────────────────────────────────────────────

  onKline(listener: KlineListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  // ─── Historical data fetch ────────────────────────────────────────────────

  async fetchHistorical(symbol: string, timeframe: Timeframe): Promise<OHLCV[]> {
    const interval = TF_TO_BINANCE[timeframe];
    const url = `${BINANCE_REST_BASE}?symbol=${symbol}&interval=${interval}&limit=${KLINES_LIMIT}`;

    const resp = await fetch(url);
    if (!resp.ok) throw new Error(`Binance REST ${resp.status}: ${resp.statusText}`);

    const raw: [number, string, string, string, string, string][] = await resp.json();

    const candles: OHLCV[] = raw.map(k => ({
      time:   Math.floor(k[0] / 1000),
      open:   parseFloat(k[1]),
      high:   parseFloat(k[2]),
      low:    parseFloat(k[3]),
      close:  parseFloat(k[4]),
      volume: parseFloat(k[5]),
    }));

    this.candles = filterAnomalies(candles, 'crypto');
    return this.candles;
  }

  // ─── WebSocket connection lifecycle ──────────────────────────────────────

  connect(symbol: string, timeframe: Timeframe): void {
    this.symbol = symbol;
    this.timeframe = timeframe;
    this.destroyed = false;
    this.openSocket();
  }

  private openSocket(): void {
    const stream = `${this.symbol.toLowerCase()}@kline_${TF_TO_BINANCE[this.timeframe]}`;
    const url = `${BINANCE_WS_BASE}/${stream}`;

    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.startHeartbeat();
      this.flushQueue();
    };

    this.ws.onmessage = (evt: MessageEvent) => {
      this.handleMessage(evt.data as string);
    };

    this.ws.onerror = () => {
      // onclose will fire immediately after, handle reconnect there
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.destroyed) {
        this.scheduleReconnect();
      }
    };
  }

  private handleMessage(raw: string): void {
    let msg: BinanceKlineMsg;
    try {
      msg = JSON.parse(raw) as BinanceKlineMsg;
    } catch {
      return;
    }

    if (msg.e !== 'kline') return;

    // If not yet connected fully (during reconnect delay), buffer
    if (this.ws?.readyState !== WebSocket.OPEN) {
      if (this.messageQueue.length < MAX_QUEUE) {
        this.messageQueue.push(msg);
      }
      return;
    }

    this.processKline(msg);
  }

  private processKline(msg: BinanceKlineMsg): void {
    const k = msg.k;
    const candle: OHLCV = {
      time:   Math.floor(k.t / 1000),
      open:   parseFloat(k.o),
      high:   parseFloat(k.h),
      low:    parseFloat(k.l),
      close:  parseFloat(k.c),
      volume: parseFloat(k.v),
    };

    // Apply anomaly filter on the last window of candles
    if (this.candles.length > 0) {
      const tail = [...this.candles.slice(-50), candle];
      const filtered = filterAnomalies(tail, 'crypto');
      const clean = filtered[filtered.length - 1]!;

      if (k.x) {
        // Closed candle: append and trim history
        this.candles = [...this.candles, clean];
        if (this.candles.length > KLINES_LIMIT) {
          this.candles = this.candles.slice(-KLINES_LIMIT);
        }
      }

      this.listeners.forEach(l => l(clean, k.x));
    } else {
      this.listeners.forEach(l => l(candle, k.x));
    }
  }

  private flushQueue(): void {
    while (this.messageQueue.length > 0) {
      const msg = this.messageQueue.shift()!;
      this.processKline(msg);
    }
  }

  // ─── Exponential backoff reconnect ────────────────────────────────────────

  private scheduleReconnect(): void {
    const delay = Math.min(
      1000 * 2 ** this.reconnectAttempt,
      MAX_BACKOFF_MS
    );
    this.reconnectAttempt++;

    this.reconnectTimer = setTimeout(() => {
      if (!this.destroyed) {
        this.openSocket();
      }
    }, delay);
  }

  // ─── Heartbeat ping/pong ─────────────────────────────────────────────────

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ method: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL_MS);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

  // ─── Cleanup ─────────────────────────────────────────────────────────────

  disconnect(): void {
    this.destroyed = true;

    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    this.stopHeartbeat();

    if (this.ws) {
      this.ws.onclose = null;
      this.ws.close();
      this.ws = null;
    }

    this.messageQueue = [];
    this.candles = [];
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getCandles(): OHLCV[] {
    return this.candles;
  }
}
