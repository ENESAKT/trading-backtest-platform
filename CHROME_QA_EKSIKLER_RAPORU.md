# PiyasaPilot — Chrome QA Eksik/Yanlış Kısımlar Raporu

> Tarih: 2026-05-16  
> Araç: `@chrome` gerçek Chrome profili + lokal Vite dev server  
> URL: `http://127.0.0.1:5173`  
> Amaç: Uygulamada eksik, yanlış, riskli, yanıltıcı veya tamamlanmamış görünen hiçbir noktayı atlamadan yazmak.

---

## 1. Test Kapsamı

Chrome ile açılıp kontrol edilen sayfalar:

- `/`
- `/pricing`
- `/login`
- `/register`
- `/waitlist`
- `/payment/success`
- `/settings`
- `/admin`
- `/shared/olmayan-slug`
- `/legal/terms`
- `/legal/privacy`
- `/legal/cookies`
- `/app`
- `/app` içi sekmeler: Grafik, Portföy, Strateji, Tarama, Sinyaller, Eğitimler, Mali Analiz, Haberler

Ek kontrol türleri:

- Public route shell sızıntısı
- URL deep-link davranışı
- Aktif tab durumu
- Scroll/overflow/clipping
- Boş durumlar
- Disabled butonlar
- Console/network gürültüsü
- Auth gerektiren sayfa davranışı
- Ürün metni ve canlı entegrasyon iddiaları
- Mobil/topbar riskleri için DOM ölçümleri

Çalıştırılan doğrulama:

- `cd frontend && npm run typecheck` başarılı.

---

## 2. Kısa Sonuç

Kod kalitesi önceki tura göre iyi durumda, public shell sızıntısı büyük ölçüde kapanmış. Fakat Chrome gerçek kullanımında hâlâ üretime çıkmadan önce kapatılması gereken ciddi ürün ve UX açıkları var.

En kritik bulgular:

1. `/app?tab=...` deep-link bozuk; son kaydedilen tab URL parametresini eziyor.
2. Misafir kullanıcı hâlâ `/app` terminaline girebiliyor; plan dokümanındaki “guest terminale giremez” kuralıyla çelişiyor.
3. Pricing ve payment success sayfaları canlı Stripe/lisans yokken kullanıcıya fazla kesin vaat veriyor.
4. Topbar ve bazı terminal panellerinde clipping/scroll davranışı hâlâ sorunlu.
5. NewsPanel API hatalarını sessizce yutuyor.
6. Register password toggle butonlarında erişilebilirlik etiketi eksik.
7. Sinyal geçmişi gerçek zamanlı/canlı sinyal gibi algılanabilecek şekilde kalıcı eski veriyi gösterebiliyor.
8. Canlı hesap/secret/deploy/lisans işleri hâlâ üretim bloklayıcı.

---

## 3. P0 — Üretim Öncesi Bloklayıcılar

### P0.1 · URL Deep-Link Bozuk: `?tab=` Parametresi Son Tab Tarafından Eziliyor

**Durum:** Açık hata.

**Chrome kanıtı:**

Chrome’da yeni tab açıp şu URL’ler tek tek denendi:

- `/app?tab=chart&symbol=BTCUSDT`
- `/app?tab=screener&symbol=BTCUSDT`
- `/app?tab=news&symbol=BTCUSDT`

Beklenen:

- `tab=chart` Grafik sekmesini açmalı.
- `tab=screener` Tarama sekmesini açmalı.
- `tab=news` Haberler sekmesini açmalı.

Gerçek:

- Hepsi son kaydedilmiş `news` sekmesine döndü.
- URL de `http://127.0.0.1:5173/app?tab=news&symbol=BTCUSDT` haline geldi.

**Kök neden:**

`frontend/src/app.ts` içinde önce localStorage’daki son tab okunup `showTab(initialTab, false)` çağrılıyor. Bu çağrı `persist=false` olsa bile URL’yi `history.replaceState` ile değiştiriyor. Sonra `applyUrlParams()` çalıştığında orijinal `?tab=chart` artık çoktan `?tab=news` olmuş oluyor.

