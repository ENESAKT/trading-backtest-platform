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

- [ ] `quant_engine/strategy/catalog.py`: strateji taksonomisi — `momentum`, `trend_following`, `mean_reversion`, `breakout`, `moving_average`, `hybrid`, `ml`
- [ ] Her strateji için metadata: beklenen piyasa koşulu, önerilen timeframe, min bar sayısı, önerilen stop/TP, repaint riski, likidite ihtiyacı
- [ ] Hazır presetler: Momentum-MO cross, RSI-HO cross, RSI çift HO, RSI-MOST, SMA/EMA cross, fiyat-HO cross, T3 renk değişimi, Kairi mean reversion, BB SS3 dönüş
- [ ] Presetler `StrategySpec` DSL'e çevrilir; Python tek doğruluk kaynağı
- [ ] Frontend Strateji Lab'da "Eğitim presetleri" segmenti; kullanıcı preset seçip parametreleri değiştirir
- [ ] **Kabul:** En az 10 preset backtest edilebilir ve grafikte marker üretir

---

## Sprint B2 — İndikatör Merkezi v2 + HO Kütüphanesi

- [ ] `quant_engine/strategy/indicators.py` genişletme:
  WMA, TMA, DEMA, TEMA, ZLEMA, TSF, WWMA, VIDYA, T3, KAMA, FRAMA, HMA, ALMA, MAMA/FAMA, MavilimW, GANN HiLo, RMTA, JMA araştırma listesi
- [ ] Her yeni indikatör için TS karşılığı veya backend hesaplanmış seri endpoint seçilir; parite testi yazılır
- [ ] Kairi, MOST, BB Width, Guppy Multiple Moving Average ve oscillator smoothing blokları
- [ ] İndikatör parametreleri: period, kaynak data, MA türü, renk, overlay/alt panel, bar kapanışı bekle
- [ ] Repaint riski yüksek indikatörler için metadata ve UI uyarısı
- [ ] **Kabul:** EMA/SMA dışı en az 8 HO türü grafikte çizilebilir, DSL'de kullanılabilir, backtestte çalışır

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

- [ ] `quant_engine/research/walk_forward.py` modülü
- [ ] Kullanıcı: optimizasyon penceresi + WFA penceresi seçer (örn. 5 ay in-sample, 1 ay out-of-sample)
- [ ] Her pencerede en iyi parametre seçilir, sonraki out-of-sample bölümde uygulanır
- [ ] Rapor alanları: WFA toplam getiri, klasik optimizasyon getirisi, WFE, pencere bazlı başarı oranı, drawdown, işlem sayısı
- [ ] WFA tablo ve grafik UI: optimizasyon pencereleri, out-of-sample performans şeritleri
- [ ] **Kabul:** Klasik optimize'de iyi görünen strateji WFA'da başarısızsa UI açıkça gösterir
- [ ] **Test:** Unit: WFA pencereleri sızıntısız ayrılır; out-of-sample veri optimizasyonda kullanılmaz

---

## Sprint B7 — Monte Carlo Risk Simülasyonu

- [ ] `quant_engine/research/monte_carlo.py` modülü
- [ ] İşlem PnL serisi üzerinden bootstrap/permutation simülasyonu
- [ ] Rapor: median final equity, %5/%95 senaryo, olası max drawdown, zarar etme olasılığı, yıllık getiri/DD dağılımı
- [ ] Kullanıcı: başlangıç sermayesi, risk yüzdesi, tekrar sayısı
- [ ] Monte Carlo sonucu paper robot öncesi son eleme kapısı
- [ ] **Kabul:** Backtestte karlı görünen stratejinin risk dağılımı ve kötü senaryo sermaye eğrisi görülebilir
- [ ] **Test:** Unit: sabit seed ile deterministik rapor üretir

---

## Sprint B8 — Parametre Deneyleri v2 + Anti-Overfit Optimizasyon

