# Quant Engine — Arayüz Planı (v3 — Matrix Terminal Vizyonu)

## Altın Kural

> **"Her grafik, her sinyal ve her trade; backtest motorunun audit trail kaydından gelsin."**
> Ekranda görünen her şey hesaplanabilir, sorgulanabilir ve tekrar üretilebilir olmalı.
> Motor yanlışsa arayüz sadece yanlış sonuçları güzel gösterir.

---

## Tasarım Felsefesi

**Hedef:** Bloomberg Terminal kalitesinde, bilgi yoğunluğu yüksek, profesyonel araştırma terminali.

- **Dark mode:** Koyu gri/siyah arka plan (`#1a1a2e`), beyaz metin, yeşil (kâr) / kırmızı (zarar)
- **Bilgi yoğunluğu:** Her piksel bilgi taşımalı — efekt değil, veri göstermeli
- **Hız:** Tıklamadan sonuç 1 saniyede gelmeli (DuckDB + Parquet avantajı)
- **Güven:** Her sayı, grafik ve sinyal audit trail'e bağlı olmalı

---

## Genel Yerleşim (Layout)

```
┌──────────┬──────────────────────────────┬──────────────┐
│          │                              │              │
│  SOL     │      ORTA                    │    SAĞ       │
│  MENÜ    │  Grafik / Backtest /         │  Strateji    │
│          │  Matrix Tarama               │  Parametre   │
│  Sembol  │                              │  Paneli      │
│  Arama   │                              │              │
│  Hızlı   │                              │  Risk        │
│  Erişim  │                              │  Limitleri   │
│          │                              │              │
├──────────┴──────────────────────────────┴──────────────┤
│  ALT: İşlem Tablosu / Loglar / Sinyal Tarayıcı        │
└────────────────────────────────────────────────────────┘
```

---

## Ekranlar (10 Adet)

### 1. Dashboard (Ana Gösterge Paneli)

Sisteme girişte karşılayan özet. "5 saniyede her şeyi gör."

- **Sistem durumu:** Toplam veri satırı, disk kullanımı, motor versiyon, son güncelleme
- **Veri sağlığı:** Kaç sembol güncel, kaçında uyarı var (sarı/kırmızı ikon)
- **Son backtest koşuları:** Tıklanabilir liste (tarih, strateji, Sharpe, MaxDD)
- **Aktif stratejiler:** Paper trading'deki stratejilerin bugünkü durumu
- **Hızlı listeler:**
  - "Bugün AL sinyali veren hisseler"
  - "Son 5 günde hacim patlayan hisseler"
  - "Backtest'te en iyi 10 hisse"

### 2. Matrix Tarama Paneli ⭐ (Killer Feature)

"Hangi hissede ne oluyor?" sorusunu 5 saniyede cevapla.

**Yapı:** Satırlar = semboller, Sütunlar = metrikler.

| Sembol | Günlük Trend | 1H Trend | RSI | Hacim Artışı | Son Sinyal | BT Net Getiri | Max DD | Sharpe | Bugün | Veri? |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| THYAO | 🟢 ↑ | 🟢 ↑ | 45 | +%30 | AL | +%120 | -%8 | 1.8 | AL | ✅ |
| GARAN | 🔴 ↓ | ⚪ → | 72 | -%5 | SAT | +%45 | -%15 | 0.9 | NÖTR | ✅ |
| AKBNK | ⚪ → | 🔴 ↓ | 28 | +%10 | AL | +%80 | -%12 | 1.2 | AL | ⚠️ |

**Hücre renkleri:**
- 🟢 Yeşil: pozitif / al sinyali
- 🔴 Kırmızı: negatif / sat sinyali
- ⚪ Gri: nötr
- 🟡 Sarı: veri uyarısı (eksik gün, outlier vb.)

**Etkileşim:**
- Satıra tıkla → o sembolün grafik ekranı açılır
- Sütun başlığına tıkla → sıralama değişir
- Filtre: "Sadece AL sinyali verenleri göster"