İlgili yer:

- `frontend/src/app.ts:541-546` → `showTab()` her durumda URL sync yapıyor.
- `frontend/src/app.ts:553-555` → localStorage son tab hemen uygulanıyor.
- `frontend/src/app.ts:590-596` → URL parametresi geç okunuyor.
- `frontend/src/app.ts:597-601` → `symbol` parametresi varsa `openSymbol()` başka tab yönlendirmesi yapabilir.

**Risk:**

- Paylaşılan linkler yanlış sekmeyi açar.
- Kullanıcı `/app?tab=financials&symbol=THYAO.IS` gibi bir linke tıkladığında son açık sekmesi neyse ona düşebilir.
- E2E testleri localStorage temiz olduğu için bu hatayı kaçırabilir.

**Yapılacak:**

- İlk açılışta URL parametreleri localStorage’dan önce okunmalı.
- `showTab(tab, false)` URL’yi değiştirmemeli veya `syncUrl=false` gibi ayrı parametre almalı.
- `applyUrlParams()` içinde `symbol` açılırken hedef tab korunmalı; `openSymbol()` otomatik chart’a atıyorsa bu davranış opsiyonel yapılmalı.
- Yeni test eklenmeli: localStorage `piyasapilot_last_tab=news` iken `/app?tab=screener` açıldığında Tarama aktif kalmalı.

---

### P0.2 · Misafir Kullanıcı Terminale Girebiliyor

**Durum:** Plan kuralıyla çelişen açık.

**Beklenen ürün kuralı:**

Kök `YAPILACAKLAR.md` rol matrisinde misafir için “Terminal’e giremez” yazıyor.

**Chrome kanıtı:**

Giriş yapılmamış durumda `/app` açıldı. Terminal shell göründü:

- Topbar: Grafik, Portföy, Strateji, Tarama, Sinyaller, Eğitimler, Mali Analiz, Haberler
- Sidebar: PiyasaPilot sembol listesi
- Grafik ve diğer sekmeler erişilebilir durumda
- Sağ üstte hâlâ “Giriş Yap / Ücretsiz Kayıt” duruyor

**Risk:**

- Ücretsiz/pro/ultra plan gate modeli zayıflar.
- Misafir kullanıcı veri endpointlerini ve terminal bundle’ını tetikler.
- Ürün vaadi ile gerçek davranış ayrışır.
- Backend auth guard olsa bile frontend terminal deneyimi “girişsiz kullanılabilir” algısı verir.

**Yapılacak:**

- `/app` route’u frontend seviyesinde `requireAuth` benzeri guard ile korunmalı.
- Misafir `/app` açarsa `/login?next=/app` veya ürün dilli “Terminal için giriş gerekli” ekranına yönlendirilmeli.
- Public landing’deki “Terminale Git / Terminale dön” CTA’ları girişsiz kullanıcı için login’e gitmeli.
- E2E eklenmeli: unauth `/app` terminal shell render etmemeli.

---

### P0.3 · Canlı Stripe Olmadan Payment Success Sayfası Kesin Başarı Söylüyor

**Durum:** Yanıltıcı ürün/ödeme durumu.

**Chrome kanıtı:**

Girişsiz ve Stripe session olmadan `/payment/success` açıldı. Sayfa şu mesajı verdi:

`Pro planına hoş geldiniz`

ve:

`Backtest Pro, Scanner ve Telegram Bot özellikleri hesabınızda aktif hale gelir. Stripe webhook birkaç saniye içinde planı günceller.`

**Risk:**

- Kullanıcı ödeme yapmadan başarı sayfasını görebilir.
- Support/ödeme anlaşmazlığı doğurabilir.
- Webhook doğrulanmadan “Pro aktif” dili kullanılıyor.

**Yapılacak:**

