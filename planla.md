# PLANLA.MD - Kabul Edilmiş Nihai Proje Sözleşmesi

Bu dosya projede bundan sonra uygulanacak ana sözleşmedir. `planlama.md` okundu; oradaki mevcut maddeler kabul edildi ve son eklenen gerçek veri, karar motoru, grafik JSON, çoklu piyasa workspace ve arayüz kuralları bu dosyada tek yerde toplandı.

## 1. Temel Kabul

| Kural | Kabul | Açıklama |
|---|---|---|
| Kullanıcıya açık akışta gerçek dışı veri olmayacak | [x] | Uygulama, CLI, matris, optimizasyon ve grafik ekranları yalnızca sağlayıcıdan gelen gerçek OHLCV ile çalışır; test fixture verisi UI/CLI'a taşınmaz |
| Veri yoksa sinyal yok | [x] | API/WebSocket/Yahoo/Matriks/BIST sağlayıcı veri vermezse ekranda bekleme/hata gösterilir |
| Sahte mum yok | [x] | Eksik veri tamamlamak için rastgele OHLC, kopyalanmış bar veya yapay fiyat üretilmez |
| Her sembol izole | [x] | SASA workspace ayarları USDTRY veya XAUUSD workspace ayarlarına karışmaz |
| Her işlem testli | [x] | Yeni motor, strateji, UI helper veya provider davranışı unit test ile korunur |
| Arayüz analiz odaklı | [x] | Güzel görünümden önce okunabilir grafik, net sinyal, hızlı tablo ve risk bilgisi gelir |

## 2. Gerçek Veri Politikası

| Alan | Kabul Edilen Davranış | Durum |
|---|---|---|
| Strateji Laboratuvarı | Yalnızca gerçek veriyle backtest çalıştırır; veri yoksa bekleme/hata gösterir | [x] |
| Karar Motoru | EMA 200 + Bollinger + RSI gerçek veriden hesaplanmadan AL/SAT üretmez | [x] |
| Grafik JSON Motoru | Gerçek dışı/statik veride strateji planı üretmez, aynı JSON şemasında `Veri Yetersiz` döndürür | [x] |
| Workspace Manager | Veri sağlayıcı başarısızsa grafik bekleme durumunda kalır | [x] |
| YFinance Provider | BIST, Forex ve Emtia sembollerini farklı ticker formatlarına çevirir | [x] |
| Gelecek sağlayıcılar | Matriks, BIST resmi veri, Foreks veya broker API aynı provider protokolüne bağlanmalıdır | [ ] |

## 3. Çoklu Piyasa Workspace Sözleşmesi

| Piyasa | Sembol Örneği | Veri Formatı | Hassasiyet | Durum |
|---|---|---|---:|---|
| BIST 30 / BIST geniş liste / özel BIST kodu | `EREGL`, `SASA`, `THYAO` | Yahoo: `.IS` suffix | 2 | [x] |
| Forex | `USDTRY`, `EURTRY`, `EURUSD` | Yahoo: `=X` formatı | 4-5 | [x] |
| Emtia | `XAUUSD`, `XAGUSD`, `BRENT`, `WTI` | Yahoo futures/commodity ticker | 2 | [x] |
| VİOP | `F_XU030`, kontratlar | Matriks/BIST/Foreks gerekir | sözleşmeye göre | [ ] |
| Kripto | `BTCUSDT` | Binance/ccxt gibi ayrı provider gerekir | 4-8 | [ ] |

### Workspace İzolasyonu

| Kural | Kabul |
|---|---|
| Her workspace `symbol + market + timeframe` birleşiminden ayrı `workspace_id` üretir | [x] |
| İndikatör seçimi `workspace:{id}:indicators` altında tutulur | [x] |
| Veri bağlantı durumu `workspace:{id}:connect` altında tutulur | [x] |
| Bir semboldeki strateji/indikatör ayarı başka sembole taşınmaz | [x] |
| Frontend her yeni sembolde ayrı chart instance başlatmalıdır | [ ] |

