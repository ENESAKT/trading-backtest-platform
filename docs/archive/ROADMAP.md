# Yol Haritası — PiyasaPilot Trading Terminali

> Arşiv notu: Bu dosya tarihsel snapshot'tır. Güncel yürütme sırası için `genelplanlama.md`, plan index'i için `planlama.md` esas alınır.
>
> Bu doküman **ne yapıldı, ne yapılacak, sonunda ne göreceksin**'i sade Türkçeyle anlatır.
> Tick listesi (`- [x]` / `- [ ]`) için: [`planlama.md`](planlama.md). Bu dosya o planın hikâyesidir.
>
> **Tarih:** 2026-04-30 · **Durum:** Sprint 1–10 ✅ tamam · `289 passed` · TSC/Vite 0 hata · Sprint 11 planlandı.

---

## Vizyon — Tek Cümleyle

BIST + kripto + döviz + emtia için **TradingView benzeri**, **Türkçe**, tarayıcıda çalışan, **otonom paper-trading** yapan, **AI sinyal** üreten ve **hiç kapanmayan** bir trading terminali.

İki kilit fark:
1. **Sıfır dış API çıkışı** — tarayıcı `api.binance.com`'a doğrudan istek atmaz; her şey lokal Python backend'inden geçer (Türkiye geo-blok riskine karşı).
2. **Strateji-bazlı izole sandık** — her stratejinin ayrı 10.000 TL sanal cüzdanı vardır; biri yansa diğerleri etkilenmez. Audit trail her trade'i JSON log'lar.

---

## Bugünkü Durum (2026-04-29)

| Katman | Durum | Detay |
|--------|-------|-------|
| Backend gateway | ✅ Hazır | FastAPI, SQLite cache, IQR spike filter, `/api/v2/candles` cache-aside, `/api/health` |
| Worker'lar | ✅ Çalışıyor | Binance WS (10 kripto), Yahoo poller (BIST endeks + FX + emtia), BIST 30 hisse poller |
| WS fan-out | ✅ Çalışıyor | `/ws/quotes` + `/ws/signals` — canlı bar + sinyal fan-out |
| Frontend tek terminal | ✅ %100 | Sidebar 98 sembol, MultiChartLayout, fullscreen, 5 tab (chart/portfolio/strategy/screener/signals) |
| Backtest (Python API) | ✅ Hazır | `POST /api/backtest/run` — 9 strateji, equity curve, trade listesi |
| Paper trading | ✅ Hazır | SQLite, strateji-bazlı izole sandık (10.000₺), otonom executor, risk limitleri |
| AI sinyal motoru | ✅ Hazır | SignalGenerator v2 — RSI+Trend confluence, konsensüs (STRONG_BUY/SELL), metadata |
| Always-on (Docker) | ✅ Hazır | 3 Dockerfile, docker-compose.yml, nginx, Makefile |
| Bildirim | ✅ Hazır | Telegram bot, Email SMTP, macOS notification, In-app toast |
| Agent ekosistemi | ✅ Hazır | 8 sub-agent, 15 skill, 5 slash command, 4 hook |
| Telegram asistan | ✅ Hazır | Long polling listener, 11 komut, güvenlik filtresi, gizli bilgi maskeleme |
| Veri sağlayıcı router | ✅ Hazır | BIST/VİOP/kripto yönlendirme, `is_real` metadata kapısı, provider health |
| Telegram tercihleri | ✅ Hazır | API + Sinyaller tab'ında bildirim filtre kontrol paneli |

**Sprint 1–10 tamamlandı.** MCP bağlantıları, Playwright E2E, Docker restart, stres smoke, lisanslı veri köprüleri, Telegram/SMTP doğrulama kapıları ve build/test zinciri tamamlandı.

---

## Hedef Son Ürün — Kullanıcı Gözünden

Bilgisayarın açıldığında otomatik başlayan bir tarayıcı sekmesi:

**Sol panel:** 130 sembol (BIST 100, kripto, döviz, emtia) tree-accordion. Her sembolün yanında canlı fiyat + günlük %.

**Orta panel:** Mum grafiği (lightweight-charts). Üstte timeframe (1m–1w), sağ üstte ⛶ tam ekran. Indikatörler (EMA, RSI, MACD, Bollinger, ATR, VWAP). Çoklu pencere (split/grid) — aynı anda 4 farklı sembol bakabilirsin.

