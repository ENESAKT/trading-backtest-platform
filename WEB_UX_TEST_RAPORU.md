# PiyasaPilot Web UX Test Raporu

Test tarihi: 16 Mayıs 2026  
Test ortamı: `frontend` Vite dev server `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000`  
Kapsam: Landing, pricing, auth, terminal sekmeleri, mobil görünüm, API sağlık kontrolü, production build.

> Not: Kullanıcı `@chrome` istedi; ancak Chrome UI kontrol aracı bu oturumda izin vermedi. Tarayıcı testleri aynı web uygulaması üzerinde Playwright/Chromium ile yapıldı. Chrome izin engeli ayrıca takip edilmeli.

## Kısa Özet

Uygulama çalışıyor, backend sağlık endpoint'i sağlıklı dönüyor, `npm run typecheck` ve `npm run build` başarılı. Buna rağmen web deneyiminde kritik seviyede route izolasyonu, mobil kullanılabilirlik ve boş/yanıltıcı durum sorunları var. En büyük problem: public sayfalarda terminal shell'i ve arka plan uygulama davranışı sızıyor; bu hem kullanıcı algısını hem de tıklama hedeflerini bozuyor.

## Test Edilen Alanlar

- Public sayfalar: `/`, `/pricing`, `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/onboarding`, `/settings`, `/admin`, `/legal/terms`, `/legal/privacy`, `/legal/cookies`, `/changelog`, `/waitlist`, `/shared/demo-slug`
- Terminal: `/app`, Grafik, Portföy, Strateji, Tarayıcı, Sinyaller, Eğitimler, Mali Analiz
- API: `/api/health`, `/api/auth/me`, `/api/shared/demo-slug`
- Teknik: TypeScript typecheck, Vite production build
- Görsel kayıtlar: `/Users/enes/AgentWorkspace/Backtest/frontend-audit-app.png`, `/Users/enes/AgentWorkspace/Backtest/frontend-audit-mobile.png`

## Kritik Bulgular

### 1. Public Sayfalarda Terminal Shell'i Sızıyor

Landing ve pricing sayfalarında olması gereken pazarlama/auth görünümünün yanında terminal butonları, favori yıldızları, sidebar sembolleri, tema paneli, hatta `✓ Backtest tamamlandı` toast mesajı görünüyor veya DOM içinde etkileşim hedefi olarak kalıyor.

Örnek gözlem:
- `/` sayfasında `Grafik`, `Portföy`, `Strateji`, `Tarayıcı`, `Sinyaller`, `Mali Analiz`, `Ayar`, favori yıldızları ve terminal bileşenleri listeleniyor.
- `/pricing` sayfasında plan kartları ile terminal shell aynı sayfada karışıyor.
- `/register` sayfasında alakasız `✓ Backtest tamamlandı` bildirimi göründü.
- `/login` sayfasında giriş butonuna tıklama denemesi gizli `strategy-card` butonuna takıldı; görünmeyen terminal elemanları etkileşimleri bozabiliyor.

Etkisi:
- İlk izlenim güven kaybettiriyor.
- Auth ve ödeme akışlarında yanlış tıklama hedefi riski var.
- SEO ve erişilebilirlik çıktısı gereksiz terminal içeriğiyle kirleniyor.

Öneri:
- Public route render edildiğinde app shell hiç mount edilmemeli veya erken `return` ile terminal init akışı durdurulmalı.
- Sadece `hidden` attribute'a güvenilmemeli; veri streamleri, toastlar, panel initleri public route'ta başlamamalı.
- Public sayfalar için ayrı root/layout, terminal için ayrı `/app` layout kuralı netleştirilmeli.

### 2. Mobil `/app` Kullanılabilir Değil

390x844 mobil viewport testinde `/app` ilk ekranda grafik veya temel işlem alanı yerine devasa sembol listesi gösteriyor. Kullanıcı ana iş akışına ulaşmadan çok uzun bir listeye maruz kalıyor.

Gözlem:
- Topbar sekmeleri dikey metin gibi akıyor.
- Grafik paneli ilk ekranda görünmüyor.
- Sidebar mobilde ana içeriği eziyor.
- Haberler sekmesi `Haberler 8 99+` gibi sıkışık okunuyor.

Etkisi:
- Mobilde terminal pratik olarak kullanılmaz hale geliyor.
- Yeni kullanıcı ne yapacağını anlayamıyor.

Öneri:
- Mobilde sidebar varsayılan kapalı olmalı.
- Sembol arama bir drawer/bottom sheet olarak açılmalı.
- Aktif grafik veya seçili mod ilk ekranın ana alanı olmalı.
- Topbar sekmeleri yatay kaydırılabilir compact nav veya alt tab bar'a dönüşmeli.