## 4. JSON Çıktı Sözleşmeleri

### Workspace JSON

Arayüz yeni sembol çalışma alanı açmak için bu yapıyı okur:

```json
{
  "calisma_alani_kurulumu": {
    "sembol_kodu": "EREGL",
    "tam_isim": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
    "piyasa_kategorisi": "BIST 100 / Hisse Senedi",
    "ondalik_hassasiyet": 2
  },
  "veri_baglanti_protokolu": {
    "talep_edilen_veri": "Gerçek Zamanlı OHLCV",
    "hata_yonetimi": "Veri akışı kesilirse grafiği dondur; sahte mum üretme."
  },
  "arayuz_bilesenleri": {
    "ana_grafik": "TradingView Lightweight Charts modülünü sembole özel başlat.",
    "sag_panel": "Bid/Ask, derinlik veya gün içi özet göster.",
    "strateji_durumu": "Aktif bot/strateji varsa sadece bu workspace içinde yükle."
  }
}
```

### Strateji Grafik JSON

Arayüz teknik analiz yerleşimini bu yapıyla çizer:

| Anahtar | Zorunlu | Açıklama |
|---|---|---|
| `planlama_ve_analiz` | [x] | İndikatörlerin birlikte nasıl çalıştığı |
| `strateji_bilgileri` | [x] | Strateji adı, açıklama, AL/SAT koşulları |
| `grafik_kurulum_haritasi` | [x] | Ana grafik overlay ve alt pencere katmanları |

## 5. Strateji ve Karar Motoru Kuralları

| Kural | Kabul | Durum |
|---|---|---|
| Tek indikatörle karar yok | [x] | [x] |
| Trend filtresi zorunlu | [x] EMA/SMA/Ichimoku gibi ana yön filtresi | [x] |
| Volatilite filtresi zorunlu | [x] Bollinger/ATR gibi fiyat bölgesi ölçümü | [x] |
| Momentum filtresi zorunlu | [x] RSI/MACD gibi momentum teyidi | [x] |
| AL/SAT mantığı açıklanmalı | [x] Kullanıcıya ve log sistemine açık metin döner | [x] |
| SL/TP mantığı açıklanmalı | [x] Fiyat seviyesi ve neden belirtilir | [x] |
| Düşük trade uyarısı korunmalı | [x] Overfitting riski gösterilir | [x] |

## 6. Grafik ve UI Kuralları

| Katman | İçerik | Durum |
|---|---|---|
| Ana grafik | Candlestick, SMA/EMA, Bollinger, Ichimoku, AL/SAT marker | [x] kısmi |
| Al/Sat marker | Büyük, okunur, AL/SAT yazılı, trade id ve PnL bağlantılı | [x] |
| Trade bağlantısı | Giriş-çıkış çizgisi, kâr yeşil zarar kırmızı | [x] |
| Hacim | Ayrı panel veya alt pencere histogram | [x] |
| RSI/MACD | Ayrı alt pencere | [x] JSON planlandı |
| Sermaye eğrisi | Ayrı çizgi panel | [x] |
| Drawdown | Kırmızı alan/çizgi panel | [x] |
| Sağ panel | Strateji kuralları ve seçili trade detayı | [x] |
| Matris tablo | Sıralanabilir lider tablo ve piyasa matrisi | [x] |
| TradingView-like workspace | Sembol bazlı ayrı çalışma ekranı | [x] ilk sürüm |
| Türkçe arayüz | Uygulama içi metinler Türkçe olmalı; Streamlit'in çevrilemeyen İngilizce toolbar/deploy parçaları gizlenmeli | [x] |

## 7. BIST / Strateji Lider Tablosu

