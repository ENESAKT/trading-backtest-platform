Sen bu projede üst düzey senior software architect, quant/backtest engine developer, finansal veri mimarı ve ürünleşebilir trading terminal uzmanı gibi çalışacaksın.

Bu projeyi baştan sona profesyonel, genişleyebilir, testli, optimize ve ileride Matriks / Borsa İstanbul / Foreks / broker API gibi kaynaklara bağlanabilecek bir BIST/VİOP backtest ve araştırma platformuna dönüştüreceksin.

ÇALIŞMA MODU: TAM OTONOM

Kullanıcıdan her aşama sonunda izin isteme.
Planı sırayla uygula.
Bir aşama bittiğinde durma; test et, checklist güncelle ve sonraki aşamaya geç.
Sadece şu durumlarda kullanıcıya sor:
- Ücretli API / abonelik / lisans gerekiyor.
- Broker hesabı, canlı emir, para riski veya credential gerekiyor.
- Destructive işlem gerekiyor: veri silme, git reset, büyük dosya kaldırma.
- Aynı anda iki mantıklı mimari yol var ve yanlış seçim ileride büyük maliyet doğuracak.
- Dış servis şifresi/API key gerekiyor.

Bunların dışında karar ver, uygula, test et, devam et.

GENEL KURALLAR

1. Önce tüm projeyi tara.
2. Mevcut kullanıcı değişikliklerini asla silme.
3. Kod yazmadan önce kısa uygulama planı çıkar.
4. Her aşamada checklist tut.
5. Bir maddeyi sadece gerçekten yaptıysan ve test ettiysen `[x]` yap.
6. Yapıldı ama test edilemediyse `[!] Test edilemedi` yaz.
7. Yapılmadıysa `[ ]` bırak.
8. Hata saklama; kırılan, riskli, eksik her şeyi açıkça raporla.
9. Her aşamadan sonra `PROJECT_STATUS.md` veya `planlama.md` içine güncel ilerlemeyi yaz.
10. UI’dan önce motorun doğruluğunu kanıtla.
11. Backtest sonuçlarını asla “garanti” veya “kesin” diye sunma.
12. Her backtest sonucu config, veri kaynağı, varsayım ve checksum ile tekrar üretilebilir olmalı.
13. Gereksiz refactor yapma; ama mimari çökme riski varsa düzelt.
14. Performans optimizasyonunu doğruluk pahasına yapma.
15. Önce doğru çalışan küçük sistem, sonra hızlı ve büyük sistem.

HER AŞAMA SONUNDA RAPOR FORMATIN

## Aşama Raporu
- Aşama:
- Durum:
- Yapılanlar:
- Değişen dosyalar:
- Eklenen testler:
- Çalıştırılan komutlar:
- Test sonucu:
- Kalan riskler:
- Sonraki otomatik adım:

Checklist:
- [x] Gerçekten tamamlanan ve test edilen iş
- [!] Yapıldı ama test edilemedi / risk var
- [ ] Bekleyen iş

PROJE HEDEFİ

BIST/VİOP için:
- Güvenilir veri toplama
- Raw / clean / adjusted / features veri katmanları
- Çoklu veri sağlayıcı desteği
- BIST takvimi ve timezone doğruluğu
- Backtest motoru
- Strategy framework
- Audit trail
- Run registry
- HTML rapor
- Matrix ekranı
- Grafik ekranı
- Optimizasyon
- İleride Matriks/BIST/Foreks/broker entegrasyonu

HEDEF MİMARİ

quant_engine/
  core/
    instruments.py
    calendar.py
    timeframes.py
    symbol_master.py
    models.py
    errors.py

  data/
    providers/
      base.py
      yfinance_provider.py
      stooq_provider.py
      matriks_csv_provider.py
      matriks_api_provider.py
      bist_verda_provider.py
    storage/
      parquet_store.py
      metadata_store.py
      schema.py
    validation/
      quality.py
      calendar_checks.py
    transforms/
      normalize.py
      adjust.py
      resample.py

  strategy/
    base.py
    indicators.py
    registry.py
    examples/
      sma_crossover.py
      rsi_reversion.py

  backtest/
    engine.py
    execution.py
    cost_model.py
    portfolio.py
    audit.py
    metrics.py
    results.py

  research/
    optimizer.py
    walk_forward.py
    run_registry.py

  reporting/
    html_report.py
    charts.py

  app/
    api/
    ui_streamlit/
    ui_react/

  cli/
    main.py

tests/
  unit/
  integration/
  golden/
  fixtures/

VERİ DİZİNİ HEDEFİ

data/
  raw/source=yfinance/market=bist/timeframe=1d/symbol=THYAO/year=2024/
  raw/source=matriks/market=bist/timeframe=1m/symbol=THYAO/year=2024/
  clean/market=bist/timeframe=1d/symbol=THYAO/year=2024/
  adjusted/market=bist/timeframe=1d/symbol=THYAO/year=2024/
  features/market=bist/timeframe=1d/symbol=THYAO/year=2024/