- `/payment/success` `session_id` veya backend subscription check olmadan kesin başarı dili göstermemeli.
- Durumlar ayrılmalı:
  - `session_id yok` → “Ödeme doğrulanamadı”
  - `webhook bekleniyor` → “Ödeme alındı, plan güncelleniyor”
  - `subscription active` → “Pro/Ultra aktif”
- Giriş yoksa önce login veya “ödeme durumunu görmek için giriş yap” ekranı.
- Stripe canlı bağlanana kadar sayfa “test/entegrasyon bekliyor” güvenli dilde kalmalı.

---

### P0.4 · Pricing Sayfası Lisanssız “Canlı Veri” İddiası Taşıyor

**Durum:** Üretim riski.

**Chrome kanıtı:**

`/pricing` Ultra planında şu özellik görünüyor:

`Canlı veri`

Kök `YAPILACAKLAR.md` ise lisans yoksa Ultra’daki canlı veri iddiasının değiştirilmesini açık görev olarak bırakmış.

**Risk:**

- BIST/VIOP lisansı olmadan “canlı veri” iddiası hukuki ve ticari risk taşır.
- Kullanıcı beklentisi yanlış kurulur.
- Ödeme açıldığında iade/şikayet riski doğar.

**Yapılacak:**

- Lisans anlaşması tamamlanana kadar metin:
  - “Öncelikli veri akışı”
  - “Gecikmeli/güvenilir veri kaynakları”
  - “Lisanslı veri entegrasyonu hazır olduğunda”
  gibi güvenli dile çekilmeli.
- Ultra plan tooltip/alt not ile veri kapsamı açık yazılmalı.
- Lisans bağlanınca metin tekrar güncellenmeli.

---

## 4. P1 — Yüksek Öncelikli Ürün/UX Hataları

### P1.1 · Topbar Clipping Devam Ediyor

**Durum:** Açık görsel/ergonomi sorunu.

**Chrome kanıtı:**

Terminal içinde DOM ölçümleri:

- `.topbar-left`: `scrollWidth=170`, `clientWidth=152`
- `.topbar-tabs`: `scrollWidth=814`, `clientWidth=752`

Chrome metin çıkarımında marka alanı bazı yerlerde `P PiyasaPilot TERMİNAL` veya `Piya aPilot` gibi parçalı okunuyor. Bu hem görsel sıkışma hem erişilebilirlik açısından zayıf.

İlgili CSS:

- `frontend/style.css:397-405` → `.symbol-title` desktop’ta tamamen `display:none`.
- `frontend/style.css:487-488` → topbar yatay scroll var ama scrollbar gizlenmiş.
- `frontend/style.css:2466-2498` → mobil sıkıştırma hâlâ çok agresif.

**Risk:**

- Sekmelerin bir kısmı keşfedilemeyebilir.
- Scrollbar gizlendiği için kullanıcı daha fazla sekme olduğunu anlamaz.
- Marka/topbar metni kırpılmış görünür.

**Yapılacak:**

- Desktop’ta topbar için gerçek responsive kırılım tanımlanmalı.
- Sekmeler ikon+kısa label veya overflow menu yapısına taşınmalı.
- Gizli scrollbar yerine gradient/fade veya scroll hint eklenmeli.
- `.symbol-title` desktop’ta kullanılacaksa kontrollü gösterilmeli; kullanılmayacaksa DOM/metin yükü azaltılmalı.
- Marka logo mark’ı `aria-hidden="true"` olmalı; screen reader “P PiyasaPilot” okumamalı.

---

### P1.2 · StrategyPanel İç Scroll Durumu Kullanıcıyı Panelin Ortasına Düşürüyor

**Durum:** Açık UX sorunu.

**Chrome kanıtı:**

Strateji sekmesinde Chrome DOM ölçümleri:

- `.strategy-wrap`: `clientHeight=725`, `scrollHeight=1558`
- Bazı kontroller sekmeye dönüşte negatif `y` koordinatına düşmüş göründü.
- Örnek: `paper-mode-banner`, `strategy-topline`, segmented mode butonları offscreen kaldı.

