import { TR, formatNumber } from '../constants/tr.js';

// Canlı sinyal akışı — backend ``/ws/signals`` WebSocket fan-out client'ı.
// Sprint 3.6: DecisionEngine + StrategyRegistry sinyallerini gerçek zamanlı
// gösterir. QuoteStream ile aynı URL çözümleme modelini kullanır.

const MAX_SIGNALS = 50;
const RECONNECT_BASE_MS = 1_000;
const RECONNECT_MAX_MS = 30_000;
const LS_SIGNAL_HISTORY = 'piyasapilot_signal_history';

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
    lgbm_prob?: number;
  };
}

interface TelegramPreferences {
  enabled: boolean;
  notify_signals: boolean;
  notify_trades: boolean;
  notify_system: boolean;
  notify_daily_summary: boolean;
  symbol_group: 'bist30' | 'bist100' | 'crypto' | 'custom';
  custom_symbols: string[];
  signal_types: string[];
  min_strength: number;
  min_consensus_ratio: number;
  cooldown_minutes: number;
  quiet_hours: string;
  consent_accepted?: boolean;
  consent_version?: string;
  consent_accepted_at?: string;
  consent_text?: string;
  selected_symbols?: string[];
}

export class SignalFeed {
  private container: HTMLElement;
  private ws: WebSocket | null = null;
  private signals: LiveSignal[] = [];
  private preferences: TelegramPreferences | null = null;
  private reconnectDelay = RECONNECT_BASE_MS;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private statusTimer: ReturnType<typeof setInterval> | null = null;
  private destroyed = false;

  constructor(container: HTMLElement) {
    this.container = container;
    this.restoreSignals();
    this.render();
    this.renderSignals();
    this.bindPreferenceControls();
    this._bindPriceAlertCreate();
    this.connect();
    this.pollTelegramStatus();
    void this.loadTelegramPreferences();
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
    el.title = sonHata ? `Son hata: ${sonHata}` : 'Telegram yapılandırması gizli tutuluyor';
  }

  private httpBase(): string {
    if (typeof window === 'undefined') return 'http://127.0.0.1:8000';
    return window.location.origin.replace(/^ws/, 'http');
  }

