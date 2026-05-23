# PiyasaPilotu — Yasal Uyum ve Risk Azaltma Planı

> Hazırlanma tarihi: 2026-05-23  
> Kapsam: Hukuki, veri lisansı, kullanıcı güvenliği ve yatırım tavsiyesi riski  
> Öncelik: Bu plandaki maddeler, ürünün canlıya alınmasından önce eksiksiz uygulanmalıdır.  
> ⚠️ Son aşamada bir hukukçuya, lisanslı veri sağlayıcısına ve SPK/BIST mevzuatına hâkim bir uzmana danışılmalıdır.

---

## A. TESPİT EDİLEN RİSKLER — DETAYLI LİSTE

### A1. Veri Lisansı Riskleri (Kritik)

**A1.1 — Yahoo Finance BIST Verisi Yeniden Dağıtımı**
- **Konum:** `backend/workers/bist_poller.py`, `quant_engine/data/providers/bist_provider.py`
- **Risk:** BIST hisse verileri `yfinance` (Yahoo Finance) kütüphanesi üzerinden çekilip kullanıcılara gösteriliyor. Yahoo Finance'in Kullanım Şartları, verisinin üçüncü taraflara **yeniden dağıtılmasını (redistribution) açıkça yasaklar.** Özellikle "display or distribute" maddesinde ticari kullanım kısıtlanmıştır. Bu veriyi bir SaaS uygulamasında kullanıcılara sunmak veri lisansı ihlali olarak değerlendirilebilir.
- **Ek Not:** `bist_provider.py` bu veriyi `is_real=False` ve kaynak `"Yahoo Finance (BIST best-effort public)"` olarak doğru etiketlemiş. Ancak `is_real=False` olan veriler için `BIST_HTTP_URL_TEMPLATE` ENV değişkeni tanımlandığında `is_real=True` dönüyor; bu URL'nin hangi kaynağa bağlandığı lisans açısından ayrıca kontrol edilmeli.

**A1.2 — BIST/VİOP Resmi Lisansı Yok**
- **Konum:** `quant_engine/data/providers/viop_provider.py`
- **Risk:** VİOP sağlayıcı `name = "viop_not_configured"`, `source = "Borsa İstanbul VİOP lisanslı/veri sağlayıcı bağlantısı yok"` diyor — bu doğru. Ancak frontend'de bu piyasa için herhangi bir ekranda veri gösteriliyor mu ya da "yakında" etiketi dışında aktif bölüm var mı kontrol edilmelidir.
- **Risk:** Borsa İstanbul, BIST ve VİOP verilerinin yeniden dağıtımı için lisans sözleşmesi zorunlu tutar. Matriks, Rasyonet, IS Investment gibi lisanslı veri sağlayıcılarla sözleşme yapılmadan BIST verisini kullanıcılara sunmak lisans ihlali riskidir.

**A1.3 — Binance WebSocket Kripto Verisi**
- **Konum:** `backend/workers/binance_ws.py`
- **Risk:** Binance public WebSocket'i (market data stream) üçüncü taraflara yeniden dağıtım için Binance API ToS'una tabidir. Gerçek zamanlı kripto verisi yeniden dağıtımı için Binance'in "Market Data License" kapsamında izin alınması gerekebilir. Binance public endpointleri bireysel kullanım için açık olsa da ticari SaaS ürünlerinde özel sözleşme gerekebilir.

---

### A2. Yatırım Tavsiyesi Riski (Kritik — SPK)

**A2.1 — "AL / SAT / GÜÇLÜ AL / GÜÇLÜ SAT" Dili**
- **Konum:** `frontend/src/constants/tr.ts` satır 98–101, `frontend/src/components/SignalFeed.ts` satır 281–282
- **Mevcut kod:**
  ```
  SIGNAL_BUY: 'AL',
  SIGNAL_SELL: 'SAT',
  SIGNAL_STRONG_BUY: 'GÜÇLÜ AL',
  SIGNAL_STRONG_SELL: 'GÜÇLÜ SAT',
  ```
  Toast bildiriminde label: `GÜÇLÜ AL` ve `GÜÇLÜ SAT` ekranda beliriyor.
- **Risk:** SPK mevzuatına göre (Sermaye Piyasası Kanunu Madde 56 ve ilgili tebliğler), yatırım tavsiyesi sunma yetkisi yalnızca SPK lisansına sahip aracı kurumlar veya portföy yönetim şirketlerine aittir. Kullanıcıya "AL" / "SAT" biçiminde bir eylem yönlendirmesi yapan her içerik — hatta "eğitim amaçlı" olduğu belirtilse dahi — yatırım tavsiyesi olarak değerlendirilebilir. "GÜÇLÜ AL" / "GÜÇLÜ SAT" özellikle yüksek risk taşır.

**A2.2 — Telegram Sinyal Bildirimleri**
- **Konum:** `backend/notifier/telegram.py` satır 230–251
- **Mevcut kod:**
  ```python
  f"{emoji} *Yeni Sinyal — {sig_type}*\n"
  f"📌 Sembol: `{symbol}`\n"
  f"💰 Fiyat: `{price:.4f}`\n"
  ```
  Ve: `bildir_alim()` → "🛒 **Alım Gerçekleşti**" / `bildir_satim()` → "💸 **Satım Gerçekleşti**"
- **Risk:** Kullanıcılara Telegram üzerinden "AL/SAT" sinyali iletmek, yatırım tavsiyesi/yönlendirmesi olarak yorumlanabilir. Ayrıca ticari elektronik ileti kanununca (6563 sayılı Kanun) açık onay mekanizması olmadan bildirim göndermek hukuka aykırı olabilir.

**A2.3 — "KONSENSÜS: X/Y strateji AL sinyali" Mesajı**
- **Konum:** `backend/signals/generator.py` satır 300
- **Mevcut kod:**
  ```python
  "reason": f"KONSENSÜS: {buy_count}/{total_strategies} strateji AL sinyali",
  ```