**Gözlem:**

Sekmeye tekrar dönünce kullanıcı panelin üstündeki kritik butonları görmeyebiliyor:

- Kural Lab / Katalog
- Kaydet
- Paper’a Al
- Çalıştır
- Sembol / Periyot / Sermaye kontrolleri

**Risk:**

- Kullanıcı “Çalıştır” butonunu kaybetmiş gibi hisseder.
- WF/MC empty state görülürken üst kontroller görünmeyebilir.

**Yapılacak:**

- Sekme değişiminde ilgili panel scroll’u kontrollü sıfırlanmalı veya son scroll bilinçli saklanmalı.
- Strateji üst aksiyonları sticky header yapılmalı.
- WF/MC boş durumundaki “Çalıştır” butonu üstteki butondan bağımsız çalışıyor; bu iyi, fakat üst ayarlar görünmediği için kullanıcı hangi parametreyle çalıştıracağını göremiyor.

---

### P1.3 · NewsPanel API Hatalarını Sessizce Yutuyor

**Durum:** Açık hata durumu eksikliği.

**Kod kanıtı:**

- `frontend/src/components/NewsPanel.ts:120-125` → sadece `res.ok` ise liste güncelleniyor.
- `frontend/src/components/NewsPanel.ts:126-127` → catch içinde hiçbir UI mesajı yok.
- `frontend/src/components/NewsPanel.ts:150-151` → boş durumda “Henüz haber yok — ⟳ Yenile” yazıyor.

**Risk:**

- API 500/401/network hatası ile gerçekten haber olmaması aynı görünüyor.
- Kullanıcı “Yenile”ye basar ama neden sonuç alamadığını bilemez.
- Production’da KAP/news provider koparsa sessiz kalır.

**Yapılacak:**

- `lastError` state eklenmeli.
- `res.ok=false` durumunda HTTP status ve kullanıcı dilli hata gösterilmeli.
- Cache varsa “son bilinen haberler gösteriliyor” ayrımı yapılmalı.
- Empty state metnindeki eski `⟳` sembolü yeni ikon/metin sistemiyle uyumlu hale getirilmeli.

---

### P1.4 · Sinyal Geçmişi Eski/Kalıcı Veriyi Canlı Sinyal Gibi Gösterebilir

**Durum:** Güvenilirlik riski.

**Chrome kanıtı:**

Sinyaller sekmesinde çok sayıda sinyal göründü:

- XRPUSDT
- ETHUSDT
- RSİ_REVERSİON
- zaman damgaları

Aynı ekranda:

- `Telegram: yapılandırılmamış`
- data status `GECİKMELİ`
- bazı live kaynaklar bağlı değil

**Risk:**

- Kullanıcı eski localStorage/history sinyalini yeni/canlı sanabilir.
- “CANLI” rozeti ile eski sinyal listesi aynı ekranda güven karışıklığı yaratır.

**Yapılacak:**

- Sinyal kartlarında kaynak ve tazelik etiketi zorunlu olmalı:
  - `Canlı`
  - `Oturum geçmişi`
  - `Local kayıt`
  - `Demo/test`
- LocalStorage’dan gelen kayıtlar ayrı başlık altında gösterilmeli.
- Sinyal yaşı kritik eşiği aşarsa soluk/stale olmalı.
- `CANLI` rozeti yalnız websocket aktif ve son ping taze ise görünmeli.

---

### P1.5 · Auth Sayfalarında Logo ve Password Toggle Erişilebilirliği Zayıf

**Durum:** Açık erişilebilirlik ve polish sorunu.

**Chrome kanıtı:**

Login/register gövde metninde marka şu şekilde okunuyor:

- `PPiyasaPilot`

Kod:

- `frontend/src/auth/LoginPage.ts:21-22`
- `frontend/src/auth/RegisterPage.ts:20-21`

Şifre göster/gizle butonları:

