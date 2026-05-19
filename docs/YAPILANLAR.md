# PiyasaPilot — Yapılanlar ve Mimari Envanteri

> Tek teknik kayıt defteri. Projeyi baştan sona anlatan ve tüm yapılanları
> belgeleyen kaynak budur. Tarih: 2026-05-05

---

## 1. Teknoloji Stack

| Katman | Teknoloji | Versiyon |
|--------|-----------|----------|
| **Backend dil** | Python | 3.11 |
| **API framework** | FastAPI + uvicorn | latest |
| **ORM / async DB** | SQLAlchemy (async), aiomysql, clickhouse-driver | latest |
| **Mevcut cache DB** | SQLite (OHLCV + paper trades) | — |
| **Hedef OHLCV DB** | ClickHouse | 24.3 |
| **Hedef metadata DB** | MySQL | 8.0 |
| **Hedef cache/pub-sub** | Redis | 7 |
| **Yedek/soğuk arşiv** | Parquet + DuckDB | — |
| **Frontend dil** | TypeScript | 5+ |
| **Frontend build** | Vite | 8 |
| **Grafik (OHLCV)** | lightweight-charts | v4 |
| **Grafik (equity/scatter)** | Chart.js | latest |
| **E2E test** | Playwright | latest |
| **Python test** | pytest | latest |
| **Reverse proxy** | nginx | alpine |
| **Container** | Docker + Docker Compose | latest |
| **Bildirim** | Telegram Bot API, SMTP, macOS notify | — |
| **AI ekosistemi** | Claude Code (agents, skills, hooks, MCP) | — |
| **ML** | LightGBM | latest |
| **Veri sağlayıcı** | yfinance, Binance WS/REST, borsapy, borsa-mcp, tradingview-mcp | — |
| **Lint/type** | TSC + Ruff | — |

---

## 2. Klasör Yapısı