- **Risk:** Bu mesaj, çok sayıda strateji aynı yönde verince yatırımcıyı harekete geçirici doğrulama etkisi (confirmation bias) yaratır. "7/9 strateji AL sinyali" gibi bir mesaj ciddi bir yönlendirme niteliği taşır.

**A2.4 — "AL" / "SAT" Butonları — Portföy Paneli**
- **Konum:** `frontend/src/constants/tr.ts` satır 71–72
- **Mevcut kod:**
  ```
  BUY: 'AL',
  SELL: 'SAT',
  ```
  `PortfolioPanel.ts` bu sabitleri kullanıcıya işlem formu butonları olarak gösteriyor.
- **Risk:** Bu butonlar paper trading içindir ve `TR.PAPER_MODE_BANNER` uyarısı mevcut. Ancak "AL" / "SAT" etiketi yerine "Sanal Al" / "Sanal Sat" gibi bir dil daha net ayrım yapar. Mevcut haliyle sanal işlem ile gerçek işlem arasındaki fark kullanıcıya yeterince güçlü vurgulanmıyor olabilir.

---

### A3. "CANLI" İfadesi ve Yanıltıcı Veri Sunumu

**A3.1 — "CANLI" Etiketinin Lisanssız Bağlantıda Gösterilmesi**
- **Konum:** `frontend/src/constants/tr.ts` satır 12: `LIVE: 'CANLI'`, `frontend/src/components/SignalFeed.ts` satır 318
- **Risk:** SignalFeed bileşeninde WebSocket bağlantısı kurulduğunda durum "CANLI" gösteriyor. Ancak bu WebSocket bağlantısının ilettiği sinyaller yfinance'ten gelen (lisanssız, gecikmeli olabilen) veriye dayanıyor. Kullanıcı "CANLI" ifadesini gerçek zamanlı ve doğru piyasa verisi olarak yorumlayabilir.

**A3.2 — ChartPanel'de "Son Güncelleme: X sn önce"**
- **Konum:** `frontend/src/constants/tr.ts` satır 27–29
- **Risk:** "Son güncelleme birkaç saniye önce" ifadesi lisanssız yfinance verisinde kullanılırsa gerçek zamanlı veri izlenimi doğurur.

**A3.3 — DataQualityBadge'de "Gerçek Veri" Etiketi**
- **Konum:** `frontend/src/components/DataQualityBadge.ts` satır 39
- **Mevcut kod:**
  ```
  ok: { label: 'Gerçek Veri', icon: '●', cssClass: 'dqb-ok' },
  ```
- **Risk:** `is_real=False` olan yfinance verisi için rozet "Gerçek Veri" değil ama `BIST_HTTP_URL_TEMPLATE` tanımlandığında `is_real=True` ve rozet "Gerçek Veri" oluyor. Kullanıcı bu rozeti görerek verinin doğru ve güncel olduğunu düşünebilir; oysa kaynak lisanssız da olabilir.

---

### A4. KVKK ve Gizlilik Riskleri

**A4.1 — Gizlilik Politikası Yetersiz**
- **Konum:** `frontend/src/pages/legal/PrivacyPage.ts`
- **Risk:** Mevcut politika sadece 14 satır ve üç başlık. KVKK (6698 sayılı Kişisel Verilerin Korunması Kanunu) kapsamında zorunlu olan aydınlatma metni unsurları eksik:
  - Veri sorumlusunun kimliği (şirket bilgileri)
  - İşlenen kişisel veri kategorileri (ad, e-posta, IP, cihaz bilgisi, kullanım logları)
  - Veri işleme amaçları ve hukuki dayanakları
  - Verilerin yurt dışına aktarımı (Stripe ABD şirketi; Telegram Hollanda/ABD; email sağlayıcı)
  - Saklama süreleri
  - Kullanıcının hakları (erişim, silme, itiraz, taşınabilirlik)
  - Başvuru kanalı ve cevap süreleri

**A4.2 — Kullanım Şartları Yetersiz**
- **Konum:** `frontend/src/pages/legal/TermsPage.ts`
- **Risk:** Mevcut şartlar sadece 15 satır. Eksikler:
  - Veri doğruluğu garantisi verilmediği
  - Lisanssız veri yayını yapılmayacağı taahhüdü / mevcut durum beyanı
  - Kullanıcı hesabı fesih koşulları
  - Uygulanacak hukuk (Türk hukuku)
  - Uyuşmazlık çözüm yeri (hangi mahkeme/arabuluculuk)
  - Sorumluluk sınırlaması maddesi
  - Yaş sınırı (18 yaş altı kullanıcı)
  - Yatırım tavsiyesi olmadığına dair ayrıntılı hüküm
  - Veri kaynakları ve lisans durumu beyanı

**A4.3 — Çerez Politikası Onay Mekanizması**
- **Konum:** `frontend/src/components/CookieBanner.ts` (mevcut)
- **Risk:** CookieBanner bileşeni var; ancak 3. taraf analitik (Sentry, Stripe, Telegram vs.) için ayrıştırılmış çerez kategorileri ve gerçek onay kaydı tutulup tutulmadığı kontrol edilmeli. LocalStorage tercihlerin "çerez" olarak muamele görüp görmediği de netleştirilmeli.

**A4.4 — Telegram Bildirim Onayı**
- **Konum:** `backend/notifier/preferences.py`, `frontend/src/components/SignalFeed.ts`
- **Risk:** Kullanıcı Telegram botunu kendisi bağlıyor; ancak bot aracılığıyla gönderilen sinyaller, işlem bildirimleri ve sistem mesajları "elektronik ticari ileti" kapsamına girebilir. 6563 sayılı Kanun ve İYS (İleti Yönetim Sistemi) kapsamında açık onay ve kolay iptal mekanizması gerekir.

