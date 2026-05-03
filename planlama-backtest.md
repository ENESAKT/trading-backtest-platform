# Backtest Lab — Plan (Sprint B1–B13)

> Kaynak: BORFİN eğitim arşivi — Kıvanç Özbilgiç Algo Trade + Hareketli Ortalamalar,
> Fuat Akman Sistem Trading, Yaşar Erdinç Teknik Analiz + İleri Düzey.
> Kural: Formüller, ekranlar, marka dili birebir kopyalanmaz. PiyasaPilot'a özgü DSL ve iş akışı.
> Tarih: 2026-05-01
> Durum: Bu plan sıfırdan başlangıç değildir; mevcut StrategySpec/backtest altyapısı üzerine kalan işleri listeler.

---

## Ürün Hedefi

PiyasaPilot, sadece indikatör gösteren terminal değil; **strateji fikri → kural → test → optimizasyon → dayanıklılık → paper robot → postmortem** zincirini tek ekranda yöneten algoritmik trade laboratuvarı.

---

## Ana Tasarım İlkeleri

- **Lookahead-free:** Sinyal `bar[t]` kapanışında, emir `bar[t+1]` açılışında
- **No fake data:** `is_real=true` ve güvenli status olmadan canlı/paper sinyal yok
- **Backtest gerçeğe yakınlık:** Komisyon, slippage, spread, hacim kapasitesi, veri eksikliği raporda
- **Overfit'e karşı şüphe:** En yüksek getiri otomatik seçim değil; düşük drawdown + stabil parametre ödüllü
- **Vade uyumu:** Strateji periyodu, timeframe ve beklenen trade süresi uyumsuzsa UI uyarır
- **Eğitim ama disiplinli:** Gerçek emir yolu yok; paper robot + alarm/sinyal ile sınırlı

---

## Mevcut Kod Durumu

| Alan | Durum | Sonraki anlamı |
|---|---|---|
| StrategySpec DSL | Var | B1/B3 sıfırdan değil, preset katalog ve görsel kurucu derinleşmesi |
| Long/short intent motoru | Var | B4'te gerçekçilik, uyarı ve varsayım kartı güçlenecek |
| CSV import ve OHLCV doğrulama | Var | B5 kalite skoru ve veri kapsama uyarılarına bağlanacak |
| Backtest report archive | Var | B13 lifecycle ve postmortem UI'a bağlanacak |
| Grid optimize ve screener v2 | Var | B8/B9'da stabil bölge, heatmap ve StrategySpec taraması büyütülecek |
| Paper aktivasyon bağlantısı | Var | B11'de operasyon paneli, kill switch ve audit görünümü eklenecek |
| WFA iskeleti | Kısmi | Ayrı modül, sızıntısız pencere testleri ve UI raporu gerekiyor |
| Monte Carlo | Yok | B7 hâlâ net yeni modül |

Bu yüzden aşağıdaki B sprintleri "mevcut yapılmış işleri tekrar et" değil, ürünleşme ve dayanıklılık katmanıdır.

---

## Sprint B1 — Strateji Kataloğu ve Eğitimden Gelen Presetler

- [x] `quant_engine/strategy/catalog.py`: strateji taksonomisi — `momentum`, `trend_following`, `mean_reversion`, `breakout`, `moving_average`, `hybrid`, `ml`
- [x] Her strateji için metadata: beklenen piyasa koşulu, önerilen timeframe, min bar sayısı, önerilen stop/TP, repaint riski, likidite ihtiyacı
- [x] Hazır presetler: Momentum-MO cross, RSI-HO cross, RSI çift HO, RSI-MOST, SMA/EMA cross, fiyat-HO cross, T3 renk değişimi, Kairi mean reversion, BB SS3 dönüş
- [x] Presetler `StrategySpec` DSL'e çevrilir; Python tek doğruluk kaynağı
- [x] Frontend Strateji Lab'da "Eğitim presetleri" segmenti; kullanıcı preset seçip parametreleri değiştirir
- [x] **Kabul:** En az 10 preset backtest edilebilir ve grafikte marker üretir