- [ ] Grid search v1 korunur; sonuçlara stabilite skoru eklenir
- [ ] Parametre heatmap: iki parametre için getiri/drawdown/profit factor yüzeyi
- [ ] En iyi tek nokta yerine "sağlam bölge": komşu parametreler de iyi mi?
- [ ] Parametre deneyleri WFA ve Monte Carlo ile zincirlenebilir
- [ ] Aşırı az işlem veya çok yüksek drawdown cezalandırılır
- [ ] **Kabul:** "En yüksek getiri" ile "en dengeli strateji" ayrımı raporda ayrı gösterilir

---

## Sprint B9 — Piyasa Tarayıcı v3

- [ ] StrategySpec tüm sembol evreninde taranabilir: BIST 100, kripto, ABD, FX/emtia, özel liste
- [ ] Tarama koşulları: son sinyal, yeni kesişim, fiyat-HO uzaklığı, Kairi eşikleri, BB band teması, RSI bölgesi, hacim filtresi, trend filtresi
- [ ] Sonuç tablosu: sembol, son fiyat, sinyal tipi, sinyal zamanı, strateji kalite skoru, veri durumu, likidite uyarısı
- [ ] Sonuçtan tek tıkla: grafik, backtest raporu, paper izleme listesi
- [ ] Toplu gerçek emir yok; sadece analiz + alarm + paper aday listesi
- [ ] **Kabul:** "EMA50 EMA200 yukarı kesen ve hacmi ortalamanın üstünde olan BIST hisseleri" taranabilir

---

## Sprint B10 — Portföy ve Strateji Çeşitlendirme Lab

- [ ] Birden fazla strateji ve sembolün birleşik equity curve'ü
- [ ] Korelasyon matrisi ve strateji korelasyonu
- [ ] Strateji başına risk bütçesi ve maksimum sermaye payı
- [ ] Portfolio-level: max drawdown, profit factor, Sharpe, aylık getiri dağılımı, en kötü dönem
- [ ] Aynı anda çalışan paper robotların toplam risk/korelasyon uyarısı
- [ ] **Kabul:** "3 strateji + 10 sembol" portföyünün geçmişte nasıl davrandığı görülebilir

---

## Sprint B11 — Paper Robot Operasyon Paneli

- [ ] Paper robot listesi: strateji, sembol, timeframe, son sinyal, son emir, PnL, sağlık
- [ ] Kill switch: tüm robotları durdur / seçili stratejiyi durdur / günlük risk limitini düşür
- [ ] Robot başlamadan kontrol listesi: gerçek veri, yeterli bar, WFA/Monte Carlo sonucu, slippage, likidite
- [ ] Alarm ve paper aksiyonu ayrılır: alarm üretmek paper trade açmak değil
- [ ] Gap/vade geçişi için "işlem yapma" filtresi
- [ ] **Kabul:** Paper robot neden işlem yaptığı/yapmadığı audit log'dan okunur

---

## Sprint B12 — Strategy Pack Import/Export

- [ ] PiyasaPilot strateji paketi formatı: `.piyasapilot-strategy.json`
- [ ] Paket içeriği: StrategySpec, parametreler, indikatör seti, açıklama, versiyon, risk ayarları, örnek backtest metadata
- [ ] "Borfin esinli eğitim preset paketi": telifsiz, PiyasaPilot-native
- [ ] TradingView/Pine için referans notu ve manuel eşleştirme alanı (birebir çeviri yok)
- [ ] Matriks formülleri doğrudan import edilmez; kullanıcı PiyasaPilot DSL ile yeniden kurar
- [ ] **Kabul:** Strateji export → başka workspace → aynı backtest varsayımlarıyla çalışır

---

## Sprint B13 — UI Bilgi Mimarisi ve Strateji Lifecycle

- [ ] Strateji Lab sekmeleri: `Fikir`, `Kurallar`, `Test`, `Optimizasyon`, `WFA`, `Monte Carlo`, `Paper`, `Postmortem`
- [ ] Her strateji raporunda kısa teknik açıklama; uzun eğitim metni yığılmaz
- [ ] Risk uyarıları kart formatında: veri, overfit, likidite, slippage, short simülasyon, repaint
- [ ] Strateji lifecycle durumları: taslak → ön test → optimize → WFA geçti → Monte Carlo geçti → paper izleniyor → emekliye ayrıldı
- [ ] **Kabul:** Strateji hangi aşamada, sıradaki mantıklı adım tek bakışta görünür

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