**A4.5 — E-posta Bildirimleri**
- **Konum:** `backend/notifier/email.py`, `backend/auth/email_sender.py`
- **Risk:** `verify_email.html`, `welcome.html`, `subscription_pro.html`, `quota_warning.html`, `payment_failed.html` şablonları mevcut. İşlem/doğrulama e-postaları onay gerektirmez; ancak pazarlama/promosyon içerikleri için açık onay alınmalıdır.

---

### A5. Performans ve Kazanç Vaadi Riski

**A5.1 — Telegram Günlük Özet: Win Rate**
- **Konum:** `backend/notifier/telegram.py` satır 336–337
- **Mevcut kod:**
  ```python
  f"📈 Kazanma Oranı: `{win_rate:.1f}%` ({len(kazananlar)}/{len(tamamlanan)} işlem)"
  ```
- **Risk:** Paper trading sonuçlarına dayalı "kazanma oranı" metriği, kullanıcıda gerçek piyasada da bu oranın geçerli olacağı algısı yaratabilir. SPK tebliğlerine göre gerçekleşmiş getiri olmayan performans verisi reklam materyallerinde yanıltıcı olarak değerlendirilebilir.

**A5.2 — BacktestResult Metrikleri ve Paylaşım**
- **Konum:** `frontend/src/pages/SharedBacktestPage.ts`
- **Risk:** Kullanıcılar backtest sonuçlarını (getiri, Sharpe oranı, kazanma oranı) üçüncü taraflarla paylaşabiliyorsa, bu paylaşılan içerikte performans beyanı niteliği taşıyan ifadeler dikkatli ele alınmalıdır.

---

## B. HANGI EKRANDA HANGİ METİN DEĞİŞMELİ

### B1. `frontend/src/constants/tr.ts`

| Satır | Mevcut | Değişecek | Gerekçe |
|---|---|---|---|
| 12 | `LIVE: 'CANLI'` | `LIVE: 'BAĞLANTI AKTİF'` | "CANLI" kelimesi lisanslı gerçek zamanlı veri olmadıkça kullanılmamalı |
| 53 | `UI_LIVE: 'Canlı'` | `UI_LIVE: 'Bağlı'` | Aynı gerekçe |
| 98 | `SIGNAL_BUY: 'AL'` | `SIGNAL_BUY: 'AL Sinyali'` | Eylem değil, teknik sinyal olduğu vurgulanmalı |
| 99 | `SIGNAL_SELL: 'SAT'` | `SIGNAL_SELL: 'SAT Sinyali'` | Aynı |
| 100 | `SIGNAL_STRONG_BUY: 'GÜÇLÜ AL'` | `SIGNAL_STRONG_BUY: 'Güçlü AL Sinyali'` | Daha az yönlendirici |
| 101 | `SIGNAL_STRONG_SELL: 'GÜÇLÜ SAT'` | `SIGNAL_STRONG_SELL: 'Güçlü SAT Sinyali'` | Aynı |
| 71 | `BUY: 'AL'` | `BUY: 'Sanal Al'` | Paper trading bağlamında gerçek alım olmadığı net olmalı |
| 72 | `SELL: 'SAT'` | `SELL: 'Sanal Sat'` | Aynı |
| 125 | `SIGNAL_FEED_INFO: 'Tüm semboller · Tüm stratejiler · Her bar kapanışında güncellenir'` | Altına uyarı eklenmeli | Teknik sinyal bilgilendirmesi |

**Eklenecek yeni sabitler:**
```typescript
// Yasal uyarı sabitleri
SIGNAL_DISCLAIMER: 'Bu sinyaller yatırım tavsiyesi değildir. Teknik analiz göstergesidir. Kararlarınızı lisanslı danışmanınızla değerlendirin.',
DATA_LICENSE_DISCLAIMER: 'Veriler gecikmeli, eksik veya hatalı olabilir. Lisans ve kaynak durumu ilgili piyasada ayrıca belirtilmiştir.',
BIST_DATA_STATUS: 'BIST verileri: Lisanslı veri sağlayıcı bağlantısı bekleniyor. Şu an yalnızca eğitim amaçlı örnek/gecikmeli veri.',
VIOP_DATA_STATUS: 'VİOP verileri: Lisanslı veri sağlayıcı bağlantısı kurulmamıştır. Bu piyasa henüz aktif değildir.',
CRYPTO_DATA_STATUS: 'Kripto verileri: Binance public feed. Ticari yeniden dağıtım koşulları Binance API ToS kapsamındadır.',
PAPER_ONLY_WARNING: 'SANAL İŞLEM — Gerçek para ve gerçek piyasa emri söz konusu değildir.',
```

---

### B2. `frontend/src/components/SignalFeed.ts`

| Satır/Alan | Mevcut | Değişecek |
|---|---|---|
| 281–282 | `label = isBuy ? 'GÜÇLÜ AL' : 'GÜÇLÜ SAT'` | `label = isBuy ? 'Güçlü AL Sinyali' : 'Güçlü SAT Sinyali'` |
| Toast başlığı | `${label} — ${sig.symbol}` | `${label} — ${sig.symbol} ⚠️ Tavsiye değildir` |
| Render fonksiyonu | SIGNAL_FEED_INFO altı | Sabit uyarı metni eklenecek (bkz. D1) |
| Status badge "CANLI" | `TR.LIVE` | `TR.LIVE` güncelleniyor (B1) + yanına parantez "(WebSocket bağlantısı)" |

---

### B3. `frontend/src/components/DataQualityBadge.ts`

| Satır | Mevcut | Değişecek |
|---|---|---|
| 39 | `ok: { label: 'Gerçek Veri', ... }` | `ok: { label: 'Kaynak Bağlı', ... }` — "Gerçek" kelimesi doğruluk garantisi çağrışımı yapıyor |
| Tooltip | `is_real ? '✓ Evet' : '✕ Hayır'` | `is_real ? '✓ Lisanslı/Kaynaktan' : '✕ Lisanssız/Gecikmeli'` |
| `license_note` alanı | Varsa gösteriliyor | Lisans notu zorunlu hale getirilmeli (boşsa "Lisans bilgisi yok" göster) |