- Login’de `aria-label` var ama görsel olarak emoji `👁`.
- Register’da iki toggle butonu `👁` ve `tabindex="-1"` kullanıyor; aria-label yok.

Kod:

- `frontend/src/auth/LoginPage.ts:56-62`
- `frontend/src/auth/RegisterPage.ts:66`
- `frontend/src/auth/RegisterPage.ts:82`

**Risk:**

- Screen reader kullanıcıları marka ve butonları kötü deneyimler.
- Emoji ikon platforma göre farklı görünür.
- Klavye kullanıcıları password toggle’a ulaşamayabilir.

**Yapılacak:**

- Logo mark `aria-hidden="true"` olmalı.
- Auth marka container’a tek `aria-label="PiyasaPilot"` verilmeli.
- Register toggle butonlarına `aria-label` eklenmeli.
- `tabindex="-1"` kaldırılmalı veya bilinçli gerekçe varsa alternatif keyboard kontrol sağlanmalı.
- Emoji yerine SVG icon kullanılmalı.

---

### P1.6 · Auth Gerektiren Sayfalarda Public Header Hâlâ Yanıltıcı

**Durum:** Ürün akışı net değil.

**Chrome kanıtı:**

Girişsiz `/settings` ve `/admin` açıldığında:

- Public header görünür: PiyasaPilot, Fiyatlandırma, Giriş Yap, Ücretsiz Başla, EN
- Gövde: “Oturum gerekli”

Bu davranış teknik olarak güvenli; fakat admin/settings gibi kapalı sayfalar public marketing shell içinde sıradan public route gibi görünüyor.

**Risk:**

- Admin route’un gerçekten korunduğu hissi zayıflar.
- “Ücretsiz Başla” CTA’sı admin sayfasında bağlam dışı kalır.

**Yapılacak:**

- Kapalı public-auth sayfaları için ayrı minimal auth shell kullanılmalı.
- `/admin` girişsiz durumda doğrudan `/login?next=/admin` yönlendirmesi veya admin odaklı erişim reddi ekranı vermeli.
- `/settings` için “Hesap ayarları için giriş yap” CTA’sı kalabilir, ama marketing nav azaltılmalı.

---

### P1.7 · Public CTA Metinleri Girişsiz Terminal Erişimiyle Çelişiyor

**Durum:** Ürün yönlendirme hatası.

**Chrome kanıtı:**

Login/Register sayfalarında:

- `← Terminale dön`

Shared/payment success sayfalarında:

- `Terminale Git`

Girişsiz kullanıcı bu CTA ile `/app` terminaline düşebiliyor.

**Risk:**

- Auth/plan gate mesajı zayıflar.
- “Ücretsiz hesap oluştur” akışı by-pass edilmiş gibi görünür.

**Yapılacak:**

- Girişsiz kullanıcı için CTA hedefi `/login?next=/app` olmalı.
- Login/Register üst linki “Ana sayfaya dön” veya “Terminal için giriş yap” şeklinde revize edilmeli.

---

## 5. P2 — Orta Öncelikli UX ve Tutarlılık Açıkları

### P2.1 · Public Landing İçerikleri Tekrarlı Görünüyor

**Chrome gözlemi:**

Landing’de birçok kart aynı cümleyi tekrarlıyor:

`Trading araştırması için sade, ölçülebilir ve paper-mode güvenli iş akışı.`

Bu cümle Grafik Lab, Backtest Pro, KAP Haberleri, Portfolio, Sinyaller, Eğitimler kartlarında tekrar ediyor.

**Risk:**

- Sayfa placeholder gibi görünür.
- Ürün özellikleri birbirinden ayrışmaz.

**Yapılacak:**

- Her özellik için gerçek, ayrı, kısa value prop yazılmalı.
- KAP Haberleri, Portfolio, Sinyaller gibi kartlarda somut çıktı anlatılmalı.

---

### P2.2 · Haberler Sekmesinde Haber Yoksa Çok Az Bağlam Var

**Chrome kanıtı:**