| Kolon | Kabul | Durum |
|---|---|---|
| Sıra | [x] | [x] |
| Sembol / Şirket | [x] | [x] |
| Strateji | [x] | [x] |
| Net Getiri % | [x] | [x] |
| Al-Tut Fark % | [x] | [x] |
| Final Sermaye | [x] | [x] |
| Maks. Düşüş % | [x] | [x] |
| Sharpe / Sortino | [x] | [x] |
| Kazanma % / Trade | [x] | [x] |
| İşlem Hacmi | [x] | [x] |
| Komisyon / Kayma / Maliyet % | [x] | [x] |
| En iyi / en kötü trade | [x] | [x] |
| Skor | [x] | [x] |

## 8. Dosya Mimarisi Hedefi

`app.py` şu an çalışıyor ama büyüdü. Bir sonraki mimari temizlikte şu yapı kabul edildi:

```text
quant_engine/app/ui_streamlit/
├── app.py
├── state.py
├── theme.py
├── data_loader.py
├── components/
│   ├── metric_cards.py
│   ├── chart_terminal.py
│   ├── trade_detail_panel.py
│   ├── strategy_panel.py
│   └── matrix_table.py
├── services/
│   ├── backtest_service.py
│   ├── strategy_catalog.py
│   ├── strategy_matrix.py
│   └── trade_overlay.py
└── pages/
    ├── backtest_lab.py
    ├── workspace_manager.py
    ├── market_matrix.py
    ├── optimizer.py
    └── data_station.py
```

## 9. Kalan Öncelikler

| Öncelik | İş | Neden |
|---:|---|---|
| 1 | `app.py` bileşenlere ayrılacak | Genişledikçe bakım zorlaşmasın |
| 2 | Matris satırı ana grafiğe bağlanacak | Tablo-grafik birlikte çalışsın |
| 3 | Strategy registry UI'a bağlanacak | Yeni strateji eklemek kolaylaşsın |
| 4 | Gerçek veri cache/storage workspace'e bağlanacak | Her tıklamada API yükü oluşmasın |
| 5 | Matriks/BIST/Foreks provider adaptörleri tasarlanacak | VİOP ve profesyonel veri yolu açılsın |
| 6 | TradingView Lightweight Charts frontend prototipi değerlendirilecek | Plotly araştırma ekranı yanında terminal hissi güçlensin |

## 10. Test ve Kalite Kabulü

| Kontrol | Zorunlu |
|---|---|
| `ruff check .` | [x] |
| `pytest -q` | [x] |
| Browser smoke test | [x] önemli UI değişimlerinde |
| Gerçek veri dışı akış yok kontrolü | [x] |
| Gerçek veri yoksa bekleme/hata | [x] |
| Yeni provider mapping testi | [x] |
| JSON şema testleri | [x] |
| İngilizce framework chrome kontrolü | [x] Deploy/toolbar kullanıcıya görünmemeli |

## 11. Yapılmayacaklar

| Yasak | Sebep |
|---|---|
| Sahte canlı fiyat üretmek | Finansal karar ekranında yanıltıcı olur |
| Test/fixture sonucunu gerçekmiş gibi göstermek | Kullanıcı güvenini ve analiz doğruluğunu bozar |
| Gerçek emir göndermek | Bu aşama araştırma/backtest terminalidir |
| TradingView/Matriks birebir kopyalamak | Amaç kopya değil, kullanılabilir profesyonel araştırma terminali |
| Tek indikatörle AL/SAT üretmek | Sahte sinyal riski yüksek |
| Kullanıcıya İngilizce framework modalı göstermek | Türkçe terminal deneyimini bozar; çevrilemiyorsa gizlenir |

## 12. Nihai Kabul Cümlesi

Bu dosyadaki maddeler kabul edildi. Bundan sonraki geliştirmelerde yeni istekler bu sözleşmeyle çelişirse önce gerçek veri, izolasyon, test ve şeffaflık kuralları korunacak; sonra arayüz ve strateji özellikleri eklenecek.
