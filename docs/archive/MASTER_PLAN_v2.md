# MASTER_PLAN_v2.md

## 1. Projenin Güncel Durum Özeti
Proje, BIST/VİOP, Kripto, Foreks ve Emtia piyasaları için çalışan, izole bir workspace sistemine sahip, BIST 30 lider tablosu üreten, ve sağlam bir veri izolasyon stratejisi barındıran profesyonel bir backtest & analiz terminali altyapısına sahiptir. Backend çekirdek kısmı, testleri (`pytest` ve `ruff` kontrolleri temiz), ve SQLite kullanan basit depolama mekanizmaları mevcuttur. Ancak UI ve mimari açısından şu an uygulanan eski planlama yöntemleri (örn. `planlama.md`, `arayuz.md`, vb.) nedeniyle karmaşıklık birikmeye başlamıştır. Bu nedenle gereksiz belgeler temizlenerek, hedefe giden süreç konsolide edilmiştir.

### Mevcut Güçlü Yönler:
- İzole edilmiş `Workspace JSON Store` modeli başarılı çalışmaktadır.
- Karar ve sinyal motorlarında "sıfır gerçek dışı veri" kuralı sıkı şekilde uygulanmaktadır.
- Backtest engine unit testleri kapsamlıdır.

### Mevcut Zayıflıklar ve İyileştirme Alanları:
- Düşük hacimli enstrümanlardaki anormal veri sıçramaları (dev fitiller) filtreleme ihtiyacı.
- "Canlı/Gerçek Zamanlı" sistem mimarisine geçerken API kısıtlamalarına karşı zayıf olan mimari.
- Portföy takibi ve paper-trading için spesifik eksiklikler (sanal bakiye, geçmiş PnL).

---

## 2. Araştırma Sonuçları: Kök Nedenler ve Çözümler

### A. Bozuk Veri Problemi: "Dev Fitiller" (Anomalous Price Spikes)
**Kök Neden:** Düşük hacimli hisselerde (örn. sığ BIST hisseleri) veya FX paritelerinde fiyat kotasyon hataları, piyasa emri boşlukları veya provider veri uyuşmazlıkları kaynaklı veri setinde aşırı standart sapma içeren "dev fitiller" (spike) oluşur. Bu veriler Z-Score gibi sadece ortalama ve varyansa bakan yöntemleri de bozar (çünkü dev bir fitil, varyansı da tek başına devasa büyütür).
**Matematiksel Çözüm Algoritması:**
- **IQR (Interquartile Range) Tabanlı Çeyreklik Filtresi + VWAP (Volume-Weighted Anomaly Detection):** 
  - Verilerdeki aykırılıklar, medyan ve çeyreklik açıklık kullanılarak (IQR) tespit edilmelidir. Örneğin, Fiyatın `Q1 - 1.5*IQR` ile `Q3 + 1.5*IQR` aralığı dışında olup olmadığına bakılır.
  - Hacim verisi ile filtre desteklenir: Ekranda büyük bir spike var ama hacim (volume) çok düşükse (veya sıfırsa), bu kesin bir "kotasyon/veri" hatasıdır. Hacimli bir spike ise "Black Swan" veya "Gerçek Piyasa Hareketi" olma ihtimali taşır.
  - **Düzeltme (Winsorization/Imputation):** Dev fitil barı tamamen "silinmez" (Time Series boşluğu olmaması için), bunun yerine fiyat IQR sınırlarına Winsorize edilir (çekilir) veya komşu barların VWAP değeri ile "Impute" (doldurma) yapılır.

