# Quant Engine — Ana Planlama Dokümanı (v3 — Code Review Sonrası)

## 📊 Proje İlerleme Tablosu

| # | Modül / Görev | Durum | İlerleme |
|:--|:---|:---:|:---:|
| 1 | Proje Scaffold & Sanal Ortam | ✅ | %100 |
| 2 | Config Sistemi (Pydantic+TOML) | 🐛 6 bug | %50 |
| 3 | Data Pipeline — Fetcher | 🐛 9 bug | %40 |
| 4 | Data Pipeline — Storage Manager | 🐛 11 bug | %30 |
| 5 | Data Pipeline — Data Validator | 🐛 7 bug | %50 |
| 6 | Data Pipeline — Orchestrator | 🐛 3 bug | %60 |
| 7 | Demo Script | 🐛 3 bug | %60 |
| 8 | Pip Bağımlılık Kurulumu | ⏳ İnternet + pandas-ta fix gerekli | %0 |
| 9 | Test Altyapısı (pytest + fixture) | 📋 | %0 |
| 10 | Veri Omurgası (raw/clean/adjusted/features) | 📋 | %0 |
| 11 | BIST Trading Calendar | 📋 | %0 |
| 12 | Execution Semantics Spec | 📋 | %0 |
| 13 | Minimal Backtest Motoru | 📋 | %0 |
| 14 | Run Registry & Experiment Tracking | 📋 | %0 |
| 15 | Raporlama | 📋 | %0 |
| 16 | Optimizasyon + Governance | 📋 | %0 |
| 17-28 | İleri seviye modüller | 📋 | %0 |

