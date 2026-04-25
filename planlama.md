# Quant Engine — Ana Planlama Dokümanı (v4 — Mimari Yeniden Yapılanma)

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
| 8 | Pip Bağımlılık Kurulumu | ⏳ Blocker | %0 |
| 9 | **Mimari Yeniden Yapılanma** | 📋 | %0 |
| 10 | Test Altyapısı | 📋 | %0 |
| 11 | Core Domain Katmanı | 📋 | %0 |
| 12 | Veri Omurgası + Transforms | 📋 | %0 |
| 13 | BIST Trading Calendar | 📋 | %0 |
| 14 | Execution Spec + Minimal Motor | 📋 | %0 |
| 15 | Run Registry + Raporlama | 📋 | %0 |
| 16 | Optimizasyon + Governance | 📋 | %0 |
| 17 | UI — Streamlit MVP | 📋 | %0 |
| 18 | UI — Matrix Terminal (React) | 📋 | %0 |

**Gerçek İlerleme: ~%8 (scaffold + bug'lı data pipeline)**

---

## 🏗️ MİMARİ KARAR: Modüler Monolit + Temiz Çekirdek

### Ana Prensip

> **Core hiçbir UI, yfinance, Streamlit, FastAPI bilmemeli.**
> Tek repo, ama katmanlar sert ayrılmış. Yeni özellik eski sonucu BOZAMAMALI.

### Neden Yeniden Yapılanma Gerekli?

Mevcut yapıda (`data_pipeline/` altında her şey düz) şu 3 noktada çöker:

| Nerede Çöker | Neden | Çözüm |
|:---|:---|:---|
| Veri büyüyünce | storage tüm dosyayı okuyor, partition yok | Katmanlı veri + yıl/sembol partition |
| Strateji sayısı artınca | sinyal/execution/maliyet karışır | Core domain nesneleri ayrılmalı |
| UI eklenince | uzun backtest arayüzü kilitler | Job queue + core-UI ayrımı |

### Hedef Mimari (Önceki vs Yeni)

```
ÖNCEKİ (düz yapı):              YENİ (katmanlı):
─────────────────                ──────────────────
quant_engine/                    quant_engine/
  config/                →        config/
  data_pipeline/                  core/           ← SAF DOMAIN
    fetcher.py                      instrument.py
    storage_manager.py              order.py
    data_validator.py               fill.py
    pipeline.py                     portfolio.py
  strategy/              →          clock.py
  backtest_engine/                  protocols.py  ← INTERFACE'LER
  optimization/                   data/
  validation/                       providers/    ← yfinance, matriks
  reporting/                        storage/      ← parquet, duckdb
  live_execution/                   validation/   ← schema, quality
  cli/                              transforms/   ← raw→clean→adj→feat
  tests/                          strategy/
                                  backtest/       ← engine, execution, cost
                                  research/       ← optimizer, walk_forward
                                  reporting/
                                  app/            ← UI TAMAMEN AYRI
                                    api/
                                    ui_streamlit/
                                    ui_react/
                                  cli/
                                  tests/
                                    unit/
                                    integration/
                                    golden/
```

### Interface / Protocol Tanımları

Core'un dış dünyayı bilmemesi için soyut arayüzler:

```python
# quant_engine/core/protocols.py

class DataProvider(Protocol):
    """yfinance, Matriks, Foreks hepsi bunu implemente eder"""
    def fetch(self, symbols, timeframe, start, end) -> FetchResult: ...

class StorageBackend(Protocol):
    """Parquet, DuckDB, hatta ileride S3"""
    def read(self, symbol, timeframe, start, end) -> DataFrame: ...
    def write(self, data, symbol, layer, metadata) -> WriteResult: ...
    def list_symbols(self) -> list[str]: ...

class Strategy(Protocol):
    """Her strateji bunu implemente eder"""
    def generate_signals(self, data, params) -> SignalFrame: ...
    def get_params(self) -> dict: ...
    def get_warm_up_bars(self) -> int: ...

class ExecutionModel(Protocol):
    """Emir doldurma simülasyonu"""
    def simulate(self, order, bar, context) -> Fill: ...

class CostModel(Protocol):
    """Maliyet hesaplama"""
    def calculate(self, fill) -> Cost: ...

class Instrument(Protocol):
    """Equity, Futures, FX"""
    def tick_size(self) -> float: ...
    def lot_size(self) -> int: ...

class BrokerAdapter(Protocol):
    """İleride canlı/paper trading"""
    def submit_order(self, order) -> OrderResult: ...

class ReportRenderer(Protocol):
    """HTML, JSON, UI API"""
    def render(self, backtest_result) -> Report: ...
```

Bu sayede: yeni veri kaynağı eklerken motor bozulmaz. VİOP eklerken strateji bozulmaz. UI değiştirirken backtest bozulmaz.

---

## 📁 Hedef Veri Yapısı

```
data/
├── raw/bist/1d/symbol=THYAO/year=2024/part.parquet     # Kaynaktan geldiği gibi
├── clean/bist/1d/symbol=THYAO/year=2024/part.parquet   # Tip, timezone, NaN temiz
├── adjusted/bist/1d/symbol=THYAO/year=2024/part.parquet # Split, temettü düzeltilmiş
└── features/bist/1d/symbol=THYAO/year=2024/features.parquet # İndikatörler

artifacts/
├── runs/<run_id>/
│   ├── config.toml           # Config snapshot
│   ├── assumptions.json      # Execution spec snapshot
│   ├── orders.parquet        # Verilen emirler
│   ├── fills.parquet         # Dolumlar (fiyat, slippage, komisyon)
│   ├── trades.parquet        # Açık→kapanış trade'ler
│   ├── equity.parquet        # Günlük bakiye
│   ├── metrics.json          # Tüm performans metrikleri
│   └── report.html           # Görsel rapor
└── run_registry.duckdb       # Tüm koşuların karşılaştırma tablosu
```

Her dosyada metadata: `source, ingest_time, schema_version, checksum, row_count, transform_lineage`

---

## 📐 Referans Projeler ve Dersler

| Proje | Ne Alacağız | Ne Almayacağız |
|:---|:---|:---|
| **VectorBT** | Vektörize NumPy/Numba ile hızlı parametre tarama. Optimizasyon katmanımız buna benzemeli | Aşırı karmaşık API'si |
| **Backtrader** | Reusable strategy/indicator/analyzer yapısı. Strategy ve metrics katmanımız bundan ders alacak | Ağır class hiyerarşisi |
| **QuantConnect LEAN** | En iyi mimari örnek: engine/security/portfolio/transactions ayrımı. Uzun vadeli hedefimiz | C# ağırlığı, çok katmanlı |
| **Freqtrade** | Trade export, fee handling, reproducibility uyarıları, sonuç analizi | Bot-first tasarımı |
| **Backtesting.py** | Küçük API, commission/spread/trade-on-close açık parametre, interaktif plot | Tek dosya sınırı |

**Hedefimiz:** LEAN kadar katmanlı ama daha hafif, VectorBT kadar hızlı parametre taraması, Freqtrade gibi export ve reproducibility, Backtesting.py kadar basit başlangıç API'si.

---

## 🐛 KOD İNCELEME RAPORU — 45 Tespit

*(Değişiklik yok — v3'teki tüm bug'lar geçerli)*

### requirements.txt (2 sorun)
| ID | Sorun | Çözüm |
|:--|:--|:--|
| REQ-1 | `pandas-ta>=0.3.14b1` kurulumu kırıyor | Kaldır veya indikatörleri kendimiz yazalım |
| REQ-2 | `>=` ile serbest bağımlılık tehlikeli | `pip-tools` / `uv.lock` ile sabitle |

### config_manager.py (6), fetcher.py (9), storage_manager.py (11), data_validator.py (7), pipeline.py (3), demo.py (3), lint (1)

> Detaylı tablo: v3'te aynı. Bug ID'leri (CFG-1→6, FET-1→9, STR-1→11, VAL-1→7, PIP-1→3, DEM-1→3) geçerli.
> Tüm bug'lar Sprint 1-2'de düzeltilecek.

---

## ⚡ PERFORMANS TASARIMI

| Katman | Yöntem | Neden |
|:---|:---|:---|
| **Storage** | Yıl/sembol/timeframe partition | Append tek yıl dosyasına dokunur |
| **Okuma** | DuckDB predicate pushdown + Polars LazyFrame | Sadece gerekli satırlar RAM'e gelir |
| **Feature** | Cache key = data checksum + indicator params | Aynı SMA tekrar hesaplanmaz |
| **Backtest** | Önce doğru Pandas/Polars, sonra hot loop Numba | Erken optimizasyon yapma |
| **Optimizasyon** | Process pool + run queue + cancellation + progress | Çoklu çekirdek kullanımı |
| **UI grafik** | 10K+ bar → resample/downsample | Tarayıcıya ham veri gönderme |
| **Matrix** | Snapshot tablo üret, UI onu okusun | Her hücreyi canlı hesaplama |

---

## YENİ SPRİNT PLANI

### Sprint 0 — Acil Blocker'lar
- [ ] REQ-1: pandas-ta kaldır/değiştir
- [ ] REQ-2: Bağımlılık lock dosyası üret
- [ ] PYP-1: testpaths düzelt
- [ ] `pip install` başarılı çalışsın
- [ ] Ruff ile lint temizliği

### Sprint 1 — Mimari Yeniden Yapılanma + Bug Düzeltme
> Mevcut kodu yeni klasör yapısına taşı + bug'ları düzelt.

**Klasör geçişi:**
- [ ] `quant_engine/core/` oluştur: `protocols.py`, `instrument.py`, `order.py`, `clock.py`
- [ ] `quant_engine/data/providers/` ← fetcher.py taşı + bug düzelt (FET-1→9)
- [ ] `quant_engine/data/storage/` ← storage_manager.py taşı + bug düzelt (STR-1→11)
- [ ] `quant_engine/data/validation/` ← data_validator.py taşı + bug düzelt (VAL-1→7)
- [ ] `quant_engine/data/transforms/` oluştur (raw→clean→adjusted→features)
- [ ] Config bug'ları düzelt (CFG-1→6)
- [ ] Pipeline bug'ları düzelt (PIP-1→3)
- [ ] Demo bug'ları düzelt (DEM-1→3)

### Sprint 2 — Test Altyapısı
- [ ] Root'ta `tests/unit/`, `tests/integration/`, `tests/golden/`
- [ ] Golden fixture: 5-10 satır elle doğrulanmış OHLCV CSV
- [ ] `test_storage.py`: fixture → write → read → karşılaştır
- [ ] `test_validator.py`: bilinen hatalı veri → hata tespit
- [ ] `test_config.py`: geçersiz config → hata fırlatma
- [ ] `test_protocols.py`: interface sözleşme testleri
- [ ] pytest yeşil, ruff temiz

### Sprint 3 — Veri Omurgası + Transforms
- [ ] 4 katmanlı dizin: raw/clean/adjusted/features
- [ ] Partition: `layer/market/timeframe/symbol=X/year=Y/part.parquet`
- [ ] Her dosyada `_metadata.json` (source, checksum, lineage)
- [ ] Schema contract (PyArrow schema her katmanda)
- [ ] Transform pipeline: raw → clean → adjusted → features
- [ ] Atomic write: temp → checksum → rename

### Sprint 4 — BIST Trading Calendar
- [ ] İşlem günleri, tatiller, yarım günler
- [ ] Müzayede dönemleri
- [ ] Timezone: `Europe/Istanbul` → UTC normalize
- [ ] `is_trading_day()`, `next_trading_day()`, `trading_days_between()`
- [ ] Seans dışı işlem yasağı
- [ ] Validator ve fetcher'a entegre

### Sprint 5 — Core Domain Nesneleri
- [ ] `Order`: market, limit, stop, stop-loss, take-profit
- [ ] `Fill`: fill_price, slippage, timestamp, partial_fill
- [ ] `Position`: quantity, entry_price, unrealized_pnl
- [ ] `Portfolio`: cash, positions, total_equity, exposure
- [ ] `Clock`: current_bar, warm_up_complete, session_active
- [ ] Invariant: `cash + sum(position_values) == total_equity` her barda

### Sprint 6 — Execution Spec + Minimal Motor
- [ ] Signal timing: bar[t].close → sinyal, bar[t+1].open → execute
- [ ] Intrabar ambiguity: conservative fill
- [ ] Fill policy: full fill, no fill (limit dışı)
- [ ] Cost model: `FixedBPS → SpreadPlusBPS → ParticipationRate`
- [ ] Warm-up bars standardı (configurable, varsayılan 200)
- [ ] Assumptions registry: her koşuya snapshot
- [ ] **Tek sembol, long-only, market order ile çalışan motor**
- [ ] Audit trail: `signal → order → fill → position → pnl`
- [ ] Anti-leakage: `feature_ts ≤ decision_ts < execution_ts`
- [ ] Golden fixture ile elle hesaplanmış sonuç eşleşmesi
- [ ] Buy & Hold baseline

### Sprint 7 — Run Registry + Raporlama
- [ ] `artifacts/runs/<run_id>/` yapısı
- [ ] Config snapshot + git hash + python versions + data checksum + seed
- [ ] `run_registry.duckdb`
- [ ] Equity curve, drawdown, aylık heatmap, trade tablosu
- [ ] Orders + fills + trades ayrı Parquet'ler
- [ ] Gross vs net ayrımı, benchmark kıyası
- [ ] HTML rapor (Plotly + Jinja2)

### Sprint 8 — Optimizasyon + Governance
- [ ] Grid search + walk-forward + Optuna
- [ ] Out-of-sample, parameter stability, cost sensitivity
- [ ] Search budget, seed kontrolü, erken durdurma
- [ ] Parameter clustering
- [ ] Process pool ile paralel koşu

### Sprint 9 — İleri Seviye Motor
- [ ] Feature cache (checksum + params → disk cache)
- [ ] Universe selection (point-in-time membership)
- [ ] Portfolio constructor (exposure caps, correlation-aware)
- [ ] Transaction cost model hierarchy
- [ ] Multi-symbol backtest
- [ ] Instrument model: EquityInstrument, FuturesInstrument
- [ ] CLI (Typer)

### ─── MOTOR BİTTİ, UI BAŞLAR ───

### Sprint 10 — Streamlit MVP
> Detay: `arayuz.md`

- [ ] Dashboard, Data Station, Strategy Builder
- [ ] Backtest Lab (Plotly equity/drawdown/heatmap)
- [ ] Run Compare, Trade Inspector
- [ ] Matrix tarama tablosu (basit)
- [ ] Backtest arka planda çalışsın (thread)

### Sprint 11 — Matrix Terminal (React Faz B)
- [ ] FastAPI backend API
- [ ] React + lightweight-charts + AG Grid
- [ ] Çoklu grafik, keyboard shortcuts, WebSocket
- [ ] Background job queue (Celery/RQ)
- [ ] Aktif matrix ekranı (snapshot tablodan beslenme)
- [ ] Paper trading bridge → canlı trading

---

## ❌ Kasıtlı Ertelenenler

| Ne | Neden |
|:--|:--|
| Order book simülasyonu | Overengineering |
| Mikrosaniye execution | HFT değiliz |
| Distributed compute | Apple Silicon tek makine yeterli |
| Tam serbest visual strategy builder | Çok karmaşık; şablon parametreleri yeterli |
| Canlı streaming (WebSocket fiyat) | Broker API entegrasyonu sonra |

---

## 🔧 Hedef Dosya Haritası

```
quant_engine/
├── core/                          # SAF DOMAIN — dış bağımlılık YOK
│   ├── protocols.py               # DataProvider, StorageBackend, Strategy, vb.
│   ├── instrument.py              # EquityInstrument, FuturesInstrument
│   ├── order.py                   # MarketOrder, LimitOrder, StopOrder
│   ├── fill.py                    # Fill, PartialFill
│   ├── portfolio.py               # Portfolio, Position, Cash
│   └── clock.py                   # TradingClock, SessionState
│
├── config/                        # Pydantic + TOML
│   └── config_manager.py
│
├── data/
│   ├── providers/                 # Dış dünya ile temas noktası
│   │   ├── base.py                # DataProvider protocol impl
│   │   ├── yfinance_provider.py   # ← eski fetcher.py
│   │   └── (matriks_provider.py)  # Gelecekte
│   ├── storage/
│   │   ├── parquet_backend.py     # ← eski storage_manager.py
│   │   └── metadata.py           # _metadata.json yönetimi
│   ├── validation/
│   │   ├── schema.py              # PyArrow schema contract
│   │   ├── quality.py             # ← eski data_validator.py
│   │   └── calendar.py           # BIST trading calendar
│   └── transforms/
│       ├── cleaner.py             # raw → clean
│       ├── adjuster.py            # clean → adjusted
│       └── feature_builder.py     # adjusted → features
│
├── strategy/
│   ├── base.py                    # Strategy protocol impl
│   ├── indicators.py
│   ├── feature_cache.py
│   ├── universe_filter.py
│   ├── registry.py                # Strateji kaydı/keşfi
│   └── examples/
│       ├── sma_crossover.py
│       ├── rsi_reversal.py
│       └── buy_and_hold.py        # Baseline
│
├── backtest/
│   ├── engine.py                  # Ana orkestratör
│   ├── execution.py               # ExecutionModel impl
│   ├── cost_model.py              # FixedBPS, SpreadPlusBPS, Participation
│   ├── portfolio_tracker.py       # Pozisyon, nakit, equity takibi
│   ├── audit.py                   # signal→order→fill→position→pnl
│   └── metrics.py                 # Sharpe, Sortino, MaxDD, vb.
│
├── research/
│   ├── optimizer.py               # Grid, Optuna, walk-forward
│   ├── walk_forward.py
│   └── run_registry.py            # Run kayıt ve karşılaştırma
│
├── reporting/
│   ├── html_report.py             # Jinja2 + Plotly
│   └── charts.py                  # Equity, drawdown, heatmap
│
├── app/                           # UI — motor bilmez, motor da onu bilmez
│   ├── api/                       # FastAPI endpoints
│   ├── ui_streamlit/              # Streamlit MVP
│   └── ui_react/                  # Matrix terminal
│
├── cli/                           # Typer CLI
│
└── tests/
    ├── unit/
    ├── integration/
    └── golden/                    # Elle doğrulanmış fixture'lar
```

**Bağımlılık akışı (TEK YÖNLÜ):**
```
core ← data ← strategy ← backtest ← research ← reporting ← app/cli
  ↑                                                            ↓
  └──────────── ASLA GERİ BAĞIMLILIK YOK ──────────────────────┘
```

Core hiçbir şeyi import etmez. App her şeyi import edebilir. Ortadaki katmanlar sadece solundakileri bilir.
