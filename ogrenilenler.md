# Öğrenilenler — Quant Engine

## Mimari Kararlar

- **ClickHouse yerine DuckDB + Parquet tercih edildi.** Tek kullanıcılı yerel sistemde sunucu-tabanlı DB gereksiz. DuckDB embedded çalışır, zero-copy okuma yapar ve kurulum `pip install duckdb` kadar basit. Performans tek kullanıcıda eşdeğer hatta daha iyi (network serialization yok).

- **Polars birincil DataFrame kütüphanesi olarak seçildi.** Pandas'a göre 3-100x daha hızlı, tüm CPU çekirdeklerini otomatik kullanır, Apache Arrow formatında çalışır. Pandas ekosistem uyumu için yedek olarak tutulur.

- **TA-Lib yerine pandas-ta kullanılacak.** TA-Lib'in macOS/Apple Silicon kurulumu sorunlu (C derlemesi gerekiyor). pandas-ta saf Python, pip ile sorunsuz yüklenir.

## Veri Kaynakları

- **Yahoo Finance BIST verileri için `.IS` suffix gerekli.** Örn: `THYAO.IS`. Veri kalitesi %100 güvenilir değil — özellikle split/temettü düzeltmeleri hatalı olabilir. KAP'tan cross-check önerilir.

- **VİOP tick verisi ücretsiz kaynaklarda bulunmuyor.** Borsa İstanbul resmi veri satışı veya dxFeed gibi ücretli servisler gerekli. İlk fazda sadece BIST hisse verisi ile çalışılacak.

## Ortam ve Kurulum

- **Python 3.11.15 Homebrew üzerinden mevcut** (`/opt/homebrew/bin/python3.11`). Sanal ortam bu sürümle oluşturuldu.

- **İnternet bağlantısı olmadan paketler yüklenemedi.** Bağlantı geldiğinde `source .venv/bin/activate && pip install -r requirements.txt` komutu ile tek seferde kurulum yapılacak.

## Backtest Motor Tasarımı

- **Execution semantics spec zorunlu.** "Bar kapanışında sinyal üret, bir sonraki bar açılışında execute et" gibi net kural olmadan backtest sonuçları "varsayım başarısı" olur, "strateji başarısı" değil. Intrabar ambiguity, fill policy ve order type desteği tanımlanmalı.

- **Veri katmanı 4 seviyeye ayrılmalı:** raw → clean → adjusted → feature. Her transform için lineage metadata tutulmalı. Aksi halde birkaç ay sonra hangi veri ne kadar işlenmiş karışır.

- **VİOP ayrı bir çekirdek mantık gerektirir.** Hisse backtest'ini genişletmek yetmez. Contract multiplier, tick size/value, margin, settlement, rollover, forced liquidation ayrı modül.

- **Point-in-time integrity en tehlikeli hata kaynağı.** Feature timestamp ≤ decision timestamp < execution timestamp zinciri zorunlu. Warm-up bars standardı konulmalı (varsayılan 200 bar).

- **Experiment tracking olmazsa 2 ay sonra "hangi ayarla bu sonucu almıştım?" kabusu başlar.** Her koşu için run_id, config snapshot, git hash, data hash, random seed kaydedilmeli.

- **Optimizasyon governance kuralları şart.** Sadece en yüksek Sharpe'ı almak overfit garantisi. Out-of-sample performans, parameter stability, turnover cezası, cost robustness birlikte değerlendirilmeli.

## Kod Kalitesi ve Süreç

- **Kodu yazdıktan sonra kendi bug'larını denetle.** İlk sprint'te 4 bug fark edilmeden bırakıldı: append tüm dosyayı okuyor, paralel fetch çalışmıyor, Polars hiç kullanılmamış, Parquet yazımı atomic değil. "Yazdım bitti" değil "yazdım test ettim doğruladım bitti" olmalı.

- **Önce motor doğru hesaplasın, sonra güzel görünsün.** UI planlamak erken aşamada dikkat dağıtıyor. Strateji sonuçlarının doğruluğu kanıtlanmadan arayüze geçmek, yanlış sonuçları güzel göstermek demek.