### 3. Public/Auth Sayfalarında Gizli Uygulama Elemanları Tıklama Hedeflerini Bozuyor

Login testinde `Giriş Yap` tıklaması için locator, görünmeyen bir `strategy-card` butonuna denk geldi. Bu tek başına kullanıcı tarafında her zaman aynı tıklama olur demek değil; fakat DOM ve erişilebilirlik ağacının public sayfalarda kirli olduğunu kanıtlıyor.

Etkisi:
- E2E testleri kararsızlaşır.
- Screen reader kullanıcıları yanlış içerik duyar.
- Otomasyon ve analitik eventleri yanlış elementleri yakalayabilir.

Öneri:
- Public sayfalarda terminal DOM'u oluşturulmamalı.
- Buton metinleri benzersizleştirilmeli; örneğin `Giriş Yap` auth formunda tek görünür submit olmalı.
- Erişilebilirlik ağacında hidden terminal elementleri bulunmamalı.

## Yüksek Öncelikli Bulgular

### 4. Shared Backtest Sayfası Kötü Boş Durum Veriyor

`/shared/demo-slug` backend tarafında `404 {"Paylaşım bulunamadı."}` döndürüyor. Bu teknik olarak doğru olabilir, ancak kullanıcı tarafında paylaşım linki bozuksa daha açıklayıcı bir ekran gerekir.

Öneri:
- "Bu paylaşım bulunamadı veya süresi doldu" mesajı.
- Terminale dön, fiyatlandırmaya git, destek/iletişim gibi net aksiyonlar.
- Link kopyalama/hatalı slug için sakin ve güven veren boş durum.

### 5. Sinyaller Sekmesi Sürekli Boş Kalıyor

Backend health çıktısında `signal_generator.evaluated=94`, `signals_emitted=0`, `skipped_untrusted=94`. UI'da "Henüz sinyal yok" görünüyor.

Sorun:
- Teknik olarak veri güvenliği nedeniyle sinyal üretilmemesi doğru olabilir.
- Kullanıcı açısından neden hiç sinyal olmadığı açıklanmıyor.

Öneri:
- Sinyaller ekranında "Lisanslı veri bağlı olmadığı için BIST sinyalleri güven kapısında bekletiliyor" gibi açık durum.
- Hangi veri kaynağı eksik, nasıl aktif edilir, kripto sinyali çalışıyor mu gibi yönlendirici detay.

### 6. Portföy Metrikleri Güven Vermeyen Değerler Gösteriyor

Portföy sekmesinde sanal cüzdanlar çok ağır zararda görünüyor: örneğin `-95,77%`, `-98,36%`. `Maks. Çöküş +-0,00%`, `Günlük K/Z +-0,00%` gibi formatlar da hatalı hissettiriyor.

Etkisi:
- Kullanıcı sistemin yanlış hesap yaptığını düşünebilir.
- `+-0,00%` profesyonel görünmüyor.

Öneri:
- Negatif/pozitif format tek standarda bağlanmalı: `-0,00%`, `+0,00%`, `0,00%`.
- Paper trading demo/gerçek ayrımı net etiketlenmeli.
- Aşırı zararların nedeni açık değilse "test cüzdanı" veya "geçmiş simülasyon" açıklaması eklenmeli.

### 7. Haberler Sekmesi Navigasyonda Tutarsız

Kodda `news` tab tipi var ve UI'da `Haberler 8 99+` butonu görünüyor, fakat ana topbar `nav` içinde sadece 7 ana sekme var. Buton metni sıkışık ve terminalde ayrı bir bilgi mimarisi gibi duruyor.

Öneri:
- Haberler sekmesi ana nav'a net şekilde 8. sekme olarak eklenmeli veya ayrı bildirim butonu olarak tasarlanmalı.
- `99+` badge anlamı açıklanmalı: okunmamış haber mi, KAP mı, tüm haber sayısı mı?

## Orta Öncelikli Bulgular

### 8. Build Başarılı Ama Ana JS Chunk Büyük

`npm run build` başarılı, ancak Vite uyarısı var:
- `dist/assets/index-*.js` yaklaşık `530.73 kB`, gzip `150.24 kB`
- 500 kB minified eşiği aşılıyor.

Öneri:
- Public sayfalar, terminal, eğitim içerikleri, Chart.js ve lightweight-charts ayrı dynamic import chunklarına bölünmeli.
- Auth/landing sayfası terminal chart kodunu yüklememeli.

### 9. README Kurulum Yolu Güncel Değil

