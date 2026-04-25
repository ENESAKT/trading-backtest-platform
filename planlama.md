# Quant Engine — Ana Planlama Dokümanı (v2 — Revize)

## 📊 Proje İlerleme Tablosu

| # | Modül / Görev | Durum | İlerleme |
|:--|:---|:---:|:---:|
| 1 | Proje Scaffold & Sanal Ortam | ✅ | %100 |
| 2 | Config Sistemi (Pydantic+TOML) | ✅ | %100 |
| 3 | Data Pipeline — Fetcher (ilk versiyon) | ⚠️ Bug var | %70 |
| 4 | Data Pipeline — Storage Manager (ilk versiyon) | ⚠️ Bug var | %70 |
| 5 | Data Pipeline — Data Validator | ✅ | %100 |
| 6 | Data Pipeline — Orchestrator | ✅ | %100 |
| 7 | Pip Bağımlılık Kurulumu | ⏳ İnternet gerekli | %0 |
| 8 | **Bug Düzeltmeleri (4 adet)** | 📋 | %0 |
| 9 | **Test Altyapısı (pytest + golden fixture)** | 📋 | %0 |
| 10 | **Veri Omurgası (raw/clean/adjusted/features)** | 📋 | %0 |
| 11 | **BIST Trading Calendar** | 📋 | %0 |
| 12 | **Execution Semantics Spec** | 📋 | %0 |
| 13 | **Minimal Backtest Motoru (tek sembol, long-only)** | 📋 | %0 |
| 14 | **Run Registry & Experiment Tracking** | 📋 | %0 |
| 15 | **Raporlama (equity, drawdown, benchmark)** | 📋 | %0 |
| 16 | **Optimizasyon + Research Governance** | 📋 | %0 |
| 17 | İndikatör + Feature Cache | 📋 | %0 |
| 18 | Universe Selection | 📋 | %0 |
| 19 | Portfolio Constructor & Risk Budget | 📋 | %0 |
| 20 | Anti-Leakage Guardrails | 📋 | %0 |
| 21 | Transaction Cost Model Hierarchy | 📋 | %0 |
| 22 | Instrument Model (Equity + Futures) | 📋 | %0 |
| 23 | VİOP Margin Engine & Rollover | 📋 | %0 |
| 24 | Invariant & Regression Tests | 📋 | %0 |
| 25 | CLI (Typer) | 📋 | %0 |
| 26 | UI — Streamlit MVP | 📋 | %0 |
| 27 | Paper Trading Bridge | 📋 | %0 |
| 28 | Canlı Trading (Broker + Redis) | 📋 | %0 |