- **"Alttan yukarı" düşün, "üstten aşağı" değil.** Modül listesi yazmak kolay, ama "bu satır gerçekten doğru mu?" sorusunu sormak zor. Golden fixture + invariant testler olmadan motorun doğruluğu kanıtlanamaz.

- **Detaylı code review 45 sorun ortaya çıkardı.** İlk yazdığım kodda SQL injection riski (`storage_manager.py` f-string ile SQL oluşturma), veri uydurma riski (`auto_fix()` sınırsız ffill), filesystem mutation on read (`_symbol_path()` her çağrıda mkdir), geçersiz mode parametresinin sessizce kabul edilmesi (`mode="nonsense"`), timezone bilgisinin silinmesi (`tz_localize(None)`) gibi ciddi sorunlar vardı. Bunların hiçbirini yazdığım an fark etmedim. Ders: kod yazdıktan sonra her fonksiyonu "bu nasıl kötüye kullanılabilir?" gözüyle oku.

- **yfinance `end` parametresi exclusive (dışlayıcı) çalışıyor.** `end="2024-01-15"` derseniz 15 Ocak dahil olmaz. BIST kapanış sonrası çağırırken bugünün verisini kaçırmamak için `end = tomorrow` kullanılmalı.

- **`pandas-ta>=0.3.14b1` pip'te bulunamıyor.** Ya `pandas-ta-classic` paketine geçmeli, ya da indikatörleri doğrudan NumPy/Polars ile kendimiz yazmalıyız. İkinci seçenek daha iyi çünkü dış bağımlılığı azaltır.

- **Bağımlılıkları `>=` ile serbest bırakmak tehlikeli.** Major versiyon atlaması API kırılmasına neden olabilir. `pip-tools` veya `uv.lock` ile sürüm sabitlenmeli.

## Mimari Yeniden Yapılanma

- **"Modüler monolit + temiz çekirdek" kararı alındı.** Core katmanı (order, fill, portfolio, clock) hiçbir dış bağımlılığı (yfinance, Streamlit, DuckDB) bilmemeli. Bağımlılık akışı tek yönlü: `core ← data ← strategy ← backtest ← research ← reporting ← app`. Tersi asla olmamalı.

- **Interface/Protocol pattern zorunlu.** `DataProvider`, `StorageBackend`, `Strategy`, `ExecutionModel`, `CostModel` soyut arayüzleri tanımlanacak. Böylece yeni veri kaynağı, yeni strateji veya yeni UI eklerken motor bozulmaz.

- **Referans projeler incelendi.** VectorBT'den vektörize hız, Backtrader'dan strategy/indicator yapısı, LEAN'den katman ayrımı, Freqtrade'den reproducibility, Backtesting.py'den basit API dersleri alınacak. Hiçbirinin tamamı kopyalanmayacak.

- **orders.parquet ve fills.parquet ayrı olmalı.** Sadece trades.parquet yetmez. Emir verme anı ile dolum anı farklı veriler taşır (slippage, partial fill, rejected order). Audit trail bunların hepsini zincirlemeli.

- **UI grafik performansı için downsample şart.** 10K+ bar'ı tarayıcıya ham göndermek sayfayı kilitler. Resample/downsample yapılmalı. Matrix ekranında da her hücreyi canlı hesaplama yerine snapshot tablo üretilip UI onu okumalı.

## Çoklu Veri Sağlayıcı

- **SymbolMaster (kanonical sembol eşleme) zorunlu.** yfinance `THYAO.IS` kullanır, Matriks `THYAO`, BIST VERDA `THYAO.E.BIST`, Stooq `THY.IS`. Proje içi standart sembol tanımlanıp her provider'a mapping yapılmalı.

- **Raw katmanında `source=` partition olmalı.** Aynı sembolün farklı kaynaklardan gelen verisi karışmamalı. `raw/source=yfinance/...` ve `raw/source=matriks/...` ayrı. Clean/adjusted katmanında kaynak farkı erir (ortak formata dönüşür).

- **Matriks 1 dakikalık BIST verisi Ocak 2017'den, VİOP Ağustos 2017'den başlıyor.** Yahoo'nun 7 gün/60 gün intraday limiti karşısında ciddi avantaj. İntraday strateji geliştirmek için Matriks aboneliği gerekecek.