---

## Sprint B2 — İndikatör Merkezi v2 + HO Kütüphanesi

- [x] `quant_engine/strategy/indicators.py` genişletme:
  WMA, TMA, DEMA, TEMA eklendi. ZLEMA, TSF, WWMA, VIDYA, T3, KAMA, FRAMA, HMA, ALMA, MAMA/FAMA, MavilimW, GANN HiLo, RMTA, JMA araştırma listesi
- [x] Her yeni indikatör için TS karşılığı veya backend hesaplanmış seri endpoint seçilir; parite testi yazılır
- [x] Kairi, MOST, BB Width, Guppy Multiple Moving Average ve oscillator smoothing blokları
- [x] İndikatör parametreleri: period, kaynak data, MA türü, renk, overlay/alt panel, bar kapanışı bekle
- [x] Repaint riski yüksek indikatörler için metadata ve UI uyarısı
- [x] **Kabul:** EMA/SMA dışı en az 8 HO türü grafikte çizilebilir, DSL'de kullanılabilir, backtestte çalışır

---

## Sprint B3 — Görsel Kurucu Bloklar + DSL Genişletme

- [ ] Görsel kurucuya yeni bloklar: `CROSS_UP`, `CROSS_DOWN`, `ABOVE`, `BELOW`, `BARS_SINCE`, `DISTANCE_PCT`, `SLOPE`, `RISING`, `FALLING`, `VOLUME_ABOVE_AVG`
- [ ] Risk blokları: sabit stop, yüzde stop, ATR stop, trailing stop, take profit, time stop, bar sayısı kadar bekle
- [ ] Vade ve trend filtresi blokları: `C > SMA(C,200)`, `MA_ORDERED`, `TREND_FILTER`, `VOLATILITY_FILTER`
- [ ] Bir stratejiye birden fazla giriş/çıkış koşulu; AND/OR grupları adlandırılabilir
- [ ] Kural açıklaması otomatik üretilir: "RSI EMA'sını yukarı kesince ve fiyat EMA200 üstündeyse AL"
- [ ] **Kabul:** Kod bilmeden momentum, trend, mean reversion ve HO sıkışma stratejisi kurulabilir

---

## Sprint B4 — Backtest Gerçekçilik: Komisyon, Slipaj, Likidite

- [ ] Backtest raporunda "varsayım kartı" zorunlu: sermaye, komisyon, slippage bps, yön, pozisyon %, veri kaynağı, fill modeli
- [ ] Slippage modelleri: sabit bps, sabit kademe/tick, hacim oranına göre artan
- [ ] Likidite kapasite kontrolü: işlem tutarı son N bar ortalama hacminin belirli yüzdesini aşarsa uyarı
- [ ] Hacimsiz tahta riski BIST'te ayrıca raporlanır
- [ ] Short BIST için "simülasyon" etiketi; gerçek piyasa uygunluğu garanti edilmez
- [ ] **Kabul:** Aynı strateji komisyon açık/kapalı çalıştırılınca metrik farkı raporda net görünür

---

## Sprint B5 — Backtest Kalite Skoru ve Tuzak Uyarıları

- [ ] Backtest raporuna "kalite kontrol" bölümü: veri kapsama, işlem sayısı, test aralığı, piyasa rejimi çeşitliliği, parametre sayısı, outlier etkisi
- [ ] Tek sembol riski uyarısı: kullanıcı sadece kazandıran sembolde test yaptıysa
- [ ] Intrabar fill uyarısı: high/low bilgisiyle gerçek dışı fill
- [ ] Optimizasyon tuzağı: parametre sayısı arttıkça kalite skoru düşer
- [ ] Minimum örneklem uyarısı: indikatör period / test bar oranı çok yüksekse
- [ ] **Kabul:** Backtest sonucu `quality_score` ve kırmızı/sarı/yeşil uyarılarla döner

---

## Sprint B6 — Walk Forward Analysis (WFA) Motoru