---

### B4. `backend/signals/generator.py`

| Satır | Mevcut | Değişecek |
|---|---|---|
| 300 | `f"KONSENSÜS: {buy_count}/{total_strategies} strateji AL sinyali"` | `f"Teknik Konsensüs: {buy_count}/{total_strategies} strateji AL yönlü — yatırım tavsiyesi değildir"` |
| 323 | `f"KONSENSÜS: {sell_count}/{total_strategies} strateji SAT sinyali"` | `f"Teknik Konsensüs: {sell_count}/{total_strategies} strateji SAT yönlü — yatırım tavsiyesi değildir"` |
| `reason` alanı (286, 300) | `f"{name}: {sig_type} @ {price:.2f}"` | `f"Teknik görünüm ({name}): {sig_type} @ {price:.2f} — tavsiye değildir"` |

---

### B5. `backend/notifier/telegram.py`

| Satır | Mevcut | Değişecek |
|---|---|---|
| 243–250 | `*Yeni Sinyal — {sig_type}*` | `*Teknik Sinyal Notu — {sig_type}*` |
| 243 | Emoji 🟢/🔴 ile başlıyor | `⚠️` uyarısı eklenmeli: "Bu bir yatırım tavsiyesi değildir." satırı |
| 260–267 | `*Alım Gerçekleşti*` | `*Sanal Alım (Paper Trading)*` |
| 275–283 | `*Satım Gerçekleşti*` | `*Sanal Satım (Paper Trading)*` |
| 295–304 | `*Cüzdan Donduruldu*` | `*Sanal Cüzdan Donduruldu (Paper Trading)*` |
| 330–338 | `📈 Kazanma Oranı: ...` | `📊 Paper Trading Oranı (gerçek getiri değil): ...` |
| Her mesajın altı | (yok) | Sabit disclaimer satırı eklenebilir: `ℹ️ Bu bildirim yatırım tavsiyesi değildir. Eğitim/paper trading amaçlıdır.` |

---

### B6. `frontend/src/pages/LandingPage.ts`

| Alan | Mevcut | Değişecek |
|---|---|---|
| Hero copy | `"Strateji fikrini kurala çevir, gerçek veriyle test et"` | `"gerçek veriyle"` → `"geçmiş veriyle"` (backtest geçmiş veri kullanır) |
| Hero counters | `<span><b>0</b> gerçek emir</span>` | Bu sayaç iyi; ama açıklamasına "Gerçek emir gönderimi desteklenmez" eklenebilir |
| Footer veya hero altı | (yok) | Kısa yasal uyarı şeridi eklenmeli (bkz. D3) |
| Feature card "Sinyaller" | `"Trading araştırması için sade..."` | "Teknik analiz sinyalleri. Yatırım tavsiyesi değildir." |

---

## C. LİSANS GELENE KADAR KAPATILMASI GEREKEN ÖZELLİKLER

### C1. Derhal Kapatılacak / Pasifleştirilecek

| Özellik | İlgili Dosya | Neden |
|---|---|---|
| BIST hisselerinde gerçek fiyat gösterimi (yfinance) | `bist_provider.py`, `bist_poller.py` | Yahoo ToS yeniden dağıtım yasağı |
| BIST hisselerinde sinyal üretimi | `generator.py` `_trusted_metadata()` | Lisanssız veriden sinyal üretilemez; `is_real=False` kontrolü zaten var AMA yfinance için is_real=False olduğundan sinyal üretilmiyor — bu kontrol doğru çalışıyor, belgelenmeli |
| BIST için "CANLI" etiketi | `tr.ts`, `DataQualityBadge.ts` | Gerçek zamanlı lisanslı feed yok |
| VİOP tabanlı tüm görünümler | `viop_provider.py`, Sidebar | Lisanssız; sağlayıcı zaten kapalı ama UI'da görünmemeli |
| Telegram'da BIST sinyali iletimi | `telegram.py`, `preferences.py` | Lisanssız veriden sinyal iletimi |

### C2. Koşullu Aktif Kalacaklar (Lisans Sonrası Açılacak)

| Özellik | Koşul |
|---|---|
| BIST gerçek zamanlı fiyat gösterimi | Matriks/Rasyonet/BIST API lisans sözleşmesi imzalanınca |
| VİOP veri gösterimi | VİOP lisanslı feed sözleşmesi imzalanınca |
| BIST hisselerinde sinyal üretimi | Lisanslı feed aktif, `is_real=True` döndüğünde |
| BIST screener | Lisanslı feed sonrası |
| "CANLI" etiketi BIST için | Lisanslı gerçek zamanlı feed aktif olduğunda |

### C3. Lisans Bağımsız Aktif Kalabilecekler

| Özellik | Not |
|---|---|
| Kripto (Binance WS) | Binance ToS'u tekrar kontrol edilmeli; bireysel use case için açık, ticari SaaS için belirsiz |
| Backtest motoru (geçmiş veriyle) | Kullanıcının kendi yüklediği veri veya lisanslı veri ile çalışırsa sorun yok |
| Paper trading | "SANAL İŞLEM" etiketi açık olduğu sürece sorun yok |
| Mali analiz (KAP RSS) | KAP RSS public feed; yeniden dağıtım koşulları KAP'ın ToS'una göre değerlendirilmeli |
| Teknik indikatörler (hesaplama) | Kendi hesaplamalar, lisans sorunu yok |
| Eğitim içerikleri | Lisans sorunu yok |

---

## D. KULLANICIYA GÖSTERİLECEK GÜVENLİ UYARI METİNLERİ

### D1. Sinyal/Analiz Uyarısı (Her sinyal ekranında sabit gösterilecek)

```
⚠️ Yatırım Tavsiyesi Uyarısı
Bu içerik yatırım tavsiyesi değildir. Yalnızca teknik analiz göstergeleri 
ve eğitim amaçlı bilgilendirme içerir. Finansal kararlarınızı kendi 
araştırmanız, risk toleransınız ve gerekiyorsa lisanslı bir yatırım 
danışmanıyla değerlendirerek veriniz. PiyasaPilotu, herhangi bir finansal 
sonuçtan sorumlu tutulamaz.
```

