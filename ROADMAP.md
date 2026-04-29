# Yol Haritası — PiyasaPilot Trading Terminali

> Bu doküman **ne yapıldı, ne yapılacak, sonunda ne göreceksin**'i sade Türkçeyle anlatır.
> Tick listesi (`- [x]` / `- [ ]`) için: [`planlama.md`](planlama.md). Bu dosya o planın hikâyesidir.
>
> **Tarih:** 2026-04-27 · **Durum:** Sprint 1 ✅ tamam · Sprint 2 yarısı tamam · 7 PR merge edildi.

---

## Vizyon — Tek Cümleyle

BIST + kripto + döviz + emtia için **TradingView benzeri**, **Türkçe**, tarayıcıda çalışan, **otonom paper-trading** yapan, **AI sinyal** üreten ve **hiç kapanmayan** bir trading terminali.

İki kilit fark:
1. **Sıfır dış API çıkışı** — tarayıcı `api.binance.com`'a doğrudan istek atmaz; her şey lokal Python backend'inden geçer (Türkiye geo-blok riskine karşı).
2. **Strateji-bazlı izole sandık** — her stratejinin ayrı 10.000 TL sanal cüzdanı vardır; biri yansa diğerleri etkilenmez. Audit trail her trade'i JSON log'lar.

---

## Bugünkü Durum (2026-04-27)

| Katman | Durum | Detay |
|--------|-------|-------|
| Backend gateway | ✅ Hazır | FastAPI, SQLite cache, IQR spike filter, `/api/v2/candles` cache-aside, `/api/health` |
| Worker'lar | ✅ Çalışıyor | Binance WS (10 kripto), Yahoo poller (BIST endeks + FX + emtia), BIST 30 hisse poller |
| WS fan-out | ✅ Çalışıyor | `/ws/quotes` — worker'ların yazdığı her bar tarayıcıya broadcast |
| Frontend tek terminal | ✅ %85 | Sidebar 98 sembol, MultiChartLayout (1×1/1×2/2×1/2×2), fullscreen, DataEngine→QuoteStream |
| Backtest (TS) | 🟡 Var | TS-içi 4 strateji, sinyaller liste olarak; **chart üstünde marker yok** |
| Backtest (Python API) | ❌ Yok | Sprint 3'te |
| Paper trading | 🟡 İskelet | JSON store mevcut; SQLite şeması ve otonom executor Sprint 4'te |
| AI sinyal | ❌ Yok | Sprint 6'da |
| Always-on (Docker) | ❌ Yok | Sprint 7'de |
| Bildirim (Telegram/email/toast) | ❌ Yok | Sprint 7'de |

