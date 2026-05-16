import { pageShell } from './pageUtils.js';

export function renderChangelogPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Yenilikler', `
    <article class="legal-page">
      <h1>Yenilikler</h1>
      <h2>Mayıs 2026 - v1.2.0</h2>
      <ul>
        <li>Backtest Pro: Monte Carlo ve Walk-Forward akışı eklendi.</li>
        <li>KAP haberleri ve haber okundu sayacı iyileştirildi.</li>
        <li>Grafik timeframe değişiminde loading/retry davranışı eklendi.</li>
        <li>Koyu tema kontrastı ve public auth sayfaları düzenlendi.</li>
      </ul>
    </article>`);
}