### D2. Veri Lisansı / Kalite Uyarısı (Her piyasa verisi ekranında)

```
📊 Veri Kaynağı ve Kalite Bildirimi
Veriler gecikmeli, eksik veya hatalı olabilir. Piyasaya göre veri durumu:
  • Kripto (BTC, ETH vb.): Binance public stream — gerçek zamanlıya yakın
  • BIST hisseleri: Lisanslı veri sağlayıcı bekleniyor — şu an eğitim amaçlı
  • VİOP sözleşmeleri: Henüz aktif değil — lisans süreci devam ediyor
Veri doğruluğu ve güncelliği garanti edilmez. Yatırım kararlarında 
yalnızca bu veriye dayanmayınız.
```

### D3. Landing Page / Genel Disclaimer (Footer veya bilgi şeridi)

```
PiyasaPilotu bir yatırım danışmanlığı hizmeti değildir. Gösterilen veriler, 
sinyaller ve analizler yalnızca eğitim ve araştırma amaçlıdır. Gerçek emir 
gönderimi desteklenmez. BIST ve VİOP verileri için lisans süreci devam 
etmektedir; bu piyasalardaki veriler şu an eğitim/demo niteliğindedir.
```

### D4. Paper Trading Ekranı Uyarısı (mevcut banner genişletilecek)

```
SANAL İŞLEM MODU
Bu ekrandaki tüm emirler, pozisyonlar ve bakiyeler tamamen simüle edilmiştir. 
Gerçek para, gerçek piyasa emri veya gerçek finansal sonuç söz konusu 
değildir. "Al" / "Sat" butonları yalnızca sanal portföy simülasyonunu 
etkiler.
```

### D5. BIST/VİOP "Lisans Bekleniyor" Ekranı

```
🔒 Bu piyasa şu an aktif değildir
BIST hisse / VİOP sözleşme verileri için lisanslı veri sağlayıcı 
görüşmeleri devam etmektedir. Lisans sürecini tamamladıktan sonra 
bu ekran aktif hale gelecektir.
Neden bu uyarıyı görüyorsunuz?
Borsa İstanbul, BIST ve VİOP verilerinin üçüncü taraflara 
dağıtılması için ayrı bir lisans sözleşmesi zorunlu kılar. 
Kullanıcılarımızı yanlış veya lisanssız veriyle yönlendirmemek 
için bu ekranı geçici olarak kapattık.
```

### D6. Telegram Bildirim Onay Metni

```
Telegram sinyal bildirimlerini aktifleştirmek üzeresiniz.
Bu bildirimler yatırım tavsiyesi değildir; teknik analiz 
göstergeleri içerir. Devam etmek için aşağıdakileri onaylamalısınız:

☐ Telegram bildirimlerinin yatırım tavsiyesi içermediğini anlıyorum.
☐ Kişisel verilerimin (Telegram chat ID) yalnızca bildirim 
  amaçlı saklanacağını ve üçüncü taraflarla paylaşılmayacağını 
  kabul ediyorum.
☐ İstediğim zaman bildirimleri kapatabileceğimi biliyorum.

[Onayla ve Aktifleştir]  [Vazgeç]
```

---

## E. KULLANIM ŞARTLARI SAYFA İÇERİK TASLAĞИ

> Mevcut `TermsPage.ts` tamamen yeniden yazılacak. Aşağıdaki başlıkların her biri için tam paragraf metni bir hukukçu tarafından gözden geçirilmelidir.

```
Kullanım Koşulları
Son güncelleme: [tarih]

1. TARAFLAR VE KAPSAM
   PiyasaPilotu ([Şirket Adı / Şahıs], [Adres]) tarafından işletilen 
   piyasapilot.com ve ilgili mobil uygulamalar (birlikte "Platform") 
   bu koşullara tabidir.

2. HİZMETİN NİTELİĞİ — YATIRIM TAVSİYESİ DEĞİLDİR
   Platform; teknik analiz araçları, backtest simülasyonu, 
   piyasa verileri ve eğitim içerikleri sunar. Platform yatırım 
   danışmanlığı, portföy yönetimi veya finansal tavsiye hizmeti 
   vermez ve veremez. Gösterilen sinyaller, analizler ve raporlar 
   yalnızca bilgilendirme ve eğitim amaçlıdır; herhangi bir menkul 
   kıymetin alınması veya satılması yönünde tavsiye niteliği taşımaz.
   SPK lisansı gerektiren faaliyetler Platform kapsamında sunulmaz.

3. VERİ KAYNAKLARI VE LİSANS DURUMU
   a) Kripto verileri: Binance public market data stream.
   b) BIST hisse verileri: [Lisans süreci devam ettiği sürece] 
      "Veri lisansı bekleniyor — bu piyasa eğitim/demo modundadır."
      Lisanslı feed aktif olduğunda güncelleme yapılacaktır.
   c) VİOP verileri: Henüz lisanslı kaynak bağlanmamıştır.
   d) KAP haberleri: KAP RSS public feed.
   Veri doğruluğu, güncelliği veya eksiksizliği garanti edilmez.
   Platforma yüklenen veya oluşturulan içeriklerin lisans 
   uyumundan kullanıcı sorumludur.

4. GERÇEK EMİR GÖNDERİMİ YOKTUR
   Platform aracılık hizmeti sunmaz. "AL" / "SAT" / "Sanal Al" / 
   "Sanal Sat" etiketli işlemler tamamen simüle olup gerçek piyasa 
   emirlerine dönüştürülmez.

5. KULLANICI SORUMLULUĞU VE SORUMLULUK SINIRLAMASI
   Kullanıcı, Platform bilgilerini esas alarak aldığı yatırım 
   kararlarından ve doğan finansal sonuçlardan münferiden 
   sorumludur. Platform, veri hatalarından, kesintilerinden, 
   gecikmelilerden veya kullanıcının bu verilere dayanarak aldığı 
   kararların sonuçlarından yasal olarak sorumlu tutulamaz.
   Platform'un sorumluluğu, yasal zorunluluklar dışında, 
   kullanıcının ödediği son aylık abonelik ücretiyle sınırlıdır.

6. YASAKLI KULLANIM
   Kullanıcılar Platform'u; başkalarını yanıltmak, piyasa 
   manipülasyonu, veri toplayıcılığı (scraping), yasa dışı 
   amaçlar veya üçüncü taraflara lisanssız veri satmak için 
   kullanamaz.

7. YAŞ SINIRI
   Platform 18 yaşını doldurmuş bireylere yöneliktir. 18 yaş 
   altı kişilerin hesap açması yasaktır.

8. HESAP VE ABONELİK
   [Abonelik, iptal, ücret iadesi koşulları]

9. FİKRİ MÜLKİYET
   [Platform içerikleri, yazılım ve tasarım hakları]

10. GİZLİLİK
    Gizlilik Politikamıza ([link]) tabi olarak kişisel veriler 
    işlenir.

11. UYGULANACAK HUKUK VE UYUŞMAZLIK ÇÖZÜMÜ
    Bu koşullar Türk hukukuna tabidir. Uyuşmazlıklarda 
    [İstanbul / Ankara] Mahkemeleri ve İcra Daireleri yetkilidir.
    Taraflar öncelikle arabuluculuğa başvurur.

12. DEĞİŞİKLİKLER
    Koşullar değiştiğinde kullanıcıya e-posta ile bildirilir ve 
    30 gün önceden duyurulur. Kullanım devam edilirse yeni 
    koşullar kabul edilmiş sayılır.
```

