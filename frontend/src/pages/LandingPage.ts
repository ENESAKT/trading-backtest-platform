import { pageShell } from './pageUtils.js';

const demoBars = [18, 24, 21, 29, 34, 31, 38, 43, 39, 46, 52, 48, 57, 61, 58, 66, 70, 64, 73, 78, 75, 82, 88, 84, 91, 96, 93, 101, 108, 104];

export function renderLandingPage(container: HTMLElement): void {
  const points = demoBars.map((v, i) => `${(i / (demoBars.length - 1)) * 100},${110 - v}`).join(' ');
  container.innerHTML = pageShell('PiyasaPilot', `
    <section class="landing-hero">
      <div class="hero-copy">
        <p class="eyebrow">BIST, kripto ve global piyasalar</p>
        <h1>Algoritmik trading terminali</h1>
        <p>Strateji fikrini kurala çevir, gerçek veriyle test et, riski gör ve paper trading akışını tek ekrandan yönet.</p>
        <div class="hero-actions">
          <a class="btn btn-warning" href="/register">Ücretsiz Başla</a>
          <a class="btn btn-outline-warning" href="/pricing">Planları İncele</a>
        </div>
        <div class="hero-counters">
          <span><b>57</b> eğitim</span>
          <span><b>9</b> strateji</span>
          <span><b>0</b> gerçek emir</span>
        </div>
      </div>
      <div class="demo-terminal" aria-label="Statik BTCUSDT demo grafiği">
        <div class="demo-head"><strong>BTCUSDT</strong><span>Statik demo</span></div>
        <svg viewBox="0 0 100 120" role="img" aria-label="30 günlük örnek fiyat çizgisi">
          <polyline points="${points}" fill="none" stroke="var(--amber)" stroke-width="3" vector-effect="non-scaling-stroke"/>
          <line x1="0" y1="92" x2="100" y2="92" stroke="var(--border2)" stroke-width="1"/>
          <line x1="0" y1="55" x2="100" y2="55" stroke="var(--border2)" stroke-width="1"/>
        </svg>
      </div>
    </section>
    <section class="feature-grid">
      ${['Grafik Lab', 'Backtest Pro', 'KAP Haberleri', 'Portfolio', 'Sinyaller', 'Eğitimler'].map((name) => `
        <article class="feature-card">
          <div class="feature-shot"></div>
          <h2>${name}</h2>
          <p>Trading araştırması için sade, ölçülebilir ve paper-mode güvenli iş akışı.</p>
        </article>`).join('')}
    </section>
    <section class="pricing-strip">
      <h2>Planınızı seçin</h2>
      <div class="mini-plans">
        <a href="/register"><b>Ücretsiz</b><span>$0</span></a>
        <a class="featured" href="/pricing"><b>Pro</b><span>$19.99/ay</span></a>
        <a href="/pricing"><b>Ultra</b><span>$49.99/ay</span></a>
      </div>
    </section>`);
}