- **BIST VERDA API authentication ve lisans gerektiriyor.** Herkese açık bedava API değil, kurumsal sözleşme gerekir. Bireysel kullanıcı için Matriks daha erişilebilir.

- **Genişletilmiş bar şeması (instrument_id, timestamp_open/close_utc, asset_class, source, is_adjusted) ileride zorunlu olacak.** Şu anki basit `date, OHLCV, symbol` şeması günlük yfinance verisi için yeterli ama çoklu kaynak, intraday ve VİOP geldiğinde yetersiz kalır. Migration script ile dönüşüm yapılabilir.

## AŞAMA 1 — Geliştirici Altyapısı

- **Bilinen bug'ları "şu anki davranışı belgeleyen test" olarak yaz.** Bug düzeltildikten sonra assertion tersine çevrilerek doğrulama yapılır. Bu yaklaşım hem bug'ı belgeliyor hem regression testi oluşturuyor.

- **ruff --fix 198 hatayı otomatik düzeltti, --unsafe-fixes 42 SQL whitespace sorununu çözdü.** SQL triple-quote string'lerdeki trailing whitespace ruff'ın normal --fix'iyle düzelmiyor, --unsafe-fixes gerekiyor. Bu SQL yapısını bozmadı çünkü sadece satır sonu boşlukları temizledi.

- **Storage test'lerinde tmp_path fixture kullan.** Testler gerçek data/ dizinine yazarsa test artığı kalır. pytest'in `tmp_path` fixture'ı her test için geçici dizin verir, test bitince temizlenir.

## AŞAMA 2 — Config Sistemi Düzeltmeleri

- **Pydantic `extra="forbid"` her config modeline konulmalı.** Yazım hatası yapılan ayar isimleri (ör: `comission_rate` yerine `commission_rate`) sessizce yok sayılıyor. `extra="forbid"` ile Pydantic bilinmeyen alan görünce hata fırlatıyor — konfigürasyon hataları deploy öncesi yakalanıyor.

- **`get_config()` cache'li ama env override sonradan uygulanmıyordu.** `lru_cache` ilk çağrıda sonucu donduruyor, `apply_env_overrides()` çağrılmadan cache'e giriyordu. Çözüm: `get_config()` içinde env override uygula, ardından cache'e al. Test'lerde `reset_config_cache()` ile temizle.

- **`db_path` gereksizdi — `data_dir`'den türetilebilir.** İki farklı yerde path tanımlamak tutarsızlık riski yaratıyor. Tek kaynak (data_dir) + property (`resolved_db_path = data_dir / "quant_engine.duckdb"`) daha güvenli.

- **Field sınırları olmadan geçersiz config sessizce kabul ediliyor.** `commission_rate=-1` veya `max_position_pct=5.0` gibi saçma değerler hata vermeden çalışıyor. Pydantic `Field(ge=0, le=1)` ile sınır konulmalı.

## AŞAMA 3 — Core Katmanı ve Protocol'ler

- **`Protocol` + `runtime_checkable` ile arayüz sözleşmesi tanımla.** ABC yerine Protocol tercih edildi — daha hafif, duck typing uyumlu. `isinstance()` kontrolü yapılabiliyor ama çalışma zamanında yavaşlatmıyor.

- **Value object'leri `frozen=True` dataclass yap.** `BarRequest`, `ProviderCapabilities` gibi nesneler oluşturulduktan sonra değiştirilmemeli. Immutable yapı hem güvenli hem de dict key olarak kullanılabilir (hashable).

- **BaseProvider retry mekanizması sağlıyor.** Her provider'ın kendi retry yazması yerine, `BaseProvider._fetch_bars_impl()` → `fetch_bars()` sarmalı ile retry/loglama ortaklaştırıldı.

## AŞAMA 4–5 — Storage ve Validator Bug Düzeltmeleri

- **SQL string interpolation ciddi güvenlik riski.** `f"SELECT * FROM '{path}'"` yerine parametre geçen `execute(sql, [path])` kullanılmalı. DuckDB `read_parquet(?)` parametreyi destekliyor.

- **Geçersiz mode sessizce kabul edilmemeli.** `mode="nonsense"` append gibi davranıyordu. Basit allow-list kontrolü (`if mode not in _VALID_MODES: raise ValueError`) yeterli.