---

## F. GİZLİLİK POLİTİKASI VE KVKK AYDINLATMA METNİ TASLAĞИ

> Mevcut `PrivacyPage.ts` tamamen yeniden yazılacak. KVKK m.10 kapsamında zorunlu aydınlatma unsurları eksiksiz yer almalıdır.

```
Gizlilik Politikası ve KVKK Aydınlatma Metni
Son güncelleme: [tarih]

VERİ SORUMLUSU
[Şirket adı veya işletmeci adı-soyadı], [adres], [e-posta]

1. İŞLENEN KİŞİSEL VERİLER VE AMAÇLARI

   Kategori         | Örnekler                     | Amaç
   ─────────────────────────────────────────────────────
   Kimlik           | Ad, soyad                    | Hesap oluşturma
   İletişim         | E-posta adresi               | Doğrulama, bildirim
   Kimlik Doğrulama | Şifrelenmiş parola, OAuth ID | Güvenli oturum
   İşlem Verisi     | Abonelik, fatura geçmişi     | Ödeme/fatura yönetimi
   Kullanım Logu    | IP, cihaz, tarayıcı          | Güvenlik, hata tespiti
   Tercihler        | Sembol tercihleri, tema      | Hizmet kişiselleştirme
   Telegram Chat ID | Telegram kullanıcı kimliği  | Bildirim hizmeti (onay ile)

2. HUKUKİ DAYANAK (KVKK m.5)
   - Sözleşmenin ifası (hesap, abonelik, ödeme)
   - Meşru menfaat (güvenlik, hata tespiti)
   - Açık rıza (pazarlama bildirimleri, Telegram botları)

3. VERİLERİN AKTARIMI
   a) Stripe Inc. (ABD): Ödeme işleme — standart sözleşme hükümleri
   b) Telegram Messenger (Hollanda/ABD): Bot bildirimleri — kullanıcı onayıyla
   c) [Email sağlayıcı]: Doğrulama ve bildirim e-postaları
   d) [Hosting/cloud]: Sunucu altyapısı — veri işleme sözleşmesi var
   e) Yetkili kamu kurumları: Yasal zorunluluk halinde

4. SAKLAMA SÜRELERİ
   - Aktif hesap verisi: Hesap silinene kadar
   - Fatura/ödeme kayıtları: 10 yıl (VUK zorunluluğu)
   - Erişim logları: 6 ay
   - Telegram ID: Kullanıcı botu devre dışı bırakana kadar
   - Silme talebi sonrası: 30 gün içinde anonimleştirme

5. KULLANICI HAKLARI (KVKK m.11)
   - Verilerinize erişim talep etme
   - Yanlış verilerin düzeltilmesini isteme
   - Verilerin silinmesini / anonimleştirilmesini talep etme
   - İşlemeye itiraz etme
   - Veri taşınabilirliği (makine okunabilir format)
   - Otomatik işlemeye karşı itiraz
   
   BAŞVURU: [email] adresine "KVKK Başvurusu" konusuyla yazın.
   30 gün içinde yanıt verilir. Yanıt verilmezse KVK Kurulu'na 
   başvurabilirsiniz.

6. KİŞİSEL VERİ GÜVENLİĞİ
   - Parolalar bcrypt ile hash'lenir, düz metin saklanmaz
   - Kart bilgileri sunucularımızda saklanmaz (Stripe'a yönlendirilir)
   - Oturumlar HttpOnly, Secure, SameSite=Lax cookie ile yönetilir
   - HTTPS zorunludur; TLS 1.2+ kullanılır

7. ÇEREZ POLİTİKASI REFERANSI
   Çerez kullanımı için ayrı [Çerez Politikası] sayfasına bakınız.

8. PAZARLAMA İLETİŞİMİ
   Ticari elektronik ileti (promosyon e-postası, pazarlama bildirimi) 
   yalnızca açık onay alınan kullanıcılara gönderilir. İptal: Her 
   mesajda "Abonelikten çık" linki bulunur veya [email] adresine 
   yazılabilir.
```

---

## G. ÇEREZ POLİTİKASI — GÜNCELLENMİŞ TASLAK

> `frontend/src/pages/legal/CookiesPage.ts` yeniden yazılacak.

