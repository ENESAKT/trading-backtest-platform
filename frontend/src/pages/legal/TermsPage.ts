import { pageShell } from '../pageUtils.js';

export function renderTermsPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Kullanım Koşulları', `
    <article class="legal-page">
      <h1>Kullanım Koşulları</h1>
      <p>Son güncelleme: 2026-05-16</p>
      <h2>Hizmet kapsamı</h2>
      <p>PiyasaPilot araştırma, backtest, sinyal izleme ve paper trading amaçlı bir yazılımdır. Gerçek emir gönderimi desteklenmez.</p>
      <h2>Yatırım tavsiyesi değildir</h2>
      <p>Uygulamadaki veri, grafik, sinyal ve raporlar yalnızca bilgilendirme amaçlıdır.</p>
      <h2>Kullanıcı sorumluluğu</h2>
      <p>Strateji kararları, risk yönetimi ve finansal sonuçlardan kullanıcı sorumludur.</p>
    </article>`);
}
