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
  private statusTimer: ReturnType<typeof setInterval> | null = null;
  private destroyed = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.render();
    this.connect();
    this.pollTelegramStatus();
  }

  destroy(): void {
    this.destroyed = true;
    if (this.reconnectTimer !== null) clearTimeout(this.reconnectTimer);
    if (this.statusTimer !== null) clearInterval(this.statusTimer);
    this.ws?.close();
  }

  private pollTelegramStatus(): void {
    const fetch_status = () => {
      if (this.destroyed) return;
      const base = window.location.origin.replace(/^ws/, 'http');
      fetch(`${base}/api/notifier/status`)
        .then(r => r.json())
        .then((d: Record<string, unknown>) => this.renderTelegramStatus(d))
        .catch(() => this.renderTelegramStatus(null));
    };
    fetch_status();
    this.statusTimer = setInterval(fetch_status, 30_000);
  }

  private renderTelegramStatus(d: Record<string, unknown> | null): void {
    const el = this.container.querySelector<HTMLElement>('#tg-status');
    if (!el) return;
    if (!d) {
      el.innerHTML = `<span class="tg-dot tg-unknown"></span> Telegram: bilinmiyor`;
      return;
    }
    const yapilandirildi = d['telegram_yapilandirildi'] as boolean;
    if (!yapilandirildi) {
      el.innerHTML = `<span class="tg-dot tg-off"></span> Telegram: yapılandırılmamış`;
      el.title = '.env dosyasında TELEGRAM_BOT_TOKEN eksik';
      return;
    }
    const sonBildirim = d['son_bildirim'] as string | null;
    const sonHata = d['son_hata'] as string | null;
    const toplam = (d['toplam_bildirim'] as number) ?? 0;
    const zamanStr = sonBildirim
      ? new Date(sonBildirim).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit' })
      : '—';
    const dotClass = sonHata ? 'tg-warn' : 'tg-on';
    el.innerHTML = `<span class="tg-dot ${dotClass}"></span> Telegram aktif · son: ${zamanStr} · ${toplam} bildirim`;
    el.title = sonHata ? `Son hata: ${sonHata}` : `Token: ${d['token_son4']} · Chat: ${d['chat_id']}`;
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
        <div id="tg-status" class="tg-status-bar">
          <span class="tg-dot tg-unknown"></span> Telegram: yükleniyor…
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
    const isStrong = sig.signal_type === 'STRONG_BUY' || sig.signal_type === 'STRONG_SELL';
    const isBuy = sig.signal_type === 'BUY' || sig.signal_type === 'STRONG_BUY';

    let badgeClass: string;
    let badgeLabel: string;
    if (sig.signal_type === 'STRONG_BUY') {
      badgeClass = 'badge-strong-buy';
      badgeLabel = TR.SIGNAL_STRONG_BUY;
    } else if (sig.signal_type === 'STRONG_SELL') {
      badgeClass = 'badge-strong-sell';
      badgeLabel = TR.SIGNAL_STRONG_SELL;
    } else if (isBuy) {
      badgeClass = 'badge-buy';
      badgeLabel = TR.SIGNAL_BUY;
    } else {
      badgeClass = 'badge-sell';
      badgeLabel = TR.SIGNAL_SELL;
    }

    const stars = '★'.repeat(Math.min(Math.max(sig.strength, 1), 10));
    const time = new Date(sig.ts).toLocaleTimeString('tr-TR', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    });
    const decimals = sig.price < 1 ? 6 : sig.price < 100 ? 4 : 2;

    // Konsensüs metadata satırı
    let metadataHTML = '';
    if (isStrong && sig.metadata) {
      const parts: string[] = [];
      if (sig.metadata.consensus_ratio !== undefined) {
        parts.push(`Oran: ${(sig.metadata.consensus_ratio * 100).toFixed(0)}%`);
      }
      if (sig.metadata.buy_count !== undefined && sig.metadata.total_strategies !== undefined) {
        const count = isBuy ? sig.metadata.buy_count : (sig.metadata.sell_count ?? 0);
        parts.push(`${count}/${sig.metadata.total_strategies} strateji`);
      }
      if (sig.metadata.rsi !== undefined) parts.push(`RSI: ${sig.metadata.rsi}`);
      if (sig.metadata.trend) parts.push(`Trend: ${sig.metadata.trend}`);
      if (parts.length > 0) {
        metadataHTML = `<div class="signal-consensus">${parts.join(' · ')}</div>`;
      }
    }

    return `
      <div class="signal-item ${isStrong ? 'signal-strong' : ''}">
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
        ${metadataHTML}
      </div>
    `;
  }
}