- [x] `quant_engine/research/walk_forward.py` modülü
- [x] Kullanıcı: mevcut backtest parametreleri WFA pencerelerinde out-of-sample doğrulanır; ayrı grid optimizasyonu sonraki genişletme notu olarak warning'e yazılır
- [x] Her pencerede in-sample skor ve sonraki out-of-sample getiri ayrı hesaplanır
- [x] Rapor alanları: WFA toplam OOS getiri, WFE, pencere bazlı sonuç, passed ve warnings
- [x] WFA UI: StrategyPanel performans görünümünde WFA özeti görünür
- [x] **Kabul:** WFA sonucu yoksa UI kırılmaz; varsa pencere sayısı, OOS getiri, WFE ve durum görünür
- [x] **Test:** Unit: WFA pencereleri sızıntısız ayrılır; out-of-sample veri optimizasyonda kullanılmaz. Integration: backtest response `walk_forward_report` döner

---

## Sprint B7 — Monte Carlo Risk Simülasyonu

- [x] `quant_engine/research/monte_carlo.py` modülü
- [x] İşlem PnL serisi üzerinden bootstrap simülasyonu
- [x] Rapor: median final equity, %5/%95 senaryo, max drawdown dağılımı ve zarar etme olasılığı
- [x] Kullanıcı: başlangıç sermayesi backtest sermayesinden alınır; büyük simülasyon array'i response'a konmaz
- [x] Monte Carlo sonucu StrategyPanel performans görünümünde paper öncesi risk özeti olarak görünür
- [x] **Kabul:** Backtestte karlı görünen stratejinin risk dağılımı ve kötü senaryosu raporda okunur
- [x] **Test:** Unit: sabit seed ile deterministik rapor üretir. Integration: backtest response `monte_carlo_report` döner ve `simulations` taşımaz

---

## Sprint B8 — Parametre Deneyleri v2 + Anti-Overfit Optimizasyon

- [x] Grid search v1 korunur; sonuçlara stabilite raporu eklenir
- [x] Parametre heatmap: iki parametre için skor yüzeyi backend response'a eklenir
- [x] En iyi tek nokta yerine "sağlam bölge": komşu parametrelerden stabil bölge hesaplanır
- [x] Parametre deneyleri WFA ve Monte Carlo raporlarıyla aynı backtest response ailesinde zincirlenebilir
- [x] Aşırı az işlem mevcut optimizer skor cezası ve warning akışıyla korunur
- [x] **Kabul:** Optimizer sonucu "Stabil Bölge" ve stabilite skoru ile StrategyPanel'de görünür

---

## Sprint B9 — Piyasa Tarayıcı v3

- [x] StrategySpec özel sembol listesi ve mevcut sembol gruplarında taranabilir
- [x] Tarama koşulları helper seviyesinde son sinyal, yeni kesişim, fiyat-HO uzaklığı, RSI bölgesi, hacim filtresi, trend ve likidite durumunu destekler
- [x] Sonuç tablosu: sembol, son fiyat, son sinyal, getiri, drawdown, işlem sayısı ve skor döner
- [x] Sonuçtan tek tıkla grafik/backtest akışı mevcut StrategyPanel üzerinden korunur
- [x] Toplu gerçek emir yok; sadece analiz response'u döner
- [x] **Kabul:** `/api/backtest/scan` response'u `scanner_version: "v3"` kontratıyla döner

---

## Sprint B10 — Portföy ve Strateji Çeşitlendirme Lab

- [x] Birden fazla strateji ve sembolün birleşik equity curve helper'ı testli
- [x] Korelasyon matrisi helper'ı testli
- [x] Strateji başına risk bütçesi ve maksimum sermaye payı helper'ı testli
- [x] Portfolio-level: max drawdown, profit factor, Sharpe-like, aylık getiri dağılımı ve en kötü dönem hesaplanır
- [x] Backtest response tek strateji Portfolio Lab özeti döndürür; çoklu strateji birleşimi helper katmanında hazırdır
- [x] **Kabul:** StrategyPanel performans görünümünde Portfolio Lab özeti görünür

---

## Sprint B11 — Paper Robot Operasyon Paneli

