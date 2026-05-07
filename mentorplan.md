# PiyasaPilot — Mentor Plan

> **Bu dosyayı ilk oku.** Yeni oturum, yeni Claude, yeni agent — hepsi önce buraya bakar.
> Tarih: 2026-05-06 · Branch: `codex/financials-ui-api-v1`

---

## 1. Projenin Kimliği

**PiyasaPilot**, TradingView benzeri, tamamen kendi yazdığımız bir algoritmik trading terminali.

- Kullanıcı: Enes (bireysel geliştirici, trader)
- Amaç: Strateji fikri → kural → backtest → optimizasyon → paper robot zincirini tek ekranda yönetmek
- Gerçek emir gönderimi kapsam **dışı** — sadece paper trading
- Tavsiye üretmez, analiz ve risk uyarısı üretir
- Veri: Gerçek piyasa verisi; sahte veri hiçbir zaman üretilmez

---

## 2. Teknoloji Stack

| Katman | Teknoloji | Not |
|--------|-----------|-----|
| Backend | Python 3.11, FastAPI + uvicorn | `backend/api/main.py` |
| Veri motoru (üretim) | ClickHouse 24.3 + MySQL 8 + Redis 7 | `infra/` |
| Veri motoru (dev) | SQLite + Parquet + DuckDB | fallback |
| Backtest | Python `quant_engine/backtest/engine.py` | korumalı |
| Frontend | TypeScript 5+, Vite 8, lightweight-charts v4 | `frontend/` |
| Grafik (equity) | Chart.js | StrategyPanel'de |
| Test | pytest (Python), Playwright (e2e) | `tests/` |
| Containerization | Docker + Docker Compose | `infra/` + `docker/` |
| Reverse proxy | nginx alpine | `docker/nginx.conf` |
| AI ekosistemi | Claude Code (skills, agents, hooks, MCP) | `.claude/` |
| Veri sağlayıcılar | yfinance, Binance WS/REST, borsapy | `backend/workers/` |
| MCP | borsa-mcp, tradingview-mcp | `.mcp.json` |
| Bildirim | Telegram Bot, SMTP, macOS native | `backend/notifier/` |
| ML | LightGBM | hazırlık aşamasında |
| Lint/type | Ruff (Python), TSC + Vite (TS) | |

---

## 3. Klasör Yapısı (Güncel — 2026-05-06)