  private async loadTelegramPreferences(): Promise<void> {
    try {
      const resp = await fetch(`${this.httpBase()}/api/notifier/preferences`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      this.preferences = await resp.json() as TelegramPreferences;
      this.renderTelegramPreferences();
    } catch {
      const status = this.container.querySelector<HTMLElement>('#tg-pref-status');
      if (status) status.textContent = 'Ayarlar okunamadı';
    }
  }

  private collectTelegramPreferences(): TelegramPreferences {
    const checked = (id: string) => this.container.querySelector<HTMLInputElement>(`#${id}`)?.checked ?? false;
    const value = (id: string) => this.container.querySelector<HTMLInputElement | HTMLSelectElement>(`#${id}`)?.value ?? '';
    const customSymbols = value('tg-custom-symbols')
      .split(',')
      .map(s => s.trim().toUpperCase())
      .filter(Boolean);
    const signalTypes = Array.from(this.container.querySelectorAll<HTMLInputElement>('[data-tg-type]'))
      .filter(input => input.checked)
      .map(input => input.value);
    return {
      enabled: checked('tg-enabled'),
      notify_signals: checked('tg-notify-signals'),
      notify_trades: checked('tg-notify-trades'),
      notify_system: checked('tg-notify-system'),
      notify_daily_summary: checked('tg-notify-daily'),
      symbol_group: value('tg-symbol-group') as TelegramPreferences['symbol_group'],
      custom_symbols: customSymbols,
      signal_types: signalTypes,
      min_strength: Number(value('tg-min-strength') || 8),
      min_consensus_ratio: Number(value('tg-min-consensus') || 60) / 100,
      cooldown_minutes: Number(value('tg-cooldown') || 30),
      quiet_hours: value('tg-quiet-hours'),
      consent_accepted: checked('tg-consent-signal') && checked('tg-consent-data') && checked('tg-consent-stop'),
      consent_version: '2026-05-23',
      consent_text: [
        'Telegram bildirimleri yatırım tavsiyesi değildir; teknik sinyal bilgisidir.',
        'Telegram chat ID yalnızca bildirim amacıyla saklanır.',
        'Bildirimler /durdur komutuyla kapatılabilir.',
      ].join(' '),
    };
  }

  private async saveTelegramPreferences(): Promise<void> {
    const status = this.container.querySelector<HTMLElement>('#tg-pref-status');
    if (status) status.textContent = 'Kaydediliyor…';
    try {
      const prefs = this.collectTelegramPreferences();
      if (prefs.enabled && !prefs.consent_accepted) {
        throw new Error('CONSENT_REQUIRED');
      }
      const resp = await fetch(`${this.httpBase()}/api/notifier/preferences`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(prefs),
      });
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      if (prefs.consent_accepted) {
        void fetch(`${this.httpBase()}/api/auth/me/consents`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            consent_type: 'telegram_notifications',
            accepted: true,
            version: prefs.consent_version,
            text: prefs.consent_text,
          }),
        }).catch(() => undefined);
      }
      this.preferences = await resp.json() as TelegramPreferences;
      this.renderTelegramPreferences();
      if (status) status.textContent = 'Kaydedildi';
    } catch (err) {
      if (status) {
        status.textContent = err instanceof Error && err.message === 'CONSENT_REQUIRED'
          ? 'Telegram için üç yasal onay zorunlu'
          : 'Kaydedilemedi';
      }
    }
  }

  private escapeHtml(value: unknown): string {
    return String(value ?? '')
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  private bindPreferenceControls(): void {
    this.container.addEventListener('click', (evt) => {
      const target = evt.target as HTMLElement;
      if (target.id === 'tg-save-prefs') void this.saveTelegramPreferences();
      if (target.id === 'tg-bist30-preset') {
        const group = this.container.querySelector<HTMLSelectElement>('#tg-symbol-group');
        const strength = this.container.querySelector<HTMLInputElement>('#tg-min-strength');
        const consensus = this.container.querySelector<HTMLInputElement>('#tg-min-consensus');
        const cooldown = this.container.querySelector<HTMLInputElement>('#tg-cooldown');
        if (group) group.value = 'bist30';
        if (strength) strength.value = '8';
        if (consensus) consensus.value = '60';
        if (cooldown) cooldown.value = '30';
      }
    });
  }

  private renderTelegramPreferences(): void {
    const prefs = this.preferences;
    if (!prefs) return;
    const setChecked = (id: string, checked: boolean) => {
      const el = this.container.querySelector<HTMLInputElement>(`#${id}`);
      if (el) el.checked = checked;
    };
    const setValue = (id: string, value: string | number) => {
      const el = this.container.querySelector<HTMLInputElement | HTMLSelectElement>(`#${id}`);
      if (el) el.value = String(value);
    };
    setChecked('tg-enabled', prefs.enabled);
    setChecked('tg-notify-signals', prefs.notify_signals);
    setChecked('tg-notify-trades', prefs.notify_trades);
    setChecked('tg-notify-system', prefs.notify_system);
    setChecked('tg-notify-daily', prefs.notify_daily_summary);
    setValue('tg-symbol-group', prefs.symbol_group);
    setValue('tg-custom-symbols', prefs.custom_symbols.join(', '));
    setValue('tg-min-strength', prefs.min_strength);
    setValue('tg-min-consensus', Math.round(prefs.min_consensus_ratio * 100));
    setValue('tg-cooldown', prefs.cooldown_minutes);
    setValue('tg-quiet-hours', prefs.quiet_hours);
    setChecked('tg-consent-signal', Boolean(prefs.consent_accepted));
    setChecked('tg-consent-data', Boolean(prefs.consent_accepted));
    setChecked('tg-consent-stop', Boolean(prefs.consent_accepted));
    this.container.querySelectorAll<HTMLInputElement>('[data-tg-type]').forEach(input => {
      input.checked = prefs.signal_types.includes(input.value);
    });
    const summary = this.container.querySelector<HTMLElement>('#tg-pref-summary');
    if (summary) {
      const count = prefs.selected_symbols?.length ?? prefs.custom_symbols.length;
      const labels = { bist30: 'BIST 30', bist100: 'BIST 100', crypto: 'Kripto', custom: 'Özel/VİOP' };
      summary.textContent = `${labels[prefs.symbol_group]} · ${count} sembol · güç ≥ ${prefs.min_strength} · ${prefs.cooldown_minutes} dk`;
    }
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
    this.persistSignals();
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
    const label = isBuy ? TR.SIGNAL_STRONG_BUY : TR.SIGNAL_STRONG_SELL;

    const toast = document.createElement('div');
    toast.className = `toast toast-${isBuy ? 'buy' : 'sell'}`;
    toast.innerHTML = `
      <div class="toast-icon">${emoji}</div>
      <div class="toast-body">
        <div class="toast-title">${label} — ${this.escapeHtml(sig.symbol)} · Tavsiye değildir</div>
        <div class="toast-detail">${this.escapeHtml(sig.reason)}</div>
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

  /** Sinyal geçmişini localStorage'a kaydet */
  private persistSignals(): void {
    try {
      localStorage.setItem(LS_SIGNAL_HISTORY, JSON.stringify(this.signals));
    } catch { /* quota exceeded — sessizce geç */ }
  }

  /** Sinyal geçmişini localStorage'dan geri yükle */
  private restoreSignals(): void {
    try {
      const raw = localStorage.getItem(LS_SIGNAL_HISTORY);
      if (raw) {
        const parsed = JSON.parse(raw) as LiveSignal[];
        if (Array.isArray(parsed)) {
          this.signals = parsed.slice(0, MAX_SIGNALS);
        }
      }
    } catch { /* bozuk veri — boş başla */ }
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
        <div class="tg-control-panel">
          <div class="tg-control-header">
            <strong>Telegram filtreleri</strong>
            <span id="tg-pref-summary">Ayarlar yükleniyor…</span>
          </div>
          <div class="tg-consent-box">
            <label><input id="tg-consent-signal" type="checkbox"> Telegram bildirimlerinin yatırım tavsiyesi değil teknik sinyal bilgisi içerdiğini anlıyorum.</label>
            <label><input id="tg-consent-data" type="checkbox"> Telegram chat ID bilgisinin yalnızca bildirim amacıyla saklanacağını kabul ediyorum.</label>
            <label><input id="tg-consent-stop" type="checkbox"> Bildirimleri istediğim zaman /durdur komutuyla kapatabileceğimi biliyorum.</label>
          </div>
          <div class="tg-control-grid">
            <label><input id="tg-enabled" type="checkbox"> Aktif</label>
            <label><input id="tg-notify-signals" type="checkbox"> Teknik sinyal</label>
            <label><input id="tg-notify-trades" type="checkbox"> Sanal işlem</label>
            <label><input id="tg-notify-system" type="checkbox"> Sistem</label>
            <label><input id="tg-notify-daily" type="checkbox"> Günlük özet</label>
            <label>
              Grup
              <select id="tg-symbol-group">
                <option value="bist30" disabled>BIST 30 — lisans sonrası</option>
                <option value="bist100" disabled>BIST 100 — lisans sonrası</option>
                <option value="crypto">Kripto</option>
                <option value="custom">Özel / VİOP</option>
              </select>
            </label>
            <label>
              Min güç
              <input id="tg-min-strength" type="number" min="1" max="10" step="1">
            </label>
            <label>
              Konsensüs %
              <input id="tg-min-consensus" type="number" min="0" max="100" step="5">
            </label>
            <label>
              Cooldown dk
              <input id="tg-cooldown" type="number" min="0" max="1440" step="5">
            </label>
            <label>
              Sessiz saat
              <input id="tg-quiet-hours" type="text" placeholder="23:00-09:00">
            </label>
          </div>
          <div class="tg-type-row">
            <label><input data-tg-type type="checkbox" value="BUY"> BUY</label>
            <label><input data-tg-type type="checkbox" value="SELL"> SELL</label>
            <label><input data-tg-type type="checkbox" value="STRONG_BUY"> STRONG_BUY</label>
            <label><input data-tg-type type="checkbox" value="STRONG_SELL"> STRONG_SELL</label>
          </div>
          <textarea id="tg-custom-symbols" class="tg-custom-symbols" placeholder="Kripto özel semboller: BTCUSDT, ETHUSDT"></textarea>
          <div class="tg-actions">
            <button id="tg-bist30-preset" type="button" disabled title="BIST sinyal bildirimi lisans sonrası açılacak">BIST lisans sonrası</button>
            <button id="tg-save-prefs" type="button">Kaydet</button>
            <span id="tg-pref-status"></span>
          </div>
        </div>
        <div class="signal-feed-info">${TR.SIGNAL_FEED_INFO}</div>
        <div class="legal-notice signal-disclaimer">${TR.SIGNAL_DISCLAIMER}</div>
        <div class="legal-notice data-license-notice">${TR.MARKET_DATA_NOTICE}</div>
        <div id="signal-feed-list" class="signal-feed-list">
          <div class="signal-feed-empty">${TR.CONNECTING}…</div>
        </div>

        <!-- Fiyat Alarmları -->
        <div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,.08)">
          <h3 style="font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;
                     color:#64748B;margin:0 0 12px">Fiyat Alarmları</h3>
          <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px">
            <input id="pa-symbol" type="text" placeholder="Sembol (THYAO)" maxlength="20"
              style="flex:1;min-width:80px;padding:5px 8px;border-radius:6px;font-size:12px;
                     background:var(--bg,#0F172A);border:1px solid rgba(255,255,255,.15);color:#F8FAFC">
            <input id="pa-target" type="number" placeholder="Hedef fiyat" step="any"
              style="flex:1;min-width:100px;padding:5px 8px;border-radius:6px;font-size:12px;
                     background:var(--bg,#0F172A);border:1px solid rgba(255,255,255,.15);color:#F8FAFC">
            <select id="pa-direction"
              style="padding:5px 8px;border-radius:6px;font-size:12px;
                     background:var(--bg,#0F172A);border:1px solid rgba(255,255,255,.15);color:#F8FAFC">
              <option value="above">▲ Üstünde</option>
              <option value="below">▼ Altında</option>
            </select>
            <input id="pa-note" type="text" placeholder="Not (isteğe bağlı)"
              style="flex:2;min-width:100px;padding:5px 8px;border-radius:6px;font-size:12px;
                     background:var(--bg,#0F172A);border:1px solid rgba(255,255,255,.15);color:#F8FAFC">
            <button id="pa-create-btn"
              style="padding:5px 14px;border-radius:6px;background:#3B82F6;color:#fff;
                     border:none;font-size:12px;cursor:pointer;font-weight:600">+ Ekle</button>
          </div>
          <div id="price-alerts-list"></div>
        </div>
      </div>
    `;
    // Fiyat alarmlarını yükle
    void this.loadPriceAlerts();
  }

  private _bindPriceAlertCreate(): void {
    this.container.querySelector('#pa-create-btn')?.addEventListener('click', () => {
      void this.createPriceAlert();
    });
  }

  private renderSignals(): void {
    const list = this.container.querySelector<HTMLElement>('#signal-feed-list');
    if (!list) return;
    if (this.signals.length === 0) {
      list.innerHTML = `<div class="signal-feed-empty">${TR.SIGNAL_FEED_EMPTY}</div>`;
      return;
    }
    list.innerHTML = this.signals.map((sig, i) =>
      this.signalHTML(sig, i)
    ).join('');

    // Kanıt paneli: her signal-item tıklandığında detay modalı açılır
    list.querySelectorAll<HTMLElement>('[data-sig-idx]').forEach(el => {
      el.addEventListener('click', (e) => {
        if ((e.target as HTMLElement).closest('button')) return;
        const idx = parseInt(el.dataset['sigIdx'] ?? '0', 10);
        const sig = this.signals[idx];
        if (sig) this.showSignalEvidence(sig);
      });
    });
  }

  // ─── Sinyal Kanıt Paneli ───────────────────────────────────────────────────

  private showSignalEvidence(sig: LiveSignal): void {
    const existing = document.getElementById('sig-evidence-modal');
    if (existing) existing.remove();

    const isBuy = sig.signal_type === 'BUY' || sig.signal_type === 'STRONG_BUY';
    const sigColor = isBuy ? '#10B981' : '#EF4444';
    const sigLabel = { BUY:'AL', SELL:'SAT', STRONG_BUY:'GÜÇLÜ AL', STRONG_SELL:'GÜÇLÜ SAT' }[sig.signal_type] ?? sig.signal_type;

    const m = sig.metadata ?? {};
    const evidenceRows: [string, string][] = [];
    if (m.rsi             !== undefined) evidenceRows.push(['RSI (14)',            m.rsi.toFixed(1)]);
    if (m.trend           !== undefined) evidenceRows.push(['Trend',               String(m.trend)]);
    if (m.atr             !== undefined) evidenceRows.push(['ATR',                 m.atr.toFixed(4)]);
    if (m.volatility_pct  !== undefined) evidenceRows.push(['Volatilite %',        m.volatility_pct.toFixed(2) + '%']);
    if (m.buy_count       !== undefined && m.total_strategies !== undefined)
      evidenceRows.push(['Strateji Oyu (AL)',  `${m.buy_count}/${m.total_strategies}`]);
    if (m.sell_count      !== undefined && m.total_strategies !== undefined)
      evidenceRows.push(['Strateji Oyu (SAT)', `${m.sell_count}/${m.total_strategies}`]);
    if (m.consensus_ratio !== undefined) evidenceRows.push(['Konsensüs Oranı',     (m.consensus_ratio * 100).toFixed(0) + '%']);
    if (m.lgbm_prob       !== undefined) evidenceRows.push(['LGBM Olasılık',       (m.lgbm_prob * 100).toFixed(0) + '%']);

    const rowsHTML = evidenceRows.map(([k, v]) =>
      `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px">
        <span style="color:#94A3B8">${this.escapeHtml(k)}</span>
        <span style="color:#F8FAFC;font-weight:500">${this.escapeHtml(v)}</span>
      </div>`
    ).join('');

    const modal = document.createElement('div');
    modal.id = 'sig-evidence-modal';
    modal.style.cssText = `
      position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:1000;
      display:flex;align-items:center;justify-content:center;padding:16px;`;
    modal.innerHTML = `
      <div style="background:#1E293B;border:1px solid rgba(255,255,255,.12);border-radius:14px;
                  padding:20px 24px;max-width:460px;width:100%;max-height:80vh;overflow-y:auto;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;">
          <span style="background:${sigColor}22;color:${sigColor};padding:4px 12px;border-radius:20px;
                       font-weight:700;font-size:13px;">${sigLabel}</span>
          <span style="color:#F8FAFC;font-size:18px;font-weight:700">${this.escapeHtml(sig.symbol)}</span>
          <span style="color:#94A3B8;font-size:13px">@ ${formatNumber(sig.price, sig.price < 1 ? 6 : 4)}</span>
          <button id="ev-close" style="margin-left:auto;background:none;border:none;
                  color:#94A3B8;font-size:18px;cursor:pointer;">✕</button>
        </div>

        <div style="font-size:11px;color:#64748B;margin-bottom:12px;line-height:1.5;">
          Strateji: <strong style="color:#94A3B8">${this.escapeHtml(sig.strategy_id)}</strong> ·
          Zaman dilimi: <strong style="color:#94A3B8">${this.escapeHtml(sig.interval || '—')}</strong> ·
          Güç: <strong style="color:#94A3B8">${sig.strength}/10</strong> ·
          ${new Date(sig.ts).toLocaleString('tr-TR')}
        </div>

        <div style="background:rgba(255,255,255,.04);border-radius:8px;padding:10px 14px;
                    margin-bottom:14px;font-size:12px;color:#94A3B8;line-height:1.5;">
          <strong style="color:#CBD5E1">Neden:</strong> ${this.escapeHtml(sig.reason)}
        </div>

        ${evidenceRows.length > 0 ? `
        <h4 style="font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:.06em;
                   color:#64748B;margin:0 0 8px;">Gösterge Kanıtı</h4>
        <div>${rowsHTML}</div>` : ''}

        <div style="margin-top:14px;padding:10px;background:rgba(239,68,68,.06);border-radius:8px;
                    font-size:10px;color:#94A3B8;line-height:1.5;">
          ⚠️ Bu teknik sinyal bilgisidir. Yatırım tavsiyesi değildir.
          Geçmiş performans gelecek sonuçların garantisi değildir.
        </div>
      </div>`;

    document.body.appendChild(modal);
    modal.querySelector('#ev-close')?.addEventListener('click', () => modal.remove());
    modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });
  }

  // ─── Fiyat Alarmları ─────────────────────────────────────────────────────

  private _priceAlerts: Array<{ id: number; symbol: string; target: number; direction: string; note?: string; triggered: number }> = [];

  async loadPriceAlerts(): Promise<void> {
    type PA = { id: number; symbol: string; target: number; direction: string; note?: string; triggered: number };
    try {
      const res = await fetch('/api/alerts/price?active_only=false');
      if (!res.ok) return;
      const data = await res.json() as { alerts: PA[] };
      this._priceAlerts = data.alerts ?? [];
      this.renderPriceAlerts();
    } catch { /* sessizce geç */ }
  }

  private renderPriceAlerts(): void {
    const el = this.container.querySelector('#price-alerts-list');
    if (!el) return;

    if (this._priceAlerts.length === 0) {
      el.innerHTML = '<div style="font-size:12px;color:var(--text-dim);padding:8px 0">Aktif fiyat alarmı yok.</div>';
      return;
    }

    el.innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:12px;">
        <thead>
          <tr style="text-align:left;border-bottom:1px solid rgba(255,255,255,.08)">
            <th style="padding:4px 8px 6px 0;color:#64748B;font-weight:600;font-size:10px;text-transform:uppercase">Sembol</th>
            <th style="padding:4px 8px 6px;color:#64748B;font-weight:600;font-size:10px;text-transform:uppercase">Hedef</th>
            <th style="padding:4px 8px 6px;color:#64748B;font-weight:600;font-size:10px;text-transform:uppercase">Yön</th>
            <th style="padding:4px 8px 6px;color:#64748B;font-weight:600;font-size:10px;text-transform:uppercase">Durum</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          ${this._priceAlerts.map(a => `
            <tr style="border-bottom:1px solid rgba(255,255,255,.03)">
              <td style="padding:5px 8px 5px 0;font-weight:600;color:#F8FAFC">${this.escapeHtml(a.symbol)}</td>
              <td style="padding:5px 8px;color:#F8FAFC">${formatNumber(a.target, 4)}</td>
              <td style="padding:5px 8px;color:${a.direction === 'above' ? '#10B981' : '#EF4444'}">
                ${a.direction === 'above' ? '▲ Üstünde' : '▼ Altında'}
              </td>
              <td style="padding:5px 8px;color:${a.triggered ? '#64748B' : '#10B981'}">
                ${a.triggered ? '✓ Tetiklendi' : '⏳ Bekliyor'}
              </td>
              <td style="padding:5px 0 5px 8px">
                <button class="del-alert-btn" data-aid="${a.id}"
                  style="background:none;border:none;color:#EF4444;cursor:pointer;font-size:12px">✕</button>
              </td>
            </tr>`).join('')}
        </tbody>
      </table>`;

    el.querySelectorAll<HTMLButtonElement>('.del-alert-btn').forEach(btn => {
      btn.addEventListener('click', async () => {
        const aid = parseInt(btn.dataset['aid'] ?? '0', 10);
        await fetch(`/api/alerts/price/${aid}`, { method: 'DELETE' });
        void this.loadPriceAlerts();
      });
    });
  }

  private async createPriceAlert(): Promise<void> {
    const sym = (this.container.querySelector<HTMLInputElement>('#pa-symbol'))?.value.trim().toUpperCase();
    const tgt = parseFloat((this.container.querySelector<HTMLInputElement>('#pa-target'))?.value ?? '');
    const dir = (this.container.querySelector<HTMLSelectElement>('#pa-direction'))?.value;
    const note = (this.container.querySelector<HTMLInputElement>('#pa-note'))?.value.trim() ?? '';
    if (!sym || isNaN(tgt) || !dir) return;

    await fetch('/api/alerts/price', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ symbol: sym, target: tgt, direction: dir, note }),
    });
    // Form temizle
    const syminp = this.container.querySelector<HTMLInputElement>('#pa-symbol');
    const tgtinp = this.container.querySelector<HTMLInputElement>('#pa-target');
    const noteinp = this.container.querySelector<HTMLInputElement>('#pa-note');
    if (syminp)  syminp.value = '';
    if (tgtinp)  tgtinp.value = '';
    if (noteinp) noteinp.value = '';
    void this.loadPriceAlerts();
  }

  private signalHTML(sig: LiveSignal, idx: number): string {
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
      if (sig.metadata.lgbm_prob !== undefined) {
        parts.push(`LGBM: ${(sig.metadata.lgbm_prob * 100).toFixed(0)}%`);
      }
      if (parts.length > 0) {
        metadataHTML = `<div class="signal-consensus">${parts.join(' · ')}</div>`;
      }
    }

    return `
      <div class="signal-item ${isStrong ? 'signal-strong' : ''}" data-sig-idx="${idx}" style="cursor:pointer" title="Kanıt detayı için tıklayın">
        <div class="signal-header">
          <span class="signal-badge ${badgeClass}">${badgeLabel}</span>
          <span class="signal-symbol">${this.escapeHtml(sig.symbol)}</span>
          <span class="signal-price">${formatNumber(sig.price, decimals)}</span>
          <span class="signal-time">${time}</span>
        </div>
        <div class="signal-meta">
          <span class="signal-strategy">${this.escapeHtml(sig.strategy_id)}</span>
          ${sig.interval ? `<span class="signal-interval">${this.escapeHtml(sig.interval)}</span>` : ''}
          <span class="signal-strength">${stars}</span>
        </div>
        <div class="signal-reason">${this.escapeHtml(sig.reason)}</div>
        <div class="signal-legal">${TR.SIGNAL_DISCLAIMER}</div>
        ${metadataHTML}
      </div>
    `;
  }
}