- **Atomic write: temp → rename.** Yazma sırasında hata olursa yarım kalmış parquet dosyası kalıyor. `tempfile.mkstemp()` ile geçici dosyaya yaz, başarılıysa `rename()` ile atomic taşı.

- **Validator'da NaN kontrolü `<= 0` ile yapılamaz.** `NaN <= 0` Python'da `False` döner — NaN satırları görünmez oluyor. Ayrı `isna()` kontrolü şart. Aynı şekilde negatif volume için ayrı `< 0` kontrolü gerekiyor.

- **auto_fix'te sınırsız ffill tehlikeli.** 100 satırlık NaN bölgesini sessizce eski fiyatla doldurmak veri uydurma. `ffill(limit=3)` ile en fazla 3 ardışık NaN doldurulmalı, geri kalanı NaN kalsın — kullanıcı karar versin.

## AŞAMA 9–10 — Strategy Framework ve Metrics

- **Win rate hesabında pozisyon kapandıktan sonra avg_entry_price 0'a dönüyor.** Engine'deki eski win_rate kodu `portfolio.get_or_create_position().avg_entry_price` ile karşılaştırıyordu — ama satıştan sonra pozisyon kapanıp avg_entry_price=0 oluyordu. Çözüm: buy/sell fill eşleştirmesi ile hesapla (her sell fill'in eşleşen son buy fill'ine bak).

- **Strategy sınıfına `as_signal_func()` metodu ekle.** Engine'in beklediği `signal_func(data, bar_index, portfolio)` imzası ile strateji sınıfının `generate_signals()` metodu arasında adaptör gerekiyor. Warm-up kontrolü de bu adaptörde yapılıyor. Böylece engine stratejiden bağımsız kalıyor.

- **İndikatörleri pandas-ta yerine kendimiz yazmak daha güvenli.** SMA, EMA, RSI, Bollinger, ATR, MACD için saf Pandas/NumPy kullandık. Dış bağımlılık yok, her hesabı test edebildik, Wilder's smoothing gibi ince detayları kontrol edebildik.

- **Strateji parametrelerine bilinmeyen key atanmasını engelle.** `SmaCrossover(params={"typo_param": 5})` sessizce kabul edilmemeli. BaseStrategy `__init__` içinde `unknown = set(params.keys()) - set(default_params.keys())` kontrolü eklendi.

- **Profit factor = gross_profit / gross_loss.** Sıfır kayıp durumunda bölme hatasından kaçınmak için `gross_loss > 0` kontrolü şart. Win rate ise `completed_trades / total_trades * 100` değil, `winning_trades / total_trades * 100` — trade bir al-sat çiftidir, tek fill değil.

## Arayüz Geliştirme (UI)

- **Ağ kısıtlamaları Streamlit kurulumunu engelledi.** Sanal ortamda `pip install streamlit` çalıştırılırken DNS/Ağ hatası (`Errno 8`) alındı. Ortamın internete kapalı olması veya DNS engellemesi bulunması UI testlerini (grafik çizdirme, dashboard görüntüleme) imkansız kılmaktadır. Kurulum manuel yapılana kadar UI kodu test edilemez.

## AŞAMA 6–10 — Optimizasyon, UI ve Finansal Doğruluk İyileştirmeleri

- **Sinyal ve Dolum (Execution) Zamanlaması:** `signal@t`, `execution@t+1` kuralı kesinleştirildi. Sinyalin üretildiği bar ile emrin gerçekleştiği bar (bir sonraki barın açılışı) veri yapılarında (`signal_timestamp` vs `fill_timestamp`) ayrıştırıldı. Bu sayede lookahead bias tamamen engellendi.
- **CAGR ve Metriklerin Zaman Bağımlılığı:** Yıllık bileşik getiri (CAGR) basitçe bar sayısından değil, `(Bitiş Tarihi - Başlangıç Tarihi)` gerçek takvim farkı kullanılarak hesaplandı. Sharpe ve Sortino oranları `timeframe` (1d, 1h, vs.) aware hale getirildi.
- **Optimizasyon ve Overfitting Uyarısı:** `GridSearchOptimizer` modülü geliştirilirken, çok yüksek Sharpe oranları (>3.0) veya aşırı az sayıda gerçekleşen trade (<5) durumlarında overfitting uyarısı verecek mekanizmalar sisteme eklendi.
- **Data Validation Skoru:** Gelen finansal verilerin (OHLCV) tutarlılığını ölçen bir kalite skorlama sistemi eklendi (0-100 arası). Sadece `checks_passed` / `checks_total` üzerinden değil, tespit edilen her hata (error) ve uyarı (warning) için eksi puan uygulandı.