**Dikkat noktası:** Bu ekrandaki her değer (trend, RSI, sinyal, backtest sonucu) motorun hesaplamasından gelmeli. UI kendi başına hesaplama YAPMAMALI.

### 3. Canlı Grafik Ekranı

> **Not:** "Canlı" = gerçek zamanlı streaming değil. Offline-first sistemde bu "en güncel veriyle çizilen interaktif grafik" demek. Gerçek canlı akış Faz 5+ (Broker API).

**Grafik bileşenleri:**
- **Mum grafik (Candlestick):** 1dk, 5dk, 15dk, 1H, günlük, haftalık
- **Volume barları:** Grafiğin altında
- **İndikatör overlay:** SMA, EMA, Bollinger Band
- **İndikatör alt panel:** RSI, MACD, ATR
- **İşlem işaretleri:** AL (🟢 yukarı ok) / SAT (🔴 aşağı ok) grafik üzerinde
- **Stop-loss / Take-profit çizgileri:** Yatay kesikli çizgiler
- **Mouse hover:** Bar üzerine gelince OHLCV + indikatör değerleri tooltip
- **Zaman dilimi hızlı değiştirici:** Üst toolbar'da 1D | 1H | 15M | 5M butonları

**Çoklu grafik:**
- 2x2 grid ile aynı anda 4 sembol
- Veya 1 sembol + ayrı panelde sermaye eğrisi

**Teknoloji:** `lightweight-charts` (TradingView açık kaynak kütüphanesi) — Streamlit'te sınırlı, React versiyonunda tam destek.

**Streamlit MVP'de:** Plotly candlestick (daha yavaş ama çalışır). Matrix terminal versiyonunda lightweight-charts.

### 4. Strategy Builder (Strateji Kurucu)

Kod yazmadan strateji kurma paneli.

**Parametreler:**
- Strateji tipi: açılır menü (SMA Crossover, RSI Reversal, Bollinger Breakout, Momentum)
- Fast SMA: slider [5-100]
- Slow SMA: slider [10-300]
- RSI filtresi: slider [20-80]
- Stop-loss: slider [%1-%20]
- Take-profit: slider [%3-%50]
- Max pozisyon: slider [%5-%50]
- Komisyon: input [binde X]
- Slippage: input [X bps]
- Tarih aralığı: date picker
- Universe: çoklu seçim (THYAO / BIST30 / Bankalar / Tüm liste)
- Warm-up bars: input [50-500]

**🚀 "BACKTEST ÇALIŞTIR" butonu**

**Dikkat noktaları:**
- Veri sorunu olan semboller için uyarı göster ("AKBNK verisinde 3 gün boşluk var, sonuç yanıltıcı olabilir")
- Backtest arka planda çalışmalı (job queue), UI donmamalı
- Progress bar + iptal butonu
- "Kod yazmadan strateji" = önceden yazılmış strateji şablonlarının parametrelerini değiştirmek. Tamamen serbest kural oluşturma çok karmaşık, MVP'de olmayacak.

### 5. Backtest Lab (Sonuç Laboratuvarı)

**Üst kartlar (tek bakışta özet):**

| Net Getiri | Yıllık Getiri | Max DD | Sharpe | Sortino | Win Rate |
|:---:|:---:|:---:|:---:|:---:|:---:|
| +%340 🟢 | +%42 | -%12 🔴 | 1.8 | 2.1 | %65 |

| Profit Factor | İşlem Sayısı | Ort. Süre | En İyi | En Kötü | Komisyon |
|:---:|:---:|:---:|:---:|:---:|:---:|
| 2.3 | 142 | 8 gün | +%18 | -%7 | -₺3,200 |

**Grafikler:**
- Sermaye eğrisi (equity curve) — benchmark (Buy & Hold) ile üst üste
- Drawdown grafiği — max drawdown noktası vurgulanmış
- Aylık getiri heatmap (satranç tahtası: yıllar × aylar)
- Yıllık getiri bar chart
- Trade dağılım grafiği (kâr/zarar histogram)
- Long vs short katkı grafiği
- Gross vs net performans ayrımı