Kök README hızlı başlangıçta `cd piyasapilot-v2 && npm install && npm run dev` yazıyor; mevcut repo yapısında frontend dizini `frontend/`.

Etkisi:
- Yeni geliştirici ilk kurulumda takılır.

Öneri:
- README ve `frontend/README.md` tek gerçek dizin yapısına göre güncellenmeli.
- "Frontend doğrudan dış API kullanır" diyen eski doküman ile kök README'deki "Zero-Demo Rule / backend üzerinden" iddiası uyumlu hale getirilmeli.

### 10. Auth Akışında Google Butonları Hazır Görünüyor Ama Durumu Belirsiz

Login/register ekranlarında `Google ile Devam Et` ve `Google ile Kayıt Ol` var. Testte gerçek entegrasyon doğrulanmadı; butonlar kullanıcıya hazır OAuth algısı veriyor.

Öneri:
- Entegrasyon hazır değilse disabled + "yakında" ya da gizli olmalı.
- Hazırsa hata durumları ve callback akışı E2E kapsamına alınmalı.

### 11. Admin ve Settings Sayfaları Public Route Olarak Açılıyor

`/admin` ve `/settings` public route listesinde yer alıyor. Yetki kontrolü olabilir, ancak route seviyesinde kullanıcıya ne olduğu net değil.

Öneri:
- Yetkisiz kullanıcı için login yönlendirmesi veya "yetki gerekli" ekranı.
- Admin route public route listesinde değil, protected layout altında ele alınmalı.

## Daha İyi Kullanılabilirlik İçin Öneriler

### Terminal İlk Açılış

- `/app` açıldığında tek ana hedef seçilmeli: grafik + sembol arama.
- Sidebar collapsed gelmeli; kullanıcı isterse açmalı.
- "Gecikmeli", "Canlı", "Lisanslı veri yok" gibi veri durumları tek bir anlaşılır status bileşeninde birleşmeli.

### Boş Durumlar

- "Henüz sinyal yok" tek başına yetersiz. Neden yok, kullanıcı ne yapabilir, sistem bekliyor mu anlatılmalı.
- Mali analizde "Oran verisi yok — Yenile ile veri çekin" iyi ama hangi semboller destekli, BTCUSDT için neden mali veri yok gibi bağlam eklenmeli.
- Shared backtest 404 ekranı ürün dilinde ele alınmalı.

### Buton ve Etiket Dili

- `Tarayıcı` kelimesi screener için kafa karıştırıyor; Türkçe finans ürününde `Piyasa Tarama` veya `Tarama` daha anlaşılır.
- `Ayar` topbar'da tema ayarı açıyor; genel ayarlar sanılabilir. `Tema` daha doğru.
- `Dondur`, `Sıfırla` gibi riskli paper cüzdan aksiyonları için onay veya açıklama gerekir.

### Görsel Hiyerarşi

- Public landing sayfası terminal artıkları yüzünden odak kaybediyor.
- Terminalde bilgi yoğunluğu çok yüksek; profesyonel araç için iyi ama onboarding veya ilk kullanım rehberi eksik.
- Mobilde sidebar ve topbar responsive davranışı yeniden tasarlanmalı.

## Çalışan ve Güçlü Taraflar

- Backend `/api/health` sağlıklı: workers çalışıyor, cache'de `85175` satır ve `59` sembol görünüyor.
- TypeScript typecheck temiz.
- Production build başarılı.
- Eğitimler paneli içerik olarak güçlü: 57 makale ve kategoriler var.
- Strateji paneli kapsamlı: kural lab, kayıtlı stratejiler, rapor arşivi, optimizasyon, piyasa taraması, export butonları mevcut.
- Mali analiz paneli, oranlar ve son bilançolar için iyi bir temel sunuyor.

## Teknik Test Sonuçları

```text
npm run typecheck
Sonuç: Başarılı

npm run build
Sonuç: Başarılı
Uyarı: index JS chunk 500 kB üstünde

GET http://127.0.0.1:8000/api/health
Sonuç: 200 OK

GET http://127.0.0.1:8000/api/auth/me
Sonuç: 401 Unauthorized, beklenen auth koruması

GET http://127.0.0.1:8000/api/shared/demo-slug
Sonuç: 404 Not Found, UI boş durum iyileştirilmeli
```

## QA Sonrası Not — 2026-05-16 Frontend Ürün Akışı

Yeni smoke QA `http://127.0.0.1:5173` üzerinde Playwright/Chromium ile desktop `1440x900` ve mobil `390x844` viewportlarda çalıştırıldı.