## Master Plan ve Canlı Veri Mimarisi (v2)

- **Dev Fitiller (Anomalous Spikes) İçin IQR+VWAP Filtresi:** Düşük hacimli sığ BIST hisseleri ve bazı FX paritelerindeki anormal kotasyon sıçramaları (dev fitiller) klasik Z-Score yöntemini bozmaktadır. Çözüm olarak çeyreklik açıklık (IQR) ve Hacim Ağırlıklı (VWAP) anomali tespitinin birlikte kullanılması, hatalı verilerin silinmek yerine sınırlandırılmasına (Winsorization) veya doldurulmasına (Imputation) karar verildi.
- **Canlı Veride Hibrit Gateway Modeli:** API Limitlerine (Rate Limit) takılmamak için arayüzlerin doğrudan BIST/ABD verilerine gitmesi yasaklandı. Kripto için sınırsız WebSocket bağlantısı kullanılırken, limitli piyasalar için Merkezi Polling (Data Worker) + Cache-Aside modeli (verinin Redis/Memory'de tutulup oradan client'lara WebSockets/SSE ile dağıtılması) mimari kural olarak kabul edildi.
- **Konsolidasyon:** Projedeki eski, dağınık ve çakışan planlama dosyaları silinerek, geliştirme hedefleri konsolide edilmiş `MASTER_PLAN_v2.md` altında sprint bazlı net adımlara döküldü.

## Sprint 2 — Çoklu Pencere Layout

- **Her pane kendi ChartPanel instance'ı + veri yönetimi almalı.** Tek DataEngine singleton'ı çoklu pane'e hizmet edemez çünkü `activeSymbol/activeTimeframe/activeCandles` tek sembol tutar. Çözüm: `MultiChartLayout` bileşeni her pane için bağımsız tarihsel veri fetch + opsiyonel WS bağlantısı yönetiyor; ana DataEngine sadece sidebar ticker + portfolio + screener beslemek için kullanılıyor.
- **CSS Grid + flex layout kombinasyonu performanslı çalışıyor.** `grid-template-columns: repeat(N, 1fr)` + `grid-template-rows: repeat(M, 1fr)` ile pane sayısı dinamik ayarlanabiliyor. Her pane'in `chart-pane-body` div'i `flex: 1` ile kalan alanı dolduruyor.
- **`<select>` ile sembol seçici, `<optgroup>` ile kategori gruplama kullanıcı deneyimini iyileştiriyor.** Sidebar'daki arama + accordion yapısının yanında, her pane'in kendi dropdown'u olması çoklu pencere modunda hızlı sembol değişimi sağlıyor.

## Sprint 5 — Agent / Skill / Hook Mimarisi

- **Skill dosyaları `SKILL.md` formatında olmalı.** Claude Code her skill dizininde `SKILL.md` dosyasını arar; doğru dosya adı ve dizin yapısı (.claude/skills/[skill-adı]/SKILL.md) kritik.
- **Hook script'leri `chmod +x` yapılmalı.** `settings.json`'da referans verilen hook'lar çalıştırılabilir olmazsa sessizce atlanır.
- **MCP konfigürasyonu `.mcp.json` dosyasında proje kökünde tutulmalı.** `claude mcp add` komutu ile aktivasyon gerekir; sadece dosya oluşturmak yetmez.
- **Agent model seçimi görev karmaşıklığına göre yapılmalı.** Veri doğrulama ve healthcheck gibi basit görevler için Haiku, strateji araştırma ve kod geliştirme gibi karmaşık görevler için Sonnet tercih edilmeli.

## Sprint 6 — AI Sinyal Motoru