```
/
├── backend/                    # FastAPI gateway + tüm Python servisleri
│   ├── api/
│   │   ├── main.py             # App factory (1352 satır) — tüm endpoint'ler burada
│   │   ├── signal_bus.py       # WebSocket sinyal fan-out
│   │   └── quote_bus.py        # WebSocket fiyat fan-out
│   ├── backtest/               # Backtest runner, blueprint'ler, arşiv
│   ├── config.py               # Env okuma, mask_sensitive, log konfigürasyonu
│   ├── env_validator.py        # Zorunlu env kontrolü, STRICT_ENV_VALIDATION
│   ├── data/
│   │   ├── cache.py            # OHLCVCache (SQLite cache-aside)
│   │   ├── historical_store.py # HistoricalStore (Parquet cold read)
│   │   ├── spike_filter.py     # IQR + hacim tabanlı spike filter
│   │   ├── symbols.py          # Sembol listeleri (BIST/Kripto/FX/Emtia)
│   │   ├── ingest/             # ClickHouse/MySQL ingest, retention, derive
│   │   └── repositories/       # DB repository soyutlamaları (5 dosya)
│   ├── mali_analiz/            # Mali Analiz metadata API + cache
│   ├── middleware/
│   │   └── api_key_auth.py     # X-API-Key middleware (opsiyonel mod)
│   ├── notifier/               # Telegram + email + macOS bildirim
│   ├── paper/                  # PaperDB + PaperExecutor (sanal işlem)
│   ├── signals/                # SignalGenerator v2 (konsensüs motoru)
│   └── workers/                # Binance WS + Yahoo poller + BIST poller
├── quant_engine/               # Bağımsız Python backtest framework
│   ├── backtest/
│   │   └── engine.py           # Lookahead-free backtest motoru (korumalı dosya)
│   ├── data/
│   │   ├── live_feed.py        # LiveDataService, PaperTradingRecorder (korumalı dosya)
│   │   ├── providers/
│   │   │   ├── binance_provider.py  # korumalı dosya
│   │   │   └── yfinance_provider.py # korumalı dosya
│   │   └── models.py
│   ├── research/
│   │   └── optimization_v2.py  # Heatmap + stabil bölge optimizasyonu
│   └── strategy/               # 9 strateji + DSL + katalog + pack
├── piyasapilot-v2/             # TypeScript SPA
│   ├── src/
│   │   ├── app.ts              # Ana giriş noktası, tab/klavye yönetimi
│   │   ├── types.ts            # Tüm TS tip tanımları
│   │   ├── components/         # 9 UI bileşeni
│   │   ├── core/               # DataEngine, QuoteStream, HistoricalLoader vb.
│   │   ├── indicators/         # 10+ teknik indikatör implementasyonu
│   │   └── content/            # Eğitim markdown dosyaları
│   ├── Dockerfile              # (docker/Dockerfile.frontend'e taşındı)
│   └── package.json
├── infra/                      # Tüm Docker Compose dosyaları
│   ├── docker-compose.yml      # Geliştirme uygulama servisleri
│   ├── docker-compose.dev.yml  # Geliştirme DB servisleri (CH/MySQL/Redis)
│   ├── docker-compose.prod.yml # Production tam stack
│   └── docker-compose.monitor.yml  # Grafana + Prometheus
├── docker/                     # Tüm Dockerfile'lar + nginx + izleme konfigürasyonu
│   ├── Dockerfile.api
│   ├── Dockerfile.workers
│   ├── Dockerfile.notifier
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   ├── prometheus.yml
│   └── grafana/
├── infra/clickhouse/           # ClickHouse şema ve init SQL
│   ├── init/001_market_bars.sql
│   └── init/002_quality_events.sql
├── infra/mysql/migrations/     # MySQL migration'ları
│   ├── 001_instruments.sql
│   ├── 002_providers.sql
│   ├── 003_inventory.sql
│   └── 004_retention.sql
├── scripts/                    # Python yardımcı ve denetim scriptleri
│   ├── deployment/             # Repo/paket/Borfin denetim scriptleri
│   └── data_platform/          # Inventory, health check, backfill
├── tests/                      # 59 dosya — unit + integration
│   ├── unit/
│   └── integration/
├── docs/                       # Teknik dokümantasyon
│   ├── DEPLOYMENT.md           # Sunucu kurulum rehberi
│   ├── MIMARI.md
│   ├── VERI_MIMARISI.md
│   ├── VERI_KATALOGU.md
│   ├── SKILL_REHBERI.md
│   ├── AGENT_REHBERI.md
│   ├── BACKFILL_RUNBOOK.md
│   └── archive/                # Tarihsel snapshot'lar
├── .claude/                    # Claude Code AI ekosistemi
│   ├── skills/                 # 20 yeniden kullanılabilir skill
│   ├── agents/                 # 12 sub-agent tanımı
│   ├── commands/               # Slash command'lar
│   ├── hooks/                  # SessionStart, Stop, vb.
│   └── memory/                 # Kalıcı bellek dosyaları
├── .agents/                    # OpenAI/Codex uyumlu agent tanımları (ayrı ekosistem)
├── CLAUDE.md                   # Claude Code proje talimatları
├── AGENTS.md                   # Agent rehberi
├── YAPILANLAR.md               # Bu dosya — teknik envanter
├── docs/YAPILACAKLAR.md        # Tamamlanan çıkış/güvenlik kontrol listesi
├── Makefile                    # Kısayol komutları
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 3. Backend Modül Envanteri

### 3.1 `backend/api/main.py` — FastAPI Gateway

Uygulama kalbi. Tüm endpoint'ler tek dosyada.

| Endpoint | Yöntem | Açıklama |
|----------|--------|----------|
| `/api/health` | GET | Cache stats, worker durumu, v1/v2 mod |
| `/api/v2/candles` | GET | Redis → ClickHouse → provider/SQLite OHLCV zinciri |
| `/api/market/defaults` | GET | Varsayılan sembol/timeframe |
| `/api/market/chart` | GET | Grafik verisi (v1 uyumlu) |
| `/api/workspace` | GET/POST | Kullanıcı çalışma alanı durumu |
| `/api/backtest/run` | POST | BacktestEngine çalıştır |
| `/api/backtest/optimize` | POST | Optimizasyon + heatmap |
| `/api/backtest/scan` | POST | Multi-sembol strateji tarayıcısı |
| `/api/backtest/blueprints` | GET | Strateji blueprint listesi |
| `/api/backtest/presets` | GET | Strateji preset kataloğu |
| `/api/backtest/{id}` | GET | Arşiv sonuç getir |
| `/api/backtest/{id}` | DELETE | Arşiv kaydı sil |
| `/api/paper/signal` | POST | Paper executor tetikle |
| `/api/paper/wallets` | GET | Sanal cüzdan listesi |
| `/api/paper/portfolio` | GET | Paper PnL ve equity |
| `/api/mali-analiz/universe` | GET | Hisse evreni |
| `/api/mali-analiz/{symbol}/reports` | GET | Finansal raporlar |
| `/api/mali-analiz/{symbol}/events` | GET | KAP olayları |
| `/api/mali-analiz/{symbol}/metric-history` | GET | Metrik geçmişi |
| `/api/strategy/import` | POST | Strategy pack import |
| `/api/strategy/export/{id}` | GET | Strategy pack export |
| `/api/notifier/filters` | POST | Telegram filtre güncelleme |
| `/ws/quotes` | WS | Canlı fiyat fan-out |
| `/ws/signals` | WS | Canlı sinyal fan-out |
| `/metrics` | GET | Prometheus metrik çıktısı |

**Middleware:**
- `CORSMiddleware` — `CORS_ORIGINS` env listesi
- `APIKeyMiddleware` — `API_KEY` env varsa yalnızca `API_KEY_PROTECTED_PATHS` iç/ops yollarında `X-API-Key` header zorunlu; browser-facing `/api/*` route'ları JWT/feature gate ile korunur

**Lifespan (başlatma/kapanma):**
- `WorkerSupervisor` → BinanceKlineWorker + YahooPoller + BistStockPoller
- `SignalGenerator` başlatılır
- `OHLCVCache` ve `HistoricalStore` bağlanır

### 3.2 `backend/data/repositories/` — DB Soyutlamaları

| Dosya | Sorumlu olduğu DB | Durum |
|-------|-------------------|-------|
| `clickhouse_repository.py` | ClickHouse — OHLCV bar okuma/yazma | Yazıldı, API'ye bağlanmadı |
| `mysql_metadata_repository.py` | MySQL — sembol, provider, inventory | Yazıldı, API'ye bağlanmadı |
| `redis_market_cache.py` | Redis — son quote, kısa cache | Yazıldı, API'ye bağlanmadı |
| `legacy_cache_repository.py` | SQLite — mevcut cache-aside | Aktif, production'da |
| `market_repository.py` | Repository arayüz soyutlaması | Aktif |

### 3.3 `backend/workers/` — Veri İşçileri

| Worker | Kaynak | Görev |
|--------|--------|-------|
| `BinanceKlineWorker` | Binance WebSocket | 10 kripto kline (1m) |
| `YahooPoller` | yfinance REST | Endeks, FX, emtia (60s) |
| `BistStockPoller` | yfinance `.IS` | 98 BIST hisse (60s) |

### 3.4 `backend/signals/` — SignalGenerator v2

- 8 tip kural motoru (SMA, EMA, RSI, Bollinger, MACD, Supertrend, VWAP, hacim)
- Konsensüs sistemi: 5+ strateji → STRONG_BUY/STRONG_SELL
- Sinyal gücü 1–10 skoru
- `is_real=true` + güvenli `status` olmadan sinyal üretmez

### 3.5 `backend/paper/` — Paper Trading

- `PaperDB`: SQLite tabanlı izole cüzdan kayıtları
- `PaperExecutor`: Sinyal → sanal emir icra, risk limitleri (%10 günlük DD)
- Başlangıç bakiyesi: 10.000 TL / cüzdan

### 3.6 `backend/mali_analiz/` — Mali Analiz

- `service.py`: `FinancialAnalysisService` — KAP provider + cache + normalize store zinciri; sahte veri üretmez
- `cache.py`: `FinancialAnalysisCache` — günlük SQLite cache
- `symbols.py`: `SYMBOL_METADATA`, `normalize_symbol` — sembol normalize
- Durum: KAP provider arayüzü, MySQL store ve oran hesaplama v1 hazır

### 3.7 `backend/notifier/` — Bildirim Sistemi

- Telegram Bot (11 komut: `/yardim`, `/durum`, `/fiyat`, `/sinyal` vb.)
- Email (SMTP)
- macOS native bildirim
- Token/chat id uç noktalarda maskelenir

---

## 4. quant_engine Modül Envanteri

### 4.1 `quant_engine/backtest/engine.py`

Projenin lookahead-free backtest motoru. Tek kaynak gerçek.

### 4.2 `quant_engine/strategy/`

| Modül | İçerik |
|-------|--------|
| `catalog.py` | `list_strategy_presets()` — önayarlı strateji listesi |
| `persistence.py` | `StrategyStore`, `StrategyRecord` — SQLite kalıcılık |
| `pack.py` | `export_strategy_pack`, `import_strategy_pack` — JSON dışa/içe aktarım |
| `dsl.py` | Strateji kural DSL genişletmesi |

### 4.3 Uygulanan Stratejiler (9)

SMA Crossover, RSI Reversion, Bollinger Reversion, Buy & Hold, Donchian Breakout, MACD Divergence, Supertrend, Mean Reversion VWAP + DSL ile genişletilmiş kural motoru

### 4.4 `quant_engine/research/optimization_v2.py`

- `generate_heatmap_data()` — parametre ızgara tarama
- `find_stable_region()` — Sharpe ratio stabil bölge tespiti

---

## 5. Frontend Bileşen Envanteri

### 5.1 `piyasapilot-v2/src/app.ts` — Ana Giriş (302 satır)

Tab yönetimi, klavye kısayolları, bileşen bootstrap.

**Klavye Haritası:**
- `1` → Grafik Lab (ChartPanel)
- `2` → Strateji Lab (StrategyPanel)
- `3` → Paper Trading (PortfolioPanel)
- `4` → Tarayıcı (Screener)
- `5` → Sinyaller (SignalFeed)
- `6` → Eğitimler (EgitimlerPanel)
- `7` → Mali Analiz (MaliAnalizPanel)
- `G` → Layout döngüsü (1×1 / 1×2 / 2×1 / 2×2)
- `F` → Tam ekran

### 5.2 `src/components/` — UI Bileşenleri (9 dosya)

| Bileşen | Satır | Açıklama |
|---------|-------|----------|
| `ChartPanel.ts` | ~1200 | OHLCV grafik, indikatörler, çizim araçları, log/% ölçek |
| `StrategyPanel.ts` | 1678 | Backtest formu, sonuç, equity, WFA, Monte Carlo, optimize |
| `MultiChartLayout.ts` | ~400 | 1×1/1×2/2×1/2×2 layout, senkron kilit |
| `Sidebar.ts` | 339 | Sembol/timeframe seçici, hızlı arama |
| `SignalFeed.ts` | 491 | Gerçek zamanlı sinyal toast, Telegram durum çubuğu |
| `Screener.ts` | 231 | Multi-sembol tarayıcı v3 |
| `PortfolioPanel.ts` | ~350 | Paper trading equity, PnL, 6 metrik kartı |
| `EgitimlerPanel.ts` | ~300 | Markdown render, arama, kategori, grafik/preset köprüsü |
| `MaliAnalizPanel.ts` | ~250 | BIST hisse seçici, sekmeli UI, empty state |

### 5.3 `src/core/` — Veri Katmanı (6 dosya)

| Modül | Görev |
|-------|-------|
| `DataEngine.ts` | REST `/api/v2/candles` → OHLCV normalize |
| `QuoteStream.ts` | WS `/ws/quotes` → canlı tick fan-out |
| `HistoricalLoader.ts` | Sayfalı tarihsel veri yükleme |
| `PollingManager.ts` | Interval tabanlı yenileme yönetimi |
| `PortfolioEngine.ts` | Paper equity hesaplama |
| `AnomalyFilter.ts` | Spike ve aykırı değer filtreleme |

### 5.4 `src/indicators/` — Teknik İndikatörler (10 dosya)

SMA, EMA, MA, RSI, MACD, Bollinger, ATR, Kairi, MOST + index.ts

### 5.5 `src/content/` — Eğitim İçerikleri

57 makale — kategoriler: İndikatörler, Formasyonlar, Sistem & Backtest, VIOP & Vadeli, Psikoloji & Disiplin

---

## 6. İnfra ve Docker Envanteri

### 6.1 Compose Dosyaları

| Dosya | Ne Zaman Kullanılır |
|-------|---------------------|
| `infra/docker-compose.yml` | Geliştirme — uygulama servisleri (api, notifier, nginx, workers) |
| `infra/docker-compose.dev.yml` | Geliştirme — DB servisleri (ClickHouse, MySQL, Redis) |
| `infra/docker-compose.prod.yml` | Production — tam stack (tüm servisler + DB + backup) |
| `infra/docker-compose.monitor.yml` | İzleme — Grafana + Prometheus |

### 6.2 Dockerfile'lar (`docker/`)

| Dosya | İmaj | Temel |
|-------|------|-------|
| `docker/Dockerfile.api` | FastAPI gateway | python:3.11-slim |
| `docker/Dockerfile.workers` | Veri işçileri | python:3.11-slim |
| `docker/Dockerfile.notifier` | Telegram/email notifier | python:3.11-slim |
| `docker/Dockerfile.frontend` | SPA (multi-stage) | node:20-alpine → nginx:alpine |

### 6.3 ClickHouse Şemaları (`infra/clickhouse/init/`)

- `001_market_bars.sql` — `market_bars` tablosu: sembol, timeframe, OHLCV, kaynak, derived flag
- `002_quality_events.sql` — `data_quality_events` tablosu: spike, gap, anomali kayıtları

### 6.4 MySQL Migration'ları (`infra/mysql/migrations/`)

- `001_instruments.sql` — Sembol ve kontrat metadata
- `002_providers.sql` — Veri sağlayıcı kaydı
- `003_inventory.sql` — Sembol/timeframe envanter, ilk/son tarih, satır sayısı
- `004_retention.sql` — Retention policy kuralları

---

## 7. AI Ekosistemi Envanteri

### 7.1 `.claude/skills/` — Skill'ler (20 adet)

| Skill | Görev |
|-------|-------|
| `health-check` | API, DB, servis sağlık raporu |
| `run-backtest` | Backtest çalıştır ve raporla |
| `backtest-expert` | Backtest analiz uzmanı |
| `morning-briefing` | Sabah piyasa brifing |
| `risk-manager` | Risk değerlendirme |
| `position-sizer` | Pozisyon boyutu hesaplama |
| `paper-trade-status` | Paper trading durum raporu |
| `signal-postmortem` | Sinyal postmortem analizi |
| `scenario-analyzer` | Senaryo analizi |
| `market-news-analyst` | Piyasa haber analizi |
| `data-inventory-check` | Veri envanter kontrolü |
| `data-retention-guardian` | Retention policy koruyucusu |
| `data-architecture-auditor` | DB mimari denetim |
| `timeframe-derivation-check` | Timeframe türetme doğrulama |
| `repo-cleanup-auditor` | Repo temizlik denetimi |
| `borfin-integration-auditor` | Borfin telif uygunluk denetimi |
| `production-package-auditor` | Docker paket kontrolü |
| `deployment-readiness-check` | Canlıya çıkış hazırlık kontrolü |
| `deploy-stack` | Stack deploy |
| `session-recap` | Oturum özeti |

### 7.2 `.claude/agents/` — Sub-agent'lar (12 adet)

backend-builder, backtest-runner, code-reviewer, data-architect, data-platform-mentor, data-validator, devops-engineer, frontend-builder, quant-researcher, release-janitor, robot-executor

**Not:** `data-platform-mentor` `.agents/` altında tanımlı ama `.claude/agents/` altına da eklenmesi gerekiyor.

### 7.3 MCP Entegrasyonları (`.mcp.json`)

- `borsa-mcp` — BIST verileri, finansal oranlar, KAP, EVDS
- `tradingview-mcp` — Teknik analiz, tarayıcı, kripto piyasa

### 7.4 Hook'lar (`.claude/hooks/`)

- `SessionStart` — Servis kontrolü, plan durumu raporu
- `Stop` / `SubagentStop` — Oturum özeti
- `UserPromptSubmit` — Prompt ön işleme

---

## 8. Tamamlanan Sprint Özeti

| Sprint / Faz | Konu | Sonuç |
|---|---|---|
| Sprint 0 | Proje iskelet, CLAUDE.md, agent yapısı | Tamamlandı |
| Sprint 1 | FastAPI gateway, SQLite cache, spike filter, workers | Tamamlandı |
| Sprint 2 | TS SPA, MultiChartLayout, DataEngine, Streamlit söküldü | Tamamlandı |
| Sprint 3 | BacktestEngine API, StrategyPanel, sinyal feed | Tamamlandı |
| Sprint 4 | PaperDB, PaperExecutor, PortfolioPanel v2 | Tamamlandı |
| Sprint 5 | 8 agent, 15 skill, slash command, 4 hook | Tamamlandı |
| Sprint 6 | SignalGenerator v2 konsensüs, sinyal gücü, metadata kapısı | Tamamlandı |
| Sprint 7 | Docker Compose, Telegram bildirim, email, macOS | Tamamlandı |
| Sprint 8 | README, MIMARI.md, rehber dokümanlar | Tamamlandı |
| Sprint 9 | MCP entegrasyonu (borsa + tradingview), Playwright e2e | Tamamlandı |
| Sprint 10 | LightGBM hazırlık, stres test, provider doğrulama, Prometheus | Tamamlandı |
| Sprint 11 | Sabah brifing Claude API entegrasyonu | Tamamlandı |
| Sprint 12 | Risk skill'leri, paper operasyon, sinyal postmortem | Tamamlandı |
| Faz 0A | Veri platformu planı + ClickHouse/MySQL/Redis infra dosyaları | Tamamlandı (infra hazır, API bağlantısı yok) |
| Faz 0B | Repo temizliği, .dockerignore, production paket kontrolü | Tamamlandı |
| Faz 0C | Denetim skill'leri + deployment script'leri | Tamamlandı |
| Faz 1A (E1–E11) | Eğitimler paneli, 57 makale, arama/kategori, köprüler | Tamamlandı |
| Faz 1B (M1–M6) | Mali Analiz metadata/API/UI v1, universe sidebar | Tamamlandı |
| Faz 2 (G1–G10) | Grafik ölçek, indikatör merkezi, PnL overlay, çizim, multi-chart, şablonlar, event marker, Fibonacci | Tamamlandı |
| Faz 3 (B1–B13) | Strateji kataloğu, WFA, Monte Carlo, optimizasyon, tarayıcı, portföy lab, paper operasyon, strategy pack, lifecycle | Tamamlandı |

---

## 9. Sembol Kapsamı

| Piyasa | Sayı | Kaynak |
|--------|------|--------|
| BIST hisse | 98/100 | yfinance `.IS` / borsapy |
| BIST endeks | 5 | yfinance |
| Kripto | 10 parite | Binance WS/REST |
| ABD hisse | 20 | yfinance |
| Forex | 5 parite | yfinance |
| Emtia | 6 | yfinance |

**Toplam:** ~130 sembol aktif cache

---

## 10. Altyapı ve Dokümantasyon Yapısı (2026-05-05)

| Madde | Durum |
|-------|-------|
| Tüm Dockerfile'lar → `docker/` altında tek yerde | ✅ |
| `nginx.conf` → `docker/nginx.conf` | ✅ |
| Tüm compose dosyaları → `infra/` altında tek yerde | ✅ |
| Production compose'da DB portları internal-only (`expose`) | ✅ |
| `Dockerfile.workers`'dan `COPY data/` kaldırıldı | ✅ |
| Kök dizin MD: 20+ dosya → 5 dosya | ✅ |
| Planlama dosyaları → `docs/planning/` | ✅ |
| Tarihsel snapshot'lar → `docs/archive/` | ✅ |
| `docs/ogrenilenler.md` — sprint ders kayıtları | ✅ |
| Legacy `.streamlit/` klasörü silindi | ✅ |
| Hook'lar `YAPILACAKLAR.md` referansına güncellendi | ✅ |
| `YAPILANLAR.md` — teknik envanter | ✅ |
| `YAPILACAKLAR.md` — checkbox + ağırlıklı ilerleme tablosu | ✅ |

---

## 11. Denetim Komutları (Makefile)

```bash
make up                       # Docker ile servisleri başlat
make down                     # Durdur
make dev                      # Yerel backend (uvicorn --reload)
make dev-frontend             # Yerel frontend (vite dev)
make test                     # Python pytest (hızlı)
make test-full                # Python pytest (detaylı)
make lint                     # TSC + vite build
make e2e                      # Playwright e2e
make health                   # /api/health çıktısı
make monitor                  # Grafana + Prometheus
make repo-cleanup-report      # Repo boyut ve artifact raporu
make borfin-integration-check # Borfin telif denetimi
make production-package-check # Docker paket kontrolü
make deployment-check         # Canlıya çıkış hazırlık kontrolü
make prod-health              # Production sağlık kontrolü
make data-inventory           # Veri envanter senkronizasyonu
make derive-timeframes        # Timeframe rollup çalıştır
make retention-cleanup        # Retention politikası uygula
make backup-now               # Manuel yedek al
```

---

## 12. Güvenlik ve Deploy Hazırlığı (2026-05-05)

| Madde | Durum |
|-------|-------|
| Production CORS wildcard kaldırıldı; origin listesi `CORS_ORIGINS` env'den okunuyor | ✅ |
| `slowapi` eklendi; `/api/backtest/run` endpoint'i 30/dk limitlendi | ✅ |
| `/ws/quotes` ve `/ws/signals` API_KEY tanımlıyken `token` query param'ı istiyor | ✅ |
| `APP_ENV=production` modunda `API_KEY` zorunlu hale getirildi | ✅ |
| Production strict env validasyonu CORS, MySQL, ClickHouse ve Redis URL'lerini kontrol ediyor | ✅ |
| `docker/nginx.conf` güvenlik header'ları ve proxy header'larıyla güncellendi | ✅ |
| `docker/nginx.https.example.conf` HTTPS/TLS geçiş şablonu olarak eklendi | ✅ |
| Production nginx ayrı `docker/nginx.prod.conf` ile frontend container'ına proxy ediyor | ✅ |
| `docker/Dockerfile.frontend` yeni `frontend/` klasör yapısına göre düzeltildi | ✅ |
| `infra/docker-compose.prod.yml` certbot volume'larını ve ClickHouse backup volume'unu bağlıyor | ✅ |
| `.env.production.example` tüm production alanlarıyla eklendi; gerçek `.env.production` git dışında | ✅ |
| `make backup-now` MySQL dump + ClickHouse native backup script'ini çalıştırıyor | ✅ |
| `make env-production`, `make tls-setup`, `make install-backup-cron` eklendi | ✅ |
| Dev MySQL/Redis portları çakışmasız hale getirildi (`3307`, `6380`) | ✅ |
| Dev ClickHouse healthcheck `127.0.0.1` ile düzeltildi ve healthy doğrulandı | ✅ |
| `/api/v2/candles` Redis sıcak cache → ClickHouse → provider/SQLite fallback zinciri aldı | ✅ |
| `backend/data/repositories/market_data_facade.py` eklendi | ✅ |
| MySQL finansal analiz migration'ı `005_financial_analysis.sql` eklendi ve dev DB'de çalıştırıldı | ✅ |
| KAP uyumlu mali analiz provider arayüzü eklendi | ✅ |
| Finansal tablo normalize store repository'si eklendi | ✅ |
| Mali analiz BIST evreni 97 sembole genişletildi | ✅ |
| Borfin OCR envanteri `docs/BORFIN_OCR_ENVANTERI.md` olarak üretildi | ✅ |
| Skill kaynak kuralı dokümante edildi ve `make skill-source-check` yeşil | ✅ |

Doğrulama:
- `python3 -m py_compile backend/api/main.py backend/env_validator.py`
- `bash -n scripts/deployment/backup_now.sh`
- `docker compose -f infra/docker-compose.dev.yml config`
- Geçici `.env.production` ile `docker compose -f infra/docker-compose.prod.yml config`
- `make test`: 464 test geçti, 1 test seçilerek hariç bırakıldı
- `make lint`: TypeScript check + Vite production build geçti
- `make production-package-check`: temiz
- `make borfin-integration-check`: temiz; Borfin artifact'leri production context dışında
- `docker build --no-cache -f docker/Dockerfile.frontend .`: başarılı
- `make deployment-check`: temiz
- `make skill-source-check`: temiz
- Data platform health check: ClickHouse, MySQL ve Redis bağlantıları başarılı