Haberler sekmesi gerçek veri yokken sadece `Yenile` butonu ve boş alan izlenimi verdi.

Kod:

- `frontend/src/components/NewsPanel.ts:150-151`

**Yapılacak:**

- Empty state şunları söylemeli:
  - Hangi kaynaklar kontrol ediliyor?
  - Sembol filtresi aktif mi?
  - Son deneme zamanı ne?
  - API hatası mı, gerçekten sonuç yok mu?

---

### P2.3 · Mali Analiz BTCUSDT İçin Sol Sidebar’da `Liste boş` Gösteriyor

**Chrome kanıtı:**

Mali Analiz sekmesinde `BTCUSDT` açıkken:

- Sol evren alanı: `Liste boş`
- Sağ içerik: kripto/FX için mali oran beklenmez mesajı

Sağ taraf doğru bağlam veriyor; sol `Liste boş` fazla ham kalıyor.

**Yapılacak:**

- Non-BIST sembolde sol evren boşsa `BIST evreni yüklenemedi` veya `BIST şirketi seçerek mali analiz görüntüleyin` mesajı verilmeli.
- Evren API yüklenemedi mi, filtre sonucu mu boş, yoksa sembol kapsam dışı mı ayrılmalı.

---

### P2.4 · Topbar Data Status Metinleri Tutarsız

**Chrome gözlemi:**

Farklı sekme/akışlarda şu durumlar görüldü:

- `BAĞLANIYOR`
- `BİLİNMİYOR`
- `GECİKMELİ`

**Risk:**

- Kullanıcı veri kalitesini yorumlayamaz.
- Aynı oturumda status anlamı değişiyor gibi görünür.

**Yapılacak:**

- Tek bir veri durumu modeli kullanılmalı.
- Tooltip ile kaynak açıklanmalı:
  - Redis/ClickHouse
  - yfinance
  - cache
  - empty
  - unknown
- `BİLİNMİYOR` kullanıcıya gösterilecek son metin olmamalı; yerine “Kaynak doğrulanıyor” gibi açıklayıcı metin kullanılmalı.

---

### P2.5 · Küçük Tıklama Hedefleri Hâlâ Var

**Chrome kanıtı:**

Özellikle:

- Public nav linkleri yaklaşık 20px yüksekliğinde.
- Sidebar collapse butonu 24x24.
- News refresh butonu 27px yüksekliğinde.
- Bazı report tab butonları 25px yüksekliğinde.

**Risk:**

- Dokunmatik cihazlarda ve trackpad kullanımında hata payı artar.

**Yapılacak:**

- Minimum hedef: desktop 32px, touch 40-44px.
- Public nav linkleri padding ile büyütülmeli.
- Sidebar collapse button 32px olmalı.
- News refresh 32px olmalı.

---

### P2.6 · Emoji/Platform Bağımlı İkonlar Tamamen Bitmemiş

**Chrome/kod kanıtı:**

Hâlâ görünen örnekler:

- Auth password toggle: `👁`
- Sidebar grup ikonları: `🇹🇷`, `🇺🇸`, `₿`, `💱`
- SignalFeed boş durum ikonları: `📡`, `⏳`, `⚠️`, `✅`
- ChartPanel alert option ikonları: `▲`, `▼`

**Yapılacak:**

- Auth toggle SVG’ye taşınmalı.
- Sidebar kategori ikonları platform bağımsız SVG veya kısa metin rozetleri olmalı.
- SignalFeed ikonları SVG durum ikonlarıyla değiştirilmeli.
- Text okları semantik sorun yaratmıyorsa kalabilir, ama toolbar/action ikonları SVG standardında tamamlanmalı.

---

### P2.7 · Register Legal Checkbox Boyutu Küçük

**Chrome kanıtı:**

Register checkbox boyutları yaklaşık 13x13.

**Risk:**

- Mobil/touch kullanımda zor.
- Hukuki onay gibi kritik kontrollerde tıklama hedefi zayıf.

**Yapılacak:**