- [x] Paper robot summary/preflight helper'ları testli
- [x] Kill switch helper'ları gerçek emir göndermeden stop komutu üretir
- [x] Robot başlamadan kontrol listesi: gerçek veri, yeterli bar, WFA/Monte Carlo, slippage ve likidite
- [x] Alarm ve paper aksiyonu helper seviyesinde ayrılır; gerçek emir yolu yoktur
- [x] Gap/vade geçişi için "işlem yapma" filtresi testli
- [x] **Kabul:** Backtest raporunda paper operasyon/preflight özeti görünür; gerçek emir etkin değildir

---

## Sprint B12 — Strategy Pack Import/Export

- [x] PiyasaPilot strateji paketi formatı: `.piyasapilot-strategy.json`
- [x] Paket içeriği: StrategySpec, parametreler, indikatör seti, açıklama, versiyon, risk ayarları, örnek backtest metadata
- [x] Export/import helper'ları ve API kontratı eklendi
- [x] TradingView/Pine için birebir çeviri yapılmaz; paket PiyasaPilot DSL taşır
- [x] Matriks formülleri doğrudan import edilmez; tehlikeli/invalid strategy_spec güvenli reddedilir
- [x] **Kabul:** Strategy pack export/import round-trip testli; invalid package 400 döner

---

## Sprint B13 — UI Bilgi Mimarisi ve Strateji Lifecycle

- [x] Strateji Lab mevcut rapor sekmeleri üzerinden WFA, Monte Carlo, Paper ve Portfolio özetlerini gösterir
- [x] Her strateji raporunda kısa teknik açıklama korunur; uzun eğitim metni yığılmaz
- [x] Risk uyarıları kart formatında: veri, overfit, likidite, slippage, short simülasyon ve repaint helper'ı testli
- [x] Strateji lifecycle durumları helper seviyesinde testli ve backtest response'a `lifecycle_summary` olarak bağlandı
- [x] **Kabul:** StrategyPanel sistem görünümünde mevcut lifecycle aşaması ve sıradaki mantıklı adım görünür

---

## Uygulama Sırası (Sprint Bağımlılıkları)

```
B1 (Katalog + Preset)
  └── B2 (İndikatör kütüphanesi)
        └── B3 (DSL blokları)

B1
  └── B4 (Backtest gerçekçilik)
        └── B5 (Kalite skoru)
              ├── B6 (WFA)
              │     └── B8 (Optimizasyon v2)
              └── B7 (Monte Carlo)
                    └── B10 (Portföy Lab)
                          └── B11 (Paper panel)
                                └── B12 (Pack export)
                                      └── B13 (UI lifecycle)

B3 → B9 (Tarayıcı v3)
```

---

## Test ve Kabul Kapıları (Tüm B Sprintleri)

- [ ] Unit: Yeni HO ve indikatör fonksiyonları sabit fixture'da beklenen çıktıyı verir
- [ ] Unit: DSL tehlikeli ifade kabul etmez; yeni bloklar StrategySpec'e doğru çevrilir
- [ ] Unit: Slippage, komisyon, hacim kontrolü, short PnL doğru hesaplanır
- [ ] Unit: WFA pencereleri sızıntısız ayrılır
- [ ] Unit: Monte Carlo sabit seed ile deterministik
- [ ] Integration: Preset → backtest → kalite skoru → WFA → Monte Carlo zinciri çalışır
- [ ] E2E: Preset seç → parametre değiştir → backtest → WFA raporu → paper izleme
- [ ] E2E: Explorer taraması → sembol grafiğe açılır → marker'lar görünür
- [ ] E2E: Strategy pack export/import → aynı kurallar geri gelir
- [ ] Kabul: Finansal gerçekçilik varsayımları eksikken "paper çalıştır" aktif olmaz

---

## Kapsam Dışı

- Gerçek aracı kurum emir iletimi
- HFT veya milisaniye emir altyapısı
- Lisanssız verinin gerçek veri olarak etiketlenmesi
- Eğitim videolarındaki formüller, ekranlar, marka dili birebir
- Gelecek getiri garantisi