**Assumptions panel (çok kritik):**
- Bu sonuç hangi varsayımlarla üretildi?
- Slippage modeli, fill policy, komisyon oranı, warm-up bars
- Execution semantics: "bar kapanışında sinyal, sonraki bar açılışında dolum"
- Veri katmanı: adjusted mı, raw mı?

**İşlem tablosu:**

| # | Giriş Tarihi | Çıkış Tarihi | Sembol | Yön | Giriş Fiyatı | Çıkış Fiyatı | Lot | Brüt Kâr | Komisyon | Net Kâr | Süre | Sinyal Sebebi |
|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|:--|
| 1 | 2023-03-15 | 2023-03-28 | THYAO | LONG | ₺85.40 | ₺92.10 | 100 | ₺670 | ₺17.7 | ₺652.3 | 13 gün | SMA(10) > SMA(50) |

- Filtrelenebilir, sıralanabilir
- "Excel'e Aktar" butonu
- Satıra tıklayınca Trade Inspector açılır

### 6. Trade Inspector (İşlem Denetçisi)

Bir işleme tıkladığında açılan detay ekranı. **Güven veren ekran.**

- **Neden açıldı?** Hangi indikatör koşulu sağlandı?
- **Ne zaman sinyal oluştu?** Hangi bar kapanışında?
- **Ne zaman execute edildi?** Hangi bar açılışında?
- **Ne kadar slippage uygulandı?** Gerçek dolum fiyatı vs beklenen fiyat
- **Komisyon ne kadar kesildi?**
- **Nasıl kapandı?** Stop mu çalıştı, sinyal mi kapattı, take-profit mi?
- **O anın grafiği:** İşlem açıldığı andaki fiyat + indikatör durumu (mini chart)
- **Audit trail:** `sinyal → emir → dolum → pozisyon → PnL` tam zincir

### 7. Run Compare (Koşu Karşılaştırma)

Birden fazla backtest koşusunu yan yana karşılaştır.

| Metrik | SMA 10/50 | SMA 20/100 | RSI 30/70 | Momentum |
|:---|:---:|:---:|:---:|:---:|
| Net Getiri | +%120 | +%85 | +%65 | +%140 |
| Max DD | -%8 | -%12 | -%18 | -%10 |
| Sharpe | 1.8 | 1.2 | 0.9 | 1.6 |
| İşlem | 142 | 87 | 210 | 95 |
| Komisyon | ₺3.2K | ₺1.8K | ₺4.5K | ₺2.1K |
| En Kötü Ay | -%4.2 | -%6.1 | -%9.3 | -%5.0 |

- Equity curve overlay: seçilen koşuların eğrilerini üst üste çiz
- Parametre diff: iki koşu arasında ne değişti?
- Config snapshot: her koşunun tam ayarları

### 8. Optimization (Parametre Optimizasyonu)

- **Parametre aralığı:** Fast SMA [5-50], Slow SMA [20-200], Stop [%2-%10], TP [%5-%30]
- **Heatmap:** X: fast, Y: slow, renk: Sharpe (veya net kâr)
- **Walk-forward fold sonuçları:** Her fold'un in-sample / out-of-sample performansı
- **Stability grafiği:** Parametreyi az değiştirince sonuç ne kadar bozuluyor?
- **Cost sensitivity:** 2bps / 5bps / 10bps'de performans değişimi
- **Overfit uyarısı:** "Bu strateji sağlam mı, tek bir parametreye mi bağlı?"
- **En iyi parametreler:** Sadece en yüksek Sharpe değil; stability + cost robustness birlikte

### 9. Data Station (Veri İstasyonu)

Backtest öncesi "veri güvenilir mi?" kapısı.

Her sembol için:
- İlk tarih / son tarih / satır sayısı
- Eksik gün var mı? (harita ile göster)
- Outlier var mı? (%20+ günlük değişim)
- Split/temettü şüphesi var mı?
- Veri katmanı: raw / clean / adjusted?
- Son güncelleme zamanı

