# PLANLAMA.MD - Grafik, Matris ve Strateji Laboratuvarı Planı

Bu dosya, mevcut Streamlit arayüzünü daha kullanışlı bir backtest terminaline çevirmek için hazırlanmış uygulama planıdır. Amaç birebir TradingView veya Matriks kopyası yapmak değil; onların iyi çalışma mantığını alıp BIST 30 backtest iş akışına daha net, okunur ve test edilebilir şekilde uyarlamak.

## Durum Özeti

| Alan | Şu Anki Durum | Ana Sorun | Hedef |
|---|---|---|---|
| Grafik | Mum, hacim, SMA, equity ve drawdown aynı figürde var | Al/sat noktaları var ama yeterince belirgin değil; trade detayı seçilemiyor | İşlem noktaları kalıcı etiketli, seçilebilir ve PnL bağlantılı olsun |
| Alım/Satım Noktaları | Yeşil/kırmızı üçgen marker var | Marker küçük, trade numarası yok, giriş-çıkış eşleşmesi yok | AL/SAT rozetleri, işlem numarası, PnL etiketi ve bağlantı çizgisi olsun |
| Kullanılabilirlik | Görsel iyi ama analiz akışı dağınık | Sidebar uzun, grafik aksiyonları az, tablo-grafik bağlantısı yok | Matris + grafik + trade detay paneli birlikte çalışsın |
| Stratejiler | SMA Kesişimi, RSI Dönüşü, Bollinger Dönüşü, Al ve Tut var | UI içinde stratejilerin kuralı ve test sonucu net görünmüyor | Otomatik strateji kataloğu, açıklama, parametre ve test matrisi olsun |
| Matris | BIST 30 hızlı tarama tablosu var | Satır seçince grafik güncellenmiyor, strateji bazlı karşılaştırma yok | BIST x strateji performans matrisi ve seçilebilir satır olsun |
| Test | Çekirdek testler güçlü | Grafik overlay ve UI davranış testleri yok | Al/sat marker, strateji katalog ve matris hesap testleri eklensin |

## Araştırma Notları