**Toplam İlerleme: ~%12 (temel scaffold hazır, bug'lar ve test eksik)**

---

## 🐛 Bilinen Bug'lar (Acil Düzeltilecek)

Mevcut kodda tespit edilen 4 kritik sorun:

### BUG-1: Append sırasında tüm Parquet okunuyor
**Dosya:** `storage_manager.py` — `write_symbol_data()` metodu  
**Sorun:** Append modunda mevcut Parquet dosyasının tamamını RAM'e okuyup, yeni veriyle birleştirip, hepsini tekrar yazıyor. 100K+ satırlık dosyalarda gereksiz yavaş.  
**Çözüm:** Yıl/sembol bazlı partition yapısı: `data/clean/bist/THYAO/2024.parquet`. Append sadece ilgili yıl dosyasına dokunur.

### BUG-2: fetch_watchlist() sıralı çalışıyor
**Dosya:** `fetcher.py` — `fetch_watchlist()` metodu  
**Sorun:** Config'te `max_workers=4` tanımlı ama kod sıralı `for` döngüsü ile tek tek çekiyor. 30 hisse × 3 saniye = 90 saniye.  
**Çözüm:** `concurrent.futures.ThreadPoolExecutor` ile paralel fetch, veya `yf.download(tickers=list, threads=True)` bulk akışı.

### BUG-3: Polars planlandı ama kod %100 Pandas
**Dosya:** Tüm pipeline  
**Sorun:** "Polars birincil kütüphane" dedik ama tek satır Polars kodu yok. Her şey `pd.DataFrame` döndürüyor.  
**Çözüm:** Storage okuma katmanında Polars LazyFrame, feature hesaplamada Polars expression API. Pandas sadece yfinance çıktısında kalacak.

### BUG-4: Parquet yazımı atomic değil
**Dosya:** `storage_manager.py` — `write_symbol_data()`  
**Sorun:** Yazma sırasında işlem kesilirse bozuk Parquet dosyası kalır, veri kaybı olur.  
**Çözüm:** Temp dosyaya yaz → `os.rename()` ile atomic taşı. Rename başarısız olursa temp silinir, orijinal bozulmaz.

---

## SPRINT 1 — Çalıştırılabilir Ortam & Bug Düzeltme

> Hedef: Kodu çalışır hale getir, bug'ları düzelt, testlerle doğrula.

### 1.1 Bağımlılık Kurulumu
- [ ] `pip install -r requirements.txt`
- [ ] `python demo.py --symbol THYAO` ile smoke test

### 1.2 Bug Düzeltmeleri
- [ ] BUG-1: Partition yapısına geç (yıl/sembol/timeframe)
- [ ] BUG-2: Paralel fetch (ThreadPoolExecutor veya bulk yf.download)
- [ ] BUG-3: Storage okuma katmanını Polars'a taşı
- [ ] BUG-4: Atomic Parquet yazımı (temp → rename)

### 1.3 Geliştirici Altyapısı
- [ ] `pre-commit` config: ruff + black + mypy
- [ ] pytest yapısı: `tests/unit/`, `tests/integration/`, `tests/fixtures/`
- [ ] 5-10 satırlık golden fixture CSV (elle doğrulanmış OHLCV)
- [ ] `test_storage.py`: fixture'dan yaz → oku → karşılaştır
- [ ] `test_validator.py`: bilinen hatalı veri → hata tespit kontrolü

---

## SPRINT 2 — Veri Omurgası

> Hedef: Verinin nereden geldiği, ne kadar temizlendiği, hangi düzeltmelerin uygulandığı her zaman izlenebilir olmalı.

### 2.1 Katmanlı Veri Yapısı
```
data/
├── raw/bist/THYAO/2024.parquet      # Kaynaktan geldiği gibi, dokunulmaz
├── clean/bist/THYAO/2024.parquet    # Tip, timezone, duplicate, NaN temiz
├── adjusted/bist/THYAO/2024.parquet # Split, temettü, bedelsiz düzeltilmiş
└── features/bist/THYAO/2024.parquet # İndikatörler eklenmiş
```

### 2.2 Metadata & Lineage
- [ ] Her Parquet dosyası yanında `_metadata.json`:
  ```json
  {
    "source": "yfinance",
    "ingest_time": "2026-04-24T19:00:00Z",
    "schema_version": "1.0",
    "row_count": 245,
    "checksum_sha256": "a1b2c3...",
    "transform_from": "raw/bist/THYAO/2024.parquet",
    "transform_date": "2026-04-24T19:01:00Z"
  }
  ```
- [ ] Schema contract: PyArrow şeması her katman için tanımlı ve doğrulanmış
- [ ] Her transform adımı lineage zincirinde kayıtlı (raw → clean → adjusted → features)

---

## SPRINT 3 — BIST Trading Calendar & Execution Spec

### 3.1 Trading Calendar
**Dosya:** `quant_engine/core/trading_calendar.py`

- [ ] BIST işlem günleri (tatiller hariç)
- [ ] Resmi tatiller listesi (Ramazan, Kurban, 29 Ekim, 1 Ocak vb.)
- [ ] Yarım gün seanslar
- [ ] Açılış müzayedesi (09:40-10:00) ve kapanış müzayedesi (17:50-18:00)
- [ ] Timezone: veri girişinde `Europe/Istanbul` → depolamada UTC normalize
- [ ] `is_trading_day(date)`, `next_trading_day(date)`, `trading_days_between(start, end)`
- [ ] Seans dışı işlem yasağı (backtest'te zorunlu kontrol)

### 3.2 Execution Semantics Spec
**Dosya:** `quant_engine/backtest_engine/execution_spec.py`

Kurallar:
```
SINYAL ÜRETİMİ:     Bar[t] kapanışında (close) sinyal üretilir
EMİR OLUŞTURMA:     Sinyal anında order nesnesi oluşur
EMİR DOLDURMA:      Bar[t+1] açılışında (open) execute edilir
KAYMA (SLIPPAGE):    open ± slippage_bps
KOMİSYON:           fill_price × quantity × commission_rate
WARM-UP:             İlk N bar sinyal üretmez (varsayılan: 200)
```

- [ ] **Signal → Execution Timing:** `signal_bar.close → next_bar.open ± slippage`
- [ ] **Intrabar Ambiguity:** Aynı barda stop ve target tetiklenirse → kötü senaryo (conservative fill)
- [ ] **Fill Policy:** Varsayılan full fill. Limit order bar range dışındaysa dolmaz.
- [ ] **Order Types:**
  - `MarketOrder` → next bar open
  - `LimitOrder` → bar.low ≤ limit ≤ bar.high ise dolar
  - `StopOrder` → stop kırılınca market'e döner
- [ ] **Assumptions Registry:** Her koşuya snapshot yazılır (slippage model, fee model, fill model, warm-up bars)

---

## SPRINT 4 — Minimal Backtest Motoru

> Hedef: Tek sembol, long-only, market order ile güvenilir sonuç üreten en basit motor.

### 4.1 Motor Bileşenleri
- [ ] `engine.py` — ana orkestratör
- [ ] Adjusted katmandan veri yükle
- [ ] Strateji sinyali üret (basit SMA crossover)
- [ ] Execution spec'e göre emir doldur
- [ ] Komisyon ve slippage uygula
- [ ] Equity curve hesapla
- [ ] `cash + positions_value = total_equity` (her barda invariant check)

### 4.2 Invariant Testler (Motor Doğrulama)
- [ ] Trade yoksa equity sabit kalmalı
- [ ] `cash + positions = total_equity` her adımda doğru olmalı
- [ ] Aynı sinyal iki kez işlenmemeli
- [ ] Golden fixture ile elle hesaplanmış sonuçla birebir eşleşme

### 4.3 İlk Strateji: SMA Crossover
```python
# Basit kural:
# SMA(fast) > SMA(slow) → AL sinyali
# SMA(fast) < SMA(slow) → SAT sinyali
```
- [ ] `base_strategy.py` — abstract sınıf
- [ ] `examples/sma_crossover.py` — ilk somut strateji
- [ ] Buy & Hold baseline ile karşılaştır

---

## SPRINT 5 — Run Registry & Raporlama

### 5.1 Experiment Tracking
```
artifacts/<run_id>/
├── config.toml           # Config snapshot
├── assumptions.json      # Execution spec snapshot
├── metrics.json          # Sharpe, Sortino, MaxDD, WinRate...
├── trades.parquet        # İşlem dökümü
├── equity_curve.parquet  # Günlük bakiye
└── report.html           # Görsel rapor
```

- [ ] `run_id` = otomatik UUID
- [ ] Git commit hash kaydı
- [ ] Python/paket versiyonları
- [ ] Input data checksum
- [ ] Random seed
- [ ] `run_registry.duckdb` — tüm koşuları sorgulayabilir tablo

### 5.2 Raporlama
- [ ] Equity curve (interaktif Plotly grafik)
- [ ] Drawdown grafiği
- [ ] Aylık getiri ısı haritası (heatmap)
- [ ] Trade tablosu (giriş/çıkış/kâr/zarar)
- [ ] Gross vs Net performans ayrımı
- [ ] Benchmark kıyası (Buy & Hold, BIST100)
- [ ] Yıl bazlı getiri tablosu
- [ ] HTML rapor çıktısı

---

## SPRINT 6 — Optimizasyon & Research Governance

### 6.1 Optimizasyon
- [ ] Grid Search — parametre taraması
- [ ] Walk-forward analiz — in-sample/out-of-sample döngüsel
- [ ] Bayesian (Optuna) — akıllı arama + erken durdurma

### 6.2 Governance Kuralları (Overfit Koruması)
- [ ] **Sadece en yüksek Sharpe'ı alma** — selection criteria:
  - Out-of-sample performans
  - Parameter stability (benzer parametreler benzer sonuç mu?)
  - Turnover cezası
  - Cost robustness (2bps/5bps/10bps'de sonuç ne olur?)
- [ ] Search budget: maks deneme sayısı + seed kontrolü
- [ ] Walk-forward aggregation: tüm fold'ların medyan performansı
- [ ] Parameter clustering: iyi sonuç tek noktada mı geniş bölgede mi?

---

## SPRINT 7+ — İleri Seviye (Sıralama Esnektir)

### İndikatör + Feature Cache
- [ ] Feature cache: aynı SMA/RSI/ATR optimizasyonda tekrar hesaplanmasın
- [ ] Parametreli isimlendirme: `sma_20`, `atr_14`, `ret_5d`
- [ ] Disk cache + versioning

### Universe Selection
- [ ] Min hacim, min fiyat, min işlem günü
- [ ] Point-in-time membership
- [ ] Günlük tekrar hesaplanabilir

### Portfolio Constructor
- [ ] Exposure caps (tek hisse max %10, sektör max %25)
- [ ] Correlation-aware sizing
- [ ] Volatility targeting
- [ ] Signal ranking mekanizması

### Anti-Leakage Guardrails
- [ ] `feature_timestamp ≤ decision_timestamp < execution_timestamp`
- [ ] Delist olmuş hisseleri veri dışında bırakma
- [ ] Warm-up bars standardı

### Transaction Cost Model
- [ ] Fixed BPS → Spread + BPS → Participation Rate Impact
- [ ] Cost sensitivity analizi

### Instrument Model & VİOP
- [ ] EquityInstrument / FuturesInstrument
- [ ] Margin engine, rollover, forced liquidation

### CLI (Typer)
- [ ] `quant fetch`, `quant backtest`, `quant optimize`, `quant report`

### UI — Streamlit MVP
- [ ] Dashboard, Data Station, Backtest Lab, Run Compare, Trade Inspector

### Paper Trading → Canlı Trading
- [ ] Shadow execution → Broker API → Redis

---

## ❌ Kasıtlı Ertelenenler

| Ne | Neden |
|:---|:---|
| Order book simülasyonu | Overengineering |
| Mikrosaniye execution | HFT değiliz |
| Distributed compute | Tek makine yeterli |
| Full React/Next.js UI | Önce Streamlit MVP |
| Glassmorphism / fütüristik efektler | Güven ve okunabilirlik önce |

---

## 🔧 Mevcut Dosya Haritası

```
/Users/enes/AgentWorkspace/Backtest/
├── ✅ .gitignore, README.md, requirements.txt, pyproject.toml
├── ✅ demo.py, ogrenilenler.md
├── ✅ planlama.md (bu dosya)
├── ✅ arayuz.md
├── ✅ config/settings.toml
├── quant_engine/
│   ├── ✅ config/config_manager.py
│   ├── ⚠️ data_pipeline/            ← BUG-1,2,3,4 burada
│   │   ├── fetcher.py               ← BUG-2,3
│   │   ├── storage_manager.py       ← BUG-1,4
│   │   ├── data_validator.py        ✅
│   │   └── pipeline.py              ✅
│   ├── 📋 core/                     ← YENİ (calendar, instruments)
│   ├── 📋 backtest_engine/          ← execution_spec, engine
│   ├── 📋 strategy/
│   ├── 📋 optimization/
│   ├── 📋 validation/
│   ├── 📋 reporting/
│   ├── 📋 live_execution/
│   └── 📋 cli/
└── 📋 tests/
```

**Semboller:** ✅ Tamamlandı | ⚠️ Bug var | 📋 Planlandı | ⏳ Bekliyor