```
/
├── backend/                    # FastAPI gateway + tüm Python servisleri
│   ├── api/
│   │   ├── main.py             # App factory — tüm endpoint'ler burada (tek kaynak)
│   │   ├── quote_bus.py        # WebSocket fiyat fan-out
│   │   └── schemas/            # Pydantic şemalar
│   ├── config.py               # Env okuma, log konfigürasyonu
│   ├── env_validator.py        # Zorunlu env kontrolü
│   ├── data/
│   │   ├── cache.py            # OHLCVCache (SQLite cache-aside)
│   │   ├── historical_store.py # Parquet cold read
│   │   ├── spike_filter.py     # IQR + hacim tabanlı spike filter
│   │   ├── symbols.py          # Sembol listeleri
│   │   ├── ingest/             # ClickHouse/MySQL ingest, retention, derive
│   │   └── repositories/       # DB soyutlamaları (5 dosya)
│   ├── mali_analiz/            # Mali Analiz API + cache
│   ├── middleware/
│   │   └── api_key_auth.py     # X-API-Key middleware
│   ├── notifier/               # Telegram + email + macOS
│   ├── paper/                  # PaperDB + PaperExecutor
│   ├── signals/                # SignalGenerator v2 + signal_bus.py
│   └── workers/                # Binance WS + Yahoo + BIST poller
│
├── frontend/                   # TypeScript SPA (eski adı: piyasapilot-v2)
│   ├── src/
│   │   ├── app.ts              # Ana giriş, tab/klavye yönetimi
│   │   ├── types.ts            # Tüm TS tip tanımları
│   │   ├── components/         # 9 UI bileşeni
│   │   ├── core/               # DataEngine, QuoteStream, vb.
│   │   ├── indicators/         # 10+ teknik indikatör
│   │   └── content/            # 57 eğitim makalesi (markdown)
│   └── package.json
│
├── quant_engine/               # Bağımsız Python backtest framework (KORUMALJ)
│   ├── backtest/engine.py      # ⛔ Dokunulmaz
│   ├── data/live_feed.py       # ⛔ Dokunulmaz
│   ├── data/providers/         # ⛔ Dokunulmaz
│   ├── research/               # Optimizasyon, heatmap
│   └── strategy/               # 9 strateji + DSL + katalog
│
├── infra/                      # Tüm Docker Compose dosyaları
│   ├── docker-compose.yml      # Dev — uygulama servisleri
│   ├── docker-compose.dev.yml  # Dev — DB servisleri (CH/MySQL/Redis)
│   ├── docker-compose.prod.yml # Production tam stack
│   ├── docker-compose.monitor.yml
│   ├── clickhouse/init/        # ClickHouse SQL şemalar
│   └── mysql/migrations/       # MySQL migration'ları (001–005)
│
├── docker/                     # Dockerfile'lar + nginx + izleme
│   ├── Dockerfile.api
│   ├── Dockerfile.workers
│   ├── Dockerfile.notifier
│   ├── Dockerfile.frontend
│   ├── nginx.conf
│   └── grafana/
│
├── scripts/                    # Yardımcı ve denetim scriptleri
│   ├── live_server.py          # uvicorn başlatıcı
│   ├── real_data_check.py      # Gerçek veri kontrol betiği
│   ├── deployment/             # Deploy denetim scriptleri
│   └── data_platform/          # Inventory, health, backfill
│
├── tests/                      # 59 dosya — unit + integration
│   ├── unit/
│   └── integration/
│
├── data/                       # Runtime veri (gitignore'da)
│   ├── bist/                   # Parquet OHLCV arşivi
│   ├── cache/                  # SQLite cache dosyaları
│   └── strategy_lab/           # Strateji SQLite
│
├── artifacts/                  # Borfin OCR/frame çıktıları (gitignore'da)
│
├── docs/                       # Teknik dokümantasyon
│   ├── DEPLOYMENT.md           # Sunucu kurulum rehberi
│   ├── MIMARI.md
│   ├── VERI_MIMARISI.md
│   ├── VERI_KATALOGU.md
│   ├── SKILL_REHBERI.md
│   ├── AGENT_REHBERI.md
│   ├── BACKFILL_RUNBOOK.md
│   ├── YAPILACAKLAR.md         # Deploy/güvenlik checklist (tümü ✅)
│   ├── YAPILANLAR.md           # Mimari envanter + sprint özeti
│   ├── matriks.md              # Matriks platform doküman özeti
│   ├── planning/               # Aktif plan dosyaları (7 dosya)
│   ├── archive/                # Tarihsel snapshot'lar
│   └── wiki/                   # Obsidian uyumlu proje wiki
│
├── .claude/                    # Claude Code ekosistemi
│   ├── skills/                 # 20+ skill
│   ├── agents/                 # 12 sub-agent
│   ├── commands/               # Slash command'lar
│   ├── hooks/                  # SessionStart, Stop, vb.
│   └── memory/                 # Kalıcı bellek
│
├── .agents/                    # OpenAI/Codex uyumlu agent tanımları
├── mentorplan.md               # Bu dosya — tek başvuru kaynağı
├── CLAUDE.md                   # Claude Code proje talimatları
├── AGENTS.md                   # Agent rehberi
├── README.md                   # Proje tanıtımı
├── Makefile                    # Tüm kısayol komutları
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## 4. Şu Anki Durum (2026-05-06)

### 4.1 Tamamlananlar

| Alan | Durum |
|------|-------|
| FastAPI gateway (tüm endpoint'ler) | ✅ |
| SQLite + Parquet cache zinciri | ✅ |
| Redis → ClickHouse → SQLite fallback | ✅ |
| Binance WS + Yahoo + BIST worker'ları | ✅ |
| SignalGenerator v2 (konsensüs, 8 kural tipi) | ✅ |
| TypeScript SPA — 9 bileşen, 6 core modül | ✅ |
| Grafik Lab (G1–G10: indikatörler, çizim, Fibonacci, multi-chart) | ✅ |
| Backtest Lab (B1–B13: WFA, Monte Carlo, optimizer, tarayıcı, pack) | ✅ |
| Paper Trading (PaperDB, PaperExecutor, PortfolioPanel) | ✅ |
| Eğitimler Paneli (57 makale, arama, köprüler) | ✅ |
| Mali Analiz — metadata/API/UI v1 (boş kontratlar) | ✅ |
| Docker Compose (dev + prod + monitor) | ✅ |
| TLS/HTTPS şablonu + certbot | ✅ |
| CORS, rate limiting, WS auth, API_KEY zorunluluk | ✅ |
| nginx güvenlik header'ları | ✅ |
| Telegram + email + macOS bildirim | ✅ |
| 20 skill, 12 agent, 4 hook, MCP entegrasyonu | ✅ |
| ClickHouse/MySQL/Redis infra (SQL şemalar, compose) | ✅ |
| MySQL migration 001–005 | ✅ |
| Backup otomasyonu (`make backup-now`) | ✅ |
| Borfin OCR (9 kurs, 469 video) | ✅ |
| Production package temizliği | ✅ |

### 4.2 Açık İşler (Öncelik Sırasıyla)

| # | Alan | Kalan İş | Dosya |
|---|------|-----------|-------|
| 1 | **Mali Analiz** | KAP gerçek provider, finansal tablo store, oran motoru | `backend/mali_analiz/` |
| 2 | **Veri Platformu** | ClickHouse/MySQL API bağlantısı (infra hazır, backend bağlanmadı) | `backend/data/repositories/` |
| 3 | **VIOP** | Vadeli veri modeli + kontrat rollover mantığı | `infra/clickhouse/` |
| 4 | **Eğitim köprüleri** | Formasyon/Fibonacci yazılarından çizim aracına köprü | `frontend/src/content/` |
| 5 | **Borfin OCR** | Kalan 17 kurs (356 video) — özellikle mali analiz ve opsiyon | `artifacts/` |
| 6 | **Production deploy** | Gerçek domain, TLS, sunucu kurulumu | `docs/DEPLOYMENT.md` |
| 7 | **LightGBM** | 3 ay cache birikmesi bekleniyor, sonra ML hazırlığı | `scripts/retrain_lightgbm.py` |

---

## 5. Sıradaki Fazlar (Yürütme Sırası)

### Faz A — Veri Platformu API Bağlantısı (en kritik)

**Neden:** İnfra hazır (ClickHouse şemalar, MySQL migration'lar, Redis compose), ama `backend/api/main.py` hâlâ SQLite cache kullanıyor. Repository katmanı var ama main.py'e bağlanmamış.

**Yapılacaklar:**
1. `backend/data/repositories/market_data_facade.py` → `main.py` lifespan'ine bağla
2. `/api/v2/candles` endpoint'ini facade üzerinden oku (Redis → ClickHouse → SQLite)
3. ClickHouse + MySQL + Redis bağlantı başlatma/kapatma lifespan'e ekle
4. `make data-inventory` ile envanter raporu al
5. `STRICT_ENV_VALIDATION=1` ile test et

**Kabul kapısı:** `make test` yeşil + `/api/v2/candles` gerçek ClickHouse/Redis'ten okuyor.

---

### Faz B — Mali Analiz Gerçek Veri

**Neden:** UI/API iskeleti hazır (metadata-only v1), ama finansal tablolar boş dönüyor.

**Yapılacaklar:**
1. KAP web scraper / provider implementasyonu (`backend/mali_analiz/service.py`)
2. Finansal tablo normalize store → MySQL `005_financial_analysis` tablosuna yaz
3. Oran motoru: F/K, PD/DD, ROE, brüt marj, net borç/EBITDA
4. `MaliAnalizPanel.ts`'i gerçek veriye bağla
5. BIST 30 listesini merkezi sembol metadata'sından üret (statik liste değil)

**Kabul kapısı:** 5 BIST 30 hissesi için gerçek bilanço gösteriyor.

---

### Faz C — VIOP Veri Modeli

**Neden:** BIST hisse sistemi çalışıyor; VIOP için ayrı kontrat ve rollover mantığı gerekiyor.

**Yapılacaklar:**
1. ClickHouse'a VIOP kontrat şeması ekle
2. Kontrat rollover mantığı (yakın vade → uzak vade geçişi)
3. `backend/data/symbols.py`'a VIOP sembol listesi ekle
4. Backfill: VIOP için 10 yıllık 1m data hedefi

---

### Faz D — Production Deploy

**Neden:** Docker compose hazır, TLS şablonu var, ama gerçek sunucuya çıkılmadı.

**Yapılacaklar:**
1. VPS / cloud sunucu seç ve docker kur
2. Domain + certbot (`sudo certbot certonly --standalone -d domain.com`)
3. `.env.production` doldur
4. `docker compose -f infra/docker-compose.prod.yml up -d`
5. Backup cron kur (`make install-backup-cron`)
6. `make prod-health` ile doğrula

**Referans:** `docs/DEPLOYMENT.md`

---

### Faz E — LightGBM Sinyal Sınıflandırması

**Neden:** Cache henüz yeterli değil. 3+ ay backfill birikmesi bekleniyor.

**Koşul:** `scripts/ml_readiness.py` yeşil çıkmalı (en az 3 ay 1m veri mevcut).

---

## 6. Mimari Kararlar (Değiştirilemez)

| Karar | Gerekçe |
|-------|---------|
| Backtest motoru tek kaynak: `quant_engine/backtest/engine.py` | Lookahead-free garantisi; tekrar yazılmaz |
| TS sadece görüntüler, hesaplamaz | Backtest sonuçları Python'dan gelir; frontend sıfırdan hesaplanamaz |
| Sahte veri yasak | Sahte sinyal/backtest/analiz üretilmez; provider boş dönerse boş gösterilir |
| Günlükten dakika veri türetme yasak | Küçük timeframe'den büyük türetilir, tersi değil |
| Borfin artifact'leri production image'a girmez | Telif + boyut riski |
| Al/sat tavsiyesi üretilmez | Analiz ve risk uyarısı üretilir |
| Gerçek emir gönderimi kapsam dışı | Sadece paper trading |
| ClickHouse = OHLCV ana deposu | MySQL = metadata; Redis = sıcak cache |

---

## 7. Dokunulmaz Dosyalar

Aşağıdaki dosyalar Enes açıkça izin vermeden değiştirilmez:

```
quant_engine/backtest/engine.py
quant_engine/data/live_feed.py
quant_engine/data/providers/binance_provider.py
quant_engine/data/providers/yfinance_provider.py
```

Bu dosyalara dair herhangi bir değişiklik isteği için: önce plan yaz, Enes onayı ver, sonra uygula.

---

## 8. Claude ile Çalışma Kuralları

### 8.1 Her Oturum Başında

1. Bu dosyayı oku (`mentorplan.md`)
2. `git status --short --branch` çalıştır
3. Hook raporu zaten gösterildi — servis durumu ve plan yüzdesi orada
4. Max 3 dosya oku → plan yaz → Enes onayını bekle
5. Kod yazmaya başlamadan önce onay al

### 8.2 Kod Değişikliği Standartları

- Commit yazmadan önce Enes'ten onay iste
- Her commit tek konuya ait olsun
- `artifacts/`, `data/`, `*.sqlite3`, `.env.production` asla commit edilmez
- Test olmadan backend değişikliği yapılmaz: `python -m pytest <hedef> -q`
- Frontend değişikliği sonrası: `cd frontend && npm run typecheck && npm run build`

### 8.3 Soru Sormak Yerine Karar Ver

- Plan yazarken seçenekler sunma — bir tavsiye ver, gerekçesini söyle
- "Evet, ilerleyelim" aldıktan sonra dur sormadan uygula
- Belirsizlik varsa → en dar kapsam al, sonra genişlet

### 8.4 Model Kuralı

- Varsayılan: **Sonnet**
- Opus/extended thinking: Enes açıkça isterse

---

## 9. Skill ve Agent Haritası

### Hızlı Referans — En Çok Kullanılanlar

| Komut / Skill | Ne Yapar |
|---------------|----------|
| `/durum` | Tüm servislerin anlık durumu |
| `/devam` | Önceki oturumdan devam et |
| `/backtest` | Backtest çalıştır ve raporla |
| `/sinyal THYAO` | Sembol sinyal raporu |
| `/strateji-yeni` | Yeni strateji önerisi (quant-researcher agent) |
| `health-check` skill | API, DB, servis sağlık raporu |
| `morning-briefing` skill | Sabah piyasa brifing |
| `risk-manager` skill | Risk değerlendirme |
| `data-inventory-check` skill | BIST/VIOP sembol-timeframe kapsamı |
| `deployment-readiness-check` skill | Canlıya çıkış hazırlık kontrolü |
| `session-recap` skill | Oturum özeti |

### Agent Listesi

| Agent | Görev |
|-------|-------|
| `backend-builder` | FastAPI endpoint, repository, servis geliştirme |
| `frontend-builder` | TS bileşen, DataEngine, WS entegrasyonu |
| `quant-researcher` | Strateji fikri, kural tasarımı, backtest analizi |
| `data-architect` | DB şema, migration, ClickHouse query optimizasyonu |
| `devops-engineer` | Docker, nginx, deploy, backup |
| `data-platform-mentor` | Veri kalitesi, retention, inventory danışmanlığı |
| `code-reviewer` | PR ve kod incelemesi |
| `release-janitor` | Temizlik, versiyon, artifact denetimi |

---

## 10. Makefile Kısayolları

```bash
make up                    # Docker ile servisleri başlat
make dev                   # Yerel backend (uvicorn --reload)
make dev-frontend          # Yerel frontend (vite dev)
make test                  # Python pytest (hızlı)
make test-full             # Python pytest (detaylı)
make lint                  # TSC + vite build
make e2e                   # Playwright e2e
make health                # /api/health çıktısı
make backup-now            # Manuel yedek al
make data-inventory        # Veri envanter senkronizasyonu
make deploy-check          # Canlıya çıkış hazırlık kontrolü
make prod-health           # Production sağlık kontrolü
make borfin-integration-check
make production-package-check
make repo-cleanup-report
```

---

## 11. Veri Kapsamı

| Piyasa | Sembol Sayısı | Kaynak | Durum |
|--------|:------------:|--------|-------|
| BIST hisse | 98/100 | yfinance `.IS` / borsapy | Aktif |
| BIST endeks | 5 | yfinance | Aktif |
| Kripto | 10 parite | Binance WS/REST | Aktif |
| ABD hisse | 20 | yfinance | Aktif |
| Forex | 5 parite | yfinance | Aktif |
| Emtia | 6 | yfinance | Aktif |
| VIOP | — | Planlanıyor | Faz C |

Toplam: ~130 sembol aktif cache

---

## 12. Kabul Kapıları (Her Alan İçin)

### Backend değişikliği
- `python -m pytest <hedef> -q` yeşil
- `python3 -m py_compile backend/api/main.py` temiz
- Yeni endpoint varsa schema + test birlikte gelir

### Frontend değişikliği
- `cd frontend && npm run typecheck` yeşil
- `cd frontend && npm run build` başarılı
- Değişiklik WS ya da API bağlantısını kırıyorsa Playwright testi gerekir

### Veri platformu değişikliği
- `data-inventory-check` yeşil
- `timeframe-derivation-check` yeşil (küçük → büyük, tersi değil)
- `data-retention-guardian` yeşil (retention policy ihlali yok)

### Production değişikliği
- `production-package-check` temiz (artifact/OCR image'a girmiyor)
- `borfin-integration-check` temiz
- `deployment-readiness-check` yeşil

### Eğitim içeriği
- Borfin'den birebir kopya yok
- `source_confidence` ve `source_method` frontmatter alanı var

---

## 13. Sık Karşılaşılan Durumlar

**"Servisleri başlatamıyorum"**
→ `cd infra && docker compose -f docker-compose.dev.yml up -d` ile DB'leri başlat, sonra `make dev`

**"ClickHouse bağlantı hatası"**
→ `docker compose -f infra/docker-compose.dev.yml ps` ile healthcheck'e bak; port 8124 (dev) veya 8123 (prod)

**"Frontend değişikliklerim görünmüyor"**
→ `cd frontend && npm run build` çalıştır; nginx `/dist` klasörünü sunuyor

**"Backtest sonucu garip"**
→ `quant_engine/backtest/engine.py`'e dokunulmadı mı kontrol et; spike filter'ı çalıştır

**"Sinyal üretilmiyor"**
→ `is_real=true` ve güvenli `status` kapısı kontrol et; `backend/signals/generator.py`

**"Production'a çıkmak istiyorum"**
→ `docs/DEPLOYMENT.md` + Faz D (bu dosyanın bölüm 5)

---

*Bu dosya her büyük karar veya faz tamamlandığında güncellenir.*
*Son güncelleme: 2026-05-06 — Klasör temizliği sonrası ilk versiyon.*