Her veri dosyası yanında metadata olmalı:
- source
- provider_symbol
- canonical_symbol
- market
- asset_class
- timeframe
- timezone
- row_count
- first_timestamp
- last_timestamp
- schema_version
- checksum_sha256
- ingest_time
- adjustment_policy
- transform_lineage

AŞAMA 0 - TAM PROJE DENETİMİ

Kod yazma. Sadece denetle ve raporla.

- [ ] Dosya yapısını çıkar
- [ ] Bağımlılıkları kontrol et
- [ ] `pip install -r requirements.txt` çalışıyor mu bak
- [ ] `pytest` çalışıyor mu bak
- [ ] `ruff` çalışıyor mu bak
- [ ] Mevcut veri pipeline akışını incele
- [ ] Storage risklerini çıkar
- [ ] Validator eksiklerini çıkar
- [ ] Backtest motoru var mı kontrol et
- [ ] Strategy framework var mı kontrol et
- [ ] UI planı motorla uyumlu mu kontrol et
- [ ] Proje büyüyünce nerede çöker raporla

AŞAMA 1 - KURULUM VE DEV ALTYAPI

- [ ] `pandas-ta` kurulum sorununu çöz
- [ ] Gereksiz/bozuk dependency’leri temizle
- [ ] Dependency lock stratejisi kur
- [ ] `pyproject.toml` test yolunu düzelt
- [ ] `tests/` klasör yapısını oluştur
- [ ] `ruff` temiz hale getir
- [ ] Minimum smoke test ekle
- [ ] `compileall`, `pytest`, `ruff` yeşil olsun

AŞAMA 2 - CONFIG SİSTEMİ

- [ ] Env override gerçekten çalışsın
- [ ] Config validation ekle
- [ ] Yanlış TOML key’leri sessiz geçmesin
- [ ] `data_dir` proje köküne göre resolve edilsin
- [ ] `timezone`, `source`, `timeframe`, `data_layer` ayarları eklensin
- [ ] Config testleri yazılsın

AŞAMA 3 - VERİ SAĞLAYICI MİMARİSİ

- [ ] `MarketDataProvider` base interface oluştur
- [ ] `BarRequest` modeli oluştur
- [ ] `FetchResult` modeli oluştur
- [ ] `ProviderCapabilities` modeli oluştur
- [ ] Mevcut yfinance fetcher provider’a taşınsın
- [ ] Hata durumunda boş DataFrame yerine typed result dönsün
- [ ] Provider symbol mapping altyapısı kurulsun
- [ ] Matriks/BIST provider stub dosyaları eklensin
- [ ] Provider testleri yazılsın

AŞAMA 4 - STORAGE MİMARİSİ

- [ ] Raw / clean / adjusted / features katmanları kur
- [ ] Partition yapısı kur: market/timeframe/symbol/year
- [ ] Atomic parquet write ekle
- [ ] Metadata json yaz
- [ ] Checksum üret
- [ ] Append tüm dosyayı yeniden yazmasın
- [ ] SQL string interpolation kaldır
- [ ] Kolon allow-list ekle
- [ ] Sembol ve market validation ekle
- [ ] Storage testleri yaz

AŞAMA 5 - VERİ DOĞRULAMA

- [ ] NaN fiyat yakalansın
- [ ] Inf yakalansın
- [ ] Negatif fiyat yakalansın
- [ ] Sıfır fiyat politikası belirlensin
- [ ] Negatif volume yakalansın
- [ ] OHLC tam tutarlılık kontrolü eklensin
- [ ] Duplicate symbol + timestamp kontrolü eklensin
- [ ] BIST calendar bazlı gap kontrolü eklensin
- [ ] Auto-fix sınırlı ve raporlu olsun
- [ ] Invalid veri storage’a yazılmasın
- [ ] Validator testleri yaz

AŞAMA 6 - BIST CALENDAR

- [ ] `Europe/Istanbul` standardı
- [ ] UTC storage standardı
- [ ] Trading day fonksiyonları
- [ ] `next_trading_day`
- [ ] `previous_trading_day`
- [ ] Session open/close
- [ ] Yarım gün yapısı
- [ ] Delta fetch calendar ile çalışsın
- [ ] Calendar testleri yaz

AŞAMA 7 - BACKTEST EXECUTION SPEC

- [ ] Sinyal zamanı tanımla
- [ ] Emir zamanı tanımla
- [ ] Fill zamanı tanımla
- [ ] Varsayılan kural: bar[t] close sinyal, bar[t+1] open execution
- [ ] Slippage modeli
- [ ] Commission modeli
- [ ] Stop/target aynı barda tetiklenirse conservative policy
- [ ] Warm-up bars
- [ ] Assumptions snapshot

AŞAMA 8 - MİNİMAL BACKTEST MOTORU

- [ ] Tek sembol long-only motor
- [ ] Market order desteği
- [ ] Cash takibi
- [ ] Position takibi
- [ ] Equity curve
- [ ] Orders tablosu
- [ ] Fills tablosu
- [ ] Trades tablosu
- [ ] Audit trail
- [ ] `cash + position_value = total_equity` invariant testi
- [ ] Golden fixture ile elle doğrulanmış backtest testi