Kontrol edilen rotalar:
- `/`, `/pricing`, `/login`, `/register`
- `/app?tab=chart`, `portfolio`, `strategy`, `screener`, `signals`, `education`, `financials`, `news`
- `/settings`, `/admin`, `/shared/olmayan-slug`
- `/legal/terms`, `/legal/privacy`, `/legal/cookies`
- `/waitlist`, `/payment/success`

Sonuç:
- Public sayfalarda `#app-layout` veya `#topbar` terminal DOM sızıntısı görülmedi.
- Desktop ve 390px mobilde yatay overflow bulunmadı.
- `#app-error-banner` görünür kalmadı.
- `/settings` ve `/admin` oturumsuz durumda net "Oturum gerekli" ekranı veriyor.
- `/shared/olmayan-slug` ürün dilinde 404/empty state gösteriyor.
- Konsoldaki `401 Unauthorized` ve `404 Not Found` kayıtları auth koruması ve olmayan shared slug için beklenen sonuçlar olarak değerlendirildi.
- `npm run typecheck` ve `npm run build` başarılı; 500 kB chunk uyarısı geri gelmedi.

## Öncelikli İyileştirme Sırası

1. Public route ve terminal app shell izolasyonunu düzelt.
2. Mobil `/app` tasarımını sidebar kapalı + ana grafik odaklı hale getir.
3. Auth, admin, settings route'larını protected/public olarak net ayır.
4. Sinyal ve mali analiz boş durumlarını sebep + aksiyon içerecek şekilde yeniden yaz.
5. Portföy yüzde formatlarını ve paper cüzdan açıklamalarını düzelt.
6. Haberler sekmesini bilgi mimarisinde netleştir.
7. Public sayfalar ve terminal için code splitting yap.
8. README ve frontend dokümantasyonunu mevcut dizin/API mimarisiyle uyumlu hale getir.

## Son Not

Bu raporda kod değişikliği yapılmadı. Sadece yerel servisler çalıştırıldı, tarayıcı üzerinden gözlem yapıldı, typecheck/build doğrulandı ve bu Markdown raporu oluşturuldu.

---

## Çözüm Sonrası QA Notu — 16 Mayıs 2026

Bu rapordaki Bölüm 9 kapsamındaki web UX blocker maddeleri uygulandı ve tekrar doğrulandı.

- Public route izolasyonu yapıldı; landing/pricing/auth/legal/shared sayfalarda terminal shell, websocket, polling ve toast akışı başlamıyor.
- Mobil `/app` ilk render'da uzun sembol listesini dökmüyor; sidebar kapalı, yatay overflow yok.
- Shared backtest 404 durumunda ürün dilinde empty state gösteriyor.
- Sinyaller, Telegram, mali analiz ve paper trading boş/uyarı durumları daha açıklayıcı hale getirildi.
- Haberler 8. sekme olarak ana nav'a alındı; `Tarayıcı` → `Tarama`, `Ayar` → `Tema`.
- Public/terminal code-splitting yapıldı. Build çıktısında 500 kB chunk uyarısı kalktı; ana `index` chunk yaklaşık 23 kB seviyesine indi.
- `npm run typecheck` ve `npm run build` başarılı.

Kalanlar bu raporun blocker kapsamından çıktı; canlı Stripe/AWS/DNS/Sentry gibi dış erişim gerektiren production işleri ana `YAPILACAKLAR.md` listesindeki ilgili bölümlerde takip ediliyor.

## QA Sonrası Not — 2026-05-16 E2E Kabul Stabilizasyonu

Frontend kabul suite'i tekrar çalıştırıldı ve güncel ürün davranışına göre stabilize edildi.

- `npm run typecheck` başarılı.
- `npm run build` başarılı; 500 kB chunk uyarısı geri gelmedi.
- `npm run e2e` başarılı; Playwright/Chromium sonucu: 24/24 test geçti.
- Doğrulanan ek akışlar: grafik toolbar hover kontrolleri, şablon kaydet/sıfırla/geri yükle, event marker çoklu filtreleme, çizim araçları, mali analiz THYAO → ASELS arama ve grafikte aç bridge'i.
- Mali analiz özet ekranı API'den gelen uyarıları kullanıcıya görünür biçimde gösteriyor; canlı veri gecikmesi/eksikliği mesajı kaybolmuyor.

KULLANICI AKSİYONU GEREKİR:
- Canlı Stripe ürün/price id, billing portal ve webhook uçtan uca doğrulaması.
- Gerçek domain/DNS/TLS ve AWS deploy doğrulaması.
- Canlı Sentry DSN, Grafana dashboard ve alert kanallarının bağlanması.
