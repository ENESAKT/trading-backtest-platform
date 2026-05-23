import { pageShell } from '../pageUtils.js';

export function renderCookiesPage(container: HTMLElement): void {
  container.innerHTML = pageShell('Çerez Politikası', `
    <article class="legal-page">
      <h1>Çerez Politikası</h1>
      <p>Son güncelleme: 2026-05-23</p>

      <h2>Zorunlu çerezler</h2>
      <p>Oturum, CSRF/güvenlik ve temel hizmet sürekliliği için zorunlu çerezler kullanılabilir. Bu çerezler platformun çalışması için gereklidir ve ayrıca açık onay gerektirmez.</p>

      <h2>Tercih çerezleri</h2>
      <p>Tema, dil, görünüm, son sekme, favori semboller ve çerez tercihi gibi ayarlar tarayıcı localStorage alanında saklanabilir. Bu kayıtlar kullanıcı deneyimini kişiselleştirmek için kullanılır.</p>

      <h2>Analitik ve hata izleme</h2>
      <p>Sentry veya benzeri analitik/hata izleme araçları production ortamında etkinleştirilirse kullanıcıya açık şekilde bildirilir ve gerekli hallerde açık onay alınır. Reklam veya davranışsal hedefleme çerezi varsayılan olarak kullanılmaz.</p>

      <h2>Ödeme çerezleri</h2>
      <p>Stripe ödeme akışı sırasında dolandırıcılık önleme, ödeme güvenliği ve oturum sürekliliği için kendi çerezlerini kullanabilir. Bu çerezler ödeme hizmetinin güvenli çalışması için zorunludur.</p>

      <h2>Üçüncü taraflar</h2>
      <p>Gömülü içerik, ödeme, hata izleme veya bildirim sağlayıcıları kendi çerez ve benzer teknolojilerini kullanabilir. Bu sağlayıcıların politikaları ayrıca geçerlidir.</p>

      <h2>Tercihleri yönetme</h2>
      <p>Tarayıcı ayarlarınızdan çerezleri silebilir veya engelleyebilirsiniz. Zorunlu çerezleri engellemeniz halinde oturum açma, ödeme veya güvenlik özellikleri çalışmayabilir.</p>

      <p class="legal-review-note">Bu metin KVKK Çerez Kılavuzu dikkate alınarak hazırlanmış teknik taslaktır; canlı yayın öncesinde hukukçu tarafından gözden geçirilmelidir.</p>
    </article>`);
}