**Mum üstünde ▲▼ marker'lar:** Her stratejinin AL (yeşil ok yukarı) ve SAT (kırmızı ok aşağı) noktaları. Üzerine gelince tooltip: hangi strateji, hangi gerekçe, kâr/zarar.

**Sağ panel — Strateji Lab:** 8 hazır strateji (EMA cross, RSI mean-rev, BB rev, breakout, donchian, MACD div, supertrend, mean-rev VWAP). Parametreleri kaydır, "Backtest çalıştır" → **equity eğrisi** + max drawdown + win rate + sharpe + son 50 trade listesi.

**Alt panel — Sinyal Akışı:** Canlı, her bar kapanışında DecisionEngine yeni sinyal üretirse buraya düşer (sembol + AL/SAT + güç skoru + açıklama).

**Portföy sekmesi:** Her stratejinin sandığı, açık pozisyonlar, equity curve, drawdown grafiği, win rate, sharpe oranı, audit log.

**Sabah 09:00:** Telegram'ına Claude API'nin oluşturduğu BIST 100 özeti + 3 odak hisse mesajı düşer. E-postaya da gider.

**Bir şey ters giderse:** macOS bildirimi pop-up çıkar, in-app toast görünür, oncall sayılır.

---

## Sprint Yolculuğu

### Sprint 0 — İskelet ✅
Plan, CLAUDE.md, `.claude/` iskelet klasörleri, kararların kayda geçmesi.
**Sonunda gördüğün:** Yeni Claude oturumu açtığında tüm bağlam (mimari, kurallar, kararlar) otomatik yükleniyor.

### Sprint 1 — Backend Veri Gateway ✅
**Amaç:** Frontend hiçbir yerden dış API'ye doğrudan çıkmasın; tüm veri lokal cache'ten gelsin.