- Label tüm satırı tıklanabilir olmalı.
- Checkbox görsel hedefi en az 20px, satır hedefi en az 36px olmalı.

---

### P2.8 · Google OAuth “Yakında” Butonları Disabled Ama Alternatif Açıklama Sınırlı

**Chrome kanıtı:**

Login/Register:

- `Google ile Devam Et — yakında`
- `Google ile Kayıt Ol — yakında`

Title var, fakat kullanıcı title’ı mobilde göremez.

**Yapılacak:**

- Buton altına kısa metin:
  - “Google girişi canlı OAuth anahtarları bağlanınca açılacak.”
- Mobilde tooltip’e bağlı kalınmamalı.

---

## 6. P3 — Düşük Öncelikli Polish ve Dokümantasyon Açıkları

### P3.1 · Footer Link Hedefleri İyi, Ama Public CTA Hiyerarşisi Biraz Gürültülü

Public sayfalarda üst nav, footer ve risk disclaimer düzgün görünüyor. Ancak login/register gibi görev odaklı sayfalarda public header yok, bunun yerine auth shell var. Settings/admin ise public header ile açılıyor. Shell tutarlılığı karar olarak netleştirilmeli.

**Yapılacak:**

- Public marketing shell
- Auth shell
- Protected app shell
- Protected minimal shell

Bu dört shell kategorisi yazılı kurala bağlanmalı.

---

### P3.2 · Landing Hero Görsel/Ürün Kanıtı Zayıf

Landing ilk görünüm metin ağırlıklı ve demo kartları statik. Ürün “terminal” olduğu için ilk viewport’ta gerçek terminal screenshot/mini canlı preview daha güçlü olur.

**Yapılacak:**

- İlk ekrana gerçek terminal ekranından güvenli bir preview konmalı.
- Demo kart “Statik demo” diye belirtiliyor; bu iyi, ama görsel daha ürün odaklı yapılmalı.

---

### P3.3 · Legal/Privacy/Cookies Sayfalarında Son Güncelleme Tarihi Yok

Hukuki sayfalarda içerik görünüyor, ancak son güncelleme tarihi ve versiyon bilgisi görünür değil.

**Yapılacak:**

- Her legal sayfaya `Son güncelleme: 2026-05-16` gibi tarih eklenmeli.
- Payment/Stripe/veri saklama maddeleri production gerçekleriyle tekrar gözden geçirilmeli.

---

## 7. Canlı Sistem / Kullanıcı Aksiyonu Gerektiren Eksikler

Bu maddeler kodla tek başına kapanmaz; production’a çıkmadan önce kullanıcı/panel/secret/deploy aksiyonu gerekir.

### 7.1 Google OAuth

- Google Cloud production proje/consent screen hazır değil.
- Authorized domain ve redirect URI canlı doğrulanmadı.
- `GOOGLE_CLIENT_ID` ve `GOOGLE_CLIENT_SECRET` production env’e girilmedi.
- Login/Register Google butonları disabled kalıyor.

### 7.2 Stripe

- Canlı Stripe ürünleri ve price id’leri bağlanmadı.
- `STRIPE_WEBHOOK_SECRET` canlı değil.
- Billing Portal dashboard’da doğrulanmadı.
- Checkout success → plan update uçtan uca canlı test edilmedi.
- Duplicate webhook idempotency canlı dashboard’dan test edilmedi.

### 7.3 AWS / Deployment

- EC2/EIP/Security Group/Data disk canlı oluşturulmadı.
- Production `.env` hazırlanmadı.
- Docker compose production canlı başlatılmadı.
- Production migration çalıştırılmadı.
- Domain üzerinden `/api/health` doğrulanmadı.

### 7.4 DNS / TLS

- METUnic A/CNAME kayıtları canlı IP ile tamamlanmadı.
- Certbot canlı sertifika alınmadı.
- HTTPS redirect ve `www` canonical redirect test edilmedi.
- Renew dry-run yapılmadı.

### 7.5 Email

