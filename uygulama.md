# PiyasaPilot — Uygulama Hata ve İyileştirme Raporu

> Hazırlanma tarihi: 2026-05-16  
> Kapsam: Tüm frontend bileşenleri, public sayfalar, terminal sekmeleri, API entegrasyonları, mobil görünüm, CSS/tasarım sorunları  
> Yöntem: Tam kaynak kodu analizi (ChartPanel, StrategyPanel, PortfolioPanel, Screener, SignalFeed, MaliAnalizPanel, NewsPanel, EgitimlerPanel, MultiChartLayout, DrawingManager, tüm public sayfalar, style.css, index.html, app.ts, backend endpoint listesi)  
> Bu rapor kod değişikliği içermez — sadece tespit ve belgeleme aşamasıdır.

---

## İÇİNDEKİLER

1. [KRİTİK — Public Sayfalarda Terminal Shell Sızması](#1-kritik--public-sayfalarda-terminal-shell-sızması)
2. [KRİTİK — Market Ticker Hiç Dolmuyor](#2-kritik--market-ticker-hiç-dolmuyor)
3. [KRİTİK — Sinyaller Sekmesi Daima Boş](#3-kritik--sinyaller-sekmesi-daima-boş)
4. [YÜKSEK — Portföy Sayısalları Yanıltıcı ve Format Hatalı](#4-yüksek--portföy-sayısalları-yanıltıcı-ve-format-hatalı)
5. [YÜKSEK — Grafik Paneli Sorunları](#5-yüksek--grafik-paneli-sorunları)
6. [YÜKSEK — Strateji Paneli Sorunları](#6-yüksek--strateji-paneli-sorunları)
7. [YÜKSEK — Mobil Kullanılabilirlik Sorunları](#7-yüksek--mobil-kullanılabilirlik-sorunları)
8. [ORTA — Mali Analiz Paneli Sorunları](#8-orta--mali-analiz-paneli-sorunları)
9. [ORTA — Haberler Sekmesi Sorunları](#9-orta--haberler-sekmesi-sorunları)
10. [ORTA — Tarama (Screener) Sorunları](#10-orta--tarama-screener-sorunları)
11. [ORTA — Auth ve Public Sayfalar Sorunları](#11-orta--auth-ve-public-sayfalar-sorunları)
12. [ORTA — Navigasyon ve Topbar Sorunları](#12-orta--navigasyon-ve-topbar-sorunları)
13. [ORTA — Eğitimler Paneli Sorunları](#13-orta--eğitimler-paneli-sorunları)
14. [DÜŞÜK — Tasarım ve Görsel Tutarsızlıklar](#14-düşük--tasarım-ve-görsel-tutarsızlıklar)
15. [DÜŞÜK — Teknik Borç ve Performans](#15-düşük--teknik-borç-ve-performans)
16. [Çalışan ve Güçlü Taraflar](#16-çalışan-ve-güçlü-taraflar)
17. [Düzeltme Öncelik Sırası](#17-düzeltme-öncelik-sırası)

---

## 1. KRİTİK — Public Sayfalarda Terminal Shell Sızması

**Konum:** `frontend/index.html`, `frontend/src/app.ts` satır 60–67  
**Sorun:** `index.html` içinde `#market-ticker`, `#topbar`, `#theme-panel`, `#app-layout`, `#sidebar` elementleri her route için DOM'a yükleniyor. Public route render edildiğinde `app.ts` bu elementleri `?.remove()` ile kaldırıyor ama kaldırma işlemi asenkron modül yükleme sırasında gecikmeli gerçekleşiyor. Bu süre zarfında terminal butonları, favori yıldızları, strategy-card butonları, backtest toast mesajları DOM'da görünür ve etkileşilebilir oluyor.

**Somut Belirtiler:**
- `/` (landing) sayfasında `Grafik`, `Portföy`, `Strateji` sekme butonları anlık görünüyor
- `/register` sayfasında `✓ Backtest tamamlandı` toast bildirimi görünebiliyor
- `/login` sayfasında gizli `strategy-card` elemanları tıklama hedeflerini bloklayabiliyor
- Screen reader kullanıcıları terminal içeriğini duyuyor, bu SEO'yu da bozuyor

**Kök Neden:** Terminal ve public sayfa aynı `index.html` shell'ini paylaşıyor; ayırım sadece JS tarafında `?.remove()` ile yapılıyor, HTML ve ilk CSS yüklemesinde ayrım yok.

**Önerilen Düzeltme:**
- Public sayfalar için ayrı HTML template veya `/app` route'una terminal taşınmalı
- Kısa vadede: public route kontrolü `app.ts`'in en başına alınmalı ve terminal elemanlarına `visibility:hidden` yerine `display:none` CSS sınıfı baştan eklenip sadece terminal route'unda kaldırılmalı

---

## 2. KRİTİK — Market Ticker Hiç Dolmuyor

**Konum:** `frontend/index.html` satır 28–31, `frontend/src/app.ts` (ticker dolduran kod yok)  
**Sorun:** HTML'de `#market-ticker` ve `#ticker-track` div'leri var, CSS'te `--ticker-h: 30px` ile 30px yükseklik ayrılıyor. Ancak `app.ts` içinde `#ticker-track`'i dolduran hiçbir kod yok. Sonuç olarak uygulama açıldığında en üstte "Canlı Piyasa" etiketi ile boş, karanlık bir şerit görünüyor.

**Somut Belirtiler:**
- Terminal açılınca üstte 30px boş alan var, içerik yok
- "Canlı Piyasa" etiketi metin olarak görünüyor ama yanında hiçbir sembol/fiyat yok
- `padding-top: calc(var(--ticker-h) + var(--topbar-h))` hesabı nedeniyle sayfa içeriği gereksiz yere 30px aşağı itiyor

**Kök Neden:** Market ticker özelliği HTML/CSS'e eklendi ama `app.ts`'te doldurulacak kod hiç yazılmadı. `sidebar.updateTicker()` sadece sidebar'ı, ticker şeridini değil güncelliyor.

**Önerilen Düzeltme:**
- A) Ticker özelliği tamamlanacaksa: `DataEngine.onPriceUpdate` veya `warmFavoriteTickers` eventi alındığında `#ticker-track`'e span elementleri ekle (sembol, fiyat, değişim yüzdesi)
- B) Ticker kısa vadede tamamlanamayacaksa: `#market-ticker` HTML'den kaldırılmalı veya `display:none` yapılmalı; `--ticker-h: 0px` olarak sıfırlanmalı

---

## 3. KRİTİK — Sinyaller Sekmesi Daima Boş

**Konum:** `frontend/src/components/SignalFeed.ts`, `backend/api/main.py`  
**Sorun:** Backend `/api/health` endpoint'i `signal_generator.evaluated=94`, `signals_emitted=0`, `skipped_untrusted=94` gösteriyor. Tüm sinyaller "güvenilmez veri" gerekçesiyle atlanıyor. Kullanıcı arayüzünde sadece "Henüz sinyal yok" boş durum mesajı görünüyor.

**Somut Belirtiler:**
- Sinyaller sekmesi açıldığında WebSocket bağlanıyor (`wss://.../ws/signals`) ama içerik gelmiyor
- Telegram ayarları formu görünüyor ancak test edilecek sinyal yok
- `STRONG_BUY`/`STRONG_SELL` toast bildirimleri hiç tetiklenmiyor
- Telegram bot yapılandırılmamışsa "yapılandırılmamış · .env içinde TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID gerekir" mesajı görünüyor ama link veya yönlendirme yok

**Kullanıcı Deneyimi:** Kullanıcı "Neden hiç sinyal yok?" diye merak ediyor, neden olduğu hiç açıklanmıyor.

**Önerilen Düzeltme:**
- Sinyaller sekmesine bilgi kartı ekle: "Lisanslı BIST verisi bağlı olmadığı için sinyaller güven filtresinden geçemiyor. Kripto sinyalleri farklı bir veri kaynağından çalışabilir. Daha fazla bilgi için: [link]"
- `health` endpoint'inden `skipped_untrusted` değerini UI'ya yansıt: "94 değerlendi, 0 onaylandı"
- Telegram bot kurulum adımlarına link ver

---

## 4. YÜKSEK — Portföy Sayısalları Yanıltıcı ve Format Hatalı

**Konum:** `frontend/src/components/PortfolioPanel.ts`

### 4.1 — `+-0,00%` Format Hatası
**Sorun:** `formatPct` fonksiyonu negatif değerlerde `+` işareti de ekliyor, bu `+-0,00%` ve `+-95,77%` gibi profesyonel olmayan çıktı üretiyor.  
**Konumlar:** `renderWallets()`, `walletCardHTML()`, `computeMetrics()`, `renderMetrics()`

### 4.2 — Günlük K/Z Hesabı Asimetrik
**Sorun:** `dailyLoss >= 0 ? dailyLossPct : -dailyLossPct` ifadesi yanlış simetri üretiyor. Negatif günlük kayıp için `abs(dailyLoss)/capital * 100` hesaplanıp sonra `-` çarpılıyor ama bu durumda negatif karda da "pozitif" bir yüzde gösterilebiliyor.

### 4.3 — Cüzdanlar Büyük Zararda Görünüyor
**Sorun:** Paper cüzdanlar `-95,77%`, `-98,36%` gibi ekstrem zararlarda. Bu test verisi mi, gerçek simülasyon mu belli değil. Kullanıcıya açıklama yok.  
**Önerilen:** Wallet kartına "Bu simülasyon/test verisidir" badge'i veya tooltip ekle.

### 4.4 — Equity ve Drawdown Chart Başlangıç Hatası
**Sorun:** `renderEquityCurve()` içinde `let peak = equityData[0]!` ile peak başlatılıyor. Equity eğrisi yüklenmeden önce (veri gelmeden) canvas elementleri DOM'da boş görünüyor, yükleme göstergesi yok.

### 4.5 — Sıfırlama/Dondurma Onay Dialogu Platform Native
**Sorun:** `resetWallet()` ve `haltWallet()` fonksiyonları `window.confirm()` kullanıyor. Bu tarayıcının native dialog'unu açıyor, uygulamanın teması ve dark mode'u ile uyumsuz görünüyor.

---

## 5. YÜKSEK — Grafik Paneli Sorunları

**Konum:** `frontend/src/components/ChartPanel.ts`

### 5.1 — Renko Butonu Disabled Ama Görünür
**Sorun:** Çizim toolbar'ında `Rnk` (Renko) butonu `disabled` ve `opacity:0.4` ile görünüyor. "Yakında" tooltip'i var ama ne zaman geleceği belirsiz. Bu buton gereksiz yer kaplıyor ve kullanıcıya "bozuk buton" izlenimi veriyor.  
**Önerilen:** Ya tamamen kaldır ya da açıkça "Yakında" etiketi ile ayrı bir konuma taşı.

### 5.2 — Layout Döngüsü G Tuşuyla 2x1 Atlıyor
**Sorun:** `app.ts`'deki klavye kısayolunda layout döngüsü `['1x1', '1x2', '2x2']` olarak tanımlanmış. `2x1` (iki satır, bir sütun) döngüye dahil değil. Ancak toolbar butonlarında `2x1` mevcut. Klavye ve fare ile davranış tutarsız.

### 5.3 — Market Ticker Görünmez "Canlı Piyasa" Şeridi (Bkz. Madde 2)

### 5.4 — ÖK, PnL, Risk, T/T Buton Açıklamaları Yetersiz
**Sorun:** Grafik kontrol toolbar'ında `ÖK` (Önceki Kapanış), `PnL`, `Risk`, `T/T` butonları aktif ama yeni kullanıcılar ne işe yaradığını anlamıyor. Tooltip'leri var (`title=""`) ama çok kısa.  
**Önerilen:** Her buton için daha açıklayıcı tooltip ekle: "Önceki Kapanış: Dünün kapanış fiyatını yatay çizgiyle gösterir"

### 5.5 — Şablon Kaydederken Boş İsim Kontrolü Yok
**Sorun:** `#new-template-name` input'una boş string girilip kaydet butonuna tıklanırsa ne olacağı belirsiz. Backend/LocalStorage'a boş isimli şablon yazılabiliyor.

### 5.6 — Karşılaştır Renk Seçici Her Zaman Gizli
**Sorun:** `#compare-options` içindeki renk seçici (`<input type="color">`) ve grafik tipi select'i (`candle/line/area`) `compare-options` div'i içinde ama bu div'in `display` durumu CSS'te kontrol edilmiyor. Sembol eklendiğinde renk seçici görünüyor mu test edilmeli.

### 5.7 — Export PNG/CSV Çalışıyor Ama Geri Bildirim Yok
**Sorun:** Export PNG tıklandığında dosya indirilmeye çalışılıyor ama başarılı/başarısız durumunda kullanıcıya bildirim yok (toast veya mesaj).

### 5.8 — Karşılaştır "maks 3" Sınırı Aşılabilir
**Sorun:** `compare-input`'a "maks 3" yazıyor ama bu limit JS tarafında kontrol ediliyor mu koda bakılmadı. Kullanıcı 4. sembol eklemeye çalıştığında ne oluyor belirsiz.

### 5.9 — Fiyat Uyarısı Modal: Başarı Durumu Belirsiz
**Sorun:** `#price-alert-btn` tıklandığında fiyat uyarısı modal'ı açılıyor. Uyarı kaydedildiğinde modal kapanıyor ama başarı/hata durumu kullanıcıya gösterilmiyor.

---

## 6. YÜKSEK — Strateji Paneli Sorunları

**Konum:** `frontend/src/components/StrategyPanel.ts`

### 6.1 — Mode Seçimi Varsayılan Olarak Aktif Değil
**Sorun:** Panel yüklendiğinde `this.mode = 'spec'` (Kural Lab) ama `syncControls()` çağrılıyor. Buna rağmen ilk açılışta hiçbir `seg-btn` `active` CSS sınıfına sahip değil — `syncControls` çalışmadan önce DOM render edilmiş oluyor. Hangi modda olduğu butonlardan anlaşılamıyor.

### 6.2 — Slippage Tick Input Her Zaman Görünüyor
**Sorun:** `bt-slippage-model` selectinde "Fixed BPS" seçiliyken `bt-slippage-tick` input'u gereksiz yere görünüyor. Kullanıcıya "Bu alan şu an aktif değil" işareti yok.

### 6.3 — Walk-Forward ve Monte Carlo Sekmeleri Çalıştırmadan Önce Boş
**Sorun:** Backtest çalıştırılmadan önce bu sekmelere tıklanırsa boş "Sonuç yok" ekranı geliyor. Kullanıcıya "Önce backtest çalıştır" yönlendirmesi yok.

### 6.4 — "Paper'a Al" Butonu Backtest Sonucu Olmadan Hata Veriyor
**Sorun:** `activate-paper` butonuna backtest çalıştırılmadan tıklanırsa `showError('Paper aktivasyonu için önce backtest çalıştır.')` çağrılıyor. Bu hata mesajı `#report-content` div'inin içine yazıldığı için küçük, soluk ve dikkat çekici değil.

### 6.5 — Parametre Deneyi Sadece EMA Parametrelerini Destekliyor
**Sorun:** `#opt-fast` ve `#opt-slow` inputları EMA periyotları için. Kullanıcı RSI, Bollinger veya başka stratejiyle çalışıyorsa bu optimizer anlamlı değil. Strateji moduna göre optimizer parametreleri değişmiyor.

### 6.6 — Piyasa Taraması "Özel" Seçeneği Açıklanmıyor
**Sorun:** Scan grubunda "Özel" seçilince `#scan-custom` input görünüyor, placeholder `BTCUSDT,ETHUSDT` yazıyor. Ancak BIST sembolleri için `.IS` eki gerektiği, VİOP için farklı format gerektiği açıklanmıyor.

### 6.7 — Walk-Forward Butonu UI'da Yok
**Sorun:** Backend'de `/api/backtest/walk-forward` endpoint'i mevcut. Ama strateji panelinde doğrudan "Walk-Forward Çalıştır" butonu yok. Sonuçları görmek için önce normal backtest çalıştırıp sonra "Walk-Fwd" sekmesine geçmek gerekiyor ama bu akış kullanıcıya anlatılmıyor.

### 6.8 — Rapor Arşivinde Silme Butonu Yok
**Sorun:** Rapor arşivinde kayıtlar listeleniyor. Backend'de `DELETE /api/backtest/reports/{run_id}` endpoint'i var ama UI'da silme butonu yok.

### 6.9 — Kayıtlı Strateji Düzenleme / Silme Yok
**Sorun:** `#saved-strategies` listesinde stratejiler görünüyor ama düzenleme veya silme butonu yok. Strateji kaydedilince listede birikmeye devam ediyor.

---

## 7. YÜKSEK — Mobil Kullanılabilirlik Sorunları

**Konum:** `frontend/style.css` (@media 768px ve altı)

### 7.1 — Sidebar Mobilde `display:none` Ama Sembol Seçimi İmkânsız
**Sorun:** 768px altında `#sidebar { display: none }` kuralıyla sidebar tamamen gizleniyor. Kullanıcı sembol değiştiremez hale geliyor. Hamburger menü, drawer veya bottom sheet alternatifi yok.

### 7.2 — Grafik Kontroller Mobilde Küçük ve Kayıyor
**Sorun:** `.chart-controls { overflow-x: auto; flex-wrap: nowrap }` ile yatay kaydırma yapılıyor. Düğmeler `font-size: 9px`, `padding: 2px 4px`. Dokunmatik ekranda 9px font ve ~20px butonlar dokunulamaz kadar küçük (Apple HIG minimum 44px, Material minimum 48px önerir).

### 7.3 — Topbar Sekmeleri Sıkışık
**Sorun:** Mobilde 8 sekme (Grafik, Portföy, Strateji, Tarama, Sinyaller, Eğitimler, Mali Analiz, Haberler) topbar'da sıkışık gösteriliyor. `.tab-btn { font-size: 10px; padding: 3px 5px }` çok küçük. Kaydırma var ama kullanıcı tüm sekmelerin olduğunu anlamıyor.

### 7.4 — `symbol-title` Mobilde Gizleniyor
**Sorun:** `.symbol-title { display: none }` ile mobilde aktif sembol başlığı görünmüyor. Kullanıcı hangi sembolde olduğunu bilemiyor.

### 7.5 — Strateji Paneli Mobilde Kullanılamaz
**Sorun:** Strateji paneli çok sayıda input, select ve tablo içeriyor, mobil için özel düzenleme yok. 768px altında tüm bu formlar ve sonuç tabloları üst üste yığılıyor.

---

## 8. ORTA — Mali Analiz Paneli Sorunları

**Konum:** `frontend/src/components/MaliAnalizPanel.ts`

### 8.1 — Non-BIST Sembollerde Boş Durum Yetersiz
**Sorun:** BTCUSDT, EURUSD, XAU/USD gibi semboller seçilince "Oran verisi yok. BIST şirketleri için 'Yenile' ile kaynak kontrolü yapılabilir; kripto/FX sembollerinde mali oran beklenmez." mesajı görünüyor. Bu mesaj teknik açıdan doğru ama:
- Kullanıcıya BIST sembolü seçmesi için yönlendirme yok
- "Hangi semboller destekleniyor?" sorusuna cevap yok

### 8.2 — "BIST 30 Yenile" Butonu Uzun Sürüyor, Loading Yetersiz
**Sorun:** `⟳ BIST 30` butonuna tıklandığında arka planda 30 şirket için veri çekimi başlıyor. Buton disabled oluyor ama ne kadar sürdüğü veya kaçta kaçının tamamlandığı belli değil. İlerleme çubuğu (progress bar) yok.

### 8.3 — Universe Liste Nokta Rengi Başlangıçta Belirsiz
**Sorun:** Sembol listesinde `dot-ok` (yeşil), `dot-empty` (gri), `dot-partial` (sarı) renkli noktalar var ama renk/durum açıklaması için legend yok. Yeni kullanıcı ne anlama geldiğini bilmiyor.

### 8.4 — Karşılaştırma Tablosunda Sıralama Oku Yok
**Sorun:** Karşılaştırma sekmesinde tablo başlıklarına tıklanarak sıralama yapılabiliyor (koda göre) ama görsel ↑↓ ok işareti yok. Kullanıcı sıralama yapılabildiğini anlamıyor.

### 8.5 — Grafikler Sekmesi Expand/Collapse Görsel Geri Bildirimi
**Sorun:** `_expandedCharts` set'i ile grafikler genişletilebilir/küçültülebilir. Ancak hangi grafiğin expand modunda olduğu ve expand butonunun görsel durumu (açık/kapalı ikon) tutarlı değil.

### 8.6 — Events Sekmesi KAP Verileri Bağımlı
**Sorun:** Olaylar sekmesi KAP verilerine bağlı. Veri yoksa "Henüz veri yok." mesajı görünüyor ama KAP entegrasyonu aktif mi, ne zaman güncelleniyor bilgisi yok.

---

## 9. ORTA — Haberler Sekmesi Sorunları

**Konum:** `frontend/src/components/NewsPanel.ts`, `frontend/src/app.ts`

### 9.1 — Tab Badge "99+" Anlamı Açıklanmıyor
**Sorun:** `#tab-news-badge` içinde okunmamış haber sayısı gösteriliyor ama badge'in ne anlama geldiği (okunmamış haber mi, toplam haber mi, KAP uyarısı mı) topbar'da anlaşılmıyor. `title` attribute'una tooltip eklenmiş ama mobilde tooltip görünmüyor.

### 9.2 — Yenile Sonrası Loading Göstergesi Eksik
**Sorun:** `⟳ Yenile` butonuna tıklanınca buton disabled oluyor (iyi). Ama herhangi bir spinner/yükleniyor göstergesi yok. Yavaş bağlantıda kullanıcı butonun çalışıp çalışmadığını bilemiyor.

### 9.3 — Mark as Read Hata Durumu Sessiz
**Sorun:** Haber kartına tıklandığında `POST /api/news/mark-read` çağrılıyor. Hata oluşursa `catch(() => { /* ignore */ })` ile sessizce atlanıyor, kullanıcıya bildirim yok.

### 9.4 — Haber Kartı URL'si Null Olduğunda Tıklanamaz
**Sorun:** Haber kartında URL varsa `<a href>` linki oluşturuluyor. `url: null` olan haberlerde link yok, kart tıklanamazl fakat görsel olarak link varmış gibi durabilir.

### 9.5 — Symbol Filtresi Enter'dan Sonra Otomatik Yenileme
**Sorun:** `symInput.addEventListener('keydown', (e) => { if (e.key === 'Enter') void this.load(true) })` — Enter'a basıldığında fresh reload başlatılıyor ama `kwInput` (keyword) için bu shortcut yok. Tutarsız UX.

---

## 10. ORTA — Tarama (Screener) Sorunları

**Konum:** `frontend/src/components/Screener.ts`

### 10.1 — İlk Taramada Cache Boş, Tüm Sonuçlar Atlınıyor
**Sorun:** Screener, `dataEngine.getAllCached()` ile önbellekteki veriyi kullanıyor. Uygulama yeni açıldıysa cache henüz dolmamış olabilir. Bu durumda "Tarama" tıklandığında `candles.length < 30` kontrolü geçilemeyen tüm semboller atlanıyor ve tablo çok az veya hiç sonuç göstermiyor. Kullanıcıya "Veri henüz yüklenmiyor, biraz bekleyin veya bir sembol seçin" açıklaması yok.

### 10.2 — "Tümünü Göster" Filtre Seçeneği Yok
**Sorun:** Filtre butonları tek tek toggle'lanıyor ama aktif filtre yokken "tüm sonuçları listele" butonu yok. Kullanıcı tüm filtreleri deaktif etse bile tarama yeniden çalıştırılmıyor — liste olduğu gibi kalıyor.

### 10.3 — Sıralama Ok İşareti Görünüyor Ama Renksiz
**Sorun:** `thHTML()` fonksiyonu `▲` / `▼` ok ekliyor. Aktif sütun `sort-active` CSS sınıfı alıyor ama CSS'te bu sınıfa özel renk tanımı olup olmadığı belirsiz; görsel olarak çok zayıf kalıyor.

### 10.4 — Sonuç Tablosunda "İşlem" Sütunu Yeterince Belirgin Değil
**Sorun:** `screener-chart` ve `screener-backtest` butonları var, tıklanınca ilgili sekmeye geçiyor (çalışıyor). Ama sütun başlığı sadece "İşlem" — bunların ne yapacağı net değil.

### 10.5 — Tarama Sonuçları Otomatik Güncelleniyor mu?
**Sorun:** Cache güncellendiğinde screener sonuçları otomatik yenilenmiyor. Kullanıcı saatler sonra aynı tabloyu görüyor. "Son tarama: XX:XX" timestamp'i yok.

---

## 11. ORTA — Auth ve Public Sayfalar Sorunları

**Konum:** `frontend/src/pages/`, `frontend/src/auth/`

### 11.1 — Admin Paneli Public Route'ta, Yetki Kontrolü Yok
**Sorun:** `/admin` route'u `publicRoutes` listesinde. `renderAdminPanel()` fonksiyonu çağrılıyor ama auth kontrolü koda bakılmadı. Yetkisiz kullanıcı admin paneline erişebilecekse bu güvenlik açığı.  
**Önerilen:** Admin route protected layout altına alınmalı, yetkisiz erişimde `/login?next=/admin` redirect yapılmalı.

### 11.2 — Google OAuth Butonları "Hazır" Görünüyor Ama Durumu Belirsiz
**Sorun:** Login/register sayfalarında "Google ile Devam Et" butonları var. Gerçek OAuth entegrasyonu çalışmıyorsa disabled + "Yakında" etiketi olmalı; çalışıyorsa hata durumları test edilmeli.

### 11.3 — Shared Backtest 404 Boş Durum Ürün Dilinde Değil
**Sorun:** `/shared/{slug}` için geçersiz slug girildiğinde backend `404 {"Paylaşım bulunamadı."}` döndürüyor. UI bu durumu nasıl ele alıyor kontrol edilmeli — boş ekran mı, hata mesajı mı gösteriyor?

### 11.4 — Fiyatlandırma Sayfasında Stripe Bağlantısı Test Edilmeli
**Sorun:** `renderPricingPage()` Stripe checkout endpoint'i çağırıyor. Canlı Stripe `product/price` id'leri ve webhook secret yapılandırılmadan checkout başlamıyor. Kullanıcıya "Stripe bağlantı hatası" yerine genel hata mesajı dönebiliyor.

### 11.5 — Settings Sayfası `requireAuth` Kullanıyor Ama Diğer Sayfalar Kullanmıyor
**Sorun:** `renderSettingsPage()` başında `requireAuth()` kontrolü var. Ama `/onboarding`, `/admin`, `/changelog` gibi sayfalar için bu kontrol yapılmıyor. Tutarsız yetki modeli.

---

## 12. ORTA — Navigasyon ve Topbar Sorunları

**Konum:** `frontend/index.html`, `frontend/src/app.ts`, `frontend/style.css`

### 12.1 — "Tema" Butonu Genel Ayarlar Sanılabiliyor
**Sorun:** Topbar sağ tarafında "Tema" butonu var. Bu buton sadece renk teması ve vurgu rengi seçimine açılıyor. Yeni kullanıcılar "genel ayarlar" veya "hesap ayarları" sanabiliyor. İsim "Görünüm" veya içerik bilinen ikon (🎨 veya 🌙) olmalı.

### 12.2 — Logo "Piyasa Pilotu" Yazıyor, Marka "PiyasaPilot"
**Sorun:** `index.html`'de `<strong>Piyasa Pilotu</strong>` yazıyor. Marka adı hem landing sayfasında hem dokümanlarda "PiyasaPilot" (bitişik). Boşluk tutarsızlık yaratıyor.

### 12.3 — Status Badge Mobilde Kesiyor
**Sorun:** `.status-badge { max-width: 78px; overflow: hidden; text-overflow: ellipsis }` kuralıyla mobilde "GECİKMELİ VERİ" yerine "GECİKMEL…" gibi kesik metin çıkabiliyor.

### 12.4 — Topbar'da `#last-update` Mobilde Gizleniyor
**Sorun:** Mobilde `#last-update { display: none }`. Bu iyi bir karar ama desktop'ta "Son güncelleme: 3dk önce" gibi bilgiler `upd-red` sınıfıyla kırmızı renk alıyor. Bu "bağlantı sorunu" gibi algılanabiliyor, gereksiz kaygı yaratıyor.

---

## 13. ORTA — Eğitimler Paneli Sorunları

**Konum:** `frontend/src/components/EgitimlerPanel.ts`

### 13.1 — Makale İçeriğinde Markdown Render Kalitesi Kontrol Edilmeli
**Sorun:** `renderMarkdown()` fonksiyonu MD içeriğini HTML'e çeviriyor. Tablo, kod bloğu, matematiksel formül gibi karmaşık MD elementlerinin doğru render edildiği doğrulanmalı.

### 13.2 — Kategori Değiştirilince Sayfanın Scroll Pozisyonu Sıfırlanmıyor
**Sorun:** `this.render()` tüm panel HTML'ini yeniden oluşturuyor (tam re-render). Bu sırada `education-article` div'inin scroll pozisyonu ve seçili makale başında kalıyor, liste scroll'u sıfırlıyor.

### 13.3 — "Bu Göstergeyi Grafikte Aç" Butonu Gösterge Yoksa Hata
**Sorun:** `data-chart-indicator` attribute'u boş string olduğunda `onOpenChartIndicator?.('')` çağrılıyor. ChartPanel bu durumda ne yapıyor kontrol edilmeli — muhtemelen sessizce geçiyor ama boş bir "gösterge ekleme" işlemi tetiklenebiliyor.

### 13.4 — Mobilde Education Sidebar Overlay Olmuyor
**Sorun:** Mobilde `education-sidebar` küçülüyor ama makale içeriği ile yan yana gösteriliyor. İçerik alanı daraldığında okunması zorlaşıyor. Sidebar'ın toggle ile açılıp kapanması daha iyi olur.

---

## 14. DÜŞÜK — Tasarım ve Görsel Tutarsızlıklar

**Konum:** `frontend/style.css`, tüm bileşenler

### 14.1 — `confirm()` ve `alert()` Dialog'ları Tema Dışı
**Sorun:** `PortfolioPanel.ts` içinde `window.confirm()` kullanılıyor. Bu tarayıcının varsayılan dialogunu açıyor, uygulamanın dark/light temasını görmüyor.  
**Etkilenen Yerler:** Cüzdan sıfırlama, cüzdan dondurma

### 14.2 — Scrollbar Stilleri Sadece WebKit İçin
**Sorun:** `::webkit-scrollbar` stilleri tanımlı ama Firefox için `scrollbar-width: thin` ve `scrollbar-color` tanımlanmamış. Firefox'ta varsayılan geniş scrollbar'lar görünüyor.  
(Not: `.topbar-tabs` için `scrollbar-width: none` var ama genel scrollbar Firefox'ta stillenmemiş)

### 14.3 — Emoji İkonlar Platform Arası Tutarsız Görünüm
**Sorun:** Toolbar butonlarında `⬜`, `⬜⬜`, `⊞`, `⏹`, `🗑`, `📏`, `⛶`, `📸`, `📊` gibi emoji ikonlar kullanılıyor. Bu emojiler Windows, macOS, Linux ve mobil cihazlarda farklı görünüyor. SVG ikon kütüphanesi (mevcut projenin bazı yerlerinde SVG kullanılıyor) tercih edilmeli.

### 14.4 — Sync Lock Butonları Emoji İkon Sorunu
**Sorun:** MultiChartLayout sync lock butonlarında `🔗`, `⏳`, `↔️`, `📏` emoji'leri kullanılıyor. Bunlar platform bağımlı görünüyor. SVG ile değiştirilmeli.

### 14.5 — Light Mode'da Bazı Renkler Okunaksız
**Sorun:** `[data-theme="light"]` CSS kural seti var ama tüm bileşenler light mode için optimize edilmemiş. Özellikle `.paper-mode-banner`, wallet card renkleri ve grafik panel arkaplanı light mode'da kontrastı düşük kalabiliyor.

### 14.6 — Strateji Panel Sinyaller Listesi Maksimum 16 Kayıt Gösteriyor
**Sorun:** `renderSignals()` fonksiyonunda `.slice(0, 16)` ile sinyal listesi 16 ile sınırlandırılıyor. "Daha fazla göster" butonu veya sayfalama yok.

### 14.7 — Toast Container DOM'a Dinamik Ekleniyor
**Sorun:** SignalFeed'deki `showToast()` fonksiyonu `#toast-container` div'ini bulamazsa `document.body`'e ekliyor. Birden fazla bileşen toast üretirse (PortfolioPanel, StrategyPanel) her biri kendi container oluşturabilir.

---

## 15. DÜŞÜK — Teknik Borç ve Performans

### 15.1 — Ana JS Chunk 530kB (Uyarı Eşiği Aşılıyor)
**Sorun:** `npm run build` çıktısında `index.js ~530kB (gzip ~150kB)`. Vite 500kB uyarı eşiğini aşıyor. Public sayfalar, terminal, Chart.js ve eğitim içerikleri ayrı dynamic import chunk'larına ayrılmalı.

### 15.2 — `any` Type Kullanımı (TypeScript Güvenliği)
**Sorun:** `StrategyPanel.ts` içinde `qw = w as any` gibi `any` cast'ları var. TypeScript strict mode kazançları azalıyor.

### 15.3 — LazyLoad Sentinel Observer Memory Leak Riski
**Sorun:** `Sidebar.ts`'de `IntersectionObserver` oluşturuluyor. Sidebar destroy edildiğinde (yoksa) observer disconnected edilmeyebiliyor.

### 15.4 — DataEngine Singleton Global State
**Sorun:** `dataEngine` tek instance olarak `core/DataEngine.ts`'den export ediliyor. Test edilemezlik ve yan etki riskleri var.

### 15.5 — Firefox Scrollbar Stillenmemiş (Bkz. 14.2)

### 15.6 — Manifest ve PWA Yapılandırması Eksik Test
**Sorun:** `index.html`'de `<link rel="manifest" href="/manifest.webmanifest" />` var. Manifest dosyası doğru yapılandırılmış mı, service worker kaydı yapılmış mı kontrol edilmeli.

---

## 16. Çalışan ve Güçlü Taraflar

Raporun dengeli olması için tespit edilen güçlü taraflar:

- **Backend `/api/health` sağlıklı**: Workers çalışıyor, cache'de 85.000+ kayıt var
- **TypeScript typecheck temiz**: `npm run typecheck` hatasız geçiyor
- **Production build başarılı**: `npm run build` çalışıyor (sadece chunk boyutu uyarısı var)
- **Eğitimler paneli güçlü**: 57 makale, kategoriler, kaynak güven puanı, grafik entegrasyonu var
- **Strateji paneli kapsamlı**: Kural lab, blueprint, preset, walk-forward, monte carlo, optimizasyon, piyasa tarama, rapor arşivi, share özelliği hepsi mevcut
- **Mali analiz altyapısı sağlam**: 9 sekme, BIST 30 karşılaştırma, KAP olayları, finansal grafikler
- **Çizim araçları çalışıyor**: Trendline, yatay çizgi, dikey çizgi, ölçüm, Fibonacci, Fibonacci uzantısı, regresyon kanalı — hepsi DrawingManager'da implementedit
- **MultiChartLayout iyi**: 1x1, 1x2, 2x1, 2x2 layout'lar çalışıyor, sync lock mekanizması var
- **Tema sistemi kapsamlı**: Dark/light, 5 vurgu rengi, localStorage ile kalıcı
- **Klavye kısayolları mevcut**: 1–8 sekme, G layout, F fullscreen, ? yardım penceresi
- **Responsive CSS var**: 768px ve 1024px breakpoint'leri tanımlanmış
- **Cookie banner ve i18n iskeleti** yerinde
- **Paper trading izolasyonu net**: "KAĞIT İŞLEM MODU" banner'ları her iki panelde de görünüyor

---

## 17. Düzeltme Öncelik Sırası

### Önce Bunlar (Kullanıcı Güvenini Etkiliyor / Blocker)

1. **Market Ticker boş şerit** — ya doldur ya kaldır (30 dakika, görsel etki büyük)
2. **Public sayfalarda terminal sızması** — route izolasyonu (1–2 saat)
3. **Sinyaller sekmesi boş durum açıklaması** — bilgi kartı ekle (30 dakika)
4. **Portföy `+-0,00%` format hatası** — `formatPct` fonksiyonunu düzelt (15 dakika)

### Sonra Bunlar (UX Kalitesi)

5. **Strateji panel mode butonu aktif durumu** — `syncControls` sıralaması düzelt
6. **Mobil sidebar — sembol seçim drawer'ı** (2–3 saat)
7. **Walk-Forward / Monte Carlo "önce çalıştır" yönlendirmesi** (30 dakika)
8. **Rapor arşivine silme butonu** (30 dakika)
9. **Screener'da cache boş durumu açıklaması** (15 dakika)
10. **Admin paneline yetki koruması** (1 saat)

### Sonra Bunlar (Tasarım Cilası)

11. Logo marka tutarlılığı ("Piyasa Pilotu" → "PiyasaPilot")
12. Emoji ikonlar → SVG (büyük ama doğru yön)
13. Firefox scrollbar stilleri
14. Light mode kontrast düzeltmeleri
15. Code splitting (performans)

---

*Bu rapor kod değişikliği içermez. Tüm bulgular kaynak kodu statik analizi ve mevcut test raporlarından (WEB_UX_TEST_RAPORU.md) derlenerek oluşturulmuştur.*
