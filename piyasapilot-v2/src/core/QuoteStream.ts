import type { OHLCV } from '../types.js';

// Backend ``/ws/quotes`` fan-out client'ı. Sprint 1.9.
// Mevcut ``WebSocketManager`` doğrudan Binance WS'sine gidiyor (geo-blok riski);
// ``QuoteStream`` lokal Python backend üzerinden cache değişikliklerini alır.
// Sprint 2'de Market Explorer çoklu sembol akışı için bu client kullanılacak.

export interface QuoteMessage {
  type: 'bars';
  symbol: string;
  interval: string;
  bars: OHLCV[];
  ts: string;
}

interface ReadyMessage {
  type: 'ready';
  client_id: string;
}

type ServerMessage = QuoteMessage | ReadyMessage;

type BarsListener = (msg: QuoteMessage) => void;

const HEARTBEAT_INTERVAL_MS = 30_000;
const MAX_BACKOFF_MS = 30_000;
const MAX_RECONNECT_ATTEMPTS = 6;

export interface QuoteStreamOptions {
  symbols?: string[];
  intervals?: string[];
  baseUrl?: string;  // testlerde mock için
}

export class QuoteStream {
  private ws: WebSocket | null = null;
  private listeners: Set<BarsListener> = new Set();
  private destroyed = false;
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private readyClientId: string | null = null;
  private readonly symbols: string[];
  private readonly intervals: string[];
  private readonly baseUrl: string;

  constructor(opts: QuoteStreamOptions = {}) {
    this.symbols = opts.symbols ?? [];
    this.intervals = opts.intervals ?? [];
    this.baseUrl = opts.baseUrl ?? this.resolveDefaultBase();
  }

  private resolveDefaultBase(): string {
    if (typeof window === 'undefined') return 'ws://127.0.0.1:8000';
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${window.location.host}`;
  }

  private buildUrl(): string {
    const params = new URLSearchParams();
    if (this.symbols.length > 0) params.set('symbols', this.symbols.join(','));
    if (this.intervals.length > 0) params.set('intervals', this.intervals.join(','));
    const qs = params.toString();
    return `${this.baseUrl}/ws/quotes${qs ? `?${qs}` : ''}`;
  }

  onBars(listener: BarsListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  connect(): void {
    this.destroyed = false;
    this.openSocket();
  }

  private openSocket(): void {
    const url = this.buildUrl();
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      this.reconnectAttempt = 0;
      this.startHeartbeat();
    };

    this.ws.onmessage = (evt: MessageEvent) => {
      let msg: ServerMessage;
      try {
        msg = JSON.parse(evt.data as string) as ServerMessage;
      } catch {
        return;
      }
      if (msg.type === 'ready') {
        this.readyClientId = msg.client_id;
        return;
      }
      if (msg.type === 'bars') {
        this.listeners.forEach(l => l(msg));
      }
    };

    this.ws.onerror = () => {
      // onclose immediately follows
    };

    this.ws.onclose = () => {
      this.stopHeartbeat();
      if (!this.destroyed) {
        this.scheduleReconnect();
      }
    };
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempt >= MAX_RECONNECT_ATTEMPTS) {
      console.warn(
        `[QuoteStream] ${MAX_RECONNECT_ATTEMPTS} reconnect denemesi başarısız, vazgeçildi.`,
      );
      this.destroyed = true;
      return;
    }
    const delay = Math.min(1000 * 2 ** this.reconnectAttempt, MAX_BACKOFF_MS);
    this.reconnectAttempt++;
    this.reconnectTimer = setTimeout(() => {
      if (!this.destroyed) this.openSocket();
    }, delay);
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, HEARTBEAT_INTERVAL_MS);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer !== null) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
  }

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
    this.readyClientId = null;
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  getClientId(): string | null {
    return this.readyClientId;
  }
}