```
Çerez Politikası
Son güncelleme: [tarih]

1. ZORUNLU ÇEREZLER (onay gerektirmez)
   - Oturum çerezi (session_id): Giriş durumu yönetimi. 30 gün.
   - CSRF token: Güvenlik. Oturum süresi.
   - Dil/tema tercihi (localStorage): Görünüm kişiselleştirme.

2. ANALİTİK ÇEREZLER (onay gerektirir)
   - [Sentry]: Hata izleme ve performans analizi.
     Sentry veri işleme politikası: sentry.io/privacy
   - [Gelecekte eklenirse Google Analytics / benzeri]: 
     Sayfada bildirilecektir.

3. ÖDEME ÇEREZLER (zorunlu, ödeme akışında)
   - Stripe tarafından ödeme güvenliği için kullanılır.
     Stripe çerez politikası: stripe.com/cookie-settings

4. ÇEREZ TERCİHLERİNİZİ YÖNETİN
   Sayfanın altındaki "Çerez Ayarları" bağlantısından 
   tercihlerinizi güncelleyebilirsiniz. Zorunlu çerezler 
   devre dışı bırakılamaz.

5. ÜÇ TARAF ÇEREZLER
   Platform'un gömülü içerikleri (varsa: YouTube, widget) 
   üçüncü taraf çerez kullanabilir. Bu çerezler üçüncü 
   tarafların politikalarına tabidir.
```

---

## H. HER PİYASA İÇİN AYRI GÜVENLİ ÜRÜN POLİTİKASI

### H1. Kripto (BTC, ETH, USDT vb.)

| Alan | Politika |
|---|---|
| Veri kaynağı | Binance public WebSocket stream |
| Lisans durumu | Public feed — Binance ToS'u incelenmeli, ticari SaaS için özel sözleşme gerekebilir |
| "CANLI" etiketi | Bağlantı aktifken "Bağlantı Aktif" etiketi kullanılabilir |
| Sinyal üretimi | `is_real=True` döndüğünde aktif — `_trusted_metadata()` kontrolü yeterli |
| Veri uyarısı | "Kripto verileri: Binance public feed. Ticari dağıtım için Binance API ToS kapsamındadır." |
| Telegram bildirimi | Aktif — ama "yatırım tavsiyesi değildir" uyarısı her mesajda olmalı |

### H2. BIST Hisseleri

| Alan | Politika |
|---|---|
| Veri kaynağı | Şu an: yfinance (Yahoo Finance) |
| Lisans durumu | **LİSANSSIZ** — Yahoo ToS yeniden dağıtımı yasaklar |
| Lisanslı seçenekler | Matriks Veri Terminali, Rasyonet, IS Investment API, Tera Yatırım, Gedik API |
| Kullanıcıya gösterim | Lisans sözleşmesi imzalanana kadar: "Bu piyasa lisans sürecindedir — veriler gösterilemiyor" |
| "CANLI" etiketi | Lisanslı gerçek zamanlı feed aktif olana kadar asla kullanılmayacak |
| Sinyal üretimi | `_trusted_metadata()` `is_real=False` kontrolü yfinance için zaten kapalı — **bu doğru** |
| Fiyat listesi/grafik | Lisanslı feed gelene kadar kapalı veya "örnek/demo" olarak işaretli |
| Screener | Lisanslı feed gelene kadar kapalı |
| Önerilen iletişim | BIST DataStore (data.borsaistanbul.com) veya Matriks ile görüşme |

### H3. VİOP (Vadeli İşlemler)

| Alan | Politika |
|---|---|
| Veri kaynağı | Şu an: Yapılandırılmamış (`NOT_CONFIGURED`) |
| Lisans durumu | **KAPALI** — backend zaten `NOT_CONFIGURED` döndürüyor |
| UI durumu | Sidebar'da gösterilecekse "Yakında — Lisans Süreci" etiketi |
| Kullanıcıya mesaj | "VİOP verileri için lisanslı kaynak bağlanmamıştır. Bu piyasa henüz aktif değildir." |
| Sinyal üretimi | `is_real=False` → sinyal üretilmiyor — doğru |

---

## I. TEKNİK DETAYA GİRMEDEN UYGULANACAK NET İŞ PLANI

### Faz 1 — Acil (Canlıya Almadan Önce Zorunlu): ~2–3 gün

1. **BIST fiyat gösterimini geçici kapat veya "Lisans Bekleniyor" ekranıyla değiştir.**
   - `bist_provider.py`'de yfinance fallback tamamen kaldırılabilir ya da `is_real=False` data için frontend'de placeholder gösterilir.
   
2. **"CANLI" / "LIVE" kelimesini `tr.ts` ve `DataQualityBadge.ts`'de güvenli alternatifle değiştir.**

3. **Sinyal dili güncelle:** AL/SAT → AL Sinyali/SAT Sinyali; GÜÇLÜ AL → Güçlü AL Sinyali. Tüm toast, badge ve Telegram mesajlarında.

4. **Her sinyal ekranına sabit uyarı metnini ekle** (D1 metnini kullan).

5. **Telegram bildirimine "yatırım tavsiyesi değildir" satırı ekle.**

6. **TermsPage, PrivacyPage, CookiesPage'i E, F, G taslağıyla yeniden yaz.**

7. **BIST sinyallerini Telegram üzerinden iletme — sadece kripto sinyalleri iletilsin.**

### Faz 2 — Kısa Vadeli (Canlıya Alındıktan Sonra İlk Hafta): ~1 hafta

8. **Binance API ToS'unu ticari SaaS kullanımı açısından hukuki danışmanla değerlendir.** Gerekirse Binance Data License başvurusu yap.

9. **BIST lisanslı veri sağlayıcılarıyla görüşmeye başla:** Matriks Veri Terminali API, Rasyonet, IS Investment API.

10. **Telegram onay akışını uygula:** Kullanıcı botu ilk aktifleştirdiğinde D6 metninde yazan onay kutucuklarını göster ve yanıtı kaydet.

