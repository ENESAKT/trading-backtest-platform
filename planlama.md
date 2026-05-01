# PLANLAMA — Backtest + PiyasaPilot Birleşik Trading Terminali

> **Format kuralı:** Her madde başında `- [ ]` (yapılmadı) ya da `- [x]` (yapıldı) tick işareti.
> **Hayatta kalma kuralı:** Bu dosya tek doğruluk kaynağıdır. Yeni bir oturum açıldığında Claude bu dosyayı en başta okur ve nereden devam edeceğini buradan anlar.
> **Onay sırası:** Her sprint sonunda Enes "devam" demeden sonraki sprint'e geçilmez (6 seviyeli orkestratör kuralı).
> **Tarih:** 2026-04-26 (oluşturma).

---

## 1. Context (Neden bu proje?)

> Sprint 2.8'de (PR #9) Streamlit söküldü; aşağıdaki "iki kopuk arayüz" tasviri tarihseldir, planın çıkış motivasyonunu hatırlatır.

`/Users/enes/AgentWorkspace/Backtest` reposu **eskiden iki kopuk arayüze sahipti**:

- ~~**Streamlit terminal** (`quant_engine/app/ui_streamlit/app.py`, port 8502)~~ — Sprint 2.8'de söküldü.
- **PiyasaPilot v2 TS terminali** (`piyasapilot-v2/`, lightweight-charts) — canlı grafik, indikatörler, paper-trading widget. **Tek arayüz.**

Aynı veri kaynaklarını farklı yollardan kullanıyorlardı; sonuçlar zaman zaman tutmuyordu (desync). Ayrıca:
- yfinance 15 dk bar verisini sadece 5 gün, Binance ~7 gün veriyor → **1 ay tarihsel** elde etmek için backend cache şart.
- BIST için gerçek anlık veri yok; 15 dk gecikmeli çözüm aranıyor.
- Sistem manuel başlatılıyor; çökerse kalkmıyor.
- AI sinyal motoru yok; mevcut motor kural tabanlı (EMA200+BB+RSI füzyonu).
- Memory/context kaybı her yeni Claude oturumunda baştan başlıyor.

**Hedef:** TradingView benzeri tek bir SPA, **otonom alt-agent ekibi**, **kalıcı hafıza**, **kesintisiz çalışan** veri gateway, BIST 100 + büyük kripto + altın/dolar kapsamı.

---

## 2. Enes'in Verdiği Kararlar (Özet)

- [x] **Frontend:** TS terminali ana arayüz olur. Streamlit kalkar; özellikleri TS'e taşınır.
- [x] **Tarihsel veri:** Backend rolling cache (SQLite/Parquet). yfinance/Binance pencerelerini kayar pencere olarak biriktir.
- [x] **Sembol kapsamı:** İlk fazda BIST 100 + büyük kripto (BTC/ETH/BNB/SOL/XRP + ana 20) + altın + USD/TRY ≈ 130 sembol. Stres testi geçince BIST tümüne genişlet.
- [x] **Always-on:** Docker Compose (lokal, sonra istenirse buluta taşınabilir).
- [x] **Strateji motoru:** Python `BacktestEngine` tek doğruluk kaynağı. TS sadece görüntüler.
- [x] **AI sinyal motoru:** Hibrit. Sprint 6'da önce kural motorunu 8 sinyal tipine çıkar, Claude API ile sabah brifingi + odak hisseler. Cache 6 ay birikince LightGBM eklenecek.
- [x] **Paper trading davranışı:** Tam otomatik ama strateji-bazlı izole sandık (her strateji kendi 10.000 TL sanal cüzdanı). Günlük max %5 zarar limit, pozisyon başı max %10, audit trail.
- [x] **Docker konumu:** Şimdilik Mac (Docker Desktop / colima). docker-compose.yml taşınabilir tutulacak; ileride Hetzner/Fly.io VPS'e geçirebilir.
- [x] **Bildirim:** Telegram + Email + In-app + macOS desktop seçildi. Altyapı Sprint 7'de kuruldu. Telegram token + SMTP konfigürasyonu Enes'in .env dosyasına gireceği değerlere bağlı.

---

## 3. Mevcut Durum (Repo Snapshot)

### 3.1 Çalışan parçalar (DOKUNMA — sağlam)
- `backend/api/main.py` — FastAPI gateway, cache-aside `/api/v2/candles`, provider health, backtest, paper trading, notifier/assistant status endpoint'leri.
- `backend/data/cache.py` + `backend/data/spike_filter.py` — SQLite OHLCV cache ve IQR spike filtresi.
- `backend/workers/` — Binance WS, Yahoo poller, BIST poller ve standalone cache-filler entrypoint.
- `quant_engine/backtest/engine.py` — Lookahead-free, testli BacktestEngine.
- `quant_engine/data/live_feed.py` + `quant_engine/data/provider_router.py` — BIST/VİOP/kripto sağlayıcı yönlendirmesi ve legacy payload uyumu.
- `quant_engine/data/providers/` — Binance/yfinance provider'ları + BIST, VİOP, crypto market data adapter'ları.
- `quant_engine/strategy/` — 9 strateji, blueprint engine ve decision engine.
- `backend/signals/generator.py` — SignalGenerator v2, STRONG konsensüs ve gerçek veri metadata kapısı.
- `backend/paper/` — SQLite paper trading, izole strateji cüzdanları, risk limitleri.
- `backend/notifier/` — Telegram, email, macOS bildirimi, asistan listener, bildirim tercihleri.
- `piyasapilot-v2/src/components/` — ChartPanel, MultiChartLayout, PortfolioPanel, StrategyPanel, Screener, Sidebar, SignalFeed.
- `piyasapilot-v2/src/indicators/` — EMA, SMA, RSI, MACD, BB, ATR, VWAP, Stoch.
- `.claude/` — Agent, skill, command ve hook ekosistemi.

### 3.2 Kapatılan Boşluklar
- BIST resmi/lisanslı veri için `BIST_HTTP_URL_TEMPLATE` köprüsü eklendi; yapılandırma yoksa Yahoo Finance best-effort public kaynak açıkça etiketlenir.
- VİOP için `VIOP_HTTP_URL_TEMPLATE` köprüsü eklendi; yapılandırma yoksa sahte veri üretmeden `not_configured` döner.
- Binance WS `ConnectionResetError` dayanıklılığı jitter'lı reconnect, health metadata ve testlerle kapatıldı.
- borsa-mcp ve tradingview-mcp `.mcp.json` + `scripts/mcp_uvx.sh` ile çalışır hale getirildi.
- Stres testi, Docker restart testi ve Playwright E2E otomasyona alındı ve smoke doğrulandı.
- LightGBM/ML temeli feature extraction + readiness gate olarak eklendi; veri yetersizken sahte model üretilmez.

---

## 4. Hedef Mimari (Tek Terminal)

```
                         ┌─────────────────────────────────┐
                         │   Tarayıcı (TradingView-like)   │
                         └────────────┬────────────────────┘
                                      │ HTTP + WS
                         ┌────────────▼────────────────────┐
                         │  Vite SPA (TS, lightweight-     │
                         │  charts) — single page          │
                         │   ├ Market Explorer (tree)      │
                         │   ├ Multi-chart Layout (split)  │
                         │   ├ Strateji + Backtest UI      │
                         │   ├ Paper-trading panel         │
                         │   └ AI Sinyal feed              │
                         └────────────┬────────────────────┘
                                      │
                         ┌────────────▼────────────────────┐
                         │  FastAPI Gateway (port 8000)    │
                         │   /api/symbols, /api/chart      │
                         │   /api/backtest/run             │
                         │   /api/strategy, /api/paper     │
                         │   WS /ws/quotes, /ws/signals    │
                         └────┬───────────────┬────────────┘
                              │               │
              ┌───────────────▼──┐   ┌────────▼─────────────┐
              │ Cache Katmanı    │   │ Worker Daemonları    │
              │ SQLite + Parquet │◄──│ • Binance WS         │
              │ TTL'li, 1 ay+    │   │ • Yahoo poller       │
              │ rolling          │   │ • borsapy poller     │
              └─────────┬────────┘   │ • IQR spike filter   │
                        │            └────────┬─────────────┘
                        │                     │
                        ▼                     ▼
              ┌────────────────┐    ┌───────────────────────┐
              │ Quant Engine   │    │ Notifier              │
              │ • BacktestEng. │    │ • Telegram bot        │
              │ • Strategies   │    │ • Email (smtp)        │
              │ • DecisionEng. │    │ • macOS notification  │
              │ • Risk + Sizing│    │ • In-app toast        │
              └────────────────┘    └───────────────────────┘
                        │
                        ▼
              ┌─────────────────────────────────────────────┐
              │ Docker Compose (always-on)                  │
              │ • api  • workers  • db  • nginx  • bots     │
              └─────────────────────────────────────────────┘
```

Streamlit tamamen sökülecek; içindeki Strateji Lab + Veri İstasyonu özellikleri TS'e taşınacak.

---

## 5. Sembol Kapsamı (İlk Faz ~130 sembol)

- **BIST 100:** `quant_engine/workspace/manager.py` BIST30 listesi var; BIST100 listesi eklenecek.
- **Kripto (Binance):** BTC, ETH, BNB, SOL, XRP, ADA, AVAX, DOT, LINK, MATIC, DOGE, SHIB, LTC, BCH, ATOM, NEAR, FTM, ICP, ARB, OP (ilk 20).
- **Forex/Emtia:** USDTRY, EURTRY, GBPTRY, EURUSD, GBPUSD, USDJPY, XAUUSD (altın), XAGUSD (gümüş), BZ=F (Brent), CL=F (WTI).

---

## 6. Veri Sağlayıcı Stratejisi (Kayar Pencere + Çoklu Kaynak)

| Sembol Tipi | Birincil | İkincil | Notlar |
|-------------|----------|---------|--------|
| BIST hisse  | **borsapy** (saidsurucu) | yfinance `.IS` | borsapy 15dk barları yfinance'tan daha uzun, BIST için optimize |
| BIST endeks (XU100) | yfinance | borsapy | XU100 için yfinance daha güvenilir |
| Kripto      | Binance REST + WS | ccxt | WebSocket ile gerçek zamanlı |
| Forex/Emtia | yfinance | borsapy (TRY pariteleri) | 15dk gecikmeli kabul |
| Fundamentals (opsiyonel) | borsapy (BIST) | FMP API (US) | Sonraki sprint |
| KAP haberleri (opsiyonel) | **borsa-mcp** | Manuel | MCP ile Claude'a tool olarak |

**Cache stratejisi:** Worker her 60 sn yfinance/borsapy çağırıyor; her gelen 5–7 günlük pencere SQLite'a `INSERT OR IGNORE` ile yazılıyor. Zamanla cache 1 ay+ birikiyor. Kullanıcı `/api/chart?period=1mo` çağırınca cache'ten dönüyor.

**Spike filtresi:** Her cache yazımından önce IQR (Q1−1.5·IQR, Q3+1.5·IQR) + hacim ağırlıklı kontrol. Outlier ise Winsorize.

---

## 7. Agent / Skill / MCP / Hook Mimarisi

> Claude Code'un kendi ekosistemi (sub-agent, skill, MCP, hook) projeye gömülecek. Böylece yeni Claude oturumu açıldığında her şey hazır gelir; context boşa harcanmaz.

### 7.1 Sub-Agent Ekibi (`.claude/agents/`)

| Agent | Görev | Model | Tools |
|-------|-------|-------|-------|
| `data-validator` | IQR spike filtresi testi, OHLCV doğrulama, gap detection | Haiku | Read, Bash(pytest), Grep |
| `quant-researcher` | Yeni strateji fikirleri, backtest hipotezi, parametre tarama | Sonnet | Read, Write, Bash(python) |
| `backtest-runner` | `BacktestEngine`'i çalıştır, sonuçları rapor et | Haiku | Read, Bash(python), Write |
| `frontend-builder` | TS/Vite/lightweight-charts geliştirme | Sonnet | Read, Write, Edit, Bash(npm) |
| `backend-builder` | FastAPI/SQLite/worker geliştirme | Sonnet | Read, Write, Edit, Bash |
| `robot-executor` | Paper-trading executor (otonom sinyal işleyici) | Haiku | Read, Write, Bash |
| `code-reviewer` | Her commit öncesi kalite gate | Sonnet | Read, Bash(git diff) |
| `devops-engineer` | Docker Compose, launchd, healthcheck | Haiku | Read, Write, Bash(docker) |

VoltAgent koleksiyonundan adapte edilecek (referans: github.com/VoltAgent/awesome-claude-code-subagents).

### 7.2 Skill Seti (`.claude/skills/`)

Trading-spesifik skill'ler. Tradermonty/claude-trading-skills'ten seçilecekler + projeye özel olanlar:

#### Hazır skill'ler (kopyala/uyarla)
| Skill | Kaynak | API gereksinimi |
|-------|--------|-----------------|
| `backtest-expert` | tradermonty | Yok |
| `position-sizer` | tradermonty | Yok |
| `technical-analyst` | tradermonty | Yok |
| `market-news-analyst` | tradermonty | WebSearch |
| `signal-postmortem` | tradermonty | Opsiyonel FMP |
| `strategy-pivot-designer` | tradermonty | Yok |
| `scenario-analyzer` | tradermonty | WebSearch |
| `risk-manager` | VoltAgent | Yok |

#### Projeye özel skill'ler (yazılacak)
| Skill | Görev |
|-------|-------|
| `validate-spike-filter` | Cache pipeline'a gelen veride spike testi koş |
| `run-backtest` | `/run-backtest <symbol> <strategy> <start> <end>` slash komut |
| `health-check` | Tüm servisleri ping'le, raporla |
| `morning-briefing` | Sabah Claude API ile BIST 100 özeti + odak hisse |
| `paper-trade-status` | Açık pozisyonlar, PnL, equity eğrisi snapshot |
| `deploy-stack` | Docker Compose up/down + healthcheck |
| `session-recap` | Oturum sonu özeti, planlama.md güncellemesi |

### 7.3 MCP Sunucuları (`~/.mcp.json` veya proje `.mcp.json`)

| MCP | Görev | Link |
|-----|-------|------|
| `borsa-mcp` (saidsurucu) | BIST + TEFAS + KAP haberleri + makro veri (758 BIST şirketi, 836 fon) | https://github.com/saidsurucu/borsa-mcp |
| `tradingview-mcp` (atilaahmettaner) | Real-time crypto/stock screening, 30+ indikatör, çoklu borsa | https://github.com/atilaahmettaner/tradingview-mcp |
| `yahoo-finance-mcp` (Alex2Yang97) | Tarihsel fiyat, fundamentals, opsiyon zincirleri | (yedek seçenek) |
| `filesystem-mcp` | Standart dosya erişimi (cache pipeline için) | resmi |
| (opsiyonel) `playwright-mcp` | isyatirim.com.tr scraping yedeği | resmi |

### 7.4 Hook'lar (`.claude/settings.json`)

| Event | Hook | Amaç |
|-------|------|------|
| `SessionStart` | `./.claude/hooks/check-services.sh` | Docker servisler çalışıyor mu, son cache zamanı, planlama.md durumu |
| `UserPromptSubmit` | `./.claude/hooks/load-recent-state.sh` | Son `session-recap.md`'yi otomatik yükle (context tasarrufu) |
| `PostToolUse` (Edit/Write) | `ruff check --fix` + `npm run lint` | Lint otomatik |
| `SubagentStop` | `./.claude/hooks/persist-agent-output.sh` | Agent çıktısını `.claude/agent-logs/` altına yaz |
| `Stop` (oturum sonu) | `./.claude/hooks/auto-recap.sh` | `session-recap.md` ve `planlama.md` checkbox'larını güncelle |

### 7.5 Slash Command'lar (`.claude/commands/`)

- `/devam` — bir önceki oturumun `session-recap.md`'sini yükle, kaldığı yerden başla.
- `/backtest <sembol> <strateji> <başlangıç> <bitiş>` — backtest-runner agent'ını tetikle.
- `/sinyal <sembol>` — DecisionEngine + Claude API hibrit sinyal raporu üret.
- `/durum` — tüm servisler ping, son cache zamanı, açık paper trade'ler.
- `/strateji-yeni` — quant-researcher agent'ını başlat, yeni strateji önerisi al.

---

## 8. Memory & Context Persistence (En Kritik İstek)