### B. Canlı Veri Mimarisi (Zero-Demo Rule)
**Kök Neden:** Streamlit gibi arayüzler ve client-side ağırlıklı istekler, BIST (örn. Yahoo/Matriks) veya ABD borsalarında saniyede çok sayıda HTTP Poll yaratır. Bu da API Rate Limit'lere anında takılmaya yol açar.
**Mimari Çözüm (Hybrid Gateway Pattern):**
- **Kripto İçin WebSocket:** Binance vb. sağlayıcılar WebSocket üzerinden sınırsız public kline akışı verir. Kripto sembolleri direkt WebSocket Listener üzerinden bellek (Redis/Memory) tabanlı state'e güncellenir.
- **BIST/ABD Borsaları İçin Polling/Cache (Backend Cache-Aside):** Frontend (Kullanıcı) asla veri sağlayıcıya doğrudan veya dolaylı gitmez. Backend sunucusunda merkezi bir Data Worker, BIST/ABD hisseleri için API'den verileri çeker (örneğin 1 dakikada bir) ve Redis/SQLite Cache içine yazar (Time-To-Live mantığı). Tüm kullanıcılar ve arayüzler veriyi (WebSockets/SSE üzerinden) sadece bu Cache'den çeker. Böylece 1000 kullanıcı bile olsa, BIST API'sine sadece 1 kez gidilmiş olur.

---

## 3. Yeni Özelliklerin Mimari Tasarımı (Gap Analysis)

### A. Grafikler İçin "Tam Ekran" (Fullscreen) Yeteneği
- Lightweight Charts'ın native Fullscreen API'sine bağlanacak özellik. UI panelleri DOM'dan veya Streamlit arayüzünden gizlenip, chart container'ı `%100 viewport` seviyesine çıkarılarak sağlanacak.

### B. Dinamik Piyasa Gezgini (Market Explorer)
- Sol panele yerleştirilecek Tree/Accordion yapısı. 
- **Kategoriler:** BIST 30, BIST 100, ABD, Kripto. 
- Backend'de `symbol_master.py` genişletilecek. Kullanıcı Market Explorer'dan hisse/coin seçtiğinde workspace izole state'i güncellenerek sağ tarafta ilgili chart'ı ve matrisleri oluşturacak.

### C. "Kendi Portföyüm" (Paper Trading) Ekranı
- **Sanal Bakiye ve PnL Engine:** Mevcut backtest motoruna entegre ancak "canlı fiyatlar" üzerinden güncellenen sanal bir "Portfolio Store".
- SQLite'a `paper_trades` ve `paper_portfolio` isimli iki tablo eklenecek.
- Her trade açıldığında/kapandığında execution log'a (Audit Trail) PnL düşülecek. Arayüzde kâr/zarar, drawdown ve win rate "Kendi Portföyüm" sekmesi altında canlı akacak.

---

## 4. Adım Adım Uygulama Sırası (Master Sprint Planı)

### Sprint 1: Veri Güvenilirliği (Data Sanitization)
1. Fiyat verisi pipeline'ı içine "Spike Filtresi" middleware'i yazılacak (IQR ve Volume-weighted filtering metodu ile).
2. Sığ hisseler test edilerek dev fitillerin Winsorize edildiği `pytest` ile doğrulanacak.

### Sprint 2: Canlı Veri Gateway Mimarisi
1. Backend'e Redis / Memory tabanlı `Cache-Aside` mekanizması kurulacak.
2. BIST/ABD verileri için `Data Worker` yazılacak (Merkezi Polling).
3. Kripto için WebSocket listener servisi entegre edilecek.
4. Tüm quant_engine API çağrıları bu yeni Data Gateway üzerinden geçirilecek.

### Sprint 3: Paper Trading (Sanal Portföy) Altyapısı
1. SQLite veritabanına Portfolio şemaları oluşturulacak.
2. Arayüzden sanal bakiye ile sanal alış/satış (Execution) mock altyapısı backtest motoruna bağlanacak.
3. Kapanan ve açık pozisyonların Canlı PnL hesaplaması Data Gateway verisi üzerinden yürütülecek.

### Sprint 4: Yeni UI ve Dinamik Araçlar
1. Dinamik Piyasa Gezgini (Market Explorer) sol panele ağaç (tree) formatında eklenecek.
2. Lightweight charts container'ı için Tam Ekran (Fullscreen) butonu entegrasyonu yapılacak.
3. "Kendi Portföyüm" ekranı arayüze bağlanacak, gerçekleşen işlemler ve equity eğrisi görselleştirilecek.