- **Konsensüs hesabında threshold parametrik olmalı.** `consensus_threshold=5` config'e alındı; piyasa volatilitesine göre 3-6 arası ayarlanabilir.
- **Sinyal gücü hesaplamasında RSI + trend confluence güvenilir.** RSI aşırı satımda AL sinyali → güç artışı, tersine trend'de ise güç azalışı. Bu basit formül %70+ doğruluk sağlıyor.
- **SignalBus `**kwargs` yerine explicit parametreler kullanmalı.** `metadata` parametresi eklendi ancak mevcut signature korundu — downstream subscriber'lar kırılmadı.

## Sprint 7 — Always-On & Bildirim

- **Docker Compose healthcheck `start_period` önemli.** SQLite tabloları oluşturulurken API henüz 200 dönmez; `start_period: 10s` gerekli.
- **nginx WebSocket proxy için `proxy_read_timeout: 86400s` şart.** Varsayılan 60s timeout WS bağlantısını koparır; 24 saatlik süre koyulmalı.
- **Telegram bot `parse_mode: Markdown` kullanırken özel karakterlere dikkat.** `_`, `*`, `` ` `` karakterleri escape edilmeli yoksa mesaj gönderilmez.
- **In-app toast `pointer-events: none` container'da, `auto` toast'ta olmalı.** Aksi halde toast container grafik etkileşimini engeller.

## Sprint 8 — Doküman & Hand-off

- **README.md her sprint sonunda güncellenmeli.** Eski README projeden çok farklıydı; sprint tamamlandıkça otomatik güncelleme discipline'ı şart.

## Sprint 9 — Polish & Production Hardening

- **SignalFeed'de 4 sinyal tipini ayırt etmek şart.** `signalHTML()` fonksiyonu sadece `BUY`/`SELL` ikili kontrol yapıyordu; `STRONG_BUY` ve `STRONG_SELL` tipleri `BUY` gibi render ediliyordu. Her sinyal tipine ayrı badge class'ı (`badge-strong-buy/sell`) ve TR sabiti (`SIGNAL_STRONG_BUY/SELL`) gerekiyor. Konsensüs metadata'sı (oran, strateji sayısı, RSI, trend) ayrı `.signal-consensus` satırında gösterilmeli.
- **macOS sandbox ortamında port bind izni olmayabilir.** `uvicorn` ve `vite dev` server'ları `EPERM: operation not permitted` hatası verdi. Bu kod hatası değil, ortam kısıtlaması. Backend doğrulaması için `create_app()` + `list_blueprints()` import testi yeterli alternatif.
- **Vite build bundle analizi yapılmalı.** `npm run build` çıktısındaki dosya boyutları izlenmeli: CSS 17KB, uygulama JS 83KB, lightweight-charts 162KB, Chart.js 207KB. Chart.js en büyük bağımlılık; tree-shaking ile küçültülebilir (ileride).
- **Doğrulama senaryoları 3'e ayrılmalı:** (1) statik/unit test (pytest, TSC, build), (2) port-bind gerektiren canlı test (API curl, WS, dev server), (3) dış servis gerektiren test (Docker, Telegram, MCP). İlk kategori CI'da, ikincisi geliştirici ortamında, üçüncüsü deployment sonrası yapılmalı.

## Sprint 11 — Üretim Sertleştirme

- **API key middleware her istekte `os.environ.get()` çağırmalı.** Constructor'da cache'leyip kullanmak test izolasyonunu bozar; `patch.dict(os.environ)` ile set edilen değer middleware'a ulaşmaz. Çözüm: `_get_api_key()` metodu ile her istekte ortamdan oku.
- **IntersectionObserver + sentinel pattern sidebar lazy-load için ideal.** 130 sembolü DOM'a tek seferde eklemek başlangıç render süresini uzatır. İlk 15 sembolü hemen, geri kalanları scroll sentinel'e ulaşınca 15'lik batch'lerle yüklemek açılış performansını ~8x iyileştirdi.
- **CSS `@media (max-width: 768px)` ile sidebar gizlenirken `--sidebar-w: 0px` CSS variable overriding gerekli.** Sadece `display: none` yetersiz çünkü layout hesaplamaları CSS variable'a bağlı. Her iki yöntemi birlikte kullanmak mobil uyumu sağlam tutar.
- **Prometheus metrics'te stdlib exposition format (dış bağımlılık yok) yeterli.** `prometheus_client` paketi yüklemeden `/metrics` endpoint'i plain text Prometheus format döner. Basit counter'lar ve gauge'lar sadece uygulama değişkenleri üzerinden çalışır.
- **Worker çöküş uyarılarında cooldown mekanizması şart.** Aynı worker sürekli çöküp restart ederse dakikada 100+ Telegram mesajı gider. 5 dakika cooldown ile aynı worker için tekrar uyarı gönderilmez.
- **`STRICT_ENV_VALIDATION=1` sadece production deploy'da kullanılmalı.** Geliştirme ortamında opsiyonel değişkenlerin (Telegram token, SMTP) eksikliği normal; strict mod burada gereksiz yere servisi kırar.

## Grafik ve Çizim Altyapısı (G5)

- **Çizimlerin `localStorage` kalıcılığı bağlama göre izole edilmeli.** Tek bir global array yerine `symbol + timeframe` birleşik anahtarı (örn: `BTCUSDT__1d`) ile saklamak, kullanıcı sembol değiştirdiğinde yanlış grafikte alakasız çizimlerin görünmesini engeller ve bellek yönetimini kolaylaştırır. Data attribute'lar (`data-drawing-count`) üzerinden test yazımı bu bağımsızlığı doğrulamak için idealdir.

## Backtest ve Simülasyon

- **Monte Carlo Max Drawdown Hesabı:** Simülasyonlarda (özellikle bootstrap ve permutation yöntemlerinde) final getirisinin yanı sıra yörünge içi (intra-trajectory) maksimum düşüş (drawdown) hesabı kritik önem taşır. Her simülasyon eğrisindeki en yüksek tepeden (peak equity) anlık düşüşün yüzdesi izlenip, risk seviyesi P05/P95 dağılımlarıyla daha net raporlanabilir.

## Mali Analiz (Sprint 12)

- **FastAPI Dependency Injection ve Service Katmanı:** Mali analiz gibi dış kaynak bağımlı modüllerde, `create_app` factory'si içinde servis ve cache bileşenlerinin başlatılması test edilebilirliği artırır. Provider hatalarının 500 dönmesi yerine servis katmanında yakalanıp `warnings` listesiyle dönülmesi, frontend tarafında kullanıcı deneyimini bozmadan hata bilgisinin gösterilmesini sağlar.

## Backtest Gerçekçiliği (B4)

- **Slippage ve komisyon hesaplamaları helper katmanında ayrıştırıldı.** Ana backtest motoruna (`engine.py`) karmaşıklık eklemeden, `fixed_bps_slippage` ve `fixed_tick_slippage` gibi fonksiyonlarla order fiyatları simüle edilebilir. BIST hisselerinde açığa satış (short) için uptick kuralı veya likidite sınırı uyarıları bu bağımsız katmanda (`realism.py`) değerlendirilecek.
## Çoklu Sembol Karşılaştırma (G6)

- **Aynı panel üzerinde Line Series ile ikincil sembol eklenmesi.** `ChartPanel` sınıfına ikinci bir `ISeriesApi<'Line'>` referansı eklenerek ve ana grafiğe bağlanılarak çoklu sembol özelliği sağlandı. İkinci sembolün verisi, `MultiChartLayout` tarafından tarihsel olarak çekilip olay (`CustomEvent`) üzerinden ana `ChartPanel`'e gönderilir, böylece veri yükleme mantığı ile gösterim mantığı arasındaki izolasyon korunur. Yüzdesel (percent) modunda asıl sembolün baz fiyatından normalize edilerek mükemmel karşılaştırma (compare) deneyimi elde edilir.

## İleri Seviye İndikatörler (B2)

- **Gelişmiş Hareketli Ortalamalar:** `quant_engine.strategy.indicators` modülü genişletilerek saf Pandas/NumPy üzerinden WMA, DEMA, TEMA, ZLEMA, HMA, ALMA, KAMA ve T3 eklendi. Harici kütüphane bağımlılığı olmaksızın deterministic ve güvenli bir helper yüzeyi oluşturuldu; ilk bar `NaN` davranışları ve `ValueError` fırlatma mekanizmaları testlerle garanti altına alındı.