11. **E-posta pazarlama onayı:** Kayıt formuna isteğe bağlı "Kampanya ve yeniliklerden haberdar olmak istiyorum" kutucuğu ekle.

12. **KVKK veri envanteri çıkar:** Hangi tablolarda hangi kişisel veriler tutuluyor listele; silme/anonimleştirme API endpoint'i ekle.

### Faz 3 — Orta Vadeli (1 Ay): ~2–4 hafta

13. **BIST lisanslı feed anlaşması imzalandığında:**
    - Mevcut `BIST_HTTP_URL_TEMPLATE` mekanizmasına yeni sağlayıcı bağla
    - `is_real=True` döndüğünde "Lisanslı Veri" etiketi göster
    - "CANLI" etiketini lisanslı feed için geri aç
    - BIST screener ve sinyallerini aç

14. **VİOP lisanslı feed anlaşması imzalandığında:**
    - `VIOP_HTTP_URL_TEMPLATE` ENV'i tanımla
    - VİOP Sidebar bölümünü aktif et

15. **SPK/BIST mevzuatı uzmanına danış:** Uygulamanın mevcut özellik seti (sinyal üretimi, tarama, paper trading) SPK kapsamında herhangi bir lisans gerektirip gerektirmediği netleştirilmeli.

16. **KAP RSS kullanım koşullarını doğrula:** KAP verisi ticari uygulamalarda yeniden dağıtım için KAP/SPK'nın iznini gerektiriyor mu?

17. **Yasal Bilgilendirme sayfası oluştur:** Tüm veri kaynakları, lisans durumları, uyarılar ve iletişim kanalını tek sayfada sun.

---

## J. YASAL BİLGİLENDİRME SAYFASI TASLAĞИ

> Uygulamaya `/legal/info` veya `/yasal` olarak eklenmeli.

```
Yasal Bilgilendirme

1. UYGULAMA HAKKINDA
   PiyasaPilotu bir fintech eğitim ve araştırma platformudur. 
   SPK lisanslı bir yatırım kuruluşu değildir ve yatırım 
   tavsiyesi hizmeti vermez.

2. VERİ KAYNAKLARI VE LİSANS DURUMU
   ─────────────────────────────────
   Kripto    │ Binance public stream │ Aktif (ToS kontrolü devam ediyor)
   BIST      │ Lisanslı kaynak       │ Süreç devam ediyor — şu an kapalı
   VİOP      │ Lisanslı kaynak       │ Süreç devam ediyor — şu an kapalı
   KAP Haber │ KAP RSS               │ Aktif (public feed)
   ─────────────────────────────────

3. YATIRIM TAVSİYESİ DEĞİLDİR BEYANI
   Platform içindeki sinyaller, analizler, screener sonuçları, 
   backtest raporları ve Telegram bildirimleri Sermaye Piyasası 
   Kanunu çerçevesinde yatırım tavsiyesi niteliği taşımaz. Bu 
   içerikler teknik analiz göstergeleri ve eğitim materyalleridir.

4. VERİ DOĞRULUĞU GARANTİSİ
   Veri doğruluğu, eksiksizliği veya gerçek zamanlılığı garanti 
   edilmez. Gösterilen her veri için kaynağı ve güvenilirliği 
   kullanıcı tarafından doğrulanmalıdır.

5. KULLANICI SORUMLULUĞU
   Yatırım kararlarınızın tüm mali ve hukuki sonuçlarından 
   kendiniz sorumlusunuzdur. Platformu kullanmadan önce kendi 
   araştırmanızı yapmanız ve gerekirse lisanslı yatırım 
   danışmanına başvurmanız önerilir.

6. İLETİŞİM VE ŞİKÂYET KANALI
   E-posta: [iletisim@piyasapilot.com]
   KVKK başvurusu: [kvkk@piyasapilot.com]
   Veri sağlayıcı lisans talebi: [veri@piyasapilot.com]
   Şikâyet için KVK Kurulu: kvkk.gov.tr
```

---

## K. SON NOT — UZMAN DANIŞMANLIK GEREKTİREN KONULAR

Aşağıdaki konularda yazılım/teknik değerlendirme yetersiz olup uzman görüşü şarttır:

1. **SPK Lisanslama:** Sinyal üretimi, tarama ve paper trading özelliklerinin "yatırım tavsiyesi" veya "portföy yönetimi" kapsamına girip girmediği, dolayısıyla SPK izni gerekip gerekmediği. → **SPK mevzuatına hâkim finans hukukçusu**

2. **BIST/VİOP Veri Lisansı:** Borsa İstanbul DataStore ile ya da yetkili veri dağıtıcılarıyla (Matriks, Rasyonet vb.) sözleşme süreci ve koşulları. → **BIST veri lisans birimi ile doğrudan iletişim**

3. **Yahoo Finance ToS:** Mevcut yfinance kullanımının tam olarak değerlendirilmesi ve meşru kullanım sınırlarının belirlenmesi. → **Hukukçu + Yahoo ToS değerlendirmesi**

4. **KVKK/GDPR Uyum Denetimi:** Mevcut veri akışlarının (Stripe, Telegram, email provider, cloud hosting) KVKK ve AB'deki kullanıcılar için GDPR uyumluluğu. → **Kişisel veri koruma hukukçusu**

5. **6563 Sayılı Kanun (Elektronik Ticaret):** Telegram ve e-posta üzerinden gönderilen bildirimlerin ticari elektronik ileti sayılıp sayılmadığı ve İYS kaydı gerekip gerekmediği. → **E-ticaret hukuku uzmanı**

---

*Bu plan bir kodlama yol haritası değil, hukuki uyum rehberidir. Yukarıdaki teknik değişiklikler uygulandıktan sonra tüm yasal içeriklerin (Kullanım Şartları, Gizlilik Politikası, Çerez Politikası, Yasal Bilgilendirme) bir hukukçu tarafından son kez gözden geçirilmesi zorunludur.*