**Yapılanlar (PR #3, #4, #5):**
- FastAPI gateway → uvicorn launcher (port 8000)
- SQLite OHLCV cache (`bars`, `meta` tablosu, WAL mode)
- IQR + hacim ağırlıklı spike filter (dev fitilleri Winsorize'lar)
- `/api/v2/candles` cache-aside endpoint (önce cache, miss → provider)
- 3 worker daemon: Binance WS (10 kripto), Yahoo poller (15s), BIST poller (60s)
- `/ws/quotes` fan-out — worker'ların yazdığı her bar tüm tarayıcılara broadcast
- `/api/health` — cache stats + worker durumu + quote bus stats
- 277 test geçiyor

**Sonunda gördüğün:** `curl localhost:8000/api/health` → cache 8000+ bar, 35 sembol; 3 worker `running:true`. Tarayıcıda chart açılınca veriler **lokal backend'den** geliyor.

---

### Sprint 2 — Frontend Birleşimi ✅
**Amaç:** TS terminali tek ve son arayüz olsun. Streamlit kalksın.

**Yapılanlar:**
- ✅ 2.1 Market Explorer (kategori-akordeon sidebar) — zaten vardı
- ✅ 2.2 BIST 100 katalogu (98/100 sembol; PR #6 + PR #10)
- ✅ 2.3 Çoklu pencere layout — `MultiChartLayout.ts`, 4 layout modu (1×1/1×2/2×1/2×2), G kısayolu
- ✅ 2.4 Fullscreen butonu — zaten vardı, retroaktif tick
- ✅ 2.7 DataEngine → QuoteStream (PR #7); WebSocketManager.ts sökündü
- ✅ 2.7+ BUY/SELL marker'ları — `setSignals/clearSignals` pipeline
- ✅ 2.8 Streamlit söküm (PR #9)

**Kapanış notu:** StrategyPanel, Sidebar, çoklu grafik, marker pipeline ve Streamlit sökümü sonraki sprintlerle tamamlandı; bu bölümde eski açık iş kalmadı.

**Sonunda göreceğin:** Tek tarayıcı sekmesi her şeyi yapıyor. Streamlit gerek yok. Mum üstünde alım-satım okları görüyorsun.

---

### Sprint 3 — Strateji & Backtest Birleşimi ✅
**Amaç:** TS'in kendi dahili backtest kodu sökülür; tek doğruluk kaynağı **Python `BacktestEngine`** olur (lookahead-free, testli).

**Yapılanlar:**
- TS dahili backtest implementasyonu söküldü.
- `POST /api/backtest/run` endpoint Python motorunu çalıştırıyor.
- Strateji blueprint formatı tek tip hale geldi.
- `StrategyPanel` API'ye POST atıyor, **equity eğrisini Chart.js** ile çiziyor.
- Live signal feed `/ws/signals` ile fan-out yapıyor.
- `SignalFeed` paneli canlı sinyal akışını gösteriyor.
- **9 strateji**:
  1. EMA cross (50/200)
  2. RSI mean-reversion
  3. Bollinger Bands reversion
  4. Breakout detector
  5. **Donchian breakout** (yeni)
  6. **MACD divergence** (yeni)
  7. **Supertrend** (yeni)
  8. **Mean-reversion VWAP** (yeni)
  9. **LightGBM probability** (model hazırsa olasılık tabanlı)

**Sonunda göreceğin:** "Backtest çalıştır" tıklayınca → equity eğrisi grafiği + metric kartları + son 50 trade listesi + chart üstünde marker'lar. **Aynı stratejinin TS sonucu = Python sonucu** (parite testi geçer).

---

### Sprint 4 — Paper Trading & Portföy ✅
**Amaç:** Otonom alım-satım yapan ama **gerçek emir vermeyen** robot. Tam audit trail.

**Yapılanlar:**
- SQLite şeması: `paper_trades`, `paper_portfolio`, `paper_equity_curve`.
- **Strateji-bazlı izole sandık** — her stratejiye 10.000 TL sanal cüzdan.
- Canlı PnL, `PortfolioPanel` v2, equity curve, drawdown, win rate ve sharpe.
- Audit trail ve risk limitleri.

**Sonunda göreceğin:** "Strateji X'i aktif et" düğmesi. Sinyal gelirse otomatik trade kaydedilir, equity eğrisi büyür/küçülür, drawdown takip edilir, riski aştıysa cüzdan donar. **Hiçbir gerçek emir gitmez** — pure simülasyon.

---

### Sprint 5 — Agent + Skill + MCP + Hook Kurulumu
**Amaç:** Claude Code'un kendi ekosistemini projeye gömmek. Yeni Claude oturumu açıldığında **her şey hazır gelir**.

**Yapılacaklar:**
- **8 sub-agent** (`.claude/agents/*.md`):
  - `data-validator` — IQR test, OHLCV doğrulama, gap detection (Haiku)
  - `quant-researcher` — yeni strateji fikri, parametre tarama (Sonnet)
  - `backtest-runner` — `BacktestEngine` çalıştırır, sonuç raporlar (Haiku)
  - `frontend-builder` — TS/Vite/lightweight-charts (Sonnet)
  - `backend-builder` — FastAPI/SQLite/worker (Sonnet)
  - `robot-executor` — paper-trading icra (Haiku)
  - `code-reviewer` — her commit öncesi kalite gate (Sonnet)
  - `devops-engineer` — Docker Compose, healthcheck (Haiku)
- **15 skill** (`.claude/skills/`):
  - 8'i tradermonty/claude-trading-skills'ten: `backtest-expert`, `position-sizer`, `technical-analyst`, `market-news-analyst`, `signal-postmortem`, `strategy-pivot-designer`, `scenario-analyzer`, `risk-manager`
  - 7'si projeye özel: `validate-spike-filter`, `run-backtest`, `health-check`, `morning-briefing`, `paper-trade-status`, `deploy-stack`, `session-recap`
- **2 MCP**:
  - `borsa-mcp` (saidsurucu) — BIST + TEFAS + KAP haberleri + makro veri
  - `tradingview-mcp` (atilaahmettaner) — real-time crypto/stock screening
- **5 hook** (`.claude/settings.json`):
  - `SessionStart` → docker servisleri ping, son cache zamanı, planlama.md durumu
  - `UserPromptSubmit` → son `session-recap.md`'yi oto-yükle
  - `PostToolUse` (Edit/Write) → `ruff check --fix` + `npm run lint`
  - `SubagentStop` → agent çıktısını `.claude/agent-logs/` altına yaz
  - `Stop` → otomatik recap (planlama.md tick'leri güncelle, session-recap.md yaz)
- **5 slash command**:
  - `/devam` — son recap'ı yükle, kaldığın yerden başla
  - `/backtest <sembol> <strateji>` — backtest-runner agent'ını tetikle
  - `/sinyal <sembol>` — DecisionEngine + Claude API hibrit raporu
  - `/durum` — tüm servisler ping, açık paper trade'ler
  - `/strateji-yeni` — quant-researcher agent başlat

**Sonunda göreceğin:** `/devam` yazdığında Claude tüm bağlamı 2-3 saniyede yükler. `/backtest THYAO ema-cross` yazdığında 30 sn'de equity raporu çıkar. Sabah 9'da otomatik brifing maili gelir.

---

### Sprint 6 — AI Sinyal Motoru (Hibrit)
**Amaç:** Mevcut kural tabanlı motor + Claude API ile sabah brifingi + ileride ML.

**Yapılacaklar:**
- Kural motoru güçlendir: 3 → **8 sinyal tipi**
- `morning-briefing` skill — Claude API ile sabah BIST 100 özeti + 3 odak hisse seçimi
- `scenario-analyzer` skill — haber → senaryo → etki analizi
- `signal-postmortem` skill — kapanan trade'i analiz et, öğrenme yaz
- (Opsiyonel) Cache 3 ay birikince **LightGBM modeli** (sembol + indikatör seti → AL/SAT olasılığı)
- AI sinyal feed `/ws/signals/ai` — frontend ayrı renk kategorisinde gösterir

**Sonunda göreceğin:** Sabah Telegram mesajı: *"BIST bugün açılışta zayıf, USDT 32.5'te direnç testi. Odak: THYAO (yükseliş kanal), ASELS (kırılma sinyali), GARAN (pullback). 3 stratejiyi izlemeye al."* Akıllı, tutarlı, action-oriented.

---

### Sprint 7 — Always-On & Bildirim
**Amaç:** Bilgisayarın açıldığında otomatik başlasın, çökerse kalksın, her sinyal seni anında bulsun.

**Yapılacaklar:**
- `Dockerfile.api`, `Dockerfile.workers`, `Dockerfile.notifier` — 3 servis ayrı imaj
- `docker-compose.yml` — `restart: unless-stopped`, healthcheck'ler
- **Telegram bot** — `python-telegram-bot`, bot token + chat ID `.env` üzerinden
- **Email** — `smtplib` + Gmail App Password, günlük 09:00 cron
- **macOS desktop notification** — `osascript -e 'display notification ...'` (sadece lokal)
- **In-app toast** — TS frontend sağ üst köşe
- `.env.example` — token'lar, smtp, secrets şablonu
- `make up` / `make down` Makefile
- **Stres testi:** 1 saat, 100 sembol paralel polling, 0 hata

**Sonunda göreceğin:** Mac'i kapatıp açıyorsun → 30 sn içinde stack ayağa kalkıyor, browser'ı açıyorsun, her şey hazır. Bir sinyal düştü → 4 yerden haber geliyor (Telegram + email + macOS notification + in-app toast).

---

### Sprint 8 — Test, Doküman, Hand-off
**Amaç:** Yeni biri (veya yeni Claude oturumu) projeyi 10 dakikada anlasın.

**Yapılacaklar:**
- `README.md` güncel — yeni mimari + quick start
- `docs/MIMARI.md` — derin teknik açıklama
- `docs/AGENT_REHBERI.md` — 8 agent'in nasıl kullanılacağı
- `docs/SKILL_REHBERI.md` — 15 skill'in tetikleme örnekleri
- `tests/e2e/` Playwright testleri — TS frontend smoke
- **Backtest paritesi testi** — TS eski sonucu ≈ Python yeni sonucu (kabul edilebilir delta)
- **Memory testi** — oturum kapat-aç, Claude kaldığı yerden devam ediyor mu
- **Final demo** — uçtan uca senaryo, Enes onayı

**Sonunda göreceğin:** README'yi okuyan biri (veya yeni Claude penceresi) 10 dakikada projeyi anlıyor, çalıştırıyor, ilk sinyalini izliyor.

---

### Sprint 11 — Üretim Sertleştirme + Canlı Veri Bağlama + ML

**Amaç:** Gerçek lisanslı BIST/VİOP feed'ini bağla, LightGBM sinyal modelini eğit, frontend'i cihaz uyumlu hale getir, gözlemlenebilirliği artır.

**Ön koşul:** Gerçek lisanslı canlı doğrulama için `.env` içinde `BIST_HTTP_URL_TEMPLATE` ve `VIOP_HTTP_URL_TEMPLATE` değerleri dolu olmalı. Repo tarafındaki adapter, mock doğrulama ve strict canlı kontrol komutları tamamlandı.

#### Adım 11.1 — Lisanslı BIST/VİOP Feed Bağlantısı ✅
- [x] `BIST_HTTP_URL_TEMPLATE` URL ile `BistProvider.fetch()` canlı doğrulama kapısı
- [x] `VIOP_HTTP_URL_TEMPLATE` URL ile `ViopProvider.fetch()` canlı doğrulama kapısı
- [x] Provider health çıktısında `is_real` etiketi
- [x] Yahoo fallback `is_real: false` label'ı her zaman görünür

**Sonunda göreceğin:** URL verilirse `make provider-check-strict` canlı feed'i doğrular. URL yoksa `make provider-check` açıkça `external_credential_missing` döner; sahte veri yoktur.

#### Adım 11.2 — LightGBM Sinyal Modeli Eğitimi ✅
- [x] `scripts/ml_readiness.py` ile cache yeterliliğini doğrula (≥ 3 ay veri gerekli)
- [x] `quant_engine/research/lightgbm_model.py` üretim modunu aktive et (sahte model üretme kaldırılır)
- [x] Günlük yeniden eğitim için cron job (Makefile target: `make retrain`)
- [x] SignalGenerator'a LightGBM probability skoru ekle (mevcut kural motoru yanında)
- [x] Backtest engine'de LightGBM stratejisi olarak göster (8 → 9 strateji)

**Sonunda göreceğin:** Sinyal akışında `lgbm_prob: 0.73` gibi olasılık skoru da görünecek. Backtest panelinde "LightGBM" seçeneği var.

#### Adım 11.3 — Frontend Performans + UX ✅
- [x] Sidebar lazy-load: 130 sembolü tek seferde değil, scroll ile yükle
- [x] Mobil/tablet düzeni: 768px altında tek sütun (ekran bölme gizlenir)
- [x] Chart'ta indikatör toggle paneli (EMA/RSI/MACD/BB/ATR/VWAP aç-kapa)
- [x] Sinyal geçmişi: `/ws/signals` son 100 sinyali localStorage'da sakla, sayfa yenilenince kaybolmasın
- [x] Playwright E2E: mobil viewport + sinyal localStorage kalıcılığı testleri

**Sonunda göreceğin:** Telefondan açıldığında tek panel kullanılabilir layout. Chart'ın üstünde EMA/RSI/MACD toggle switch'leri var.

#### Adım 11.4 — Gözlemlenebilirlik + Uyarılar ✅
- [x] Prometheus `/metrics` endpoint (FastAPI middleware): request latency, cache hit rate, worker durumu
- [x] Grafana dashboard JSON (`docker/grafana/`) — 3 panel: latency, cache, worker
- [x] Worker çöktüğünde Telegram uyarısı (`WorkerHealthMonitor` + 30s periyodik kontrol)
- [x] `scripts/daily_health_report.py` — günlük sabah 09:00'da Telegram'a cache boy + test sonuçları
- [x] `make monitor` target → Grafana `localhost:3000`

**Sonunda göreceğin:** Sabah 09:05'te Telegram'a "gateway: ✅ cache: 18k bar, 45 sembol, p99: 42ms" geliyor. Bir worker çöktüyse anında bildirim.

#### Adım 11.5 — Güvenlik + Temiz Kapanma ✅
- [x] API key auth middleware (opsiyonel X-API-Key header) — dışa açılacaksa zorunlu
- [x] `SIGTERM` yakalayıp paper_trades'i flush eden graceful shutdown
- [x] `.env` validation başlangıçta: eksik kritik değer varsa servis başlamaz, açık hata mesajı verir
- [x] `docker compose down` sonrası SQLite WAL checkpoint doğrulama testi

---



| # | Branch / Commit | Konu | Durum | Sprint |
|---|--------|------|-------|--------|
| 1 | fix/v2-api-route-via-local-backend | v2 API → lokal backend route | ✅ MERGED | 0 |
| 2 | chore/sprint-0-skeleton | Sprint-0 iskelet | ✅ MERGED | 0 |
| 3 | feat/sprint-1-gateway-foundation | FastAPI + cache + spike filter | ✅ MERGED | 1 |
| 4 | feat/sprint-1-workers | Binance WS + Yahoo + BIST poller | ✅ MERGED | 1 |
| 5 | feat/sprint-1-ws-fanout | QuoteBus + /ws/quotes | ✅ MERGED | 1 |
| 6 | feat/sprint-2-bist100-fullscreen | Katalog temizliği | ✅ MERGED | 2 |
| 7 | feat/sprint-2-data-engine-stream | DataEngine → QuoteStream | ✅ MERGED | 2 |
| 8 | — | Backtest BUY/SELL marker'ları | ✅ MERGED | 2 |
| 9 | — | Streamlit söküm | ✅ MERGED | 2 |
| 10 | — | BIST 100 +10 sembol | ✅ MERGED | 2 |
| 11 | — | POST /api/backtest/run + blueprints | ✅ MERGED | 3 |
| 12 | — | StrategyPanel API'ye geçti, TS backtest söküldü | ✅ MERGED | 3 |
| 13 | — | SignalBus + SignalGenerator + /ws/signals | ✅ MERGED | 3 |
| 14 | — | MultiChartLayout çoklu pencere | ✅ MERGED | 2 |
| 15 | — | PortfolioPanel v2 + Paper Trading | ✅ MERGED | 4 |
| 16 | — | Agent + Skill + MCP + Hook ekosistemi | ✅ MERGED | 5 |
| 17 | — | AI sinyal motoru + bildirim altyapısı | ✅ MERGED | 6+7 |
| 18 | — | README + Mimari + Agent/Skill rehberleri | ✅ MERGED | 8 |

---

## Riskler ve Sınırlar

| Risk | Olasılık | Etki | Azaltım |
|------|----------|------|---------|
| yfinance rate-limit (60/dk) | Yüksek | Veri kaybı | Batch download + exp. backoff (Sprint 2.x) |
| Binance WS Türkiye geo-blok | **Aktif** | Kripto canlı tick gelmez | Backend daemon arkada reconnect dener; tarihsel veri ccxt REST'le yine gelir |
| BIST 15dk gecikmeli verinin bozuk gelmesi | Orta | Yanlış sinyal | IQR spike filter + `BIST_HTTP_URL_TEMPLATE` lisanslı feed köprüsü + Yahoo fallback etiketi |
| Docker Mac kaynak tüketimi | Düşük | Yavaşlık | `mem_limit` (Sprint 7) |
| Tam otomatik paper trading bug → tüm sandık yanması | Orta | Kayıp eğitim değeri | İzole sandık + günlük max DD limiti + audit trail |
| MCP sunucularının kararsızlığı | Orta | Skill bozulması | Doğrudan Python kütüphane fallback'i |
| Memory persistence script'i kırılırsa | Düşük | Oturum geçişi sıkıntı | Manuel `/devam` slash komutu yedek |

---

## Kritik Doğrulama Senaryoları

- [x] **Veri:** `/api/v2/candles` cache-aside, provider health ve veri-yok HTTP ayrımı testli
- [x] **WebSocket:** Binance WS reconnect health metadata + SignalFeed E2E smoke
- [x] **Backtest paritesi:** Python API tek doğruluk kaynağı, test suite içinde korunuyor
- [x] **Always-on:** `docker compose build`, `docker compose up -d`, `scripts/docker_restart_check.sh`
- [x] **Stres:** `scripts/stress_live_data.py`; smoke 470 istek / 0 altyapı hatası, tam koşu `make stress-live`
- [x] **Agent:** `/devam` ve agent/skill rehberleri güncel
- [x] **Skill:** `/morning-briefing` MCP bağlantılarıyla çalışacak şekilde dokümante
- [x] **Notifier:** Telegram tercih UI, email status, handler smoke ve gizli bilgi maskeleme testli

---

## Sıradaki Adım

**Sprint 10 tamamlandı.** Repo içindeki denetim eksikleri kapandı.

**Sıradaki:** Sprint 11 yalnızca yeni lisans/secret sağlandığında dış servis bağlama ve uzun süreli izleme işidir.

---

## Hızlı Linkler

- [`planlama.md`](planlama.md) — tick'li sprint listesi (tek doğruluk kaynağı)
- [`CLAUDE.md`](CLAUDE.md) — yeni Claude oturumu için sabit bağlam
- [`ILERLEME.md`](ILERLEME.md) — son oturum snapshot
- GitHub PR'lar: https://github.com/ENESAKT/Backtest/pulls?q=is%3Apr