**Kritik özellik:** Backtest öncesi sistem demeli ki:
- ✅ "Bu veri güvenilir, backtest yapabilirsin."
- ⚠️ "Bu sembolde veri sorunu var, sonuç yanıltıcı olabilir."
- ❌ "Bu veri bozuk, backtest yapma."

"Yeni Hisse Ekle" ve "Tüm Verileri Güncelle" butonları.

### 10. Sinyal Tarayıcı & Akıllı Listeler

Dashboard'un bir parçası veya ayrı ekran.

- **"Bugün AL sinyali verenler"** — aktif stratejiye göre filtrelenmiş
- **"Son 5 günde hacim patlayanlar"** — ortalama hacmin X katı üstünde
- **"Backtest'te en iyi 10 hisse"** — en yüksek Sharpe sıralaması
- **"En düşük drawdown'lu stratejiler"** — güvenilirlik sıralaması
- **Alarm sistemi:** Belirli koşul sağlandığında bildirim (Telegram veya UI)

---

## Ek Özellikler (Matrix Terminal Hissi)

- **Çoklu grafik penceresi:** 2x2 grid ile 4 sembol aynı anda
- **Watchlist:** Favori semboller hızlı erişim
- **Favori stratejiler:** Sık kullanılan parametreleri kaydet
- **Sembol arama:** Üst toolbar'da arama kutusu
- **Zaman dilimi değiştirici:** Tek tıkla 1D / 1H / 15M / 5M
- **Keyboard shortcuts:** Enter: backtest çalıştır, Esc: iptal, ↑↓: sembol gezin

---

## Teknoloji Yol Haritası

### Faz A: Streamlit MVP (Motor hazır olduktan sonra)
- **Avantaj:** 2-3 günde çalışan prototip, saf Python
- **Sınırlar:**
  - Candlestick grafik = Plotly (yavaş, sınırlı interaktivite)
  - Çoklu pencere yok
  - Keyboard shortcuts yok
  - Matrix taraması çalışır ama yavaş
  - Job queue kısıtlı (backtest UI'ı bloklar)
- **Kapsam:** Dashboard, Strategy Builder, Backtest Lab, Data Station, basit Matrix tablosu, Trade Inspector

### Faz B: FastAPI + React + lightweight-charts (Nihai)
- **Avantaj:** TradingView kalitesinde grafikler, gerçek terminal deneyimi
- **Gereklilik:** Motor ve API stabil olduktan sonra
- **Kapsam:** Tüm 10 ekran, çoklu pencere, keyboard shortcuts, WebSocket canlı güncelleme, background job queue (Celery/RQ)

---

## Uygulama Sırası (Değişmez Kural: Motor Önce)

```
1. Bug düzeltme + test altyapısı          ← ŞİMDİ
2. Veri omurgası (raw/clean/adjusted)
3. BIST Trading Calendar
4. Execution Spec
5. Minimal backtest motoru + invariant test
6. Run registry + HTML rapor
7. Optimizasyon + governance
8. ─── MOTOR BİTTİ, UI BAŞLAR ───
9. Streamlit MVP (Faz A)
10. Matrix tarama paneli
11. Grafik + işlem gösterimi
12. Trade Inspector
13. Optimizasyon ekranı
14. ─── STREAMLIT SINIRA GELDİ ───
15. FastAPI + React terminal (Faz B)
```

---

## İlk Çalışan Versiyonda (Streamlit MVP) Olması Gerekenler

- [x] Sembol seçimi
- [ ] Mum grafik (Plotly candlestick)
- [ ] SMA / RSI göstergesi grafik üzerinde
- [ ] Strateji seçimi + parametre ayarı
- [ ] Backtest çalıştırma butonu
- [ ] Equity curve + drawdown
- [ ] Trade tablosu
- [ ] Grafik üzerinde al/sat noktaları
- [ ] Matrix ekranında sembol bazlı son sinyal ve performans
- [ ] Data Station — veri sağlık kontrolü