AŞAMA 9 - STRATEGY FRAMEWORK

- [ ] `BaseStrategy`
- [ ] `generate_signals`
- [ ] Params schema
- [ ] Warm-up desteği
- [ ] Indicator registry
- [ ] SMA crossover stratejisi
- [ ] RSI stratejisi
- [ ] Buy & Hold baseline
- [ ] Strategy testleri

AŞAMA 10 - METRICS VE RAPORLAMA

- [ ] Total return
- [ ] CAGR
- [ ] Max drawdown
- [ ] Sharpe
- [ ] Sortino
- [ ] Win rate
- [ ] Profit factor
- [ ] Average holding period
- [ ] Gross vs net performans
- [ ] Equity curve chart
- [ ] Drawdown chart
- [ ] Monthly heatmap
- [ ] Trade table
- [ ] HTML report

AŞAMA 11 - RUN REGISTRY

- [ ] Her koşuya `run_id`
- [ ] Config snapshot
- [ ] Execution assumptions snapshot
- [ ] Input data checksum
- [ ] Git commit hash
- [ ] Python/package versions
- [ ] Metrics json
- [ ] Trades parquet
- [ ] Equity parquet
- [ ] `run_registry.duckdb`
- [ ] Run compare altyapısı

AŞAMA 12 - OPTİMİZASYON

- [ ] Grid search
- [ ] Walk-forward analysis
- [ ] Out-of-sample ayrımı
- [ ] Cost sensitivity
- [ ] Parameter stability
- [ ] Overfit uyarısı
- [ ] Heatmap çıktısı
- [ ] En yüksek getiri yerine sağlamlık metriği

AŞAMA 13 - STREAMLIT / DASH MVP UI

UI hesap yapmasın. Sadece motor ve registry output’unu göstersin.

- [ ] Sembol seçimi
- [ ] Timeframe seçimi
- [ ] Mum grafik
- [ ] Volume bar
- [ ] İndikatör overlay
- [ ] Al/sat işaretleri
- [ ] Backtest parametre paneli
- [ ] Equity curve
- [ ] Drawdown
- [ ] Trade table
- [ ] Matrix ekranı
- [ ] Data quality ekranı
- [ ] Run compare ekranı
- [ ] Trade inspector

AŞAMA 14 - PROFESYONEL TERMİNAL HAZIRLIĞI

- [ ] FastAPI backend tasarımı
- [ ] React frontend tasarımı
- [ ] lightweight-charts entegrasyon planı
- [ ] Background job queue
- [ ] Job progress/cancel/retry
- [ ] API endpoint sözleşmeleri
- [ ] UI state modeli
- [ ] Büyük grafik datası için downsampling/resampling

AŞAMA 15 - MATRİKS / BIST ENTEGRASYON HAZIRLIĞI

Ücretli servis bağlantısı için kullanıcı onayı olmadan gerçek credential isteme veya canlı bağlantı kurma.

- [ ] Matriks CSV importer tasarla
- [ ] Matriks API provider stub oluştur
- [ ] Matriks MQTT/WebSocket canlı veri tasarımı yap
- [ ] BIST VERDA provider stub oluştur
- [ ] Credential güvenliği tasarla
- [ ] Provider capabilities matrix oluştur
- [ ] Hangi kaynak ne verir, ne vermez raporla
- [ ] VİOP için instrument model genişlet

FİNANSAL DOĞRULUK KURALLARI

- Lookahead bias engellenecek.
- Survivorship bias raporlanacak.
- Raw ve adjusted veri karıştırılmayacak.
- Sinyal üretirken gelecekteki veri kullanılmayacak.
- Warm-up olmadan sinyal üretilemeyecek.
- Komisyon/slippage olmadan sonuç gerçekçi diye sunulmayacak.
- Benchmark olmadan strateji başarısı yorumlanmayacak.
- Her backtest sonucu tekrar üretilebilir olacak.
- Audit trail olmadan grafik üzerinde işlem gösterilmeyecek.

ÇÖKMEYİ ÖNLEME KURALLARI

- Uzun süren işler UI thread’inde çalışmayacak.
- Büyük veri tek dosyada tutulmayacak.
- Append tüm dataset’i rewrite etmeyecek.
- Yazma atomic olacak.
- Her provider ayrı modül olacak.
- Backtest engine provider bilmeyecek.
- UI storage’a doğrudan yazmayacak.
- Strategy execution yapmayacak.
- Execution strategy hesaplamayacak.
- Portfolio sadece pozisyon/equity takip edecek.
- Reporting hesaplama yapmayacak; motor output’unu görselleştirecek.

İLK GÖREVİN

AŞAMA 0’dan başla.
Kod yazma.
Tüm projeyi tara.
Kurulum, test, lint, veri pipeline, mimari, çökme riski, genişleme riski, performans riski ve finansal doğruluk risklerini raporla.
Sonra AŞAMA 1’e otomatik geç ve uygulamaya başla.
Her aşama sonunda rapor ver ama kullanıcıdan onay bekleme.
