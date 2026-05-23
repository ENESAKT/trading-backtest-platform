import { pageShell } from '../pageUtils.js';

export function renderPrivacyPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Gizlilik Politikası', `
    <article class="legal-page">
      <h1>Gizlilik Politikası ve KVKK Aydınlatma Metni</h1>
      <p>Son güncelleme: 2026-05-23</p>

      <h2>Veri sorumlusu</h2>
      <p>Veri sorumlusu işletmeci adı ve adresi canlı yayın öncesinde tamamlanacaktır. KVKK başvuruları için varsayılan kanal kvkk@piyasapilot.com adresidir.</p>

      <h2>İşlenen kişisel veriler</h2>
      <p>Hesap ve hizmet sunumu kapsamında ad-soyad, e-posta, parola özeti, OAuth kimliği, abonelik/fatura bilgileri, IP adresi, cihaz ve tarayıcı bilgisi, kullanım logları, uygulama tercihleri ve kullanıcı onayı varsa Telegram chat ID işlenebilir.</p>

      <h2>İşleme amaçları ve hukuki dayanak</h2>
      <p>Veriler; hesap oluşturma, oturum güvenliği, abonelik yönetimi, ödeme/fatura süreci, hata tespiti, kötüye kullanımın önlenmesi, kullanıcı tercihlerini saklama ve açık onay verilen bildirimleri göndermek için işlenir. Hukuki dayanaklar sözleşmenin ifası, veri sorumlusunun meşru menfaati, hukuki yükümlülük ve açık rızadır.</p>

      <h2>Aktarım ve üçüncü taraflar</h2>
      <p>Kart bilgileri PiyasaPilot sunucularında saklanmaz; ödeme akışı Stripe tarafından yürütülür. Telegram bildirimleri kullanıcı onayıyla Telegram altyapısı üzerinden gönderilir. E-posta sağlayıcısı, barındırma hizmeti, hata izleme ve yetkili kamu kurumlarıyla sınırlı veri aktarımı yapılabilir.</p>

      <h2>Saklama süreleri</h2>
      <p>Aktif hesap verileri hesap açık kaldığı sürece; ödeme ve fatura kayıtları mevzuat gereği gerekli süre boyunca; güvenlik logları makul güvenlik süresi boyunca; Telegram chat ID bilgisi bot devre dışı bırakılana veya silme talebi tamamlanana kadar saklanır.</p>

      <h2>Kullanıcı hakları</h2>
      <p>KVKK m.11 kapsamında verilerinize erişim, düzeltme, silme veya anonimleştirme, işlemeye itiraz, aktarım bilgisi talep etme ve zararın giderilmesini isteme haklarınız vardır. Başvurular kvkk@piyasapilot.com üzerinden alınır ve 30 gün içinde yanıtlanır.</p>

      <h2>Güvenlik</h2>
      <p>Parolalar düz metin saklanmaz; oturumlar güvenli cookie yapısıyla yönetilir. Production ortamında HTTPS, güvenli secret yönetimi, erişim kontrolü ve log denetimi zorunludur.</p>

      <h2>Pazarlama iletişimi</h2>
      <p>Promosyon ve pazarlama içerikleri yalnızca ayrı açık onay alınan kullanıcılara gönderilir. Doğrulama, şifre sıfırlama, ödeme ve güvenlik bildirimleri işlem mesajı niteliğindedir.</p>

      <p class="legal-review-note">Bu metin KVKK uyum taslağıdır; canlı yayın öncesinde KVKK/GDPR uzmanı tarafından gözden geçirilmelidir.</p>
    </article>`);
}
