# PiyasaPilot — Kişisel Veri Envanteri

> Son güncelleme: 2026-05-23
> Amaç: KVKK m.12 kapsamında işlenen kişisel veri kategorilerini, amaçları, hukuki dayanakları ve saklama yaklaşımını teknik düzeyde izlenebilir yapmak.

## Veri Sorumlusu

Canlı yayın öncesinde şirket/işletmeci unvanı, MERSİS/vergi bilgisi, adres ve başvuru e-postaları kesinleştirilecektir. Varsayılan başvuru kanalları:

- Genel: `destek@piyasapilot.com`
- KVKK başvuruları: `kvkk@piyasapilot.com`
- Veri lisansı talepleri: `veri@piyasapilot.com`

## Tablo Bazlı Envanter

| Tablo / Kayıt | Kişisel Veri | Amaç | Hukuki Dayanak | Saklama |
|---|---|---|---|---|
| `users` | e-posta, ad-soyad, avatar URL, rol, dil, giriş zamanı | Hesap oluşturma, kimlik doğrulama, plan yönetimi | Sözleşmenin ifası, meşru menfaat | Hesap aktif olduğu sürece; silme talebinde anonimleştirme |
| `refresh_tokens` | IP, user-agent, cihaz adı | Oturum güvenliği, token iptali | Meşru menfaat, güvenlik | Token süresi ve güvenlik denetimi süresince |
| `oauth_accounts` | OAuth sağlayıcı ID, token metadata | Google/GitHub ile giriş | Sözleşmenin ifası, açık kullanıcı aksiyonu | Hesap aktif olduğu sürece; silme talebinde silinir |
| `user_settings` | tercih, favori sembol, bildirim tercihi | Ürün deneyimi ve tercih saklama | Sözleşmenin ifası | Hesap aktif olduğu sürece; silme talebinde temizlenir |
| `user_subscriptions` | Stripe müşteri/abonelik ID, plan durumu | Abonelik ve ödeme yönetimi | Sözleşmenin ifası, hukuki yükümlülük | Vergi/ticaret mevzuatı süresince |
| `stripe_events` | Stripe event ID ve işlem tipi | Webhook idempotency ve muhasebe izi | Meşru menfaat, hukuki yükümlülük | Denetim süresince |
| `daily_usage` | kullanıcı ID, kullanım sayaçları | Kota ve kötüye kullanım önleme | Sözleşmenin ifası, meşru menfaat | Operasyonel raporlama süresince |
| `audit_log` | kullanıcı ID, IP, user-agent, aksiyon | Güvenlik, admin denetimi, kötüye kullanım önleme | Meşru menfaat, hukuki yükümlülük | Güvenlik denetimi süresince |
| `api_keys` | API key hash, ad, kullanım zamanı | API erişimi ve yetkilendirme | Sözleşmenin ifası | Anahtar silinene veya hesap kapanana kadar |
| `user_legal_consents` | onay tipi, zaman, IP, user-agent, metin versiyonu | Açık onay ispatı | Açık rıza, hukuki yükümlülük | Onayın ispatı için gerekli süre boyunca |
| `waitlist` | e-posta, kaynak | Bekleme listesi | Açık kullanıcı talebi | Talep geri çekilene kadar |
| `public_backtests` | run ID, public slug | Kullanıcı isteğiyle paylaşım | Sözleşmenin ifası | Paylaşım kaldırılana kadar |
| Telegram tercih dosyası | bildirim tercihi, onay versiyonu | Telegram bildirimleri | Açık onay | Onay geri alınana kadar |

## Silme / Anonimleştirme

`DELETE /api/auth/me` hesabı pasifleştirir ve doğrudan kimlik verilerini anonimleştirir. Fatura, ödeme, güvenlik ve hukuki ispat kayıtları mevzuat gerektirdiği sürece saklanabilir.

## Açık Onaylar

- Terms ve Privacy kabulü kayıt sırasında `user_legal_consents` içine yazılır.
- Pazarlama e-postası onayı varsayılan kapalıdır; kullanıcı ayrıca işaretlerse kaydedilir.
- Telegram bildirimleri varsayılan kapalıdır; üç ayrı onay kutusu işaretlenmeden aktif edilemez.
- Dijital hizmet/cayma hakkı bilgilendirmesi ücretli checkout öncesinde ayrıca alınır.