**Açık PR:** Yok şu an (4 PR merge edildi: #1 v2-route, #3 foundation, #4 workers, #5 ws-fanout, #6 katalog, #7 DataEngine→QuoteStream).

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

### Sprint 2 — Frontend Birleşimi 🟡 (%60)
**Amaç:** TS terminali tek ve son arayüz olsun. Streamlit kalksın.

**Yapılanlar:**
- ✅ 2.1 Market Explorer (kategori-akordeon sidebar) — zaten vardı
- ✅ 2.2 BIST 100 katalogu (98/100 sembol; PR #6 + PR #10)
- ✅ 2.3 Çoklu pencere layout — `MultiChartLayout.ts`, 4 layout modu (1×1/1×2/2×1/2×2), G kısayolu
- ✅ 2.4 Fullscreen butonu — zaten vardı, retroaktif tick
- ✅ 2.7 DataEngine → QuoteStream (PR #7); WebSocketManager.ts sökündü
- ✅ 2.7+ BUY/SELL marker'ları — `setSignals/clearSignals` pipeline
- ✅ 2.8 Streamlit söküm (PR #9)

**Kalanlar:**
- [~] **2.5 Strateji Lab port** — StrategyPanel temel özellikleri kapsıyor; advanced param formu Sprint 3'te
- [~] **2.6 Veri İstasyonu port** — Sidebar + her pane dropdown ile kapsanıyor; watchlist Sprint 4'te
- ⏳ **2.8 Streamlit söküm** — `quant_engine/app/ui_streamlit/` arşivle. PR #12.

**Mini PR (sıradaki):**
**PR #8 — Backtest BUY/SELL marker'ları**
- `ChartPanel.setSignals(Signal[])` → lightweight-charts `setMarkers`
- ▲ yeşil = AL, ▼ kırmızı = SAT, mum üstünde tooltip
- 30-45 dakikalık iş, görsel kazanç büyük

**Sonunda göreceğin:** Tek tarayıcı sekmesi her şeyi yapıyor. Streamlit gerek yok. Mum üstünde alım-satım okları görüyorsun.

---

### Sprint 3 — Strateji & Backtest Birleşimi
**Amaç:** TS'in kendi dahili backtest kodu sökülür; tek doğruluk kaynağı **Python `BacktestEngine`** olur (lookahead-free, testli).

**Yapılacaklar:**
- TS dahili backtest implementasyonu sökülür
- `POST /api/backtest/run` endpoint — Python motoru çalışır, JSON sonuç döner
- Strateji blueprint formatı (parametre şeması + meta) — tek tip yapı
- `StrategyPanel` → API'ye POST atıyor, **equity eğrisini Chart.js** ile çiziyor
- Live signal feed `/ws/signals` — DecisionEngine her bar kapanışında çalışır, sinyal varsa fan-out
- `SignalFeed` paneli — sağ alt köşede canlı sinyal akışı
- **8 strateji** (4 mevcut + 4 yeni):
  1. EMA cross (50/200)
  2. RSI mean-reversion
  3. Bollinger Bands reversion
  4. Breakout detector
  5. **Donchian breakout** (yeni)
  6. **MACD divergence** (yeni)
  7. **Supertrend** (yeni)
  8. **Mean-reversion VWAP** (yeni)

**Sonunda göreceğin:** "Backtest çalıştır" tıklayınca → equity eğrisi grafiği + metric kartları + son 50 trade listesi + chart üstünde marker'lar. **Aynı stratejinin TS sonucu = Python sonucu** (parite testi geçer).

---

### Sprint 4 — Paper Trading & Portföy
**Amaç:** Otonom alım-satım yapan ama **gerçek emir vermeyen** robot. Tam audit trail.

**Yapılacaklar:**
- SQLite şeması: `paper_trades`, `paper_portfolio`, `paper_equity_curve`
- **Strateji-bazlı izole sandık** — her stratejiye 10.000 TL sanal cüzdan
- `robot-executor` sub-agent — `/ws/signals` mesajını alır, sandığa kaydeder, açık pozisyon listesini günceller
- Canlı PnL hesabı — gateway fiyatı × açık miktar
- `PortfolioPanel` v2: equity curve, drawdown, win rate, sharpe oranı
- Audit trail — her trade JSON log
- Risk limitleri:
  - Her cüzdan max %10 günlük zarar → otomatik durdur
  - Pozisyon başı max %10
  - Gün-içi stop-out

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

## PR Tablosu (Bugüne Kadar)

| # | Branch | Konu | Durum | Sprint |
|---|--------|------|-------|--------|
| 1 | fix/v2-api-route-via-local-backend | v2 API → lokal backend route | ✅ MERGED | 0 |
| 2 | chore/sprint-0-skeleton | Sprint-0 iskelet | ✅ MERGED | 0 |
| 3 | feat/sprint-1-gateway-foundation | FastAPI + cache + spike filter | ✅ MERGED | 1 |
| 4 | feat/sprint-1-workers | Binance WS + Yahoo + BIST poller | ✅ MERGED | 1 |
| 5 | feat/sprint-1-ws-fanout | QuoteBus + /ws/quotes | ✅ MERGED | 1 |
| 6 | feat/sprint-2-bist100-fullscreen | Katalog temizliği + 2.4 retroaktif | ✅ MERGED | 2 |
| 7 | feat/sprint-2-data-engine-stream | DataEngine → QuoteStream | ✅ MERGED | 2 |
| **8** | (sıradaki) | **Backtest BUY/SELL marker'ları** | ⏳ HENÜZ | 2-bonus |
| 9 | (planlanan) | Çoklu pencere layout | ⏳ HENÜZ | 2.3 |
| 10 | (planlanan) | Strateji Lab + Veri İstasyonu port | ⏳ HENÜZ | 2.5–2.6 |
| 11 | (planlanan) | BIST 100 tam katalog (yfinance batch) | ⏳ HENÜZ | 2.2 son |
| 12 | (planlanan) | Streamlit söküm | ⏳ HENÜZ | 2.8 |
| 13+ | (Sprint 3 başlar) | API tabanlı backtest + 8 strateji | ⏳ HENÜZ | 3 |

---

## Riskler ve Sınırlar

| Risk | Olasılık | Etki | Azaltım |
|------|----------|------|---------|
| yfinance rate-limit (60/dk) | Yüksek | Veri kaybı | Batch download + exp. backoff (Sprint 2.x) |
| Binance WS Türkiye geo-blok | **Aktif** | Kripto canlı tick gelmez | Backend daemon arkada reconnect dener; tarihsel veri ccxt REST'le yine gelir |
| BIST 15dk gecikmeli verinin bozuk gelmesi | Orta | Yanlış sinyal | IQR spike filter (zaten devrede) + iki provider çapraz kontrol |
| Docker Mac kaynak tüketimi | Düşük | Yavaşlık | `mem_limit` (Sprint 7) |
| Tam otomatik paper trading bug → tüm sandık yanması | Orta | Kayıp eğitim değeri | İzole sandık + günlük max DD limiti + audit trail |
| MCP sunucularının kararsızlığı | Orta | Skill bozulması | Doğrudan Python kütüphane fallback'i |
| Memory persistence script'i kırılırsa | Düşük | Oturum geçişi sıkıntı | Manuel `/devam` slash komutu yedek |

---

## Kritik Doğrulama Senaryoları (Sprint 8'de)

- [ ] **Veri:** `curl /api/chart?symbol=THYAO&interval=15m&period=1mo` → 30 gün × 15dk bar
- [ ] **WebSocket:** Tarayıcıda 5 dk açık tut; XU100 + BTCUSDT canlı güncelleniyor
- [ ] **Backtest paritesi:** TS UI sonucu == `/api/backtest/run` sonucu
- [ ] **Always-on:** `docker compose kill api` → 5 sn'de restart
- [ ] **Stres:** 100 sembol × 1 saat polling → 0 hata
- [ ] **Agent:** `/devam` → Claude son durumu özetlesin
- [ ] **Skill:** `/morning-briefing` → 3 odak hisse + tutarlı rapor
- [ ] **Notifier:** Test sinyal → 4 kanala düşüyor

---

## Sıradaki Adım

**Sprint 2 büyük ölçüde tamamlandı.** Sprint 3 de tamamlandı (backtest API + 8 strateji + sinyal feed).

**Sıradaki: Sprint 4 — Paper Trading & Portföy.** SQLite paper_trades/paper_portfolio şemaları, strateji-bazlı izole sandık, otonom robot-executor, canlı PnL hesabı.

---

## Hızlı Linkler

- [`planlama.md`](planlama.md) — tick'li sprint listesi (tek doğruluk kaynağı)
- [`CLAUDE.md`](CLAUDE.md) — yeni Claude oturumu için sabit bağlam
- [`ILERLEME.md`](ILERLEME.md) — son oturum snapshot
- GitHub PR'lar: https://github.com/ENESAKT/Backtest/pulls?q=is%3Apr