| Konu | Sonuç | Uygulamadaki Karar |
|---|---|---|
| Plotly candlestick | Plotly candlestick finansal OHLC grafiği için doğru temel yapı; annotation, shape ve scatter marker ile zenginleştirilebilir. Kaynak: [Plotly Candlestick](https://plotly.com/python/candlestick-charts/) | Mevcut candlestick korunacak, üzerine işlem markerları ve entry-exit segmentleri eklenecek |
| Plotly range slider/selector | Plotly range slider ve range selector tarih aralığını hızlı daraltmak için uygun. Kaynak: [Plotly Range Slider](https://plotly.com/python/range-slider/) | 1A, 3A, 6A, YTD, 1Y, Tümü hızlı tarih butonları eklenecek |
| Streamlit Plotly seçimi | `st.plotly_chart` seçim olaylarını `on_select="rerun"` ile uygulamaya döndürebiliyor. Kaynak: [Streamlit st.plotly_chart](https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart) | Marker seçilince sağ panelde seçilen trade detayı gösterilecek |
| Streamlit dataframe seçimi | `st.dataframe` satır seçimlerini `on_select` ile yakalayabiliyor. Kaynak: [Streamlit Dataframe Selection](https://docs.streamlit.io/develop/tutorials/elements/dataframe-row-selections) | BIST 30 matrisinde satır seçimi grafiği ve strateji detayını güncelleyecek |

## Ana Hedef

Uygulama şu hale gelmeli:

```text
Sol panel:
  BIST 30 sembol listesi, strateji seçimi, veri kaynağı, zaman aralığı

Orta alan:
  Büyük fiyat grafiği, al/sat noktaları, pozisyon alanları, hacim, equity, drawdown

Sağ panel:
  Seçili trade detayı, strateji kuralları, aktif parametreler, maliyet/PnL özeti

Alt alan:
  BIST 30 matrisi, strateji karşılaştırma matrisi, işlem dökümü, test sonuçları
```

## Faz Matrisi

| Faz | İş | Yapılacaklar | Kabul Kriteri | Test | Durum |
|---|---|---|---|---|---|
| 1 | Al/Sat marker modeli | `fills` ve `trades` üzerinden tek bir `trade_overlay_df` üret | Her AL ve SAT noktası trade id ile eşleşir | Unit test: fill sayısı ve marker sayısı eşit | [x] app.py içinde ilk sürüm |
| 2 | Grafikte belirgin işlem noktaları | AL/SAT rozetleri, büyük marker, hover detayı, trade numarası | Grafikte AL/SAT çıplak gözle net görülür | Browser screenshot kontrolü | [x] |
| 3 | Giriş-çıkış bağlantısı | Her kapanmış trade için girişten çıkışa çizgi; kazanç yeşil, zarar kırmızı | Trade sonucu grafikte çizgiyle anlaşılır | Unit test: trade segment sayısı | [x] |
| 4 | Seçilebilir grafik | Plotly marker seçimiyle sağ panelde trade detayı | Kullanıcı marker seçince tarih, fiyat, adet, PnL görünür | Browser interaction kontrolü | [~] seçilebilir marker eklendi |
| 5 | Kullanışlı grafik kontrolleri | Tarih aralığı, log skala, indicator toggle, marker toggle, volume toggle | Grafik analiz için hızlı kullanılır | UI smoke test | [x] |
| 6 | Strateji kataloğu | Registry’den otomatik strateji listesi, açıklama ve parametre şeması | Yeni strateji eklenince UI otomatik görür | Unit test: katalog 3 strateji bulur | [ ] |
| 7 | Strateji test paneli | Her stratejiyi aynı sembol/veri üzerinde tek tuşla test et | SMA, RSI, Bollinger, Al-Tut yan yana sonuç verir | Integration test | [x] ilk sürüm |
| 8 | BIST 30 x strateji matrisi | Satırlarda sembol, sütunlarda strateji performans özeti | En iyi strateji/sembol kombinasyonu görülebilir | Matrix hesap testleri | [ ] |
| 9 | Matris satırı grafiğe bağlama | Matris satırı seçilince grafik aynı sembole geçer | Tablo ve grafik birlikte çalışır | Browser interaction kontrolü | [~] satır özeti eklendi, grafik bağlantısı sonraki faz |
| 10 | Dosya mimarisi düzeni | 1000+ satırlık `app.py` bileşenlere ayrılır | UI kodu okunur ve genişletilebilir olur | Ruff + pytest | [ ] |

## Grafik Arayüz Planı

### Şu an düzeltilmesi gerekenler

| Sorun | Etki | Çözüm |
|---|---|---|
| Markerlar küçük ve sadece hover ile anlamlı | Kullanıcı işlemi kaçırıyor | AL/SAT marker boyutu büyütülecek, marker üzerinde kısa etiket olacak |
| Giriş ve çıkış birbirine bağlı değil | Hangi satış hangi alışa ait anlaşılmıyor | Trade segment çizgisi eklenecek |
| Sinyal tarihi ve işlem tarihi ayrımı görünmüyor | Backtest mantığı yanlış anlaşılabilir | Hover içinde `sinyal tarihi` ve `işlem tarihi` ayrı gösterilecek |
| PnL grafikte yok | İşlemin iyi/kötü olduğu hemen anlaşılmıyor | SAT marker yanında `+%` veya `-%` etiketi olacak |
| Sağ detay paneli yok | Grafiğe bakınca tabloya inmek gerekiyor | Seçili trade detayı sağ panelde gösterilecek |
| Tarih aralığı hızlı değişmiyor | Grafik güzel ama ağır hissettiriyor | 1A/3A/6A/YTD/1Y/Tümü butonları eklenecek |
| Sidebar fazla uzun | Ana iş akışı yavaşlıyor | Sembol/strateji üst kontrol bandına, detaylar sekmelere taşınacak |

### Hedef grafik özellikleri

| Özellik | Davranış | Teknik Not |
|---|---|---|
| AL marker | Yeşil yukarı ok, üzerinde `AL #12` | `go.Scatter(mode="markers+text")` |
| SAT marker | Kırmızı aşağı ok, üzerinde `SAT #12` | Aynı trade id ile eşleşir |
| Kâr trade çizgisi | Girişten çıkışa yeşil çizgi | `fig.add_shape(type="line")` veya scatter segment |
| Zarar trade çizgisi | Girişten çıkışa kırmızı çizgi | PnL değerine göre renk |
| Açık pozisyon | Son bara kadar kesikli çizgi | `has_open_position` kontrolü |
| Sinyal/işlem ayrımı | Hover içinde iki tarih | `customdata` kullanılır |
| Trade seçimi | Marker seçilince sağ panel açılır | `st.plotly_chart(..., on_select="rerun")` |
| Göster/gizle | SMA, volume, equity, drawdown, trade çizgileri toggle | `st.toggle` veya segmented control |
| Hızlı tarih | 1A, 3A, 6A, YTD, 1Y, Tümü | `rangeselector` veya Streamlit segmented control |
| Log skala | Fiyat ekseni log/normal | `fig.update_yaxes(type="log")` |

## Yeni Grafik Veri Modeli

Grafiği temiz tutmak için UI içinde doğrudan `fills` dolaşmak yerine ayrı bir hazırlık fonksiyonu yazılmalı.

```python
def build_trade_overlay(result) -> TradeOverlay:
    return TradeOverlay(
        marker_df=...,
        segment_df=...,
        open_position_df=...,
        selected_trade_df=...,
    )
```

### `marker_df` kolonları

| Kolon | Açıklama |
|---|---|
| `trade_id` | Aynı alış/satış çiftini bağlayan id |
| `side` | `AL` veya `SAT` |
| `signal_date` | Sinyalin oluştuğu bar tarihi |
| `fill_date` | İşlemin gerçekleştiği bar tarihi |
| `price` | İşlem fiyatı |
| `quantity` | Adet |
| `commission` | Komisyon |
| `slippage` | Kayma maliyeti |
| `pnl` | Trade kapandıysa net PnL |
| `pnl_pct` | Trade kapandıysa yüzde PnL |
| `is_open` | Açık pozisyon mu |
| `label` | Grafikte görünecek kısa yazı |

### `segment_df` kolonları

| Kolon | Açıklama |
|---|---|
| `trade_id` | Trade id |
| `entry_date` | Giriş tarihi |
| `entry_price` | Giriş fiyatı |
| `exit_date` | Çıkış tarihi |
| `exit_price` | Çıkış fiyatı |
| `net_pnl` | Net PnL |
| `color` | Kâr yeşil, zarar kırmızı |

## Strateji Kataloğu Planı

Şu anda UI içinde strateji listesi manuel:

```python
STRATEGY_MAP = {
    "SMA Kesişimi": SmaCrossover,
    "RSI Dönüşü": RsiReversion,
    "Al ve Tut": BuyAndHold,
}
```

Bu çalışıyor ama büyüyünce sorun çıkarır. Hedef, stratejileri registry’den otomatik okumak.

| Strateji | İçerik | Varsayılan Parametre | Test Edilecek Ana Davranış |
|---|---|---|---|
| SMA Kesişimi | Hızlı SMA yavaş SMA’yı yukarı keserse AL, aşağı keserse SAT | `fast_period=10`, `slow_period=30` | Kesişim olmadan sinyal üretmemeli, warm-up öncesi işlem açmamalı |
| RSI Dönüşü | RSI aşırı satışta AL, aşırı alımda SAT | `rsi_period=14`, `oversold=30`, `overbought=70` | RSI eşikleri doğru çalışmalı, pozisyon yokken SAT üretmemeli |
| Bollinger Dönüşü | Kapanış alt banda sarkarsa AL, orta/üst banda dönerse SAT | `period=20`, `num_std=2.0`, `exit_band=middle` | Alt bant alımı, çıkış bandı satışı ve parametre doğrulaması çalışmalı |
| Al ve Tut | İlk barda AL, sonra bekle | Parametre yok | Sadece bir alış üretmeli, benchmark olarak kullanılmalı |

### Strateji detay paneli

Her strateji seçildiğinde sağ panelde şunlar görünmeli:

| Alan | Örnek |
|---|---|
| Strateji adı | SMA Kesişimi |
| Kod adı | `sma_crossover` |
| Açıklama | Çift hareketli ortalama kesişimi |
| Warm-up | 30 bar |
| Kullanılan indikatör | SMA |
| AL kuralı | Hızlı SMA, yavaş SMA’yı yukarı keser |
| SAT kuralı | Hızlı SMA, yavaş SMA’yı aşağı keser |
| Parametreler | Hızlı SMA, Yavaş SMA |
| Risk uyarısı | Az trade varsa istatistiksel güven düşük |

## Strateji Test Planı

| Test | Amaç | Dosya |
|---|---|---|
| `test_strategy_catalog_discovers_all_examples` | UI/registry tüm stratejileri buluyor mu | `tests/unit/test_strategy_catalog.py` |
| `test_sma_cross_marker_dates` | SMA sinyali ve işlem tarihi doğru ayrılıyor mu | `tests/unit/test_chart_overlays.py` |
| `test_rsi_threshold_signals` | RSI eşikleri doğru sinyal üretiyor mu | `tests/unit/test_strategy.py` |
| `test_buy_and_hold_single_entry` | Al ve Tut yalnızca bir AL üretiyor mu | `tests/unit/test_strategy.py` |
| `test_trade_overlay_pairs_entry_exit` | AL ve SAT aynı trade id ile bağlanıyor mu | `tests/unit/test_chart_overlays.py` |
| `test_open_position_overlay` | Açık pozisyon grafikte açık olarak gösteriliyor mu | `tests/unit/test_chart_overlays.py` |
| `test_matrix_runs_all_strategies` | Matris tüm stratejileri tüm sembollerde koşturuyor mu | `tests/integration/test_strategy_matrix.py` |
| `test_no_future_leakage` | Strateji gelecek bar verisini kullanmıyor mu | `tests/unit/test_financial_correctness.py` |

## BIST 30 Matris Planı

Mevcut matris sadece tek stratejiye yakın hızlı tarama veriyor. Hedef, hem piyasa taraması hem strateji karşılaştırması yapabilen bir terminal matrisidir.

### Strateji Lider Tablosu

Freqtrade raporlarında toplam kâr, trade sayısı, toplam işlem hacmi, ücretler ve drawdown aynı tabloda özetleniyor; QuantConnect raporları Sharpe, drawdown, toplam işlem ve ücret gibi KPI'ları öne çıkarıyor; Backtesting.py optimizasyonu seçilen metriği büyütmeye göre sonuç sıralıyor. Bizim lider tablomuz da bu mantıkla çalışmalı: sadece "en çok getiren" değil, maliyet ve riskle beraber okunabilir olmalı.

İncelenen referanslar:

| Kaynak | Alınan fikir |
|---|---|
| [Freqtrade Backtesting](https://www.freqtrade.io/en/stable/backtesting/) | Toplam kâr, trade sayısı, işlem hacmi, ücret ve drawdown'ın aynı raporda okunması |
| [Backtesting.py Optimization](https://kernc.github.io/backtesting.py/doc/examples/Parameter%20Heatmap%20%26%20Optimization.html) | Sonuçları seçilen metriğe göre optimize edip sıralama yaklaşımı |
| [QuantConnect Key Statistics](https://www.quantconnect.com/docs/v2/writing-algorithms/statistics/key-statistics) | Sharpe, drawdown, toplam işlem ve ücret gibi risk/performans istatistikleri |
| [VectorBT](https://vectorbt.dev/) | Çoklu sembol ve çoklu strateji testlerinde vektörize, ölçeklenebilir araştırma ekranı fikri |

| Kolon | Amaç | Durum |
|---|---|---|
| Sıra | Seçili metriğe göre büyükten küçüğe/lower-good sıralama | [x] |
| Sembol / Şirket | Hangi BIST 30 hissesi | [x] |
| Strateji | SMA, RSI, Bollinger, Al-Tut vb. | [x] |
| Net Getiri % | Ana sıralama metriği | [x] |
| Al Tut Fark % | Strateji benchmark'ı yeniyor mu | [x] |
| Final Sermaye | Başlangıç sermayesinin geldiği değer | [x] |
| Maks. Düşüş % | Risk ve sermaye erimesi | [x] |
| Sharpe / Sortino | Risk ayarlı performans | [x] |
| Kazanma % / Trade | İşlem kalitesi ve örnek büyüklüğü | [x] |
| İşlem Hacmi | Simüle edilen toplam alış/satış hacmi | [x] |
| Komisyon / Kayma / Maliyet % | Getiriyi yiyen maliyetler | [x] |
| En iyi / en kötü trade | Tekil işlem uçları | [x] |
| Skor | Getiri, risk, Sharpe ve maliyet karması | [x] |

### Strateji Analiz ve Karar Motoru

Bu katman backtest sonucu değil, son gerçek bar üzerinden loglanabilir karar çıktısı üretir. Gerçek dışı/test verisiyle AL/SAT üretmesi yasaktır; veri eksikse standart `VERİ YETERSİZ` formatı döndürür.

| Kural | Uygulama | Durum |
|---|---|---|
| Sadece gerçek veri | Gerçek veri işareti yoksa karar motoru reddeder | [x] |
| Trend filtresi | EMA 200 ile ana yön belirlenir | [x] |
| Volatilite filtresi | Bollinger alt/orta/üst bandı fiyat bölgesini belirler | [x] |
| Momentum filtresi | RSI 14 ve önceki RSI birlikte okunur | [x] |
| Tek indikatör yasağı | EMA + Bollinger + RSI birlikte onaylamadan AL/SAT üretmez | [x] |
| Şeffaf çıktı | `KARAR`, `STRATEJİ TÜRÜ`, mantık ve SL/TP metni standart formatta döner | [x] |
| UI entegrasyonu | Strateji Laboratuvarı içinde `Karar Motoru` sekmesi | [x] |
| Test | Gerçek dışı veri reddi, füzyon AL, RSI onaysız BEKLE, SAT ve eksik veri testleri | [x] |

### Grafik Kurulum JSON Motoru

Bu katman seçili indikatörleri frontend'in doğrudan parse edebileceği TradingView benzeri grafik kurulum haritasına çevirir. TradingView Lightweight Charts dokümantasyonundaki ana fiyat pane'i ve çoklu alt pane yaklaşımı baz alınır: mum grafik ve fiyat üstü overlay'ler ana grafikte; hacim, RSI, MACD, sermaye eğrisi ve drawdown alt pencerelerde tutulur.

İncelenen referanslar:

| Kaynak | Alınan fikir |
|---|---|
| [TradingView Lightweight Charts](https://www.tradingview.com/lightweight-charts/) | Candlestick, line, area ve histogram seri tiplerinin frontend tarafında ayrı çizilmesi |
| [Lightweight Charts Panes](https://tradingview.github.io/lightweight-charts/tutorials/how_to/panes) | Fiyat ve hacim/indikatörleri senkron zaman eksenli ayrı pencerelere bölme |
| [TradingView Panes and Scales](https://www.tradingview.com/charting-library-docs/latest/ui_elements/Panes-And-Scales-Behavior/) | Overlay çalışmaların fiyat pane'inde, osilatörlerin ayrı scale/pane içinde tutulması |
| [Stockopedia Ichimoku Clouds](https://www.stockopedia.com/ratios/ichimoku-clouds-9003/) | Ichimoku bulutunun destek/direnç ve trend rejimi haritası olarak kullanılması |

| Kural | Uygulama | Durum |
|---|---|---|
| Katı JSON | Üst anahtarlar `planlama_ve_analiz`, `strateji_bilgileri`, `grafik_kurulum_haritasi` | [x] |
| Gerçek veri koruması | Gerçek dışı/statik veri seçiliyse aynı şemada `Veri Yetersiz` döner | [x] |
| Ana grafik overlay | Mum, Ichimoku, SMA/EMA, Bollinger, AL/SAT marker katmanları | [x] |
| Alt pencereler | Hacim, RSI, MACD, sermaye eğrisi, drawdown ayrı pane olarak planlanır | [x] |
| İndikatör hesapları | Ichimoku, SMA/EMA, Bollinger, RSI, MACD son değerleri plan metnine girer | [x] |
| UI entegrasyonu | Strateji Laboratuvarı içinde `Grafik JSON` sekmesi | [x] |
| Test | Gerçek dışı veri reddi, eksik OHLCV, Ichimoku ve katman eşleşme testleri | [x] |

### Çoklu Piyasa Workspace Manager

Bu katman kullanıcının tıkladığı sembol için bağımsız analiz ekranı konfigürasyonu üretir. Amaç, BIST hissesi, forex paritesi ve emtia sembollerinin aynı terminal içinde ama ayrı state anahtarlarıyla çalışmasıdır.

| Kural | Uygulama | Durum |
|---|---|---|
| Sıfır gerçek dışı veri toleransı | Veri sağlayıcı başarısız olursa grafik bekleme/hata durumunda kalır, sahte OHLC üretilmez | [x] |
| Workspace izolasyonu | Her sembol+piyasa+zaman dilimi için `workspace_id` ve ayrı `session_state` anahtarı | [x] |
| BIST desteği | BIST 30, BIST 100 ve BIST Tüm modları `.IS` Yahoo formatına bağlanır | [x] |
| Forex desteği | USDTRY, EURTRY, EURUSD vb. semboller `.IS` almadan `=X` formatına gider | [x] |
| Emtia desteği | XAUUSD, XAGUSD, Brent, WTI gibi semboller gerçek Yahoo futures/commodity ticker'larına eşlenir | [x] |
| Ondalık hassasiyet | BIST 2 hane, TRY pariteleri 4 hane, majör forex 5 hane, emtia 2 hane | [x] |
| JSON protokolü | `calisma_alani_kurulumu`, `veri_baglanti_protokolu`, `arayuz_bilesenleri` üretir | [x] |
| UI entegrasyonu | Ana menüde `Çalışma Alanları` sayfası | [x] |
| Test | BIST/Forex/Emtia çözümleme, bilinmeyen sembol bekleme protokolü ve provider mapping testleri | [x] |

### Matris 1: Piyasa Matrisi

| Sembol | Son | Gün % | Trend | RSI | Sinyal | Skor | Durum |
|---|---:|---:|---|---:|---|---:|---|
| THYAO | 0.00 | +0.00 | Güçlü yukarı | 55 | Bekle | 20 | [ ] |

### Matris 2: Strateji Performans Matrisi

| Sembol | Al ve Tut Getiri | SMA Getiri | RSI Getiri | En İyi Strateji | Maks. Düşüş | Trade | Sharpe | Durum |
|---|---:|---:|---:|---|---:|---:|---:|---|
| THYAO | +0.0% | +0.0% | +0.0% | SMA | 0.0% | 0 | 0.00 | [ ] |

### Matris etkileşimi

| Kullanıcı Aksiyonu | Sistem Davranışı |
|---|---|
| Satır seçer | Grafik seçilen sembole geçer |
| Strateji sütununa tıklar | Grafik o strateji ile yeniden backtest eder |
| Sinyal filtresi seçer | Sadece AL/Bekle/Riskli satırları kalır |
| En iyi skor filtresi kullanır | Zayıf kombinasyonlar gizlenir |
| Trade sayısı filtresi kullanır | İstatistiksel olarak zayıf sonuçlar elenir |

## UI Yerleşim Planı

| Bölge | İçerik | Neden |
|---|---|---|
| Üst kontrol bandı | Sembol, strateji, veri kaynağı, tarih, çalıştır butonu | En sık kullanılan şeyler görünür olsun |
| Sol dar liste | BIST 30 watchlist ve skor rengi | Hızlı sembol geçişi |
| Orta büyük alan | Fiyat grafiği ve işlem overlay | Ana analiz alanı |
| Sağ detay paneli | Strateji kuralları, seçili trade, metrik özeti | Grafikten kopmadan karar desteği |
| Alt sekmeler | İşlem dökümü, maliyet, tüm metrikler, strateji matrisi | Derin analiz için |

## Dosya Yapısı Planı

`app.py` şu an büyüdü. Bir sonraki düzenlemede parçalanmalı.

```text
quant_engine/app/ui_streamlit/
├── app.py                         # sadece route ve ana iskelet
├── state.py                       # session state yardımcıları
├── theme.py                       # CSS ve tema
├── data_loader.py                 # gerçek veri yükleme
├── components/
│   ├── metric_cards.py            # metrik kartları
│   ├── chart_terminal.py          # ana grafik
│   ├── trade_detail_panel.py      # seçili trade paneli
│   ├── strategy_panel.py          # strateji açıklama/parametre paneli
│   └── matrix_table.py            # BIST 30 matrisi
├── services/
│   ├── backtest_service.py        # run_backtest wrapper
│   ├── strategy_catalog.py        # registry okuma
│   ├── strategy_matrix.py         # tüm strateji x sembol koşuları
│   └── trade_overlay.py           # marker/segment üretimi
└── pages/
    ├── backtest_lab.py
    ├── market_matrix.py
    ├── optimizer.py
    └── data_station.py
```

## Uygulama Sırası

### Aşama 1 - Grafik okunabilirliği

| Adım | İş | Durum |
|---|---|---|
| 1.1 | `trade_overlay.py` oluştur | [~] fonksiyon app.py içinde, dosyaya ayırma sonraki mimari faz |
| 1.2 | AL/SAT marker metinlerini büyüt | [x] |
| 1.3 | Giriş-çıkış çizgilerini ekle | [x] |
| 1.4 | Hover içeriğine sinyal tarihi, işlem tarihi, maliyet, PnL ekle | [x] |
| 1.5 | Açık pozisyonu grafikte ayrı göster | [x] |
| 1.6 | `test_chart_overlays.py` ekle | [ ] |

### Aşama 2 - Grafik kontrol paneli

| Adım | İş | Durum |
|---|---|---|
| 2.1 | SMA/Hacim/Equity/Drawdown/Trade çizgileri için toggle ekle | [x] |
| 2.2 | Log skala toggle ekle | [x] |
| 2.3 | Hızlı tarih aralığı butonları ekle | [x] |
| 2.4 | Plotly modebar ayarlarını sadeleştir | [x] |
| 2.5 | Marker seçimini sağ panelle bağla | [~] seçili trade paneli ilk sürüm |

### Aşama 3 - Strateji kataloğu ve test laboratuvarı

| Adım | İş | Durum |
|---|---|---|
| 3.1 | `strategy_catalog.py` oluştur | [ ] |
| 3.2 | Stratejileri static map yerine registry’den oku | [ ] |
| 3.3 | Her strateji için açıklama/parametre kartı göster | [x] |
| 3.4 | Tüm stratejileri aynı sembolde tek tuşla test et | [x] |
| 3.5 | Sonuçları Buy & Hold benchmark ile karşılaştır | [x] |
| 3.6 | Strateji katalog unit testlerini ekle | [ ] |

### Aşama 4 - Matris terminali

| Adım | İş | Durum |
|---|---|---|
| 4.1 | BIST 30 x strateji matrix servisi yaz | [ ] |
| 4.2 | Matris tablosuna row selection ekle | [~] seçili satır özeti eklendi |
| 4.3 | Seçili satır grafiği güncellesin | [ ] sonraki faz |
| 4.4 | En iyi strateji, riskli strateji, düşük trade uyarısı kolonları ekle | [ ] |
| 4.5 | Matris hesaplarını cache’le | [ ] |
| 4.6 | Matrix integration test ekle | [ ] |

### Aşama 5 - Mimari temizlik

| Adım | İş | Durum |
|---|---|---|
| 5.1 | `app.py` route dosyasına indir | [ ] |
| 5.2 | Chart, matrix, strategy, data loader bileşenlerini ayır | [ ] |
| 5.3 | UI fonksiyonlarına küçük unit test yazılabilir helperlar çıkar | [ ] |
| 5.4 | Ruff ve pytest tamamını çalıştır | [ ] |
| 5.5 | Tarayıcıda desktop ve dar ekran kontrolü yap | [ ] |

## Kabul Kriterleri

| Kriter | Ölçüm |
|---|---|
| Al/sat noktaları belli | Grafik screenshot’ında AL/SAT markerları zoom yapmadan görülecek |
| Trade bağlantısı anlaşılır | Her kapanmış trade giriş-çıkış çizgisiyle bağlanacak |
| Seçili trade detayı görünür | Marker veya trade satırı seçilince sağ panel detay gösterecek |
| Strateji içeriği anlaşılır | Kullanıcı SMA/RSI/Al-Tut ne yapıyor görebilecek |
| Tüm stratejiler test edilebilir | Tek tuşla seçili sembolde tüm stratejiler karşılaştırılacak |
| Matris kullanışlı | BIST 30 satırı seçilince grafik ve özet güncellenecek |
| Performans kabul edilebilir | Gerçek veri matrisi cache ile çalışacak, geniş taramada kullanıcı uyarılacak |
| Testler temiz | `ruff check .` ve `pytest -q` geçecek |

## Yapılmayacaklar

| Konu | Neden |
|---|---|
| Gerçek emir gönderme | Bu uygulama şu aşamada araştırma/backtest terminali |
| Birebir TradingView/Matriks klonu | Amaç kopya değil, backtest odaklı daha kullanışlı terminal |
| Test/fixture verisini gerçek sonuç gibi sunma | UI her zaman veri kaynağını açıkça gösterecek |
| Az trade sonucu yüksek güvenle göstermek | Overfitting ve düşük örnek uyarısı korunacak |

## Son Not

Öncelik sırası net: önce grafikte alım/satım noktalarını gerçekten okunur yap, sonra strateji kataloğunu otomatikleştir, sonra BIST 30 x strateji matrisini grafiğe bağla. Böyle yapılırsa arayüz sadece güzel görünmez; gerçekten analiz yapılabilir bir backtest terminaline dönüşür.