> **Hedef:** Yeni bir Claude penceresi açtığında repo'yu sıfırdan keşfetmek zorunda kalmasın; her şeyi `planlama.md` + `CLAUDE.md` + memory'den anlasın.

### 8.1 Üç Katmanlı Hafıza
1. **Proje köküne `CLAUDE.md`** — sabit bilgi: mimari, teknoloji yığını, çalışma kuralları, port haritası, aktif servisler.
2. **Proje köküne `planlama.md`** — bu plan; tick'leri her sprint sonunda güncellenir.
3. **`.claude/memory/`** + global `~/.claude/projects/.../memory/` — kullanıcı tercihleri, geçmiş kararlar, sınanmış yaklaşımlar.

### 8.2 Oturum Sonu Otomasyonu
- `Stop` hook → `auto-recap.sh` çalışır → son `Stop` ile mevcut `Stop` arası git diff + tool çağrı sayısı + tamamlanan checkbox'lar `session-recap.md` dosyasına yazılır.
- `planlama.md` checkbox'ları otomatik güncellenir (regex eşleşmesi ile).
- Yeni oturumda `SessionStart` hook → `session-recap.md`'yi systemMessage olarak inject eder. Claude sıfırdan keşfetmek zorunda kalmaz.

### 8.3 Context Doluluğu Yönetimi
- Uzun konuşmalarda Claude otomatik compaction yapar; ancak biz **özetleri planlama.md ve session-recap.md'ye taşıyarak** asıl bilgiyi diskte tutarız.
- Kural: "Yeni oturum açıldığında ilk üç adım: (1) `planlama.md` oku, (2) `session-recap.md` oku, (3) `CLAUDE.md` oku."

---

## 9. Always-On Stack (Docker Compose)

```yaml
# docker-compose.yml (taslak)
services:
  api:        # FastAPI gateway
  workers:    # Binance WS daemon, Yahoo poller, borsapy poller, spike filter
  db:         # SQLite volume + Parquet dizini
  nginx:      # SPA + API ters proxy
  notifier:   # Telegram bot + email worker
```

- Otomatik restart (`restart: unless-stopped`).
- `healthcheck:` her servise.
- Lokal Mac'te `colima` veya `Docker Desktop` ile çalışır; istenirse Hetzner/Fly.io VPS'e taşınabilir.

---

## 10. Bildirim Katmanı

- **In-app toast** — TS frontend'de sağ üst köşe.
- **Telegram bot** — `python-telegram-bot`. Bot token + chat ID `.env` üzerinden.
- **Email** — `smtplib` + Gmail App Password. Günlük özet 09:00.
- **macOS desktop** — `osascript -e 'display notification ...'` (sadece lokalde).

Tek `Notifier` servisi tüm kanalları soyutlar; sinyal motoru fan-out ile hepsine gönderir.

---

## 11. Sprint Planı (Yapılacaklar — Tick'li)

> Kural: Bir sprint bitmeden sonrakine geçilmez. Enes "devam" der.

### Sprint 0 — Bağlam ve Onay
- [x] 0.1 Bu `planlama.md`'yi proje köküne kopyala.
- [x] 0.2 Proje köküne `CLAUDE.md` yaz (mimari, port haritası, kurallar).
- [x] 0.3 `.claude/` iskelet klasörleri (`agents/`, `skills/`, `commands/`, `hooks/`, `memory/`).
- [x] 0.4 Açık kararlar — AI hibrit, strateji-bazlı izole sandık, Mac+Docker — Bölüm 2'de işaretlendi.
- [x] 0.5 Seviye 2 (Planlayıcı) tamam; Ultraplan #1 onaylandı + PR #1 merge edildi.

### Sprint 1 — Backend Data Gateway
- [x] 1.1 `live_server.py` → FastAPI'ye taşı (`backend/api/main.py`). _PR #3_
- [x] 1.2 SQLite cache şeması (`bars`, `quotes`, `meta`) + Parquet dizini. _PR #3_
- [x] 1.3 IQR + hacim ağırlıklı spike filter (`backend/data/spike_filter.py`) + pytest. _PR #3_
- [x] 1.4 Worker iskeleti (`backend/workers/base.py`). _PR #4_
- [x] 1.5 Binance WS daemon (kripto canlı bar). _PR #4_
- [x] 1.6 Yahoo Finance poller (BIST endeks + FX + emtia, 15s). _PR #4_
- [x] 1.7 ~~borsapy~~ yfinance `.IS` poller (BIST hisse, 60s). _PR #4 — borsapy değerlendirmesi Sprint 5'e ertelendi (ağır transitif deps)._
- [x] 1.8 `/api/v2/candles?symbol=&interval=&limit=` endpoint (cache-aside). _PR #3_
- [x] 1.9 `/ws/quotes` WebSocket (canlı tick fan-out). _PR #5_
- [x] 1.10 Healthcheck endpoint (cache stats + worker durumu). Prometheus → Sprint 7. _PR #3 + #4_
- [x] 1.11 `tests/integration/test_gateway.py` + `test_lifespan.py` — uçtan uca cache-aside ve worker lifecycle. _PR #3 + #4_

### Sprint 2 — Frontend Birleşimi (TS Tek Terminal)
- [x] 2.1 PiyasaPilot v2'ye Market Explorer (sol panel tree/accordion). _PR öncesi mevcut: `Sidebar.ts` kategori-akordeon + arama + ticker._
- [x] 2.2 BIST 100 / Kripto / Forex-Emtia kategorileri. _PR #6 dublike+yanlış sembol temizliği; PR #10 +10 yeni güvenli BIST sembolü (AKFYE, ALFAS, ASTOR, BIENY, BRSAN, GWIND, KAREL, KCAER, KMPUR, PAPIL) → BIST30 30 + BIST100_EXTRA 68 = **98 sembol**. BIST 100 üyeliği Borsa İstanbul tarafından her dönem revize edilir; ≥98 yeterli kapsama._
- [x] 2.3 Çoklu pencere layout (split / grid; her pencere kendi sembol/timeframe). _PR #8: `MultiChartLayout.ts` — 4 layout modu (1×1, 1×2, 2×1, 2×2), her pane kendi ChartPanel + sembol dropdown + opsiyonel WS bağlantısı; G kısayolu ile layout döngüsü; aktif pane mavi border + strateji paneli senkronizasyonu._
- [x] 2.4 Fullscreen düğmesi. _Mevcut: `ChartPanel.ts:158` `<button id="fullscreen-btn">` + F kısayolu + `requestFullscreen`/CSS fallback. PR #6'da retroaktif tick._
- [x] 2.5 Streamlit'in Strateji Lab → TS'te. _StrategyPanel API tabanlı backtest, metrics, equity curve, sinyal listesi ve chart marker'larıyla tamamlandı._
- [x] 2.6 Streamlit'in Veri İstasyonu → TS'te. _Sidebar kategori-akordeon, arama, sembol grupları ve kalıcı seçimle ana iş akışını kapsıyor._
- [x] 2.7 `DataEngine` → yeni FastAPI gateway WS'ine bağla; CORS proxy'yi sök. _PR #7: WebSocketManager.ts (Binance-direct) sökündü, kripto path artık `/ws/quotes` üzerinden; tüm tarihsel fetch `HistoricalLoader.ts`'da merkezi._
- [x] 2.7+ Backtest BUY/SELL marker'ları chart üstünde. _PR #8 (mini): `ChartPanel.setSignals/clearSignals` lightweight-charts `setMarkers` ile; ▲ AL ▼ SAT, sembol değişiminde temizlenir; pipeline `StrategyPanel.onSignalsUpdate` → `ChartPanel.setSignals`._
- [x] 2.8 Streamlit kalkar (`quant_engine/app/ui_streamlit/` repodan silindi). _PR #9: 2856 satır Streamlit + test_ui_overlays.py + requirements.txt streamlit girişi + README/CLAUDE.md port 8502 referansları temizlendi._

