import { pageShell } from '../pageUtils.js';

export function renderTermsPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Kullanım Koşulları', `
    <article class="legal-page">
      <h1>Kullanım Koşulları</h1>
      <p>Son güncelleme: 2026-05-23</p>

      <h2>Taraflar ve kapsam</h2>
      <p>PiyasaPilot, işletmeci bilgileri canlı yayından önce bu sayfada tamamlanacak olan bir finansal araştırma ve eğitim platformudur. Platformu kullanarak bu koşulları, gizlilik politikasını ve çerez politikasını kabul etmiş olursunuz.</p>

      <h2>Hizmet kapsamı</h2>
      <p>Platform; grafik, teknik analiz, backtest simülasyonu, eğitim içerikleri, haber/KAP takibi, sanal portföy ve paper trading araçları sunar. Platform aracılık hizmeti, portföy yönetimi veya yatırım danışmanlığı hizmeti sunmaz.</p>

      <h2>Yatırım tavsiyesi değildir</h2>
      <p>Uygulamadaki veri, grafik, sinyal, tarama sonucu, eğitim içeriği, backtest raporu ve Telegram bildirimi herhangi bir menkul kıymetin alınması, satılması veya elde tutulması yönünde tavsiye niteliği taşımaz. Finansal kararlarınızı kendi araştırmanız, risk toleransınız ve gerekiyorsa SPK lisanslı yatırım danışmanınızla değerlendirerek vermelisiniz.</p>

      <h2>Veri kaynakları ve lisans durumu</h2>
      <p>Kripto verileri Binance public feed üzerinden sağlanabilir ve sağlayıcı kullanım şartlarına tabidir. BIST ve VİOP fiyat/grafik/sinyal gösterimleri lisanslı veri sağlayıcı bağlantısı tamamlanana kadar kapalıdır. KAP haberleri kamuya açık kaynaklardan izlenir; yeniden dağıtım koşulları ayrıca değerlendirilecektir.</p>

      <h2>Gerçek emir gönderimi yoktur</h2>
      <p>"Sanal Al", "Sanal Sat", paper trading, backtest ve portföy simülasyonu yalnızca eğitim ve araştırma amaçlıdır. Gerçek para, gerçek piyasa emri veya broker bağlantısı söz konusu değildir.</p>

      <h2>Kullanıcı sorumluluğu</h2>
      <p>Platformdaki bilgilerin doğruluğu, eksiksizliği veya gerçek zamanlılığı garanti edilmez. Kullanıcı, platformdaki içeriklere dayanarak aldığı kararların mali, vergisel ve hukuki sonuçlarından kendisi sorumludur.</p>

      <h2>Abonelik, iptal ve cayma hakkı</h2>
      <p>Ücretli planlar Stripe üzerinden tahsil edilir. Abonelik iptali, dönem sonu erişim, iade ve cayma hakkı koşulları ödeme akışında ve fatura bilgilerinde ayrıca gösterilir. Dijital hizmetin hemen başlaması istenirse cayma hakkına ilişkin açık onay gerekebilir.</p>

      <h2>Yasaklı kullanım</h2>
      <p>Platform; piyasa manipülasyonu, yanıltıcı paylaşım, lisanssız veri yeniden dağıtımı, scraping, üçüncü kişilerin haklarını ihlal veya yasa dışı amaçlarla kullanılamaz. Platform 18 yaşını doldurmuş kullanıcılar içindir.</p>

      <h2>Sorumluluk sınırlaması</h2>
      <p>Yasal zorunluluklar saklı kalmak kaydıyla PiyasaPilot; veri gecikmesi, veri hatası, bağlantı kesintisi, simülasyon varsayımı veya kullanıcı kararlarından doğan zararlardan sorumlu tutulamaz.</p>

      <h2>Uygulanacak hukuk</h2>
      <p>Bu koşullar Türk hukukuna tabidir. Uyuşmazlıklarda öncelikle arabuluculuk dahil yasal başvuru yolları işletilir; yetkili mahkeme bilgisi işletmeci tüzel kişiliği kesinleştiğinde tamamlanacaktır.</p>

      <p class="legal-review-note">Bu metin teknik uyum taslağıdır; canlı yayın öncesinde hukukçu tarafından son kez gözden geçirilmelidir.</p>
    </article>`);
}