- SMTP/Postmark/Resend/Gmail App Password seçilmedi.
- SPF/DKIM/DMARC canlı DNS kayıtları yok.
- Email verification ve password reset gerçek inbox ile test edilmedi.

### 7.6 Sentry / Grafana / Alert

- Production Sentry DSN yok.
- Backend/frontend test exception canlı Sentry’ye düşmedi.
- Grafana admin secret production’a çekilmedi.
- Alert kanalı seçilmedi.
- Uptime monitor/status page kurulmadı.

### 7.7 Backup / Restore

- S3 backup bucket yok.
- IAM backup user/role yok.
- İlk backup ve restore drill canlı yapılmadı.

### 7.8 Lisanslı BIST/VIOP Veri

- Matriks/Foreks/BIST resmi veri lisansı yok.
- Provider endpoint/secrets production’a girilmedi.
- Ultra plan “canlı veri” dili lisans tamamlanana kadar riskli.

### 7.9 Mobil Yayın

- Apple Developer ve Play Console hesapları hazır değil.
- Android/iOS signing yok.
- Firebase push kurulmadı.
- Store metadata, privacy label, screenshots hazır değil.

---

## 8. Test Açıkları

### 8.1 Deep-Link Regresyon Testi Eksik

Eklenmesi gereken test:

1. `localStorage.setItem('piyasapilot_last_tab', 'news')`
2. `/app?tab=screener&symbol=BTCUSDT` aç
3. Tarama sekmesinin aktif olduğunu doğrula
4. URL’nin `tab=screener` kaldığını doğrula

### 8.2 Guest Terminal Guard Testi Eksik

Eklenmesi gereken test:

1. Unauthenticated browser context
2. `/app` aç
3. Terminal shell görünmemeli
4. Login/guard ekranı görünmeli

### 8.3 Payment Success Guard Testi Eksik

Eklenmesi gereken test:

1. `/payment/success` session olmadan aç
2. “Pro planına hoş geldiniz” görünmemeli
3. “Ödeme doğrulanamadı” veya “Giriş yap” görünmeli

### 8.4 News API Error Testi Eksik

Eklenmesi gereken test:

1. `/api/news` 500 dönsün
2. NewsPanel inline hata göstersin
3. Cache varsa “son bilinen haberler” ayrımı yapılsın

### 8.5 Accessibility Smoke Eksik

Eklenmesi gereken testler:

- Password toggle aria-label
- Logo mark `aria-hidden`
- Legal checkbox label hit area
- Topbar tab keyboard navigation

---

## 9. Öncelikli Düzeltme Sırası

1. `/app` auth guard ve guest terminal kapatma.
2. URL deep-link boot sırası düzeltme.
3. Payment success doğrulama guard’ı.
4. Pricing canlı veri dilini lisans tamamlanana kadar güvenli hale getirme.
5. NewsPanel error state.
6. SignalFeed stale/local history ayrımı.
7. Topbar clipping ve scroll hint.
8. Auth logo/password toggle erişilebilirliği.
9. Mali Analiz non-BIST/empty sol panel dili.
10. Public/auth/protected shell kararlarını dokümante etme.
11. Canlı Stripe/Google/AWS/DNS/TLS/Sentry/email/backup/lisans aksiyonları.

---

## 10. Kapanış Notu

Chrome gerçek kullanımında public route terminal shell sızıntısı görünmedi; bu olumlu. Ancak uygulama hâlâ production-ready sayılmadan önce özellikle auth guard, deep-link, ödeme doğrulama ve canlı veri iddiası tarafında sertleştirilmeli.

Bu rapor kod düzeltmesi değil, eksik/yanlış envanteridir. Sonraki turda en mantıklı ilk paket:

- `P0.1 URL deep-link`
- `P0.2 guest /app guard`
- `P0.3 payment success guard`
- `P0.4 pricing live-data claim`

Bu dört madde kapanmadan ödeme açmak veya domain’i canlı kullanıcıya duyurmak risklidir.
