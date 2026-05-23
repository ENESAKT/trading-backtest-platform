import { pageShell } from '../pageUtils.js';

export function renderLegalInfoPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Yasal Bilgilendirme', `
    <article class="legal-page">
      <h1>Yasal Bilgilendirme</h1>
      <p>Son güncelleme: 2026-05-23</p>

      <h2>Uygulamanın niteliği</h2>
      <p>PiyasaPilot bir finansal araştırma, eğitim, backtest ve paper trading platformudur. SPK lisanslı yatırım kuruluşu değildir; yatırım danışmanlığı, portföy yönetimi, aracılık veya gerçek emir iletim hizmeti vermez.</p>

      <h2>Veri kaynakları ve lisans durumu</h2>
      <table class="legal-table">
        <thead><tr><th>Piyasa</th><th>Kaynak</th><th>Durum</th></tr></thead>
        <tbody>
          <tr><td>Kripto</td><td>Binance public feed</td><td>Aktif; sağlayıcı kullanım şartları izlenir.</td></tr>
          <tr><td>BIST</td><td>Lisanslı sağlayıcı bekleniyor</td><td>Fiyat, grafik ve sinyal gösterimi lisans tamamlanana kadar kapalı.</td></tr>
          <tr><td>VİOP</td><td>Lisanslı sağlayıcı bekleniyor</td><td>Henüz aktif değildir.</td></tr>
          <tr><td>KAP haberleri</td><td>KAP/RSS ve ilgili public kaynaklar</td><td>Kullanım koşulları ayrıca doğrulanacaktır.</td></tr>
        </tbody>
      </table>

      <h2>Yatırım tavsiyesi değildir</h2>
      <p>Platform içindeki sinyaller, analizler, screener sonuçları, backtest raporları ve Telegram bildirimleri yatırım tavsiyesi değildir. Bu içerikler teknik analiz göstergeleri ve eğitim materyalleridir.</p>

      <h2>Veri doğruluğu garantisi yoktur</h2>
      <p>Verilerin doğruluğu, eksiksizliği veya gerçek zamanlılığı garanti edilmez. Her veri ekranında kaynak ve kalite durumu ayrıca gösterilir.</p>

      <h2>Kullanıcı sorumluluğu</h2>
      <p>Yatırım kararlarının tüm mali, vergisel ve hukuki sonuçlarından kullanıcı sorumludur. Gerekli hallerde lisanslı yatırım danışmanı, veri lisansı uzmanı, hukukçu veya mali müşavir görüşü alınmalıdır.</p>

      <h2>İletişim kanalları</h2>
      <p>Genel destek: destek@piyasapilot.com · KVKK başvuruları: kvkk@piyasapilot.com · Veri lisansı talepleri: veri@piyasapilot.com</p>
    </article>`);
}