**Gerçek İlerleme: ~%8 (scaffold hazır, mevcut kod ciddi bug'lı)**

---

## 🐛 KOD İNCELEME RAPORU — Tüm Tespit Edilen Sorunlar

### requirements.txt (2 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| REQ-1 | 19 | `pandas-ta>=0.3.14b1` kurulumu kırıyor, paket bulunamıyor | Kaldır veya `pandas-ta-classic` kullan veya indikatörleri kendimiz yazalım |
| REQ-2 | * | `>=` ile serbest bağımlılık tehlikeli; major versiyon atlayabilir | `pip-tools` veya `uv.lock` ile sürüm sabitle |

### pyproject.toml (1 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| PYP-1 | 15 | `testpaths = ["tests"]` ama root'ta `tests/` yok, pytest test bulamıyor | `testpaths = ["quant_engine/tests"]` veya root'ta `tests/` aç |

### config_manager.py (6 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| CFG-1 | 132 | `get_config()` env override uygulamıyor. `apply_env_overrides()` hiç çağrılmıyor | `get_config()` içinde `apply_env_overrides()` çağır veya `pydantic-settings`'e geç |
| CFG-2 | 26-85 | Modellerde `extra="forbid"` yok; yanlış TOML key'leri sessizce yutulur | Tüm modellere `model_config = ConfigDict(extra="forbid")` ekle |
| CFG-3 | 42-49 | Numeric alanlara sınır yok; negatif komisyon, %200 pozisyon mümkün | `Field(ge=0)`, `Field(le=1)`, `Field(ge=1)` ekle |
| CFG-4 | 30 | `db_path` config'te var ama hiçbir yerde kullanılmıyor | Ya DuckDB dosyasına bağlan ya config'ten çıkar |
| CFG-5 | 29,64 | `data_dir` CWD'ye göre çözülüyor; farklı dizinden çalışınca yanlış yol | `Path(__file__).resolve()` ile proje köküne göre çöz |
| CFG-6 | * | timezone, calendar, data_layer, retry, timeout, rate_limit ayarları eksik | Config'e ekle |

### fetcher.py (9 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| FET-1 | 80 | `end = today` — yfinance end'i exclusive kullanır; kapanış sonrası bugünün verisini kaçırabilir | `end = tomorrow` veya BIST takvimine göre hesapla |
| FET-2 | 124 | Delta fetch takvim bilmiyor; hafta sonu, tatil, seans kapanışı kontrolü yok | Trading calendar modülüne bağla |
| FET-3 | 97 | Intraday (1h, 5m) çağrılarında `KeyError: 'date'` — kolon adı `Datetime` oluyor | Date/Datetime kolonlarını normalize et |
| FET-4 | 255 | `fetch_bulk_yfinance()` tek sembolde kırılıyor (tuple parse hatası) | Single vs multi-symbol parse ayrı ele al |
| FET-5 | 160 | `fetch_watchlist()` sıralı; `max_workers` config'te var ama kullanılmıyor | `ThreadPoolExecutor` veya bulk `yf.download` kullan |
| FET-6 | 120 | Hata durumunda boş DataFrame dönüyor; hata tipi kayboluyor | `FetchResult(success, data, error_type, message)` döndür |
| FET-7 | 86 | `auto_adjust` politikası net değil; raw vs adjusted veri karışıyor | Raw ayrı sakla, adjusted ayrı transform et |
| FET-8 | 106 | `tz_localize(None)` timezone bilgisini siliyor | Exchange timezone koru, depoda UTC normalize et |
| FET-9 | * | Retry, timeout, backoff, rate-limit, sembol whitelist yok | Ağ dayanıklılığı ekle |

### storage_manager.py (11 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| STR-1 | 126 | Append tüm Parquet'i okuyup yeniden yazıyor | `layer/market/symbol/year.parquet` partition yapısı |
| STR-2 | 150 | Dönüş değeri yanıltıcı — kaç satır eklendi belli değil | `WriteResult(rows_added, rows_total, duplicates_removed)` döndür |
| STR-3 | 93 | `mode="nonsense"` sessizce overwrite gibi davranıyor | `Literal["append", "overwrite"]` veya enum ile validate et |
| STR-4 | 77-81 | `_symbol_path()` read çağrılarında bile klasör oluşturuyor (mkdir) | Read/exists işlemleri filesystem mutate etmemeli |
| STR-5 | 216,263 | SQL string interpolation — injection riski + path escape sorunu | Parametreli sorgu veya allow-list kullan |
| STR-6 | 215 | `columns` parametresi validate edilmiyor; kötü input SQL'i bozar | Allow-list kontrolü ekle |
| STR-7 | 79 | `market` validate edilmiyor; "bist" dışı her şey otomatik VİOP | `Literal["bist", "viop"]` veya enum |
| STR-8 | 137-143 | Parquet yazımı atomic değil; yarıda kesilirse veri kaybı | Temp dosya → checksum → rename |
| STR-9 | * | Concurrent write için file lock yok | `fcntl.flock` veya `filelock` ekle |
| STR-10 | 137 | Schema doğrulaması yazmadan önce yok; eksik volume PyArrow error | Yazmadan önce schema validate et |
| STR-11 | 305 | `get_symbol_stats()` dosya dosya loop; yavaş | Tek DuckDB glob query ile çöz |

### data_validator.py (7 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| VAL-1 | 132 | NaN fiyatları yakalamıyor (`<= 0` NaN'ı geçer) | `isna()`, `isfinite()`, dtype kontrolü ekle |
| VAL-2 | 153 | Negatif volume yakalamıyor | `volume >= 0` zorunlu kontrol |
| VAL-3 | 140 | OHLC kuralı eksik: `low > close` veya `low > open` kontrol edilmiyor | `low <= min(open, close)` ve `high >= max(open, close)` |
| VAL-4 | 128 | Duplicate kontrolü sadece `date`; multi-symbol veride `date + symbol` olmalı | Subset'e `symbol` ekle |
| VAL-5 | 145-151 | Ağır OHLC tutarsızlıkları warning, error olmalı | `High < Low` → error'a yükselt |
| VAL-6 | 177 | Gap kontrolü takvim günüyle; BIST trading calendar'a göre olmalı | Trading calendar modülüne bağla |
| VAL-7 | 227 | `auto_fix()` sınırsız forward-fill — veri uydurma riski, leakage | Limitli ffill (max 3 gün), sembol bazlı, re-validation zorunlu |

### pipeline.py (3 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| PIP-1 | 84 | Validasyon başarısız → auto-fix → write; hard error'da yazma durmalı | Error seviyesinde yazma engelle |
| PIP-2 | * | "0 satır" ile "fetch hatası" ayırt edilemiyor | Sonuç modeli (FetchResult) kullan |
| PIP-3 | * | Sıralı işleme, retry ve partial failure raporu yok | Toplu hata raporu ekle |

### demo.py (3 sorun)

| ID | Satır | Sorun | Çözüm |
|:--|:--|:--|:--|
| DEM-1 | * | Exception'da storage kapanmayabilir | `with` context manager kullan |
| DEM-2 | 148 | `results` değişkeni kullanılmıyor (unused) | Lint temizle |
| DEM-3 | * | Gerçek data dizinine yazıyor; smoke test için temp dir lazım | `--temp-dir` opsiyonu ekle |

### Kullanılmayan importlar

| Dosya | Import | Durum |
|:--|:--|:--|
| data_validator.py:20 | `import numpy as np` | np hiçbir yerde kullanılmıyor → kaldır |

**Toplam: 45 tespit (2 req + 1 pyp + 6 cfg + 9 fet + 11 str + 7 val + 3 pip + 3 dem + 1 lint + 2 genel)**

---

## YENİ SPRİNT PLANI (Code Review Sonrası)

### Sprint 0 — Acil Düzeltmeler (Blocker)
> Bunlar olmadan hiçbir şey çalışmaz.

- [ ] REQ-1: pandas-ta kaldır veya değiştir
- [ ] REQ-2: Bağımlılık sürümlerini sabitle (pip-tools/uv)
- [ ] PYP-1: testpaths düzelt
- [ ] `pip install` başarılı şekilde çalışsın
- [ ] Ruff ile 240 lint sorununu temizle

### Sprint 1 — Config & Fetcher Düzeltmeleri
- [ ] CFG-1: get_config() env override
- [ ] CFG-2: extra="forbid"
- [ ] CFG-3: Field sınırları
- [ ] CFG-5: data_dir deterministic resolve
- [ ] FET-1: end tarih exclusive fix
- [ ] FET-3: Intraday kolon normalize
- [ ] FET-4: Bulk tek-sembol fix
- [ ] FET-5: Paralel fetch
- [ ] FET-6: FetchResult sonuç nesnesi
- [ ] FET-8: Timezone UTC normalize

### Sprint 2 — Storage & Validator Düzeltmeleri
- [ ] STR-1: Partition yapısı (year/symbol)
- [ ] STR-3: mode validation (Literal)
- [ ] STR-4: _symbol_path read'de mkdir kaldır
- [ ] STR-5: SQL injection düzelt
- [ ] STR-7: market validation
- [ ] STR-8: Atomic write (temp → rename)
- [ ] STR-10: Schema validation before write
- [ ] VAL-1: NaN/inf fiyat kontrolü
- [ ] VAL-2: Negatif volume kontrolü
- [ ] VAL-3: Tam OHLC kuralı
- [ ] VAL-5: Ağır tutarsızlık → error
- [ ] VAL-7: Limitli auto_fix + re-validation
- [ ] PIP-1: Hard error'da yazma engelle

### Sprint 3 — Test Altyapısı
- [ ] Root'ta `tests/` klasörü oluştur (unit, integration, fixtures)
- [ ] 5-10 satırlık golden fixture CSV (elle doğrulanmış OHLCV)
- [ ] `test_storage.py`: fixture → write → read → karşılaştır
- [ ] `test_validator.py`: bilinen hatalı veri → hata tespit
- [ ] `test_config.py`: geçersiz config → hata fırlatma
- [ ] pytest yeşil, ruff temiz, CI baseline

### Sprint 4 — Veri Omurgası (raw/clean/adjusted/features)
- [ ] 4 katmanlı dizin yapısı
- [ ] Her dosya yanında `_metadata.json` (source, checksum, lineage)
- [ ] Schema contract (PyArrow schema her katmanda)
- [ ] Transform pipeline: raw → clean → adjusted

### Sprint 5 — BIST Trading Calendar
- [ ] İşlem günleri, tatiller, yarım günler
- [ ] Açılış/kapanış müzayede dönemleri
- [ ] Timezone standardı (Europe/Istanbul → UTC)
- [ ] Seans dışı işlem yasağı
- [ ] `is_trading_day()`, `next_trading_day()`, `trading_days_between()`
- [ ] Validator ve fetcher'a entegre et (gap kontrolü, delta fetch)

### Sprint 6 — Execution Semantics Spec
- [ ] Signal → Execution timing kuralı
- [ ] Intrabar ambiguity politikası
- [ ] Fill policy (full, partial, no fill)
- [ ] Order types (Market, Limit, Stop)
- [ ] Warm-up bars standardı
- [ ] Assumptions registry (her koşuya snapshot)

### Sprint 7 — Minimal Backtest Motoru
- [ ] Tek sembol, long-only, market order
- [ ] Komisyon + slippage
- [ ] Equity curve hesaplama
- [ ] Invariant: `cash + position_value == total_equity` her barda
- [ ] Audit trail: signal → order → fill → position → pnl
- [ ] Anti-leakage: `feature_ts ≤ decision_ts < execution_ts`
- [ ] Golden fixture ile elle doğrulanmış sonuç eşleşmesi
- [ ] Buy & Hold baseline ile karşılaştırma

### Sprint 8 — Run Registry & Raporlama
- [ ] Run ID, config snapshot, git hash, data hash, seed
- [ ] `artifacts/<run_id>/` yapısı
- [ ] `run_registry.duckdb`
- [ ] Equity curve, drawdown, aylık heatmap, trade tablosu
- [ ] Gross vs net ayrımı, benchmark kıyası
- [ ] HTML rapor çıktısı

### Sprint 9 — Optimizasyon + Governance
- [ ] Grid search, walk-forward, Optuna
- [ ] Out-of-sample, parameter stability, cost sensitivity
- [ ] Search budget, seed kontrolü, erken durdurma

### Sprint 10 — İleri Seviye Motor
- [ ] Feature cache (aynı SMA/RSI optimizasyonda tekrar hesaplanmasın)
- [ ] Universe selection (min hacim, min fiyat, point-in-time membership)
- [ ] Portfolio constructor (exposure caps, correlation-aware sizing)
- [ ] Anti-leakage guardrails (feature_ts ≤ decision_ts < execution_ts)
- [ ] Transaction cost model hierarchy (fixed bps → spread+bps → participation)
- [ ] Instrument model (EquityInstrument, FuturesInstrument)
- [ ] VİOP margin engine, rollover
- [ ] CLI (Typer): `quant fetch`, `quant backtest`, `quant optimize`

### ─── MOTOR BİTTİ, UI BAŞLAR ───

### Sprint 11 — Streamlit MVP (Faz A)
> Detaylı tasarım: `arayuz.md`

- [ ] **Dashboard:** Sistem durumu, veri sağlığı, son koşular, hızlı listeler
- [ ] **Data Station:** Sembol bazlı coverage, boşluk haritası, veri güvenilirlik kapısı
- [ ] **Strategy Builder:** Strateji seçimi, slider parametreler, universe, tarih, backtest butonu
- [ ] **Backtest Lab:** Equity curve (Plotly), drawdown, heatmap, trade tablosu, assumptions panel
- [ ] **Run Compare:** Koşu karşılaştırma tablosu, equity overlay
- [ ] **Trade Inspector:** Audit trail, sinyal sebebi, dolum detayı
- [ ] Arka plan backtest: Progress bar, iptal butonu (Streamlit sınırında)

### Sprint 12 — Matrix Tarama Paneli
- [ ] **Matrix ekranı:** Sembol × metrik tablosu (trend, RSI, hacim, sinyal, BT sonucu)
- [ ] Hücre renkleri: yeşil/kırmızı/gri/sarı
- [ ] Tıkla → grafik aç, sütun sırala, filtrele
- [ ] Sinyal tarayıcı: "Bugün AL verenler", "Hacim patlayanlar"
- [ ] Akıllı listeler: En iyi 10 hisse, en düşük DD stratejiler

### Sprint 13 — Grafik + İşlem Gösterimi
- [ ] Candlestick grafik (Plotly MVP / lightweight-charts nihai)
- [ ] Volume barları, SMA/EMA/Bollinger overlay, RSI/MACD alt panel
- [ ] Grafik üzerinde AL/SAT okları, stop-loss/take-profit çizgileri
- [ ] Mouse hover OHLCV tooltip
- [ ] Zaman dilimi değiştirici (1D | 1H | 15M | 5M)

### Sprint 14 — Optimizasyon Ekranı
- [ ] Parametre heatmap, walk-forward fold sonuçları
- [ ] Stability grafiği, cost sensitivity
- [ ] Overfit uyarısı, parameter clustering

### ─── STREAMLIT SINIRA GELDİ ───

### Sprint 15+ — FastAPI + React Terminal (Faz B)
- [ ] FastAPI backend API
- [ ] React + lightweight-charts (TradingView kalitesi)
- [ ] Çoklu grafik penceresi (2x2 grid)
- [ ] Keyboard shortcuts, WebSocket canlı güncelleme
- [ ] Background job queue (Celery/RQ)
- [ ] Paper trading bridge → canlı trading

---

## ❌ Kasıtlı Ertelenenler
| Ne | Neden |
|:--|:--|
| Order book simülasyonu | Overengineering |
| Mikrosaniye execution | HFT değiliz |
| Distributed compute | Tek makine yeterli |
| Full React/Next.js UI | Önce Streamlit MVP |
| Glassmorphism / efektler | Güven ve okunabilirlik önce |
| Web UI genel | Motor kanıtlanmadan arayüz anlamsız |

---

## 🔧 Mevcut Dosya Haritası
```
/Users/enes/AgentWorkspace/Backtest/
├── ✅ .gitignore, README.md, pyproject.toml (🐛 PYP-1)
├── ⚠️ requirements.txt (🐛 REQ-1, REQ-2)
├── 🐛 demo.py (DEM-1,2,3)
├── ✅ ogrenilenler.md, planlama.md, arayuz.md
├── ✅ config/settings.toml
├── quant_engine/
│   ├── 🐛 config/config_manager.py (CFG-1→6)
│   ├── 🐛 data_pipeline/
│   │   ├── fetcher.py (FET-1→9)
│   │   ├── storage_manager.py (STR-1→11)
│   │   ├── data_validator.py (VAL-1→7)
│   │   └── pipeline.py (PIP-1→3)
│   ├── 📋 core/ (calendar, instruments)
│   ├── 📋 backtest_engine/ (execution_spec, engine)
│   ├── 📋 strategy/, optimization/, validation/
│   ├── 📋 reporting/, live_execution/, cli/
│   └── 📋 tests/ (boş)
```

**Semboller:** ✅ Hazır | 🐛 Bug var | ⚠️ Blocker | 📋 Planlandı