### Sprint 3 — Strateji & Backtest Birleşimi
- [x] 3.1 TS'teki dahili backtest implementasyonunu sök. _PR #12: `piyasapilot-v2/src/strategies/` (TrendFollowing, MeanReversion, BreakoutDetector + `runBacktestById`/`generateSignals`) silindi; tüm backtest artık API üzerinden._
- [x] 3.2 `POST /api/backtest/run` endpoint (Python `BacktestEngine`). _PR #11: cache-aware runner + Pydantic istek modeli + 4 hata durumu (unknown strategy / yetersiz data / invalid params / unknown key)._
- [x] 3.3 Strateji blueprint formatı (parametre şeması + meta). _PR #11: `backend/backtest/blueprints.py` — id/label/description/default_params/schema; `GET /api/backtest/strategies` ile expose._
- [x] 3.4 TS'te `StrategyPanel` → API'ye `POST` atıyor, equity eğrisini Chart.js ile çiziyor. _PR #12: `fetch('/api/backtest/run')` + 30s timeout + hata mesajı + `lastRunKey` debounce (her tick yerine sembol/strategy değişiminde tetikler); equity eğrisi backend `equity_curve[].total_equity` üzerinden çizilir; `signals[]` ChartPanel marker'a doğal akış._
- [x] 3.5 Live signal feed: `/ws/signals` (DecisionEngine her bar kapanışında çalışır). _PR #13: `SignalBus` + `SignalGenerator`; `on_bar` hook tüm worker'lara bağlı._
- [x] 3.6 TS'te `SignalFeed` panel. _PR #14: `SignalFeed.ts` — `/ws/signals` WS, otomatik yeniden bağlanma, max 50 sinyal, en yeni üstte; "Sinyaller" tab (klavye kısayolu 5)._
- [x] 3.7 Eski 4 strateji + yeni 4 strateji (Sprint 3'te toplam 8): EMA cross, RSI mean-rev, BB rev, breakout, **donchian breakout, MACD div, supertrend, mean-reversion VWAP**. _Sprint 11'de `lightgbm_probability` ile güncel toplam 9 strateji._

### Sprint 4 — Paper Trading & Portföy
- [x] 4.1 SQLite şeması: `paper_trades`, `paper_portfolio`, `paper_equity_curve`. _Backend `paper/db.py` — 3 tablo + index'ler._
- [x] 4.2 Strateji-bazlı sanal cüzdan modeli (her strateji ayrı sandık). _`PaperDB.get_or_create_wallet()` — 10.000 TL başlangıç._
- [x] 4.3 `robot-executor` sub-agent'ı yaz (otonom işlem icra). _`PaperExecutor` — signal_bus'tan otomatik emir; lifespan'da asyncio task._
- [x] 4.4 Canlı PnL hesabı (gateway fiyatı × açık miktar). _`PaperExecutor.update_prices()` + `_equity_snapshot()`._
- [x] 4.5 TS'te `PortfolioPanel` v2: equity curve, drawdown, win rate, sharpe. _Chart.js equity + drawdown grafikleri, 6 metrik kartı, wallet seçimi, halt/resume._
- [x] 4.6 Audit trail (her trade JSON log). _SQLite `paper_trades` tablosu — tüm alanlar kayıt altında._
- [x] 4.7 Risk limitleri (her cüzdana max %, gün-içi stop-out). _`DAILY_LOSS_LIMIT_PCT=10%`, `POSITION_SIZE_PCT=10%`, gün sonu otomatik reset, limitten halt._

### Sprint 5 — Agent + Skill + MCP + Hook Kurulumu
- [x] 5.1 `.claude/agents/data-validator.md` yaz. _IQR spike filter testi, OHLCV doğrulama, cache tutarlılığı._
- [x] 5.2 `.claude/agents/quant-researcher.md` yaz. _Yeni strateji fikirleri, parametre tarama, literatür tarama._
- [x] 5.3 `.claude/agents/backtest-runner.md` yaz. _POST /api/backtest/run ile çalıştırma ve raporlama._
- [x] 5.4 `.claude/agents/frontend-builder.md` yaz. _TS/Vite/lightweight-charts, mimari kurallar, kalite kontrol._
- [x] 5.5 `.claude/agents/backend-builder.md` yaz. _FastAPI/SQLite/Worker, test prosedürü._
- [x] 5.6 `.claude/agents/robot-executor.md` yaz. _Paper-trading pozisyon izleme, risk analizi._
- [x] 5.7 `.claude/agents/code-reviewer.md` yaz. _Diff analizi, kalite kontrolü, mimari uyumluluk._
- [x] 5.8 `.claude/agents/devops-engineer.md` yaz. _Docker Compose, healthcheck, launchd._
- [x] 5.9 `borsa-mcp` konfigürasyon hazırlandı (`.mcp.json`). _Kurulum: `claude mcp add borsa --type stdio --command "uvx" --args ["--from","git+https://github.com/saidsurucu/borsa-mcp","borsa-mcp"]`._
- [x] 5.10 `tradingview-mcp` konfigürasyon hazırlandı (`.mcp.json`). _Kurulum: `claude mcp add tradingview --type stdio --command "npx" --args ["-y","tradingview-mcp"]`._
- [x] 5.11 `tradermonty/claude-trading-skills`'ten 8 skill kopyalandı/uyarlandı. _backtest-expert, position-sizer, technical-analyst, market-news-analyst, signal-postmortem, strategy-pivot-designer, scenario-analyzer, risk-manager._
- [x] 5.12 Projeye özel 7 skill yazıldı. _validate-spike-filter, run-backtest, health-check, morning-briefing, paper-trade-status, deploy-stack, session-recap._
- [x] 5.13 `.claude/settings.json`'a hook'lar eklendi. _SessionStart (check-services.sh), Stop (auto-recap.sh), SubagentStop (persist-agent-output.sh)._
- [x] 5.14 5 slash command yazıldı. _/devam, /backtest, /sinyal, /durum, /strateji-yeni._
- [x] 5.15 Memory persistence: `session-recap.md` + hook'lar oluşturuldu. _auto-recap.sh oturum sonunda otomatik; load-recent-state.sh oturum başında yükler._

### Sprint 6 — AI Sinyal Motoru (Hibrit)
- [x] 6.1 Kural motorunu güçlendir: 8 sinyal tipi (mevcut 3 → 8). _Sinyal gücü (1-10), RSI/trend/ATR metadata, konsensüs (5+ strateji → STRONG_BUY/STRONG_SELL). _compute_strength() + _compute_rsi() + _trend_direction()._
- [x] 6.2 `morning-briefing` skill: Claude API ile sabah BIST 100 özeti + 3 odak hisse. _Sprint 5'te `.claude/skills/morning-briefing/SKILL.md` yazıldı._
- [x] 6.3 `scenario-analyzer` skill (haber → senaryo → etki). _Sprint 5'te `.claude/skills/scenario-analyzer/SKILL.md` yazıldı._
- [x] 6.4 `signal-postmortem` skill (kapanan trade → öğrenme). _Sprint 5'te `.claude/skills/signal-postmortem/SKILL.md` yazıldı._
- [x] 6.5 ML model temelleri: LightGBM readiness gate. _`quant_engine/research/lightgbm_model.py` + `scripts/ml_readiness.py`; veri yetersizse sahte model yok._
- [x] 6.6 AI sinyal feed'i `WS /ws/signals`'e fan-out. _Mevcut `/ws/signals` endpoint'i yeni sinyal tiplerini (STRONG_BUY/STRONG_SELL) + metadata desteğini otomatik taşıyor. SignalBus.publish() metadata parametresi eklendi._

### Sprint 7 — Always-On & Bildirim
- [x] 7.1 `Dockerfile.api`, `Dockerfile.workers`, `Dockerfile.notifier`. _3 ayrı Dockerfile, Python 3.11 slim._
- [x] 7.2 `docker-compose.yml` (api, workers, db, nginx, notifier). _API (8000), notifier, nginx reverse proxy (80); healthcheck'li._
- [x] 7.3 Healthcheck'ler tüm servislere. _docker-compose healthcheck: curl /api/health, 30s interval._
- [x] 7.4 Telegram bot (`backend/notifier/telegram.py`). _httpx async client, sinyal formatı, günlük rapor._
- [x] 7.5 Email (smtp, günlük rapor). _`backend/notifier/email.py` — SMTP TLS, HTML rapor template._
- [x] 7.6 macOS desktop notification (sadece lokal mod). _`macos_notify()` — AppleScript `display notification`, Glass ses._
- [x] 7.7 In-app toast (TS). _`SignalFeed.showToast()` — STRONG_BUY/STRONG_SELL sinyallerinde sağ üst toast, 5sn otomatik kapanma, slide-in animasyon._
- [x] 7.8 `.env.example` (token'lar, smtp). _Telegram, SMTP, notifier, API port konfigürasyonu._
- [x] 7.9 `make up` / `make down` Makefile. _up, down, restart, logs, status, build, dev, test, lint, health, paper kısayolları._
- [x] 7.10 Stres testi: 1 saat 100 sembol paralel polling otomasyonu. _`make stress-live`; smoke koşusu 470 istek / 0 altyapı hatası._

### Sprint 8 — Test, Doküman, Hand-off
- [x] 8.1 README.md güncelle (yeni mimari). _Mimari diyagramı, özellik listesi, proje yapısı, sprint tablosu._
- [x] 8.2 `docs/MIMARI.md`, `docs/AGENT_REHBERI.md`, `docs/SKILL_REHBERI.md`. _5 katmanlı mimari dokümanı, 8 agent rehberi, 15 skill + 5 command + 4 hook rehberi._
- [x] 8.3 `tests/e2e/` Playwright (TS frontend smoke). _`piyasapilot-v2/tests/e2e/smoke.spec.ts`; 2 test passed._
- [x] 8.4 Backtest paritesi testi (Python API sonuçları tutarlı). _Güncel tam paket 328 pytest geçiyor; `test_backtest_api.py` 9 strateji doğruluyor._
- [x] 8.5 Memory testi: session-recap.md + hook'lar. _auto-recap.sh oturum sonunda otomatik; load-recent-state.sh başlangıçta yükler._
- [x] 8.6 Final demo doğrulama kapıları. _Docker up/restart, E2E, MCP ve stres smoke bu oturumda çalıştırıldı._

### Sprint 9 — Polish & Production Hardening
- [x] 9.1 `ILERLEME.md` ve `ROADMAP.md` güncelle (Sprint 1–8 tamamlandı). _Tarih, durum tablosu, PR tablosu ve sıradaki adım güncel._
- [x] 9.2 Frontend UI/UX iyileştirmeleri: STRONG sinyal badge, gradient glow, konsensüs metadata gösterimi. _badge-strong-buy/sell CSS, signal-strong left-border, signal-consensus satırı._
- [x] 9.3 `signalHTML()` fonksiyonunda STRONG_BUY/STRONG_SELL sinyal tiplerini doğru render et. _4 sinyal tipi ayırt ediliyor, TR.SIGNAL_STRONG_BUY/SELL eklendi, metadata (oran, RSI, trend) gösteriliyor._
- [x] 9.4 Vite build doğrulama: `npm run build` → 0 hata. _38 modül, CSS 17KB + JS 83KB + charts 370KB, 403ms._
- [x] 9.5 Backend API doğrulama: `create_app()` + `list_blueprints()` import testi. _9 strateji, PaperDB, SignalGenerator tümü import başarılı._
- [x] 9.6 Frontend tarayıcı testi. _Playwright Chromium smoke: 5 tab, açılış sekmesi persistence, Telegram tercih paneli._
- [x] 9.7 `planlama.md` Bölüm 13 doğrulama senaryoları (yapılabilenler). _Spike filter 5/5, backtest 24/24, signal 22/22, paper 2/2, strategy 50/50 — toplam 292/292 geçiyor._
- [x] 9.8 `ogrenilenler.md` Sprint 9 bölümü eklendi.
- [x] 9.9 Git commit: Sprint 9 tamamlandı.
- [x] 9.10 `backend/workers/__main__.py` — standalone cache-filler entrypoint yazıldı.
- [x] 9.11 `Dockerfile.workers` düzeltildi — `python -m backend.workers` ile standalone modu kullanıyor.
- [x] 9.12 `docker-compose.yml` güncellendi — workers servisi `split` profiliyle eklendi; mimari notu eklendi.
- [x] 9.13 Planlama açık maddeleri kapatıldı (Telegram/SMTP → `.env` bekliyor, BIST listesi yeterli).

### Sprint 10 — Gerçek Veri Güven Kapısı ve MCP Entegrasyonu

#### Aşama 1 — ProviderRouter + MarketDataResult ✅
- [x] 10.1 Ortak piyasa veri modelleri: `MarketDataResult`, `MarketDataHealth`, `MarketDataStatus`.
- [x] 10.2 `ProviderRouter`: BIST, VİOP ve kripto sembollerini doğru provider'a yönlendirir.
- [x] 10.3 BIST provider: Yahoo Finance best-effort public kaynak; veri yoksa `no_data`.
- [x] 10.4 VİOP provider: lisanslı kaynak yoksa sahte bar üretmeden `not_configured`.
- [x] 10.5 Crypto provider: Binance public REST + fallback.
- [x] 10.6 `/api/data/providers/health` endpoint'i.
- [x] 10.7 `/api/v2/candles` response metadata: `is_real`, `status`, `provider_name`, `source`.
- [x] 10.8 SignalGenerator gerçek veri kapısı: `is_real=true` ve `status in {"ok","live"}` olmadan sinyal yok.
- [x] 10.9 Telegram `/fiyat`, `/sinyal`, `/strateji` komutları provider metadata'sını kontrol eder.
- [x] 10.10 Telegram bildirim tercihleri API + frontend kontrol paneli.
- [x] 10.11 Doğrulama: provider/router, signal gate, Telegram handler testleri; güncel tam paket `328 passed`, TSC ve Vite build temiz.

#### Aşama 2 — borsa-mcp Entegrasyonu
- [x] 10.12 `borsa-mcp` proje MCP konfigürasyonu çalışır hale getirildi. _`scripts/mcp_uvx.sh` wrapper + `.mcp.json`; `claude mcp list` → borsa ✓ Connected._
- [x] 10.13 `tradingview-mcp` npm paketinin yayından kalktığı doğrulandı ve GitHub+uvx yoluna taşındı. _`claude mcp list` → tradingview ✓ Connected._
- [x] 10.14 MCP smoke doğrulaması eklendi: `python scripts/verify_mcp.py`.
- [x] 10.15 `/morning-briefing` entegrasyon yolu MCP üzerinden hazır; agent/skill dokümanı güncellendi.
- [x] 10.16 Lisanslı BIST/VİOP HTTP feed köprüsü eklendi. _`BIST_HTTP_URL_TEMPLATE`, `VIOP_HTTP_URL_TEMPLATE`; sahte veri yok, gerçek feed varsa `is_real=true`._
- [x] 10.17 Binance WS reset dayanıklılığı eklendi. _Reconnect metadata, jitter'lı backoff, health alanları ve unit test._
- [x] 10.18 Telegram `/kontrol` doğrulaması eklendi. _Handler smoke: `python scripts/telegram_roundtrip_check.py`; canlı token varsa `--live` getMe kontrolü._
- [x] 10.19 Playwright E2E smoke tamamlandı. _5 tab + açılış sekmesi persistence + Telegram tercih paneli; Sprint 11'de mobil/localStorage ekleriyle 4 teste çıktı._
- [x] 10.20 Docker build/up/restart doğrulandı. _`docker compose build`, `docker compose up -d`, `bash scripts/docker_restart_check.sh`._
- [x] 10.21 Stres testi otomasyonu eklendi ve smoke koşuldu. _15 sn / 30 sembol / 470 istek / 0 altyapı hatası; 1 saatlik hedef için `make stress-live`._
- [x] 10.22 LightGBM temeli eklendi. _Feature/readiness gate; veri yetersizse sahte model üretmez._

---

## 12. Açık Sorular (Kalan netleştirmeler)

- [x] AI sinyal motoru hibrit yaklaşımı — onaylandı (Sprint 6).
- [x] Paper trading — strateji-bazlı izole sandık + risk limitleri onaylandı (Sprint 4).
- [x] Docker konumu — Mac şimdilik, taşınabilir tutulacak (Sprint 7).
- [x] Telegram bot chat ID — `.env` içinde kalır; endpoint/log/Telegram cevabı maskeleme ve `telegram_roundtrip_check.py` doğrulaması hazır.
- [x] Email SMTP — `.env.example` + `backend.notifier.email.email_status()` + `/api/notifier/status.email` ile güvenli durum raporu hazır.
- [x] BIST 100 listesi + 20 kripto + FX/Emtia listesi — 98 BIST + 10 kripto + FX/Emtia aktif; yeterli kapsama.

---

## 13. Doğrulama (Uçtan Uca Test)

- [x] **Veri:** `/api/v2/candles` cache-aside + provider health + `no_data/not_configured` HTTP 200 ayrımı testlendi.
- [x] **WebSocket:** Binance WS health metadata (`last_message_at`, reconnect count) ve Playwright UI smoke doğrulandı.
- [x] **Spike filtre:** `tests/unit/test_spike_filter.py` (yapay outlier inject). _5/5 passed._
- [x] **Backtest paritesi:** `tests/*backtest*`; 9 strateji `list_blueprints()` ile doğrulandı.
- [x] **Always-on:** Docker build/up + `scripts/docker_restart_check.sh` geçti. _Not: `docker compose kill` Docker tarafından manuel durdurma sayıldığı için test `docker compose restart api` ile health dönüşünü ölçer._
- [x] **Stres:** `scripts/stress_live_data.py` eklendi; smoke 470 istek / 0 altyapı hatası. _Tam hedef: `make stress-live`._
- [x] **Agent:** `.claude/` dizini altında 8 sub-agent, 15 skill, 5 slash command, hook'lar mevcut ve yapılandırılmış.
- [x] **Skill:** `.claude/skills/morning-briefing/SKILL.md` mevcut; tetikleme rehberi `docs/SKILL_REHBERI.md`'de.
- [x] **MCP:** `claude mcp list` → `borsa` ve `tradingview` Connected.
- [x] **Notifier:** Telegram tercih UI, email status, handler smoke ve notifier status endpoint testleri geçiyor; gerçek token varsa canlı gönderim kodu hazır.

---

## 14. Riskler ve Azaltım

| Risk | Olasılık | Etki | Azaltım |
|------|----------|------|---------|
| yfinance rate-limit (60/dk) | Yüksek | Veri kaybı | Worker batch + exponential backoff + borsapy fallback |
| Binance WS bağlantı düşmesi | Orta | Kısa veri boşluğu | Auto-reconnect + REST snapshot ile boşluk doldurma |
| BIST 15dk gecikmeli verinin bile bozuk gelmesi | Orta | Yanlış sinyal | IQR spike filter + iki provider çapraz kontrol |
| Docker Mac'te kaynak tüketimi | Düşük | Yavaşlık | Kaynak limitleri (`mem_limit`) |
| Tam otomatik paper trading'de bug → tüm sandık yanması | Orta | Kayıp eğitim değeri | Strateji-bazlı izole sandık + günlük max DD limiti + audit trail |
| MCP sunucularının kararsızlığı | Orta | Skill bozulması | Fallback olarak doğrudan Python kütüphane |
| Memory persistence script'i kırılırsa | Düşük | Oturum geçişi rahatsız | Manuel `/devam` slash komutu yedek |

---

## 15. Kaynak Linkler

- [VoltAgent awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills)
- [aitmpl.com — Claude Code Templates](https://www.aitmpl.com/)
- [saidsurucu/borsa-mcp](https://github.com/saidsurucu/borsa-mcp)
- [saidsurucu/borsapy](https://github.com/saidsurucu/borsapy)
- [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp)
- [Claude Code Agent Teams (resmi)](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Sub-agents (resmi)](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Hooks (resmi)](https://code.claude.com/docs/en/hooks)

---

## 16. Sprint 11 — Üretim Sertleştirme + Canlı Veri + ML

> Sprint 0–10 tamamlandı (2026-04-30). Sprint 11 adımları bağımsız; dış credential gerektirenleri beklerken diğerleri yapılabilir.

### 16.1 Lisanslı BIST/VİOP Feed Bağlantısı _(dış credential gerekli)_
- [x] `.env` içinde `BIST_HTTP_URL_TEMPLATE` doldurulunca `BistProvider.fetch()` canlı doğrulama. _`scripts/provider_feed_check.py --require-config`; URL yoksa `external_credential_missing`, mock feed ile uçtan uca geçti._
- [x] `.env` içinde `VIOP_HTTP_URL_TEMPLATE` doldurulunca `ViopProvider.fetch()` canlı doğrulama. _Aynı script VİOP HTTP köprüsünü strict modda doğrular._
- [x] Provider health endpoint'ine `is_real` etiketi eklendi. _`MarketDataHealth.is_real`; lisanslı HTTP true, Yahoo fallback false._
- [x] Yahoo fallback durumunda `is_real: false` uyarı her zaman görünür. _BIST Yahoo best-effort artık gerçek/lisanslı veri sayılmaz; sinyal motoru güven kapısına takılır._

### 16.2 LightGBM Sinyal Modeli _(≥ 3 ay cache dolunca)_
- [x] `scripts/ml_readiness.py` ile cache yeterliliği doğrula. _Yetersiz veri `insufficient_data` olarak temiz raporlanır._
- [x] `quant_engine/research/lightgbm_model.py` üretim modunu aktive et. _Yeterli veri + `lightgbm` varsa model eğitir; yoksa sahte model yazmaz._
- [x] `make retrain` Makefile target — günlük yeniden eğitim cron. _`scripts/retrain_lightgbm.py`; yetersiz veri cron kırmaz, JSON rapor üretir._
- [x] SignalGenerator'a `lgbm_prob` skoru ekle (kural motoru yanında). _`LIGHTGBM_MODEL_PATH` varsa sinyal metadata'sına olasılık girer._
- [x] Backtest engine'de "LightGBM" strateji olarak listele (8 → 9). _`lightgbm_probability` stratejisi model yoksa HOLD döner._

### 16.3 Frontend Performans + UX _(tamamlandı)_
- [x] Sidebar lazy-load: scroll ile yükle (130 sembol tek seferde değil). _IntersectionObserver + sentinel; 15'lik batch'ler._
- [x] 768px altı mobil layout: tek sütun, ekran bölme gizlenir. _CSS @media query; sidebar gizle, tek sütun grid._
- [x] Chart indikatör toggle (EMA/RSI/MACD/BB/ATR/VWAP aç-kapa switch). _CSS görsel iyileştirmesi: yeşil dot, line-through toggle._
- [x] Sinyal geçmişi localStorage kalıcılığı (sayfa yenilenmede kaybolmaz). _persistSignals/restoreSignals + LS_SIGNAL_HISTORY._
- [x] Playwright E2E: mobil viewport + sinyal localStorage kalıcılığı. _Smoke suite 2'den 4 teste çıktı; restore bug'ı düzeltildi._

### 16.4 Gözlemlenebilirlik + Uyarılar _(tamamlandı)_
- [x] FastAPI Prometheus `/metrics` middleware (latency, cache hit rate, worker count). _Stdlib exposition format; dış bağımlılık yok._
- [x] Grafana dashboard JSON (`docker/grafana/`) — 3 panel: latency / cache / worker. _docker-compose.monitor.yml + prometheus.yml._
- [x] Worker çöküş → Telegram anında uyarı (WorkerHealthMonitor). _30s periyodik kontrol, 5dk cooldown._
- [x] `scripts/daily_health_report.py` — sabah 09:00 Telegram özeti. _/api/health çek, build_message, send_telegram._
- [x] `make monitor` target → Grafana localhost:3000. _docker compose overlay; `make monitor-down` ile kapat._

### 16.5 Güvenlik + Graceful Shutdown _(tamamlandı)_
- [x] `.env` validation başlangıçta: eksik kritik değer → servis başlamaz, açık hata. _backend/env_validator.py; STRICT_ENV_VALIDATION=1 modu._
- [x] `SIGTERM` → paper_trades SQLite flush → graceful exit. _Lifespan finally: paper_db.checkpoint() + WAL pragma._
- [x] API key auth middleware (X-API-Key header, dışa açılacaksa zorunlu). _backend/middleware/api_key_auth.py; /api/health muaf._
- [x] `docker compose down` sonrası WAL checkpoint doğrulama testi. _scripts/wal_checkpoint_test.py + make wal-check._

---

## 17. Sprint 12 — Kodsuz/Korumalı Strateji Lab + Long/Short Backtest

> Kaynak fikir: Matriks PDF dokümanlarındaki System Tester, Algo Trader, Explorer, indikatör builder, alarm, optimizasyon ve rapor mantığı incelendi. Kopyalama yok: ekran, metin, fonksiyon dili, C# yapısı veya marka akışı birebir alınmayacak. PiyasaPilot'a özgü, Türkçe, web tabanlı ve güvenli bir strateji laboratuvarı yapılacak.
>
> Kullanıcı hedefi: Enes kendi stratejisini kuracak/yazacak, geçmiş yıllarda deneyecek, grafikte nerede AL/SAT/SHORT/COVER yaptığını görecek ve "şu sermayeyle geçmişte denenseydi sonuç yaklaşık ne olurdu" raporunu alacak.

### 17.1 Ürün Kararı — Matriks Karşılığı Ama PiyasaPilot'a Özgü

- [x] Matriks `System Tester` fikrinin PiyasaPilot karşılığı: **Strateji Lab**.
- [x] Matriks `İndikatör Builder` fikrinin PiyasaPilot karşılığı: **Gösterge/Kural Tasarımcısı**.
- [x] Matriks `Explorer` fikrinin PiyasaPilot karşılığı: **Piyasa Tarayıcı**.
- [x] Matriks `Expert Advisor` fikrinin PiyasaPilot karşılığı: **Alarm ve Sinyal Danışmanı**. _Mevcut signal bus/notifier hattına bağlanır; Telegram/SMTP değerleri .env'e bağlı._
- [x] Matriks `Algo Trader` fikrinin PiyasaPilot karşılığı: **Paper Robot / Strateji Çalıştırıcı**.
- [x] Matriks `Optimizasyon` fikrinin PiyasaPilot karşılığı: **Parametre Deneyleri**.
- [x] UI dili PiyasaPilot'a ait olacak; Matriks adları, ekranları, doküman metinleri ve örnek kodları kopyalanmayacak.

### 17.2 Strateji Yazma/Kurma Akışı

- [x] Strateji Lab ekranı eklenecek. _TS StrategyPanel, Kural Lab/Hazır Strateji modlarıyla yenilendi._
- [x] Kullanıcı sembol seçebilecek: BIST, kripto, ABD, FX/emtia, VİOP destekli semboller. _Aktif chart pane/sidebar sembolü backtest formuna bağlandı._
- [x] Kullanıcı periyot seçebilecek: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1w`.
- [x] Kullanıcı tarih aralığı seçebilecek: başlangıç tarihi + bitiş tarihi.
- [x] Kullanıcı başlangıç sermayesi girecek: varsayılan `100.000 TL`.
- [x] Kullanıcı komisyon oranı girecek: varsayılan `%0.1`.
- [x] Kullanıcı slippage girecek: varsayılan `5 bps`.
- [x] Kullanıcı pozisyon büyüklüğü seçebilecek: varsayılan maksimum sermayenin `%20`si.
- [x] Kullanıcı strateji notu/açıklaması yazabilecek.
- [x] Kullanıcı stratejiyi kaydedebilecek; aynı adla kayıt yeni sürüm olarak saklanacak, eski kayıt ezilmeyecek. _StrategyStore her kaydı ayrı uid/checksum ile saklıyor; frontend Kayıtlı Stratejiler paneli açabiliyor._

### 17.3 Görsel Kurucu + Güvenli Formül Dili

- [x] İlk sürümde iki strateji yazma yolu birlikte olacak: görsel kurucu + gelişmiş güvenli formül editörü.
- [x] Görsel kurucu ana yol olacak: kullanıcı indikatör, karşılaştırma, kesişim, eşik, AND/OR bloklarıyla strateji kuracak. _Blok kurucu v1 EMA/SMA/RSI/C, kesişim/karşılaştırma, AND/OR ve hacim filtresi üretir._
- [x] Güvenli formül dili ileri kullanıcı yolu olacak; Python/C#/eval/exec/import/shell kesinlikle çalıştırılmayacak. _`quant_engine/strategy/spec.py` eval/exec kullanmadan tokenize/parse eder._
- [x] Formül dili sadece allowlist parser/AST ile çalışacak.
- [x] Alanlar: `O`, `H`, `L`, `C`, `V`, `HL2`, `HLC3`.
- [x] Fonksiyonlar v1: `SMA`, `EMA`, `RSI`, `MACD_LINE`, `MACD_SIGNAL`, `MACD_HIST`, `BB_UPPER`, `BB_MID`, `BB_LOWER`, `ATR`, `VWAP`, `HIGHEST`, `LOWEST`, `CROSS_UP`, `CROSS_DOWN`, `BARS_SINCE`.
- [x] Operatörler: `>`, `<`, `>=`, `<=`, `==`, `AND`, `OR`, parantez.
- [x] Strateji alanları: `long_entry`, `long_exit`, `short_entry`, `short_exit`, `stop_loss`, `take_profit`, `trailing_stop`.
- [x] Görsel kurucudan çıkan kural ile formül editöründeki kural aynı `strategy_spec` şemasına dönüşecek. _Blok kurucu doğrudan `long_entry/long_exit/short_entry/short_exit` DSL alanlarını dolduruyor._
- [x] Hatalı formülde satır/kolon, bilinmeyen fonksiyon, eksik parantez ve hatalı parametre Türkçe mesajla gösterilecek.

### 17.4 Örnek Kullanıcı Stratejileri

- [x] Örnek long strateji: `RSI(C,14) 30 altından yukarı dönerse ve C EMA(C,200) üstündeyse AL; RSI 70 üstüne çıkarsa veya C EMA(C,50) altına inerse SAT`.
- [x] Örnek trend stratejisi: `EMA 50 EMA 200'ü yukarı keserse AL; EMA 50 EMA 200'ü aşağı keserse SAT`.
- [x] Örnek short strateji: `C EMA(C,200) altındayken RSI 70 bölgesinden aşağı dönerse SHORT; RSI 40 altına inerse veya fiyat EMA 50 üstüne dönerse COVER`.
- [x] Örnek risk kuralı: `%3 stop loss`, `%8 take profit`, `%5 trailing stop`.
- [x] Örnek hacim filtresi: `AL/SHORT barındaki hacim son 20 bar hacim ortalamasının üstünde olmalı`. _Görsel kurucu `V > SMA(V,20)` filtresini ekler._

### 17.5 Backtest API ve Veri Kaynağı

- [x] `POST /api/backtest/run` geriye uyumlu kalacak.
- [x] Yeni `BacktestRequest v2` alanları eklenecek: `start_date`, `end_date`, `commission_rate`, `slippage_bps`, `max_position_pct`, `allow_short`, `source_mode`, `strategy_spec`.
- [x] `lookback_bars` desteklenmeye devam edecek; ancak tarih aralığı ana kullanım yolu olacak.
- [x] `source_mode=cache_then_provider`: önce cache bakılacak, eksik tarih aralığı provider ile doldurulacak.
- [x] `source_mode=cache_only`: sadece mevcut cache ile çalışacak, eksik veri varsa net hata verecek.
- [x] `source_mode=csv_import`: dışarıdan yüklenen OHLCV verisiyle backtest yapılacak.
- [x] CSV kolonları: `time` veya `date`, `open`, `high`, `low`, `close`, `volume`.
- [x] CSV doğrulama: tarih sırası, duplicate bar, boş fiyat, sıfır/negatif OHLC, eksik volume, spike/outlier uyarısı.
- [x] Provider metadata rapora yazılacak: `source`, `provider_name`, `is_real`, `status`, `data_coverage_pct`.
- [x] Veri eksikse raporda açıkça "Bu test veri aralığının tamamını kapsamıyor" uyarısı gösterilecek.

### 17.6 Long/Short Backtest Motoru

- [x] Mevcut `+1 AL / -1 SAT / 0 BEKLE` sinyal modeli trade intent modeline genişletilecek. _`BacktestEngine.run_intents` eklendi; eski `run` korundu._
- [x] Yeni intentler: `BUY`, `SELL`, `SHORT`, `COVER`, `HOLD`.
- [x] Long pozisyon: `BUY` ile açılır, `SELL` ile kapanır.
- [x] Short pozisyon: `SHORT` ile açılır, `COVER` ile kapanır.
- [x] Aynı barda çakışan long/short sinyal olursa işlem reddedilecek ve rapora uyarı yazılacak.
- [x] Long pozisyon açıkken yeni `BUY` yok sayılacak; short pozisyon açıkken yeni `SHORT` yok sayılacak.
- [x] Long açıkken `SHORT` sinyali gelirse varsayılan davranış: önce long kapanır, aynı barda short açılmaz.
- [x] Short açıkken `BUY` sinyali gelirse varsayılan davranış: önce short kapanır, aynı barda long açılmaz.
- [x] Execution kuralı korunacak: sinyal `bar[t].close`, emir `bar[t+1].open`.
- [x] Komisyon ve slippage hem long hem short işlemlerde uygulanacak.
- [x] Açık pozisyon test sonunda piyasa değeriyle final equity'ye katılacak ve raporda uyarı görünecek.
- [x] BIST short sonuçları "simülasyon" etiketiyle gösterilecek; gerçek piyasa uygunluğu garanti edilmeyecek.

### 17.7 Grafikte AL/SAT/SHORT/COVER Gösterimi

- [x] Backtest sonucu aktif grafiğe marker olarak gönderilecek.
- [x] `BUY`: yeşil yukarı ok.
- [x] `SELL`: kırmızı aşağı ok.
- [x] `SHORT`: turuncu aşağı ok.
- [x] `COVER`: mavi yukarı ok.
- [x] Marker tooltip içeriği: tarih, fiyat, adet, yön, tetikleyen koşul, işlem PnL, kümülatif equity.
- [x] Grafiğin altında equity curve ve drawdown alt paneli gösterilecek. _Strateji Lab rapor panelinde equity + drawdown aynı grafikte._
- [x] İşlem tablosundaki trade satırına tıklanınca grafik ilgili bar'a odaklanacak.
- [x] Son açık pozisyon varsa grafikte "açık pozisyon" etiketi görünecek.

### 17.8 Backtest Sonuç Raporu

- [x] Rapor başlığı: strateji adı, sembol, periyot, tarih aralığı, veri kaynağı, test zamanı.
- [x] Ana metrikler: başlangıç sermayesi, bitiş sermayesi, net kar/zarar, toplam getiri %, yıllıklandırılmış getiri %, max drawdown %, toplam işlem.
- [x] Ek metrikler: win rate, profit factor, Sharpe, toplam komisyon, toplam slippage, en iyi işlem, en kötü işlem, ortalama kar, ortalama zarar.
- [x] Benchmark karşılaştırması: aynı dönemde buy & hold getirisi.
- [x] Sonuç metni net yazılacak: "Bu strateji seçilen tarih aralığında ve varsayımlarla test edilseydi yaklaşık sonuç budur; gelecek kazancı garanti etmez."
- [x] Rapor sekmeleri: Özet, İşlemler, Pozisyonlar, Performans, Sistem Bilgileri, Veri Uyarıları.
- [x] Sistem Bilgileri sekmesinde strateji kuralları, parametreler, risk ayarları ve backtest varsayımları gösterilecek.

### 17.9 Rapor Arşivi ve Dışa Aktarım

- [x] Her backtest sonucu SQLite arşivine kaydedilecek.
- [x] Arşivde strateji tanımı, parametreler, tarih aralığı, veri kaynağı, metrikler, equity curve, trades ve marker sinyalleri saklanacak.
- [x] Geçmiş raporlar listelenebilecek.
- [x] Eski rapor tekrar açılıp grafikte izlenebilecek. _Rapor GET endpoint'i hazır; frontend liste ekranı ayrı açık._
- [x] Eski rapor aynı ayarlarla yeniden çalıştırılabilecek. _Rapor Arşivi `Tekrar` butonu raporu açıp aynı ayarlarla yeniden POST eder._
- [x] JSON export: tam rapor.
- [x] CSV export: işlem listesi.
- [x] CSV export: equity curve.
- [x] CSV export: optimizasyon sonuçları. _Frontend Parametre Deneyi paneli CSV üretir._

### 17.10 Optimizasyon / Parametre Deneyleri v1

- [x] Kullanıcı parametre aralığı verebilecek: örn. RSI periyodu 7-21, EMA hızlı 10-50, EMA yavaş 100-250. _v1 comma-list grid: `10,20,30,50`._
- [x] İlk sürüm grid search olacak.
- [x] Her kombinasyon backtest edilecek.
- [x] Sonuç tablosu getiri, max drawdown, profit factor, win rate, işlem sayısı ve skor ile sıralanacak.
- [x] En iyi sonuç sadece "en yüksek getiri"ye göre seçilmeyecek; aşırı drawdown ve az işlem yapan sonuçlar uyarı alacak.
- [x] En iyi parametreye tıklayınca grafik ve rapor o koşuyla açılacak. _`Uygula` butonu spec'i doldurup backtest'i yeniden çalıştırır._
- [x] İleri sürüm notu: Bayesian optimizasyon sonra değerlendirilecek.

### 17.11 Piyasa Tarayıcı v2

- [x] Tek sembol backtest tamamlandıktan sonra aynı strateji sembol listesinde taranabilecek.
- [x] Tarama modları: BIST 100, kripto listesi, ABD listesi, FX/emtia listesi, özel liste.
- [x] Tarayıcı sonucu: sembol, son fiyat, son sinyal, sinyal tarihi, toplam getiri, max drawdown, işlem sayısı.
- [x] Sonuçlardan seçilen sembol grafikte açılacak.
- [x] İlk sürüm toplu gerçek emir göndermeyecek; sadece analiz ve paper-trading aday listesi üretecek.

### 17.12 Alarm ve Paper Robot Bağlantısı

- [x] Backtestte başarılı bulunan strateji "paper çalıştır" moduna alınabilecek.
- [x] Paper mode gerçek emir göndermeyecek.
- [x] Strateji sinyalleri mevcut `PaperExecutor` ve strateji-bazlı izole cüzdan yapısına bağlanacak.
- [x] Alarm kanalları: in-app toast, Telegram, email, macOS notification. _Signal bus/notifier bağlantısı Docker'da `api:8000` üzerinden doğrulandı; email gerçek gönderimi SMTP değerleri girilince aktif olur._
- [x] Alarmda veri kaynağı ve `is_real` durumu görünecek.
- [x] Gerçek veri kapısı korunacak: `is_real=true` ve güvenli provider status olmadan canlı/paper sinyal üretilmeyecek.

### 17.13 Test ve Kabul Kriterleri

- [x] DSL parser geçerli RSI/EMA/MACD/kesişim formüllerini parse eder.
- [x] DSL parser bilinmeyen fonksiyon, Python kodu, import, shell, dosya erişimi ve tehlikeli ifadeleri reddeder.
- [x] Görsel kurucudan üretilen DSL tekrar aynı `strategy_spec` yapısına döner.
- [x] Long giriş/çıkış doğru PnL üretir.
- [x] Short giriş/cover doğru PnL üretir.
- [x] Komisyon, slippage, pozisyon oranı ve açık pozisyon final equity hesabına yansır.
- [x] `bar[t].close` sinyal ve `bar[t+1].open` execution kuralı testle korunur.
- [x] Tarih aralığıyla backtest çalışır.
- [x] Cache eksikse provider doldurma yolu çalışır veya net hata döner.
- [x] CSV import geçerli/geçersiz dosyada doğru davranır.
- [x] Backtest raporu arşivlenir, tekrar okunur ve export edilir.
- [x] Frontend grafikte `BUY`, `SELL`, `SHORT`, `COVER` marker'larını doğru gösterir.
- [x] İşlem tablosu ve marker tooltip fiyat/tarih/adet/PnL açısından aynı sonucu gösterir.
- [x] Playwright smoke: strateji oluştur, backtest çalıştır, marker gör, rapor export et. _Mevcut e2e smoke 4/4 geçti; API backtest/export smoke konteynerde çalıştı._

### 17.14 Sprint 12 Teslim Tanımı

- [x] Enes görsel kurucuyla bir strateji oluşturabiliyor.
- [x] Enes güvenli formül diliyle aynı stratejiyi yazabiliyor.
- [x] Enes 3-5 yıllık tarih aralığı seçip cache/provider veya CSV verisiyle backtest yapabiliyor.
- [x] Grafikte AL/SAT/SHORT/COVER noktaları görünüyor.
- [x] Sistem "100.000 TL ile denenseydi sonuç X TL, net kar Y TL, getiri Z%" raporu veriyor.
- [x] Rapor arşive kaydoluyor.
- [x] Rapor JSON/CSV dışa aktarılıyor.
- [x] Long/short PnL ve execution timing testleri geçiyor.
- [x] Gerçek emir gönderimi yok; paper-trading güvenli simülasyon olarak kalıyor.

### 17.15 Uygulama Sırası

- [x] 12.1 DSL sözlüğü, parser ve `strategy_spec` şeması.
- [x] 12.2 Backtest request/response v2 ve rapor şeması.
- [x] 12.3 Long/short trade intent motoru.
- [x] 12.4 Backtest rapor arşivi.
- [x] 12.5 CSV import ve veri doğrulama.
- [x] 12.6 Strateji Lab frontend ekranı.
- [x] 12.7 Grafik marker + tooltip + işlem tablosu senkronu.
- [x] 12.8 Export endpoints.
- [x] 12.9 Grid optimizasyon v1.
- [x] 12.10 Piyasa Tarayıcı v2.
- [x] 12.11 Paper robot ve alarm bağlantısı. _Paper bağlantısı tamam; notifier WebSocket bağlantısı sağlıklı. Gerçek Telegram/email gönderimi .env secret değerlerine bağlı._

---

## 18. Öğrenilenler — Hafıza Snapshot (2026-04-30)

> Bu bölüm, oturum kaybolursa veya context dolarsa **tek başına okunarak** nereden devam edileceğini söyler. Yeni Claude penceresi: önce bu bölümü oku, sonra Sprint listesinden ilk açık tick'i bul.

### 18.1 Repo Gerçekleri (Doğrulanmış)
- **Konum:** `/Users/enes/AgentWorkspace/Backtest`
- **İki katman:** Python backend (`quant_engine/`) + TypeScript frontend (`piyasapilot-v2/`).
- **Sağlam, dokunulmayacak parçalar:**
  - `quant_engine/backtest/engine.py` — lookahead-free, testli BacktestEngine. Signal bar `t` close'da üretilir, execution bar `t+1` open'da. `tests/unit/test_financial_correctness.py` koruyor.
  - `quant_engine/data/providers/binance_provider.py` — public REST `data-api.binance.vision`, sayfalama `for _ in range(20)` × 1000 kline. Rate limit 1200 req/dk.
  - `quant_engine/data/providers/yfinance_provider.py` — `.IS` suffix mantığı, fallback `period="5d"`/`period="1mo"`. Rate limit 60 req/dk.
  - `quant_engine/data/live_feed.py` — `resolve_symbol()` fonksiyonu USDT → ccxt, TRY/diğer → yfinance ayrımı yapıyor.
  - `quant_engine/strategy/decision_engine.py` — `Decision = Literal["AL","SAT","BEKLE","VERİ YETERSİZ"]`. EMA200+BB+RSI füzyonu.
  - `quant_engine/workspace/manager.py` — `BIST30_CORE_SYMBOLS` tuple var, atomic JSON write (temp → rename).
- **TS frontend katmanları:**
  - `src/app.ts` — 4 tab (chart, portfolio, strategy, screener), keybindings 1–4 + F.
  - `src/core/DataEngine.ts` — `assetType === 'crypto'` ise `WebSocketManager`, değilse `PollingManager`.
  - `src/core/AnomalyFilter.ts` — IQR + Z-Score (kısmi, V2 hybrid değil).
  - `src/components/ChartPanel.ts` — lightweight-charts v4.2.0, 4 alt-grafik (Main/Volume/RSI/MACD), CORS proxy `corsproxy.io`.
  - `src/strategies/` — TrendFollowing, MeanReversion, BreakoutDetector (TS implementasyonu — Sprint 3'te sökülecek).
  - `src/indicators/` — 9 indikatör (EMA, SMA, RSI, MACD, BB, ATR, VWAP, Stochastic).
- **Persistence:** SQLite (`data/strategy_lab/strategies.sqlite3`), JSON workspace (`data/workspaces/workspace.json`), DuckDB+Parquet (`data/bist/symbol=*/data.parquet`).
- **Mevcut endpoint'ler (`live_server.py` port 8000):** `/api/health`, `/api/market/defaults`, `/api/market/chart`, `/api/workspace`, `POST /api/paper/signal`. CORS `*`.

### 18.2 Veri Sağlayıcı Sınırları (KRİTİK)
- **yfinance 15 dk:** Sadece **5 gün** geriye gider. (`period="5d"` hardcoded.)
- **Binance 15 dk:** ~**7 gün** (1000 kline × 15 dk = 250 saat).
- **borsapy** (saidsurucu): yfinance benzeri Python kütüphanesi; BIST için 1m/3m/5m/15m/30m/45m/1d/1w/1M intervals; `period="max"` mümkün; ~15 dk gecikmeli; 758 BIST şirketi, 836+ TEFAS fonu.
- **borsa-mcp** (saidsurucu): FastMCP server, 26 tool, BIST + US + TEFAS + KAP haberleri + döviz/emtia + ekonomik takvim. `uvx --from git+https://github.com/saidsurucu/borsa-mcp borsa-mcp` ile kurulur.
- **Sonuç:** 1 ay tarihsel istemek için **backend rolling cache** zorunlu — worker her 60 sn çağrılan 5–7 günlük pencereleri SQLite'a `INSERT OR IGNORE` ile birikir.

### 18.3 Enes'in Onayladığı Kararlar (Kesin)
1. ✅ TS terminal ana arayüz; Streamlit kalkar.
2. ✅ Backend rolling cache (SQLite/Parquet, kayar pencere).
3. ✅ İlk faz ~130 sembol: BIST 100 + 20 büyük kripto + USD/TRY + altın.
4. ✅ Docker Compose ilk başta Mac'te (Docker Desktop / colima). Taşınabilir.
5. ✅ Strateji motoru tek kaynak: Python `BacktestEngine`. TS sadece görüntüler.
6. ✅ AI hibrit: kural motorunu 8 sinyal tipine çıkar + Claude API sabah brifing + cache 6 ay birikince LightGBM.
7. ✅ Paper trading tam otomatik AMA strateji-bazlı izole sandık (her strateji 10.000 TL); günlük max %5 zarar, pozisyon başı max %10, audit trail.
8. ✅ Bildirim 4 kanal: Telegram + Email + In-app toast + macOS desktop.

### 18.4 Claude Code Ekosistemi — Pratik Bilgi
- **Sub-agent** (`.claude/agents/<name>.md`): Ayrı context window, kendi system prompt'u, tools allowlist, model seçimi (Haiku ucuz/deterministic, Sonnet research, Opus deep). Main session geçmişini görmez. Maliyet düşük çünkü sonuç özetlenip ana context'e döner.
- **Agent Team** (deneysel, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): Çoklu paralel session, paylaşımlı task list, peer-to-peer messaging, file locking. Token maliyeti yüksek. Tasarımdaki 8 agent için **subagent yeterli**, agent team'i sadece çoklu PR review/cross-layer iş için ileride kullanırız.
- **Skill** (`.claude/skills/<name>/SKILL.md`): Reusable playbook. User invoke (`/skill-name`) veya Claude oto-tetik (description-match). Main context'te kalır, supporting files (scripts, refs) içerebilir.
- **Hook** (`settings.json`): SessionStart/Stop, PreToolUse/PostToolUse, UserPromptSubmit, SubagentStart/Stop, TeammateIdle/TaskCreated/TaskCompleted. Shell script çalıştırır, exit code 2 = blok et.
- **MCP** (`~/.mcp.json` veya proje `.mcp.json`): External tool feed. stdio (lokal proc) vs HTTP/SSE (remote). `claude mcp add ...` ile kurulur.
- **Slash Command** (`.claude/commands/<name>.md`): User `/<name>` yazınca tetikler. Frontmatter: `description`, `argument-hint`, `allowed-tools`, `model`.

### 18.5 Hazır Kullanılacak Üçüncü-Parti Bileşenler
- **Sub-agent kaynağı:** [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) — `quant-analyst`, `fintech-engineer`, `risk-manager`, `data-engineer`, `ml-engineer`, `code-reviewer`, `debugger`, `docker-expert`, `fastapi-developer`, `react-specialist`, `typescript-pro`, `python-pro`.
- **Skill kaynağı:** [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) — 47 skill. Bizim için seçilen 8: `backtest-expert`, `position-sizer`, `technical-analyst`, `market-news-analyst`, `signal-postmortem`, `strategy-pivot-designer`, `scenario-analyzer`, `exposure-coach`. (FMP API free tier 250 req/gün — bazıları gerektirir.)
- **MCP'ler:** `borsa-mcp`, `tradingview-mcp` (atilaahmettaner), `yahoo-finance-mcp` (Alex2Yang97 — yedek), opsiyonel `playwright-mcp` (isyatirim scraping yedek).
- **Şablon marketi:** [aitmpl.com](https://www.aitmpl.com/) — JS-rendered, alt-sayfaları doğrudan WebFetch ile okumadı; gerekirse claude-code-templates CLI ile çekilir.

### 18.6 Mimari Tek Cümle Özetleri
- **Veri akışı:** `Worker (yfinance/Binance/borsapy) → SpikeFilter (IQR + hacim) → SQLite cache → FastAPI gateway → (REST GET /api/chart) + (WS /ws/quotes) → TS DataEngine → ChartPanel`.
- **Backtest akışı:** `TS StrategyPanel → POST /api/backtest/run → Python BacktestEngine → BacktestResult → TS Chart.js equity curve`.
- **Sinyal akışı:** `Bar kapanışı → DecisionEngine + (sabah Claude API briefing) → /ws/signals → TS SignalFeed + Notifier (telegram/email/desktop/toast)`.
- **Paper trading akışı:** `/ws/signals → robot-executor sub-agent → SQLite paper_trades + paper_portfolio → canlı PnL hesabı (gateway fiyatı × açık miktar) → /ws/portfolio → PortfolioPanel`.
- **Always-on:** `docker-compose up -d` → api + workers + db + nginx + notifier; `restart: unless-stopped`; healthcheck'ler.

### 18.7 Memory Persistence Stratejisi (3 Katmanlı)
1. **`/Users/enes/AgentWorkspace/Backtest/CLAUDE.md`** — sabit bilgi: mimari, port haritası, çalışma kuralları. Her oturumda otomatik yüklenir.
2. **`/Users/enes/AgentWorkspace/Backtest/planlama.md`** — bu plan. Tick'ler her sprint sonunda güncellenir. Tek doğruluk kaynağı.
3. **`.claude/memory/session-recap.md`** — `Stop` hook'u her oturum sonunda otomatik yazar; `SessionStart` hook'u yeni oturumda systemMessage olarak inject eder. Böylece Claude sıfırdan keşfetmek zorunda kalmaz.

Globaldeki `~/.claude/projects/-Users-enes-AgentWorkspace-Backtest/memory/` (kullanıcı profili, geçmiş kararlar) zaten dolu ve aktif.

### 18.8 Şu Anki Durum (Snapshot — 2026-04-30)
- ✅ **Sprint 0–10 tamamlandı:** Gateway, cache, workers, frontend, backtest, paper trading, notifier, Telegram asistan, ProviderRouter, MCP, E2E, Docker ve stres kapıları hazır.
- ✅ **MCP:** `borsa` ve `tradingview` Connected.
- ✅ **Docker:** build/up/restart check geçti.
- ✅ **E2E:** Playwright smoke 2/2 geçti.
- ✅ **Stres:** smoke 470 istek / 0 altyapı hatası.
- ✅ **Sıradaki:** Sprint 11 yalnızca gerçek dış credential/lisans URL'leri sağlandığında canlı bağlama ve uzun izleme.

### 18.9 Yeni Claude Penceresi Açıldığında — Yapılacaklar
1. `planlama.md` (proje köküne kopyalandıysa) ya da bu dosyayı oku.
2. Bölüm 17.8'deki "Şu Anki Durum" üzerinden nereye kalındığını anla.
3. `git log --oneline -20` ile son commit'leri ve cloud session'ından gelen PR'ı kontrol et.
4. Sprint 11 dış bağlantı değerleri verilmediyse önce test/doğrulama kapılarını çalıştır.
5. Risk listesini (Bölüm 14) hatırla; her teknik karar bu çerçevede değerlendirilsin.

### 18.10 Önemli Linkler
- [VoltAgent awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills)
- [saidsurucu/borsa-mcp](https://github.com/saidsurucu/borsa-mcp)
- [saidsurucu/borsapy](https://github.com/saidsurucu/borsapy)
- [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp)
- [Claude Code Sub-agents docs](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Agent Teams docs](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Hooks docs](https://code.claude.com/docs/en/hooks)
- [aitmpl.com](https://www.aitmpl.com/)
- Cloud Ultraplan session: `https://claude.ai/code/session_017FSq3n9MJQELSXcEA8iiFN`

---

## 19. Matriks Grafik Menüleri Uyarlama Planı (2026-05-01)

> **Kaynak:** `/Users/enes/Downloads/_matriks-veri-terminali-grafik-menuleri-dokumani.pdf`
> **İnceleme durumu:** 70 sayfalık Matriks Grafik Menüleri PDF'i metin ve görsel temas sayfalarıyla tarandı.
> **Kural:** Amaç Matriks'i kopyalamak değil; olgun terminal davranışlarını PiyasaPilot'un mevcut `lightweight-charts`, TS component yapısı, backend cache ve paper/backtest mimarisiyle uyumlu yeni özelliklere çevirmek.
> **Bu oturum sınırı:** Kod yazılmadı. Bu bölüm yalnızca uygulanacak işleri ve kabul kriterlerini tanımlar.

### 19.1 Mevcut Grafik Gerçekleri

- [x] `piyasapilot-v2/src/components/ChartPanel.ts` mevcutta ana mum/bar/çizgi grafiği, hacim, RSI, MACD alt panelleri ve BB/EMA/VWAP overlay'lerini çiziyor.
- [x] `piyasapilot-v2/src/components/MultiChartLayout.ts` 1x1, 1x2, 2x1, 2x2 çoklu pencere düzenini yönetiyor.
- [x] `piyasapilot-v2/src/indicators/` içinde EMA, SMA, RSI, MACD, Bollinger, ATR, VWAP, Stochastic hazır.
- [x] Mevcut grafik `setData()` sonunda sadece zaman ölçeğini `fitContent()` yapıyor; fiyat ölçeği, sembol değişimlerinde açıkça resetlenmiyor.
- [x] Backtest/paper sinyal marker'ları grafiğe basılıyor; fakat açık pozisyon maliyeti, yüzdesel kar/zarar, stop/take-profit ve işlem çizgileri henüz terminal seviyesinde değil.

### 19.2 Birinci Kritik Hata: Sembol Değişiminde Fiyat Skalası Merkezleme

- [ ] 10 TL civarı bir hisseden 1000 TL civarı bir hisseye, sonra tekrar düşük fiyatlı hisseye geçiş test senaryosu oluşturulacak.
- [ ] Sembol değişince fiyat skalası eski manuel/otomatik aralığı taşımayacak; yeni sembolün son görünen mumları dikeyde otomatik ortalanacak.
- [ ] Yeni veri seti yüklendiğinde ana seri, hacim ve alt indikatör panelleri için autoscale reset akışı tanımlanacak.
- [ ] Kullanıcı bilinçli olarak fiyat aralığını kilitlediyse bu tercih ayrı bir "Tarih aralığını koru / fiyatı yeniden ortala" ayarıyla yönetilecek.
- [ ] Kabul: `AKBNK.IS -> yüksek fiyatlı sembol -> düşük fiyatlı sembol` geçişlerinde ekran boş kalmayacak; son fiyat, mumlar ve son fiyat çizgisi görünür alanda olacak.
- [ ] Kabul: Sembol fiyat medyanı önceki sembole göre çok farklıysa sistem otomatik "price scale reset" yapacak; aynı sembolde timeframe değişiminde kullanıcı zoom tercihi korunabilecek.

### 19.3 Grafik Ölçeği ve Karşılaştırma Modları

- [ ] Ölçek menüsü eklenecek: `Lineer`, `Logaritmik`, `Yüzdesel`, ileride `Indexed/100`.
- [ ] Yüzdesel modda kullanıcı başlangıç tarihi/barı seçebilecek; o nokta %0 kabul edilip sonraki değişim yüzde olarak çizilecek.
- [ ] Yüzdesel mod çoklu sembol karşılaştırmasında birincil kullanım olacak: farklı fiyat seviyesindeki hisseler aynı panelde anlamlı karşılaştırılacak.
- [ ] "Farkı yüzdesel göster" davranışı crosshair bilgi paneline eklenecek: seçili bar için önceki kapanışa, başlangıç barına ve pozisyon maliyetine göre yüzde fark gösterilecek.
- [ ] "Birim" fikri PiyasaPilot'a uyarlanacak: TL/USD/USDT, XU100'e göre performans, başka sembole bölünmüş relatif grafik ve portföy para birimi görünümü ayrı modlar olarak planlanacak.
- [ ] Kabul: 10 TL ve 1000 TL fiyatlı iki sembol aynı grafikte karşılaştırılırken ya ayrı skala ya da yüzdesel normalize mod kullanılır; biri diğerini ekrandan dışarı itmez.

### 19.4 Son Fiyat, Referans Çizgileri ve Fiyat Etiketleri

- [ ] Son fiyat yatay çizgisi ve sağ fiyat skalasında renkli son fiyat etiketi standart hale getirilecek.
- [ ] Önceki kapanış seviyesi kesik çizgi olarak açılıp kapatılabilecek.
- [ ] BIST için tavan/taban seviyeleri çizgi olarak planlanacak; veri yoksa pasif/gri state gösterilecek.
- [ ] Paper/backtest pozisyonu varsa ortalama maliyet, başabaş, stop-loss, take-profit ve hedef fiyat çizgileri opsiyonel overlay olacak.
- [ ] Her çizgi için tooltip: fiyat, yüzde fark, mutlak fark, ilgili pozisyon/işlem bilgisi.
- [ ] Kabul: Kullanıcı grafikte "şu an neredeyim, maliyetim nerede, yüzde kaç kardayım/zarardayım" sorusunu panel değiştirmeden görebilecek.

### 19.5 İndikatör Merkezi v2

- [ ] Mevcut basit butonlar yerine sağ/üst açılır "İndikatörler" paneli tasarlanacak.
- [ ] Panelde arama, kategori, favori ve aktif indikatör listesi olacak.
- [ ] Her indikatör için parametre penceresi olacak: periyot, veri kaynağı (`close/open/high/low/hlc3/ohlc4`), renk, çizgi kalınlığı, çizgi tipi, bölge, öteleme.
- [ ] Aynı indikatörden birden fazla instance desteklenecek: örn. `EMA 9`, `EMA 21`, `EMA 50`, `SMA 200`.
- [ ] İndikatör bölgesi seçilebilecek: ana grafik overlay, yeni alt panel, mevcut alt panel.
- [ ] RSI/Stochastic gibi osilatörlerde 30/70, 20/80 alarm seviyeleri kalıcı çizgi olarak görünecek.
- [ ] İndikatör grupları tanımlanacak: "Trend seti", "Mean reversion seti", "Momentum seti" gibi kaydedilip tek tıkla uygulanacak.
- [ ] Kabul: Kullanıcı BB/EMA/VWAP/RSI/MACD dışında ATR ve Stochastic'i de panelden açıp kapatabilecek; parametre değişimi grafiği yeniden hesaplatacak.

### 19.6 Çizim ve Ölçüm Araçları

- [ ] İlk çizim seti: trend çizgisi, yatay çizgi, dikey çizgi, ray/sağa uzat, paralel çizgi, kanal, dikdörtgen, ok, not.
- [ ] Ölçüm aracı eklenecek: iki nokta arasında bar sayısı, süre, fiyat farkı, yüzde fark, yıllıklandırılmış yaklaşık getiri, risk/ödül oranı.
- [ ] Trend çizgisi özellikleri: isim, renk, kalınlık, çizgi tipi, başlangıç/bitiş zamanı, başlangıç/bitiş fiyatı.
- [ ] Trend çizgisi üzerinde yüzde değişim etiketi ve son değer fiyat skalası etiketi desteklenecek.
- [ ] Çizimler sembol + timeframe + layout bağlamında saklanacak; şablonla gelen çizimler ve sembole özel çizimler ayrılacak.
- [ ] İkinci faz çizim seti: Fibonacci düzeltme, Fibonacci extension/impulse, Fibonacci fan, zaman bölgeleri, regresyon kanalı.
- [ ] Üçüncü faz araştırma seti: Gann, Andrew's Pitchfork, quadrant, Tirone, otomatik trend/fibo.
- [ ] Kabul: Çizilen trendler pan/zoom sırasında doğru koordinatta kalacak ve sembol değişince yanlış sembolde görünmeyecek.

### 19.7 Trend ve İndikatör Alarmları

- [ ] Trend çizgisi kırılım alarmı planlanacak: fiyat trendi yukarı/aşağı kırınca in-app, Telegram, email, macOS bildirimi.
- [ ] İndikatör seviye alarmı planlanacak: RSI 30 altı/70 üstü, MACD kesişimi, fiyat EMA/SMA kesişimi, Bollinger band teması.
- [ ] Alarm listesi UI: aktif, tetiklendi, susturuldu, silindi durumları.
- [ ] Alarm kaynağı ve veri güvenilirliği gösterilecek: `is_real`, provider, gecikmeli/canlı.
- [ ] Paper robot bağlantısı kontrollü olacak; alarm otomatik emir değil, önce sinyal/paper aksiyonu üretir.
- [ ] Kabul: Trend çizgisi sağa uzatılmışsa kırılım alarmı anlamlı çalışır; çizgi silinirse alarm da pasif olur.

### 19.8 Çoklu Sembol, Çoklu Skala ve Data Eşitleme

- [ ] Aynı panelde karşılaştırma sembolü ekleme özelliği planlanacak; mevcut çoklu pencere düzeninden ayrı bir "compare overlay" davranışı olacak.
- [ ] Çoklu sembolde üç skala modu olacak: aktif sembol skalası, her sembole ayrı skala, yüzdesel normalize skala.
- [ ] Her sembolün renkli etiketi zaman aksı/legend üzerinde görünecek.
- [ ] Tatil/gap farkları için data serisi eşitleme planlanacak: eksik günlerde boşluk, forward-fill veya ortak takvim seçenekleri açıkça ayrılacak.
- [ ] Aynı skalaya çizme sadece fiyat seviyeleri yakınsa önerilecek; fiyat oranı çok farklıysa UI kullanıcıyı yüzdesel moda yönlendirecek.
- [ ] Kabul: BIST + kripto veya BIST + ABD gibi farklı takvimli semboller üst üste konduğunda tarih kayması yanlış sinyal üretmeyecek.

### 19.9 Periyot, Tarih Aralığı ve Bar Sayısı Kontrolleri

- [ ] `N bar göster` kontrolü eklenecek: son 100/250/500/1000/özel bar.
- [ ] `İki tarih arası göster` tarih aralığı seçici olarak eklenecek.
- [ ] Timeframe kısayolları korunacak; özel N-bar aggregation ileride değerlendirilecek.
- [ ] Tick/N tick grafikler, gerçek tick data gelene kadar v1 kapsamına alınmayacak; plan notu olarak kalacak.
- [ ] Backend `limit` ve cache davranışı grafik UI'dan yönetilebilir hale getirilecek.
- [ ] Kabul: Kullanıcı 500 bar ile hızlı çalışabilir, gerektiğinde 3000+ bar isteyebilir; veri yoksa boş ekran yerine net kapsama uyarısı alır.

### 19.10 Senkronize Grafikler ve Layout Davranışı

- [ ] Çoklu pencere için ayrı senkron kilitleri tasarlanacak: sembol senkronu, timeframe senkronu, zaman aralığı senkronu, crosshair senkronu, ölçek modu senkronu.
- [ ] Aktif pane net vurgulanacak; üst toolbar işlemleri sadece aktif pane'e mi yoksa senkron gruba mı uygulanıyor açık olacak.
- [ ] Bir pane'de sembol değişince diğerlerinin otomatik değişip değişmeyeceği kullanıcı seçimine bağlanacak.
- [ ] Crosshair senkronu ile aynı tarihte farklı sembollerin OHLC/performans değerleri okunabilecek.
- [ ] Kabul: 2x2 layout'ta bir grafiği pan/zoom yapmak diğer grafikleri sadece ilgili senkron kilidi açıksa etkiler.

### 19.11 Haber, KAP, Bilanço, Temettü ve Kurumsal Olay Çubukları

- [ ] Zaman aksında haber/KAP/bilanço/temettü/sermaye artırımı event marker'ları planlanacak.
- [ ] Marker hover tooltip'i: başlık, kaynak, saat, ilgili sembol, kısa özet.
- [ ] Event katmanı filtrelenebilir olacak: haber, bilanço, temettü, sermaye artırımı, sistem sinyali.
- [ ] Kaynaklar backend tarafında ayrılacak: KAP/MCP/haber sağlayıcı yoksa UI'da "kaynak bağlı değil" state'i.
- [ ] Kabul: Event marker'ları mum ve indikatörleri kapatmayacak; kullanıcı isterse tamamen gizleyebilecek.

### 19.12 Chart Ayarları, Şablonlar ve Kaydetme

- [ ] Grafik ayarları paneli planlanacak: tema, zemin, grid, yazı, crosshair, son fiyat çizgisi, kılavuz çizgileri, tooltip, scroll bar.
- [ ] Şablon sistemi iki seviyeli olacak: genel grafik şablonu ve sembole özel kaydedilmiş grafik.
- [ ] Varsayılan şablon seçme/kaydetme eklenecek.
- [ ] İndikatör grupları şablon içinde saklanacak; çizimler sembole özel saklanacak.
- [ ] PNG olarak kaydet, görünümü panoya kopyala, OHLCV/indikatör CSV export planlanacak.
- [ ] İlk faz localStorage/workspace JSON; ikinci faz backend workspace persistence.
- [ ] Kabul: Kullanıcı bir trend+indikatör görünümünü kaydedip uygulamayı yenilediğinde aynı grafik düzeni geri gelir.

### 19.13 Kısayollar ve Profesyonel Terminal Ergonomisi

- [ ] Mevcut `1-5`, `F`, `G` kısayolları korunacak ve çakışmalar temizlenecek.
- [ ] Yeni aday kısayollar: `Ctrl+T` trend çiz, `Delete` seçili çizimi sil, `Insert/Delete` bar aralığı genişlet/daralt, `Home/End` görünür aralık başı/sonu, `L` log/lineer toggle, `%` yüzdesel moda geç.
- [ ] Klavyeden sembol yazınca aktif pane sembol aramasına odaklanan komut paleti planlanacak.
- [ ] Destructive veri silme kısayolları v1'de eklenmeyecek; yanlışlıkla veri kaybı yaratmayacak.
- [ ] Kabul: Kısayol basıldığında input/select odaktaysa grafik komutu çalışmaz.

### 19.14 Kar/Zarar Görünümü ve İşlem Analizi

- [ ] Açık paper pozisyonu grafikte maliyet çizgisi ve canlı PnL etiketiyle gösterilecek.
- [ ] Backtest trade'leri giriş-çıkış bağlantı çizgileriyle izlenebilecek.
- [ ] Crosshair tooltip'te işlem varsa adet, giriş fiyatı, çıkış fiyatı, net PnL, yüzde getiri, equity ve reason birlikte gösterilecek.
- [ ] "Mesafe ölçer" aracı risk/ödül planlama için kullanılacak: giriş, stop, hedef seçildiğinde potansiyel kar/zarar yüzdesi.
- [ ] Portföy para birimi ile sembol para birimi farklıysa PnL hesaplamasında dönüşüm kaynağı ayrıca gösterilecek.
- [ ] Kabul: Kullanıcı strateji/backtest/paper tabına gitmeden grafikte işlemin yüzde karda mı zararda mı olduğunu okuyabilir.

### 19.15 Gelişmiş Grafik Tipleri

- [ ] Mevcut mum/çizgi/bar korunacak.
- [ ] OHLC bar görünümü iyileştirilecek.
- [ ] Renko için araştırma yapılacak: ATR bazlı otomatik brick size ve manuel brick size.
- [ ] Ters grafik ve relatif grafik özellikleri ayrı deneysel mod olarak planlanacak.
- [ ] 3D mum gibi görsel ama analiz değeri düşük özellikler kapsam dışı tutulacak.
- [ ] Kabul: Yeni grafik tipi veri anlamını bozmayacak; strateji/backtest hesapları yine orijinal OHLCV üstünden yapılacak.

### 19.16 Uygulama Sırası

- [ ] **Sprint G1:** Fiyat skalası reset/merkezleme hatası, son fiyat çizgisi, önceki kapanış çizgisi, görünür veri yok state'i.
- [ ] **Sprint G2:** Ölçek menüsü: lineer/log/yüzdesel, başlangıç barı seçimi, crosshair yüzde farkları.
- [ ] **Sprint G3:** İndikatör merkezi v2, parametre penceresi, çoklu indikatör instance, indikatör grupları.
- [ ] **Sprint G4:** Kar/zarar overlay'leri, maliyet/stop/hedef çizgileri, backtest trade bağlantıları.
- [ ] **Sprint G5:** Çizim altyapısı: trend/yatay/dikey/paralel/kanal/not/ölçüm ve per-symbol persistence.
- [ ] **Sprint G6:** Aynı panelde çoklu sembol karşılaştırma, ayrı skala ve data eşitleme.
- [ ] **Sprint G7:** Multi-chart senkron kilitleri, crosshair senkronu, layout ergonomisi.
- [ ] **Sprint G8:** Şablonlar, kaydedilmiş grafikler, PNG/CSV export.
- [ ] **Sprint G9:** Haber/KAP/bilanço/temettü event marker'ları.
- [ ] **Sprint G10:** Fibonacci/regresyon/renko gibi ileri teknik analiz araçları.

### 19.17 Test ve Kabul Kapıları

- [ ] Playwright: düşük fiyatlı sembolden yüksek fiyatlı sembole geçişte grafik boş kalmıyor.
- [ ] Playwright: yüksek fiyatlı sembolden düşük fiyatlı sembole geçişte mumlar görünür ve son fiyat çizgisi ölçek içinde.
- [ ] Playwright: yüzdesel modda iki farklı fiyat seviyeli sembol aynı panelde okunabilir.
- [ ] Unit: yüzde normalize dönüşümü doğru; başlangıç barı %0, sonraki barlar `(close/base - 1) * 100`.
- [ ] Unit: PnL etiketi uzun/kısa işlem için doğru yüzde ve TL/USDT değerini hesaplar.
- [ ] E2E: indikatör parametresi değişince seri yeniden hesaplanır ve ayar yenilemeden sonra korunur.
- [ ] E2E: çizim ekle, taşı, sil, reload sonrası sembole özel çizim geri gelir.
- [ ] E2E: multi-pane senkron kilitleri açık/kapalı durumda doğru davranır.

### 19.18 Tasarım Notları

- [ ] Matriks'in yoğun masaüstü terminal mantığı korunacak ama görsel kopyası alınmayacak; PiyasaPilot'un mevcut koyu, sade, yoğun ama okunabilir terminal dili sürdürülecek.
- [ ] Toolbar ikonları küçük ve tanıdık olacak; uzun metinli butonlar yerine tooltip'li ikon/segment kullanılacak.
- [ ] Ayarlar tek seferde ekrana yığılmayacak; ana grafik hızlı kalacak, detaylar drawer/modal ile açılacak.
- [ ] Boş/yanlış/eksik veri durumları grafik boşmuş gibi görünmeyecek; kullanıcıya net durum mesajı ve yeniden dene aksiyonu verilecek.
- [ ] Her yeni görsel özellik önce veri doğruluğunu koruyacak; analiz motoru ve backtest orijinal veri serisini kullanmaya devam edecek.

---

## 20. Borfin Algoritmik Trade Entegrasyon Master Planı (2026-05-01)

> **Kaynak:** Yerel Borfin eğitim videoları:
> - `/Users/enes/Documents/Ders videoları/BORFİN/KIVANÇ ÖZBİLGİÇ  Algo Trade`
> - `/Users/enes/Documents/Ders videoları/BORFİN/KIVANÇ ÖZBİLGİÇ Hareketli Ortalamalarla Algo Trade`
>
> **İnceleme yöntemi:** Video dosyalarından aralıklı kareler alındı, slayt ve platform ekranları macOS Vision OCR ile okundu. Ham rapor: `artifacts/borfin_ocr/ocr_report.md`.
>
> **Kural:** Eğitimlerdeki kavramlar PiyasaPilot'a özgü ürün akışına dönüştürülecek. Borfin/Matriks/TradingView ekranları, metinleri, özel dosyaları veya marka dili birebir kopyalanmayacak. Amaç: aynı olgun algoritmik trade prensiplerini kendi güvenli backend, DSL, backtest, paper robot ve grafik mimarimize taşımak.

### 20.1 Ürün Hedefi

- [ ] PiyasaPilot, sadece indikatör gösteren bir terminal değil; **strateji fikri -> kural -> test -> optimizasyon -> dayanıklılık analizi -> paper robot -> postmortem** zincirini tek ekranda yöneten algoritmik trade laboratuvarı olacak.
- [ ] Kullanıcı bir strateji fikrini momentum, trend takip, mean reversion, fırsat/kırılım, hareketli ortalama veya hibrit kategori olarak tanımlayabilecek.
- [ ] Her strateji için hedef, vade, piyasa koşulu, veri kaynağı, komisyon, slippage, hacim uygunluğu ve risk kuralı açıkça kaydedilecek.
- [ ] Backtest sonucu tek başına "başarılı" sayılmayacak; walk-forward, out-of-sample, Monte Carlo, işlem sayısı, drawdown, profit factor ve canlı/paper karşılaştırması birlikte değerlendirilecek.
- [ ] Gerçek emir gönderimi kapsam dışı kalacak; otomasyon **paper robot** ve alarm/sinyal üretimiyle sınırlı olacak.

### 20.2 Video Konularının Modül Haritası

| Eğitim konusu | PiyasaPilot karşılığı | Mevcut durum | Açık entegrasyon |
|---|---|---:|---|
| Algoritma nedir, sistem oluşturma | Strateji Lab + StrategySpec | Kısmen hazır | Strateji hedef/hipotez alanları |
| Momentum stratejileri | Momentum presetleri | Kısmen hazır | Momentum/RSI/MO preset katalogu |
| Trend takip | EMA/SMA/T3/MOST trend stratejileri | Kısmen hazır | Gelişmiş HO ve T3/MOST blokları |
| Mean reversion | BB/Kairi/VWAP dönüş stratejileri | Kısmen hazır | Kairi, BB SS3, uzaklık tabanlı bloklar |
| Fırsat/kırılım | Breakout, mum/formasyon, trend çizgi alarmı | Kısmen hazır | Formasyon/kırılım tarayıcı v2 |
| İndikatör seçimi ve repaint | İndikatör Merkezi + güvenli sinyal kapısı | Kısmen hazır | Repaint uyarı sistemi |
| Bilimsel yöntem | Strateji lifecycle ve kalite kapıları | Planlanacak | Hipotez, ön eleme, test notları |
| Backtest tuzakları | Veri uyarıları, bias kontrolleri | Kısmen hazır | Bias checklist ve kalite skoru |
| Optimizasyon | Parametre Deneyleri | v1 hazır | Overfit cezası, heatmap, stabilite |
| Komisyon/slippage | Backtest varsayımları | Hazır | Likidite ve hacim kapasite kontrolü |
| Walk Forward | Robustness Lab | Yok | WFA motoru ve WFE raporu |
| Monte Carlo | Risk simülasyonu | Yok | İşlem sırası/olasılık simülasyonu |
| Portföy çeşitlendirme | Portfolio Lab | Kısmen hazır | Korelasyon, multi-strategy allocation |
| Robot kurma | Paper Robot | Hazır | Robot sağlık paneli ve kill switch UX |
| Paylaşılan dosyalar | Şablon/preset import-export | Kısmen hazır | PiyasaPilot strategy pack formatı |
| Matriks/TradingView kullanımı | Interop/export | Kısmen hazır | Pine/Matriks değil, PiyasaPilot DSL odaklı |
| Hareketli ortalama türleri | Indicator Center v2 | Kısmen hazır | Geniş HO kütüphanesi |
| HO period/vade | Vade rehberi ve period guard | Yok | Timeframe/period uygunluk uyarısı |
| HO stratejileri | MA Strategy Pack | Kısmen hazır | Sıkışma, sıralama, destek/direnç, smoothing |

### 20.3 Ana Tasarım İlkeleri

- [ ] **Lookahead-free:** Sinyal `bar[t]` kapanışında, emir simülasyonu `bar[t+1]` açılışında kalacak.
- [ ] **No fake data:** Provider `is_real=true` ve güvenli status yoksa canlı/paper sinyal üretimi yapılmayacak.
- [ ] **Backtest gerçeğe yakınlığı:** Komisyon, slippage, spread/kademe, hacim kapasitesi ve veri eksikliği rapora dahil edilecek.
- [ ] **Overfit'e karşı şüphe:** En yüksek getiri varsayılan seçim olmayacak; daha düşük drawdown, daha stabil parametre ve yeterli işlem sayısı ödüllendirilecek.
- [ ] **Vade uyumu:** Strateji periyodu, grafik timeframe'i ve beklenen trade süresi birbiriyle uyumsuzsa UI uyarı verecek.
- [ ] **Eğitim ama disiplinli:** Kullanıcıya sonuçların garanti olmadığı raporda gösterilecek; gerçek emir yoluna otomatik geçiş eklenmeyecek.

### 20.4 Sprint B1 - Strateji Kataloğu ve Eğitimden Gelen Presetler

- [ ] `quant_engine/strategy/catalog.py` içinde strateji taksonomisi oluşturulacak: `momentum`, `trend_following`, `mean_reversion`, `breakout/opportunity`, `moving_average`, `hybrid`, `ml`.
- [ ] Her strateji için metadata alanları eklenecek: beklenen piyasa koşulu, önerilen timeframe, minimum bar sayısı, önerilen stop/TP, repaint riski, likidite ihtiyacı.
- [ ] Hazır presetler eklenecek: Momentum-MO cross, RSI-HO cross, RSI çift HO cross, RSI-MOST, SMA/EMA cross, fiyat-HO cross, T3 renk değişimi, Kairi mean reversion, BB SS3 dönüş.
- [ ] Presetler `StrategySpec` DSL'e çevrilecek; Python tarafında tek doğruluk kaynağı korunacak.
- [ ] Frontend Strateji Lab'da "Eğitim presetleri" segmenti olacak; kullanıcı preset seçip parametreleri değiştirebilecek.
- [ ] Kabul: En az 10 Borfin kaynaklı preset backtest edilebilir ve grafikte marker üretebilir.

### 20.5 Sprint B2 - İndikatör Merkezi v2 ve Hareketli Ortalama Kütüphanesi

- [ ] `quant_engine/strategy/indicators.py` genişletilecek: WMA, TMA, DEMA, TEMA, ZLEMA, TSF, WWMA, VIDYA, T3, KAMA, FRAMA, HMA, ALMA, MAMA/FAMA, MavilimW, GANN HiLo, RMTA, McNMA/JMA araştırma listesi.
- [ ] Her yeni indikatör için TypeScript karşılığı veya backend hesaplanmış seri endpoint'i seçilecek; frontend ile backend sonuçları için parite testi yazılacak.
- [ ] Kairi, MOST, BB Width, Guppy Multiple Moving Average ve oscillator smoothing blokları eklenecek.
- [ ] İndikatör parametreleri: period, kaynak data, MA türü, renk, çizgi kalınlığı, overlay/alt panel, sinyal için bar kapanışı bekle.
- [ ] Repaint riski yüksek indikatörler için metadata ve UI uyarısı eklenecek.
- [ ] Kabul: EMA/SMA dışı en az 8 hareketli ortalama türü grafikte çizilebilir, DSL içinde kullanılabilir ve backtestte çalışabilir.

### 20.6 Sprint B3 - Görsel Kurucu Blokları ve Güvenli DSL Genişletmesi

- [ ] Görsel kurucuya yeni bloklar eklenecek: `CROSS_UP`, `CROSS_DOWN`, `ABOVE`, `BELOW`, `BARS_SINCE`, `DISTANCE_PCT`, `SLOPE`, `RISING`, `FALLING`, `VOLUME_ABOVE_AVG`.
- [ ] Risk blokları genişletilecek: sabit stop, yüzde stop, ATR stop, trailing stop, take profit, time stop, bar sayısı kadar bekle.
- [ ] Vade ve trend filtresi blokları eklenecek: `C > SMA(C,200)`, `MA_ORDERED`, `TREND_FILTER`, `VOLATILITY_FILTER`.
- [ ] Bir stratejiye birden fazla giriş/çıkış koşulu eklenebilecek; AND/OR grupları adlandırılabilecek.
- [ ] Kural açıklaması otomatik üretilecek: "RSI kendi EMA'sını yukarı kesince ve fiyat EMA200 üstündeyse AL".
- [ ] Kabul: Kod bilmeden momentum, trend, mean reversion ve HO sıkışma stratejisi kurulabilir.

### 20.7 Sprint B4 - Backtest Gerçekçilik, Komisyon, Slipaj ve Likidite

- [ ] Backtest raporunda "varsayım kartı" zorunlu olacak: başlangıç sermayesi, komisyon, slippage bps, işlem yönü, pozisyon yüzdesi, veri kaynağı, fill modeli.
- [ ] Slippage modelleri eklenecek: sabit bps, sabit kademe/tick, hacim oranına göre artan slippage.
- [ ] Likidite kapasite kontrolü: işlem tutarı son N bar ortalama hacminin belirli yüzdesini aşarsa uyarı.
- [ ] Hacimsiz tahta riski BIST sembollerinde ayrıca raporlanacak.
- [ ] Short işlemler BIST için "simülasyon" etiketiyle kalacak; gerçek piyasa uygunluğu garanti edilmeyecek.
- [ ] Kabul: Aynı strateji komisyon/slippage açık ve kapalı çalıştırıldığında metrik farkı raporda net görünür.

### 20.8 Sprint B5 - Backtest Tuzakları ve Kalite Skoru

- [ ] Backtest raporuna "kalite kontrol" bölümü eklenecek: veri kapsama, işlem sayısı, test aralığı, piyasa rejimi çeşitliliği, parametre sayısı, outlier etkisi.
- [ ] Önyargı tuzağı uyarısı: kullanıcı sadece kazandıran sembolde test yaptıysa "tek sembol riski" işaretlenecek.
- [ ] Geçmiş veri tuzağı uyarısı: intrabar high/low bilgisiyle gerçek dışı fill varsa rapor uyaracak.
- [ ] Optimizasyon tuzağı uyarısı: parametre sayısı arttıkça kalite skoru düşecek.
- [ ] Minimum örneklem kuralı: indikatör periodu / test bar sayısı oranı çok yüksekse uyarı.
- [ ] Kabul: Backtest sonucu "getiri" yanında `quality_score` ve kırmızı/sarı/yeşil uyarılarla döner.

### 20.9 Sprint B6 - Walk Forward Analysis ve Out-of-Sample Lab

- [ ] `quant_engine/research/walk_forward.py` modülü eklenecek.
- [ ] Kullanıcı optimizasyon penceresi ve walk-forward penceresi seçecek: örn. 5 ay in-sample, 1 ay out-of-sample.
- [ ] Her pencere için en iyi parametre seçilecek, sonraki out-of-sample bölümde uygulanacak.
- [ ] Rapor alanları: WFA toplam getiri, klasik optimizasyon getirisi, WFE, pencere bazlı başarı oranı, drawdown, işlem sayısı.
- [ ] WFA tablo ve grafik UI eklenecek: optimizasyon pencereleri, out-of-sample performans şeritleri.
- [ ] Kabul: Bir strateji klasik optimize edilmiş sonuçta iyi görünse bile WFA'da başarısızsa UI bunu açıkça gösterir.

### 20.10 Sprint B7 - Monte Carlo Risk Simülasyonu

- [ ] `quant_engine/research/monte_carlo.py` modülü eklenecek.
- [ ] İşlem PnL serisi üzerinden bootstrap/permutation simülasyonu yapılacak.
- [ ] Rapor alanları: median final equity, %5/%95 senaryo, olası max drawdown, zarar etme olasılığı, yıllık getiri/drawdown dağılımı.
- [ ] Kullanıcı başlangıç sermayesi, risk yüzdesi ve tekrar sayısı seçecek.
- [ ] Monte Carlo sonucu paper robot öncesi son eleme kapısı olacak.
- [ ] Kabul: Backtestte karlı görünen stratejinin risk dağılımı ve kötü senaryo sermaye eğrisi görülebilir.

### 20.11 Sprint B8 - Parametre Deneyleri v2 ve Anti-Overfit Optimizasyon

- [ ] Grid search v1 korunacak; sonuçlara stabilite skoru eklenecek.
- [ ] Parametre heatmap'i eklenecek: iki parametre için getiri/drawdown/profit factor yüzeyi.
- [ ] En iyi tek nokta yerine "sağlam bölge" yaklaşımı gösterilecek: komşu parametreler de iyi mi?
- [ ] Parametre deneyleri WFA ve Monte Carlo ile zincirlenebilecek.
- [ ] Aşırı az işlem yapan veya çok yüksek drawdown üreten sonuçlar sıralamada cezalandırılacak.
- [ ] Kabul: "En yüksek getiri" ile "en dengeli strateji" ayrımı raporda ayrı gösterilir.

### 20.12 Sprint B9 - Piyasa Tarayıcı / Explorer v3

- [ ] StrategySpec tüm sembol evreninde taranabilecek: BIST 100, kripto, ABD, FX/emtia, özel liste.
- [ ] Tarama koşulları: son sinyal, yeni kesişim, fiyat-HO uzaklığı, Kairi eşikleri, BB band teması, RSI bölgesi, hacim filtresi, trend filtresi.
- [ ] Sonuç tablosu: sembol, son fiyat, sinyal tipi, sinyal zamanı, strateji kalite skoru, veri durumu, likidite uyarısı.
- [ ] Tarama sonucu tek tıkla grafiğe, backtest raporuna veya paper izleme listesine taşınacak.
- [ ] Toplu gerçek emir yok; sadece analiz, alarm ve paper aday listesi.
- [ ] Kabul: "EMA50 EMA200 yukarı kesen ve hacmi ortalamanın üstünde olan BIST hisseleri" gibi taramalar yapılabilir.

### 20.13 Sprint B10 - Portföy ve Strateji Çeşitlendirme Lab

- [ ] Birden fazla strateji ve sembolün birleşik equity curve'ü hesaplanacak.
- [ ] Korelasyon matrisi ve strateji korelasyonu gösterilecek.
- [ ] Strateji başına risk bütçesi ve maksimum sermaye payı ayarlanacak.
- [ ] Portfolio-level max drawdown, profit factor, Sharpe, aylık getiri dağılımı ve en kötü dönem raporlanacak.
- [ ] Aynı anda çalışan paper robotların toplam risk/korelasyon uyarısı eklenecek.
- [ ] Kabul: Kullanıcı tek strateji değil, "3 strateji + 10 sembol" portföyünün geçmişte nasıl davrandığını görebilir.

### 20.14 Sprint B11 - Paper Robot Operasyon Paneli

- [ ] Paper robot listesi: aktif stratejiler, semboller, timeframe, son sinyal, son emir, PnL, sağlık durumu.
- [ ] Kill switch: tüm paper robotları durdur, sadece seçili stratejiyi durdur, günlük risk limitini düşür.
- [ ] Robot başlamadan önce kontrol listesi: gerçek veri, yeterli bar, WFA/Monte Carlo sonucu, komisyon/slippage varsayımları, likidite.
- [ ] Alarm ve paper aksiyonu ayrılacak: alarm üretmek paper trade açmak anlamına gelmeyecek.
- [ ] Gap/vade geçişi gibi özel durumlar için "işlem yapma" filtresi eklenecek.
- [ ] Kabul: Paper robot canlı çalışırken neden işlem yaptığı veya yapmadığı audit log'dan okunur.

### 20.15 Sprint B12 - Strategy Pack, Import/Export ve Interop

- [ ] PiyasaPilot strateji paketi formatı tanımlanacak: `.piyasapilot-strategy.json`.
- [ ] Paket içeriği: StrategySpec, parametreler, indikatör seti, açıklama, versiyon, risk ayarları, örnek backtest metadata.
- [ ] Hazır "Borfin esinli eğitim preset paketi" oluşturulacak; telifli/proprietary kod veya metin içermeyecek.
- [ ] TradingView/Pine için doğrudan birebir çeviri yerine referans notu ve manuel eşleştirme alanı olacak.
- [ ] Matriks formülleri doğrudan import edilmeyecek; kullanıcı PiyasaPilot DSL ile yeniden kuracak.
- [ ] Kabul: Kullanıcı stratejisini dışa aktarır, başka workspace'e alır ve aynı backtest varsayımlarıyla tekrar çalıştırır.

### 20.16 Sprint B13 - UI Bilgi Mimarisi

- [ ] Strateji Lab sekmeleri netleşecek: `Fikir`, `Kurallar`, `Test`, `Optimizasyon`, `WFA`, `Monte Carlo`, `Paper`, `Postmortem`.
- [ ] Her strateji raporunda "Bu ne anlatıyor?" açıklaması kısa ve teknik olacak; ekranda uzun eğitim metni yığılmayacak.
- [ ] Risk uyarıları kart formatında gösterilecek: veri, overfit, likidite, slippage, short simülasyon, repaint.
- [ ] Strateji lifecycle durumları eklenecek: taslak, ön test, optimize edildi, WFA geçti, Monte Carlo geçti, paper izleniyor, emekliye ayrıldı.
- [ ] Kabul: Kullanıcı bir stratejinin hangi aşamada olduğunu ve sıradaki mantıklı adımı tek bakışta görür.

### 20.17 Test ve Kabul Kapıları

- [ ] Unit: Yeni hareketli ortalama ve indikatör fonksiyonları sabit fixture veride beklenen çıktıyı verir.
- [ ] Unit: DSL tehlikeli ifade kabul etmez; yeni bloklar StrategySpec'e doğru çevrilir.
- [ ] Unit: Slippage, komisyon, hacim kapasite kontrolü ve short PnL doğru hesaplanır.
- [ ] Unit: WFA pencereleri sızıntısız ayrılır; out-of-sample veri optimizasyonda kullanılmaz.
- [ ] Unit: Monte Carlo sabit seed ile deterministik rapor üretir.
- [ ] Integration: Strateji preset -> backtest -> kalite skoru -> WFA -> Monte Carlo zinciri çalışır.
- [ ] E2E: Kullanıcı preset seçer, parametre değiştirir, backtest çalıştırır, WFA raporunu açar, paper izlemeye alır.
- [ ] E2E: Explorer taraması sonucundan sembol grafiğe açılır ve marker'lar görünür.
- [ ] E2E: Strategy pack export/import sonrası aynı kurallar geri gelir.
- [ ] Kabul: Finansal gerçekçilik varsayımları raporda eksiksiz görünmeden "paper çalıştır" aktif olmaz.

### 20.18 Uygulama Sırası

- [ ] **Sprint B1:** Strateji kataloğu, Borfin presetleri, metadata ve StrategySpec eşlemesi.
- [ ] **Sprint B2:** İndikatör Merkezi v2 için geniş HO/indikatör kütüphanesi ve parite testleri.
- [ ] **Sprint B3:** Görsel kurucu + DSL blokları: cross, distance, slope, volume, risk kuralları.
- [ ] **Sprint B4:** Backtest gerçekçilik katmanı: slippage, komisyon, likidite, bias kalite skoru.
- [ ] **Sprint B5:** Backtest tuzakları UI ve kalite skoru raporu.
- [ ] **Sprint B6:** Walk Forward Analysis motoru, WFE ve pencere grafikleri.
- [ ] **Sprint B7:** Monte Carlo simülasyonu ve risk dağılım raporu.
- [ ] **Sprint B8:** Optimizasyon v2, heatmap ve stabil parametre bölgesi.
- [ ] **Sprint B9:** Explorer v3, strateji tarama ve aday listesi.
- [ ] **Sprint B10:** Portföy/strateji çeşitlendirme labı.
- [ ] **Sprint B11:** Paper robot operasyon paneli ve kill switch.
- [ ] **Sprint B12:** Strategy pack import/export ve eğitim preset paketi.
- [ ] **Sprint B13:** UI bilgi mimarisi, lifecycle durumları ve postmortem akışı.

### 20.19 Borfin İçeriklerinden Çıkan Özellik Backlog'u

- [ ] Momentum: MO/RSI/CCI/Stochastic tabanlı momentum ve aşırı alım-satım strateji blokları.
- [ ] Trend takip: fiyat-HO, HO-HO, T3 renk değişimi, trend çizgisi kırılımı ve Guppy ribbon blokları.
- [ ] Mean reversion: Kairi, BB SS3, VWAP uzaklığı, HO uzaklık yüzdesi ve dönüş hedefi blokları.
- [ ] Fırsat stratejileri: mum formasyonu, kanal/kırılım, formasyon teyit seviyesi ve önceden tanımlı stop/TP.
- [ ] İndikatör kullanımı: leading/lagging ayrımı, kategori etiketleri, repaint uyarısı ve bar kapanışı bekleme ayarı.
- [ ] Bilimsel yöntem: hipotez, ön eleme, optimizasyon, analiz, canlı/paper kıyaslama ve vazgeçme kararı.
- [ ] Backtest: önyargı, geçmiş veri, intrabar fill, overfit ve piyasa rejimi uyarıları.
- [ ] Optimizasyon: parametre aralığı, test sayısı, sonuç sıralama, stabilite ve overfit cezası.
- [ ] Komisyon/slippage: bps, kademe, hacim ve işlem sayısı maliyet etkisi.
- [ ] Walk Forward: in-sample/out-of-sample pencereler, WFE ve pencere bazlı rapor.
- [ ] Monte Carlo: işlem sırası simülasyonu, kayıp olasılığı, final equity dağılımı.
- [ ] Çeşitlendirme: farklı period, sembol, strateji ve korelasyonla risk dağıtımı.
- [ ] Robot: paper çalışma, sinyal/alarm/emir ayrımı, audit log ve güvenli durdurma.
- [ ] Veri aktarımı: CSV import, tarih/saat format kontrolü ve özel sembol veri seti.
- [ ] Paylaşılan dosyalar: PiyasaPilot'a özgü strateji paketi, indikatör seti ve rapor dışa aktarımı.

### 20.20 Kapsam Dışı ve Güvenlik Notları

- [ ] Gerçek aracı kurum emir iletimi bu planın kapsamı dışında kalacak.
- [ ] HFT veya milisaniye seviye emir altyapısı yapılmayacak; proje bar/tick verisi güvenilir hale gelmeden bu alana girmeyecek.
- [ ] Lisanssız veri gerçek veri gibi etiketlenmeyecek.
- [ ] Eğitim videolarındaki platform arayüzleri, formül dosyaları ve metinleri birebir kopyalanmayacak.
- [ ] Her strateji sonucu eğitim/araştırma simülasyonu olarak etiketlenecek; gelecek getiri garantisi verilmediği raporda kalacak.

---

## 21. Eğitim Kaynaklı Fark Yaratan Özellik Radar'ı (2026-05-01)

> **Amaç:** Borfin arşivindeki her bilgiyi ürüne taşımak değil; PiyasaPilot'u grafik, teknik analiz, backtest, strateji, risk ve paper trading tarafında farklılaştıracak fikirleri seçmek.
>
> **Kaynak yönetimi:** Detaylı video okuma ve kürasyon `egitimplanlama.md` içinde tutulur. Bu bölüm yalnızca ürüne girecek seçilmiş özellik backlog'udur.
>
> **Checkpoint kuralı:** Her anlamlı aşama küçük commit ve push ile ilerler. Kirli çalışma ağacında yalnızca ilgili dosya/hunk stage edilir.

### 21.1 Değer Filtresi

Her eğitim fikri `planlama.md` içine ancak şu soruların cevabı netse girer:

- [ ] Kullanıcı problemi: Kullanıcı grafikte, strateji kurarken, backtest okurken veya VİOP varsayımı yaparken hangi somut sorunu çözüyor?
- [ ] Ürün noktası: Fikir grafik paneli, indikatör merkezi, StrategySpec, backtest raporu, tarayıcı, paper robot veya eğitim drawer'ına bağlanıyor mu?
- [ ] Test edilebilirlik: Unit, integration, E2E veya kabul senaryosu yazılabiliyor mu?
- [ ] Risk görünürlüğü: Repaint, gecikme, overfit, slippage, veri kalitesi, likidite, VİOP vade/kontrat veya davranışsal disiplin risklerinden en az birini daha görünür yapıyor mu?
- [ ] Özgünleştirme: Eğitimdeki marka/metin/formül kopyalanmadan PiyasaPilot'a özgü bir iş akışına dönüşüyor mu?

### 21.2 İndikatör Merkezi v2 - Eğitimden Ürüne

- [ ] Kullanıcı problemi: Kullanıcı "Bollinger, RSI, MACD, ADX, CCI, OBV, MFI, Ichimoku, Parabolic SAR veya MOST ne işe yarar?" sorusunu grafikten ayrılmadan cevaplayabilmeli.
- [ ] Ürün noktası: Grafik üstünde indikatör ekleme paneli, parametre drawer'ı ve StrategySpec kural kurucu.
- [ ] Özellik: İndikatörler kategoriye ayrılacak: trend, momentum, volatilite/bant, hacim, yön-güç, fiyat dönüşü, formasyon yardımcıları.
- [ ] Özellik: Her indikatör kartında kullanım amacı, gecikme/repaint riski, önerilen veri uzunluğu, backtest uyumluluğu ve stratejiye çevir aksiyonu olacak.
- [ ] Özellik: Aynı indikatörün birden fazla instance'ı desteklenecek; kullanıcı Bollinger 20/2 ve Bollinger 50/2.5 gibi varyasyonları aynı grafikte karşılaştırabilecek.
- [ ] Özellik: Parametre değişimi rapora kaydedilecek; backtest sonucunda "bu sinyal hangi parametrelerle üretildi?" geriye dönük okunabilecek.
- [ ] Test: E2E'de Bollinger grafiğe eklenir, parametre değiştirilir, aynı ayarlar backtest preset'ine taşınır.

### 21.3 Teknik Analiz Uygulama Labı

- [ ] Kaynak odağı: Yaşar Erdinç teknik analiz ve ileri teknik analiz eğitimleri, teknik analiz araçlarını sadece açıklama olarak değil uygulama akışı olarak besleyecek.
- [ ] Kullanıcı problemi: Kullanıcı trend çizgisi, destek/direnç, kanal, formasyon veya hacim teyidini çizdikten sonra bunu unutulan bir çizim olarak bırakmamalı; alarm veya backtest fikrine dönüştürebilmeli.
- [ ] Ürün noktası: Grafik çizim altyapısı, alarm motoru, StrategySpec aday kural üretimi ve eğitim drawer'ı.
- [ ] Özellik: Çizimlerden türetilen olaylar planlanacak: trend çizgisi kırılımı, yatay destek/direnç teması, kanal üst/alt bant teması, formasyon teyit seviyesi, hacimle kırılım.
- [ ] Özellik: Analiz checklist'i olacak: trend yönü, ana destek/direnç, hacim teyidi, risk/ödül, stop seviyesi, geçersizleşme şartı, backtest edilebilir kural.
- [ ] Özellik: "Analizi strateji fikrine çevir" akışı kullanıcı çizimlerini doğal dil açıklama ve StrategySpec taslağına dönüştürecek; otomatik gerçek emir yok.
- [ ] Test: E2E'de kullanıcı destek çizgisi ekler, alarm taslağı açılır, aynı seviye backtest kural adayında görünür.

### 21.4 Sistem Trading Labı

- [ ] Kaynak odağı: Fuat Akman Sistem Trading ve Kıvanç Özbilgiç Algo Trade eğitimlerinden kural kurma, sistem testi, rapor okuma ve debug akışı süzülecek.
- [ ] Kullanıcı problemi: Kullanıcı "stratejim neden çalıştı/çalışmadı?" sorusunu yalnızca equity curve ile değil kural bazlı nedenlerle görebilmeli.
- [ ] Ürün noktası: StrategySpec editörü, backtest runner, rapor arşivi, kalite skoru ve tarayıcı.
- [ ] Özellik: Kural debug paneli eklenecek: her bar için hangi giriş/çıkış koşulu true/false oldu, hangi filtre sinyali engelledi, kaç bar sonra sinyal geldi.
- [ ] Özellik: Explorer mantığı StrategySpec tarayıcıya bağlanacak; kullanıcı "son barda RSI dönen, hacmi artan ve fiyat EMA üstünde olan semboller" gibi setleri tarayabilecek.
- [ ] Özellik: Backtest raporunda eğitim kaynaklı kalite kapıları olacak: minimum işlem sayısı, parametre sayısı, tek sembol yanlılığı, out-of-sample durumu, maliyet etkisi.
- [ ] Test: Integration testte bir StrategySpec koşulu tarayıcıda sembol listesi üretir; backtest raporu kural debug özetini döndürür.

### 21.5 VİOP / Vadeli Labı

- [ ] Kaynak odağı: VOB, Vadeli Trade, opsiyon/varant ve türev eğitimleri yalnızca PiyasaPilot'un ana kapsamına uygun risk ve varsayım katmanlarını besleyecek.
- [ ] Kullanıcı problemi: Kullanıcı VİOP backtest sonucunu spot hisse backtesti gibi okumamalı; kontrat, vade, teminat, kaldıraç ve rollover varsayımlarını açıkça görmeli.
- [ ] Ürün noktası: VİOP provider, backtest varsayım kartı, risk raporu ve eğitim drawer'ı.
- [ ] Özellik: VİOP backtestlerinde kontrat türü, yakın vade, vade geçişi, teminat varsayımı, kaldıraç etkisi, tick size, komisyon ve slippage alanları zorunlu varsayım olarak gösterilecek.
- [ ] Özellik: Lisanslı veri yoksa VİOP sonuçları gerçek veri gibi sunulmayacak; `not_configured` ve veri kaynağı uyarısı raporda kalacak.
- [ ] Özellik: Rollover simülasyonu v1'de uyarı ve manuel varsayım olarak başlayacak; gerçek kontrat zinciri bağlanmadan otomatik birleştirme yapılmayacak.
- [ ] Test: VİOP sembolünde backtest raporu veri kaynağı, vade/kontrat ve slippage varsayımı olmadan "paper'a al" aksiyonunu pasif bırakır.

### 21.6 Eğitim Bağlantılı Kullanım Deneyimi

- [ ] Kullanıcı problemi: Eğitim bilgisi ayrı bir dokümanda kaybolmamalı; kullanıcı merak ettiği kavramdan doğrudan grafiğe, stratejiye veya backteste geçebilmeli.
- [ ] Ürün noktası: Yeni Eğitimler sekmesi, bağlamsal drawer, indikatör kartları, strateji presetleri ve backtest raporu.
- [ ] Özellik: Eğitimler sekmesinde arama olacak: Bollinger, RSI, trend çizgisi, stop, backtest, walk-forward, Monte Carlo, VİOP, slippage.
- [ ] Özellik: Konu sayfası üç aksiyonla bitecek: grafikte göster, strateji preset'ine geç, backtest raporunda ilgili metrikleri aç.
- [ ] Özellik: Her konu sayfasında "bu bilgi nerede yaniltir?" alanı olacak; özellikle overfit, repaint, gecikme, işlem maliyeti ve veri kalitesi uyarıları öne çıkarılacak.
- [ ] Test: E2E'de kullanıcı Eğitimler'de Bollinger arar, konu detayını açar, Bollinger'i grafiğe ekler ve Bollinger backtest preset'ine geçer.

### 21.7 GitHub Checkpoint Uygulaması

- [x] Branch oluştur: `codex/education-feature-planning`.
- [x] Commit 1: `egitimplanlama.md` iskeleti ve Borfin okuma süreci.
- [x] Commit 2: `planlama.md` eğitim kaynaklı özellik radar'ı ve ürün backlog başlıkları.
- [ ] Commit 3: Algo Trade + Hareketli Ortalamalar OCR'ına dayalı seçilmiş özelliklerin ilk detaylandırması.
- [ ] Commit 4: İndikatör ve teknik analiz eğitimlerinin OCR/transkript çıktılarından seçilen özellikler.
- [ ] Commit 5: VİOP/Vadeli ve Sistem Trading eğitimlerinin OCR/transkript çıktılarından seçilen özellikler.
- [ ] Commit 6+: Uygulama geliştirmeleri başladığında API, frontend, eğitim drawer'ı, testler ve demo ayrı commit'lere bölünecek.
