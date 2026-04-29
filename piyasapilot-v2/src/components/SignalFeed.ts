import { TR, formatNumber } from '../constants/tr.js';

// Canlı sinyal akışı — backend ``/ws/signals`` WebSocket fan-out client'ı.
// Sprint 3.6: DecisionEngine + StrategyRegistry sinyallerini gerçek zamanlı
// gösterir. QuoteStream ile aynı URL çözümleme modelini kullanır.

const MAX_SIGNALS = 50;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;

interface LiveSignal {
  type: 'signal';
  symbol: string;
  signal_type: 'BUY' | 'SELL' | 'STRONG_BUY' | 'STRONG_SELL';
  price: number;
  strategy_id: string;
  reason: string;
  strength: number;
  interval: string;
  ts: string;
  metadata?: {
    rsi?: number;
    trend?: string;
    atr?: number;
    volatility_pct?: number;
    buy_count?: number;
    sell_count?: number;
    total_strategies?: number;
    consensus_ratio?: number;
  };
}

export class SignalFeed {
  private container: HTMLElement;
  private ws: WebSocket | null = null;
  private signals: LiveSignal[] = [];
  private reconnectDelay = RECONNECT_BASE_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private destroyed = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    this.connect();
  }

  destroy(): void {
    this.destroyed = true;
    if (this.reconnectTimer !== null) clearTimeout(this.reconnectTimer);
    this.ws?.close();
  }

  private resolveBase(): string {
    if (typeof window === 'undefined') return 'ws://127.0.0.1:8000';
    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws';
    return `${proto}://${window.location.host}`;
  }

  private connect(): void {
    if (this.destroyed) return;
    this.setStatus('connecting');
    const ws = new WebSocket(`${this.resolveBase()}/ws/signals`);
    this.ws = ws;

    ws.onopen = () => {
      this.reconnectDelay = RECONNECT_BASE_MS;
      this.setStatus('live');
    };

    ws.onmessage = (evt) => {
      try {
        const msg = JSON.parse(evt.data as string) as { type: string } & Partial<LiveSignal>;
        if (msg.type === 'signal') {
          this.addSignal(msg as LiveSignal);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => { /* onclose handles reconnect */ };

    ws.onclose = () => {
      if (this.destroyed) return;
      this.setStatus('offline');
      this.reconnectTimer = setTimeout(() => this.connect(), this.reconnectDelay);
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, RECONNECT_MAX_MS);
    };
  }

  private addSignal(sig: LiveSignal): void {
    this.signals.unshift(sig);
    if (this.signals.length > MAX_SIGNALS) this.signals.pop();
    this.renderSignals();

    // STRONG sinyaller için in-app toast bildirimi
    if (sig.signal_type === 'STRONG_BUY' || sig.signal_type === 'STRONG_SELL') {
      this.showToast(sig);
    }
  }

  /** In-app toast bildirimi — 5 saniye sonra otomatik kapanır */
  private showToast(sig: LiveSignal): void {
    const isBuy = sig.signal_type.includes('BUY');
    const emoji = isBuy ? '🟢' : '🔴';
    const label = isBuy ? 'GÜÇLÜ AL' : 'GÜÇLÜ SAT';

    const toast = document.createElement('div');
    toast.className = `toast toast-${isBuy ? 'buy' : 'sell'}`;
    toast.innerHTML = `
      <div class="toast-icon">${emoji}</div>
      <div class="toast-body">
        <div class="toast-title">${label} — ${sig.symbol}</div>
        <div class="toast-detail">${sig.reason}</div>
        <div class="toast-meta">Güç: ${sig.strength}/10 · ${sig.interval}</div>
      </div>
      <button class="toast-close" onclick="this.parentElement.remove()">✕</button>
    `;

    // Toast container
    let container = document.getElementById('toast-container');
    if (!container) {
      container = document.createElement('div');
      container.id = 'toast-container';
      document.body.appendChild(container);
    }
    container.appendChild(toast);

    // Animasyon: slide in
    requestAnimationFrame(() => toast.classList.add('toast-visible'));

    // 5 saniye sonra kaldır
    setTimeout(() => {
      toast.classList.remove('toast-visible');
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }

  private setStatus(status: 'connecting' | 'live' | 'offline'): void {
    const badge = this.container.querySelector<HTMLElement>('#signal-feed-status');
    if (!badge) return;
    const labels: Record<string, string> = {
      connecting: TR.CONNECTING,
      live: TR.LIVE,
      offline: TR.OFFLINE,
    };
    badge.textContent = labels[status] ?? status;
    badge.className = `status-badge status-${status}`;
  }

  private render(): void {
    this.container.innerHTML = `
      <div class="signal-feed-wrap">
        <div class="signal-feed-header">
          <h2>${TR.SIGNAL_FEED}</h2>
          <span id="signal-feed-status" class="status-badge status-offline">${TR.OFFLINE}</span>
        </div>
        <div class="signal-feed-info">${TR.SIGNAL_FEED_INFO}</div>
        <div id="signal-feed-list" class="signal-feed-list">
          <div class="signal-feed-empty">${TR.CONNECTING}…</div>
        </div>
      </div>
    `;
  }

  private renderSignals(): void {
    const list = this.container.querySelector<HTMLElement>('#signal-feed-list');
    if (!list) return;
    if (this.signals.length === 0) {
      list.innerHTML = `<div class="signal-feed-empty">${TR.SIGNAL_FEED_EMPTY}</div>`;
      return;
    }
    list.innerHTML = this.signals.map(sig => this.signalHTML(sig)).join('');
  }

  private signalHTML(sig: LiveSignal): string {
    const isBuy = sig.signal_type === 'BUY';
    const badgeClass = isBuy ? 'badge-buy' : 'badge-sell';
    const badgeLabel = isBuy ? TR.SIGNAL_BUY : TR.SIGNAL_SELL;
    const stars = '★'.repeat(Math.min(Math.max(sig.strength, 1), 10));
    const time = new Date(sig.ts).toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const decimals = sig.price < 1 ? 6 : sig.price < 100 ? 4 : 2;
    return `
      <div class="signal-item">
        <div class="signal-header">
          <span class="signal-badge ${badgeClass}">${badgeLabel}</span>
          <span class="signal-symbol">${sig.symbol}</span>
          <span class="signal-price">${formatNumber(sig.price, decimals)}</span>
          <span class="signal-time">${time}</span>
        </div>
        <div class="signal-meta">
          <span class="signal-strategy">${sig.strategy_id}</span>
          ${sig.interval ? `<span class="signal-interval">${sig.interval}</span>` : ''}
          <span class="signal-strength">${stars}</span>
        </div>
        <div class="signal-reason">${sig.reason}</div>
      </div>
    `;
  }
}
