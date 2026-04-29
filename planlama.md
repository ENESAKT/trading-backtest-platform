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
- [ ] **Bildirim:** Telegram + Email + In-app + macOS desktop seçildi. Telegram bot token + chat ID setup'ı Sprint 7'de yapılacak.

---

## 3. Mevcut Durum (Repo Snapshot)

### 3.1 Çalışan parçalar (DOKUNMA — sağlam)
- `quant_engine/backtest/engine.py` — Lookahead-free, testli BacktestEngine.
- `quant_engine/data/providers/binance_provider.py` — Public REST, 1200 req/dk, sayfalama 20×1000.
- `quant_engine/data/providers/yfinance_provider.py` — `.IS` suffix mantığı, 60 req/dk.
- `quant_engine/data/live_feed.py` — ccxt + yfinance ayrımı.
- `quant_engine/strategy/decision_engine.py` — EMA200+BB+RSI füzyonu (kural tabanlı).
- `piyasapilot-v2/src/components/ChartPanel.ts` — lightweight-charts v4, 4 alt-grafik (Main + Volume + RSI + MACD), F-fullscreen.
- `piyasapilot-v2/src/strategies/` — TrendFollowing, MeanReversion, BreakoutDetector.
- `piyasapilot-v2/src/indicators/` — EMA, SMA, RSI, MACD, BB, ATR, VWAP, Stoch.
- `piyasapilot-v2/src/core/AnomalyFilter.ts` — IQR + Z-Score (kısmi).

### 3.2 Eksikler / Boşluklar
- Backend cache yok; her istekte yfinance.
- Streamlit ve TS terminal **birbirine bağlı değil**.
- TS backtest, Python `BacktestEngine`'i değil kendi TS implementasyonunu kullanıyor (desync riski).
- Sembol kataloğu dağınık (BIST 100/Tümü, US, FX eşlemeleri tek tek).
- Always-on yok; Vite + live_server.py manuel başlatılıyor.
- AI sinyal motoru yok.
- Paper trading SQLite şeması (`paper_trades`, `paper_portfolio`) yok.
- Market Explorer (tree/accordion sembol gezgini) yok.
- Memory/context kalıcılığı projeye özel kurulu değil (genel `~/.claude/projects/.../memory/` var ama proje köküne CLAUDE.md yok).

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
- [~] 2.5 Streamlit'in Strateji Lab → TS'te. _Mevcut TS `StrategyPanel` çekirdek özellikleri kapsıyor (3 strateji + backtest metrics + equity curve + sinyal listesi + chart marker'ları). Advanced parametre formu (ema fast/slow input vs.) Sprint 3'te API tabanlı `POST /api/backtest/run`'la birlikte gelecek; oraya kadar TS-içi yeterli._
- [~] 2.6 Streamlit'in Veri İstasyonu → TS'te. _Sidebar zaten kategori-akordeon + arama yönetimi sağlıyor. Sembol grup persistence (custom watchlist'ler) Sprint 4 paper portfolio ile birlikte JSON store üzerinden gelecek._
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
- [x] 3.7 Eski 4 strateji + yeni 4 strateji (toplam 8): EMA cross, RSI mean-rev, BB rev, breakout, **donchian breakout, MACD div, supertrend, mean-reversion VWAP**. _PR #14: `donchian_breakout`, `macd_divergence`, `supertrend`, `mean_reversion_vwap` eklendi; `blueprints.py` 8 stratejiye güncellendi; `StrategyPanel.ts` 8 kart._

### Sprint 4 — Paper Trading & Portföy
- [ ] 4.1 SQLite şeması: `paper_trades`, `paper_portfolio`, `paper_equity_curve`.
- [ ] 4.2 Strateji-bazlı sanal cüzdan modeli (her strateji ayrı sandık).
- [ ] 4.3 `robot-executor` sub-agent'ı yaz (otonom işlem icra).
- [ ] 4.4 Canlı PnL hesabı (gateway fiyatı × açık miktar).
- [ ] 4.5 TS'te `PortfolioPanel` v2: equity curve, drawdown, win rate, sharpe.
- [ ] 4.6 Audit trail (her trade JSON log).
- [ ] 4.7 Risk limitleri (her cüzdana max %, gün-içi stop-out).

### Sprint 5 — Agent + Skill + MCP + Hook Kurulumu
- [ ] 5.1 `.claude/agents/data-validator.md` yaz.
- [ ] 5.2 `.claude/agents/quant-researcher.md` yaz.
- [ ] 5.3 `.claude/agents/backtest-runner.md` yaz.
- [ ] 5.4 `.claude/agents/frontend-builder.md` yaz.
- [ ] 5.5 `.claude/agents/backend-builder.md` yaz.
- [ ] 5.6 `.claude/agents/robot-executor.md` yaz.
- [ ] 5.7 `.claude/agents/code-reviewer.md` yaz.
- [ ] 5.8 `.claude/agents/devops-engineer.md` yaz.
- [ ] 5.9 `borsa-mcp` kur (`claude mcp add borsa --type stdio --command "uvx" --args ["--from","git+https://github.com/saidsurucu/borsa-mcp","borsa-mcp"]`).
- [ ] 5.10 `tradingview-mcp` kur.
- [ ] 5.11 `tradermonty/claude-trading-skills`'ten 8 skill kopyala (madde 7.2'deki liste).
- [ ] 5.12 Projeye özel 7 skill yaz (madde 7.2'deki ikinci liste).
- [ ] 5.13 `.claude/settings.json`'a 5 hook ekle.
- [ ] 5.14 5 slash command (`/devam`, `/backtest`, `/sinyal`, `/durum`, `/strateji-yeni`).
- [ ] 5.15 Memory persistence: `auto-recap.sh` + `load-recent-state.sh` test et.

### Sprint 6 — AI Sinyal Motoru (Hibrit)
- [ ] 6.1 Kural motorunu güçlendir: 8 sinyal tipi (mevcut 3 → 8).
- [ ] 6.2 `morning-briefing` skill: Claude API ile sabah BIST 100 özeti + 3 odak hisse.
- [ ] 6.3 `scenario-analyzer` skill (haber → senaryo → etki).
- [ ] 6.4 `signal-postmortem` skill (kapanan trade → öğrenme).
- [ ] 6.5 (Opsiyonel) ML model temelleri: cache verisi 3 ay birikince LightGBM trial.
- [ ] 6.6 AI sinyal feed'i `WS /ws/signals/ai`'ye fan-out.

### Sprint 7 — Always-On & Bildirim
- [ ] 7.1 `Dockerfile.api`, `Dockerfile.workers`, `Dockerfile.notifier`.
- [ ] 7.2 `docker-compose.yml` (api, workers, db, nginx, notifier).
- [ ] 7.3 Healthcheck'ler tüm servislere.
- [ ] 7.4 Telegram bot (`backend/notifier/telegram.py`).
- [ ] 7.5 Email (smtp, günlük 09:00 cron).
- [ ] 7.6 macOS desktop notification (sadece lokal mod).
- [ ] 7.7 In-app toast (TS).
- [ ] 7.8 `.env.example` (token'lar, smtp).
- [ ] 7.9 `make up` / `make down` Makefile.
- [ ] 7.10 Stres testi: 1 saat 100 sembol paralel polling, 0 hata.

### Sprint 8 — Test, Doküman, Hand-off
- [ ] 8.1 README.md güncelle (yeni mimari).
- [ ] 8.2 `docs/MIMARI.md`, `docs/AGENT_REHBERI.md`, `docs/SKILL_REHBERI.md`.
- [ ] 8.3 `tests/e2e/` Playwright (TS frontend smoke).
- [ ] 8.4 Backtest paritesi testi (TS'in eski sonucu ≈ Python yeni sonucu, kabul edilebilir delta).
- [ ] 8.5 Memory testi: oturum kapat-aç, Claude kaldığı yerden devam ediyor mu.
- [ ] 8.6 Final demo + Enes onayı.

---

## 12. Açık Sorular (Kalan netleştirmeler)

- [x] AI sinyal motoru hibrit yaklaşımı — onaylandı (Sprint 6).
- [x] Paper trading — strateji-bazlı izole sandık + risk limitleri onaylandı (Sprint 4).
- [x] Docker konumu — Mac şimdilik, taşınabilir tutulacak (Sprint 7).
- [ ] Telegram bot chat ID Enes'ten alınacak (Sprint 7'de).
- [ ] Email için Gmail App Password mı, başka SMTP mi (Sprint 7'de).
- [ ] BIST 100 listesi + 20 kripto + FX/Emtia listesi nihai onayı (Sprint 0 sonu).

---

## 13. Doğrulama (Uçtan Uca Test)

- [ ] **Veri:** `curl /api/chart?symbol=THYAO&interval=15m&period=1mo` → 30 gün × 15dk bar.
- [ ] **WebSocket:** Tarayıcıda 5 dk açık tut; XU100 + BTCUSDT her 15s/her tick güncelleniyor.
- [ ] **Spike filtre:** `tests/unit/test_spike_filter.py` (yapay outlier inject).
- [ ] **Backtest paritesi:** Aynı sembol/aynı strateji/aynı periyot → TS UI'dan ve `/api/backtest/run` üzerinden aynı sonuç.
- [ ] **Always-on:** `docker compose kill api` → 5 sn'de restart.
- [ ] **Stres:** 100 sembol × 1 saat polling, 0 hata.
- [ ] **Agent:** `claude` aç, `/devam` yaz; `session-recap.md`'den son durumu özetlesin.
- [ ] **Skill:** `/morning-briefing` çalıştır; 3 odak hisse + tutarlı rapor.
- [ ] **MCP:** `borsa-mcp` üzerinden THYAO 13F benzeri özet alınıyor mu.
- [ ] **Notifier:** Test sinyali → Telegram + email + in-app toast'a düşüyor.

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

## 16. Sıradaki Adım

ExitPlanMode ile bu plan onaya sunulacak. Onaylandığında ilk uygulama adımı:

1. Bu dosyayı `/Users/enes/AgentWorkspace/Backtest/planlama.md` olarak kopyala.
2. Proje köküne `CLAUDE.md` yaz.
3. `.claude/` iskelet klasörlerini oluştur.
4. Sprint 0'ın kalan tick'lerini netleştir (açık sorular).

> Bu noktadan sonra hiç kod yazılmayacak; sadece plan dosyasının çoğaltılması ve iskelet klasörler hazırlanacak. Sonra Enes "Sprint 1'e geç" der.

---

## 17. Öğrenilenler — Hafıza Snapshot (2026-04-26)

> Bu bölüm, oturum kaybolursa veya context dolarsa **tek başına okunarak** nereden devam edileceğini söyler. Yeni Claude penceresi: önce bu bölümü oku, sonra Sprint listesinden ilk açık tick'i bul.

### 17.1 Repo Gerçekleri (Doğrulanmış)
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

### 17.2 Veri Sağlayıcı Sınırları (KRİTİK)
- **yfinance 15 dk:** Sadece **5 gün** geriye gider. (`period="5d"` hardcoded.)
- **Binance 15 dk:** ~**7 gün** (1000 kline × 15 dk = 250 saat).
- **borsapy** (saidsurucu): yfinance benzeri Python kütüphanesi; BIST için 1m/3m/5m/15m/30m/45m/1d/1w/1M intervals; `period="max"` mümkün; ~15 dk gecikmeli; 758 BIST şirketi, 836+ TEFAS fonu.
- **borsa-mcp** (saidsurucu): FastMCP server, 26 tool, BIST + US + TEFAS + KAP haberleri + döviz/emtia + ekonomik takvim. `uvx --from git+https://github.com/saidsurucu/borsa-mcp borsa-mcp` ile kurulur.
- **Sonuç:** 1 ay tarihsel istemek için **backend rolling cache** zorunlu — worker her 60 sn çağrılan 5–7 günlük pencereleri SQLite'a `INSERT OR IGNORE` ile birikir.

### 17.3 Enes'in Onayladığı Kararlar (Kesin)
1. ✅ TS terminal ana arayüz; Streamlit kalkar.
2. ✅ Backend rolling cache (SQLite/Parquet, kayar pencere).
3. ✅ İlk faz ~130 sembol: BIST 100 + 20 büyük kripto + USD/TRY + altın.
4. ✅ Docker Compose ilk başta Mac'te (Docker Desktop / colima). Taşınabilir.
5. ✅ Strateji motoru tek kaynak: Python `BacktestEngine`. TS sadece görüntüler.
6. ✅ AI hibrit: kural motorunu 8 sinyal tipine çıkar + Claude API sabah brifing + cache 6 ay birikince LightGBM.
7. ✅ Paper trading tam otomatik AMA strateji-bazlı izole sandık (her strateji 10.000 TL); günlük max %5 zarar, pozisyon başı max %10, audit trail.
8. ✅ Bildirim 4 kanal: Telegram + Email + In-app toast + macOS desktop.

### 17.4 Claude Code Ekosistemi — Pratik Bilgi
- **Sub-agent** (`.claude/agents/<name>.md`): Ayrı context window, kendi system prompt'u, tools allowlist, model seçimi (Haiku ucuz/deterministic, Sonnet research, Opus deep). Main session geçmişini görmez. Maliyet düşük çünkü sonuç özetlenip ana context'e döner.
- **Agent Team** (deneysel, `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): Çoklu paralel session, paylaşımlı task list, peer-to-peer messaging, file locking. Token maliyeti yüksek. Tasarımdaki 8 agent için **subagent yeterli**, agent team'i sadece çoklu PR review/cross-layer iş için ileride kullanırız.
- **Skill** (`.claude/skills/<name>/SKILL.md`): Reusable playbook. User invoke (`/skill-name`) veya Claude oto-tetik (description-match). Main context'te kalır, supporting files (scripts, refs) içerebilir.
- **Hook** (`settings.json`): SessionStart/Stop, PreToolUse/PostToolUse, UserPromptSubmit, SubagentStart/Stop, TeammateIdle/TaskCreated/TaskCompleted. Shell script çalıştırır, exit code 2 = blok et.
- **MCP** (`~/.mcp.json` veya proje `.mcp.json`): External tool feed. stdio (lokal proc) vs HTTP/SSE (remote). `claude mcp add ...` ile kurulur.
- **Slash Command** (`.claude/commands/<name>.md`): User `/<name>` yazınca tetikler. Frontmatter: `description`, `argument-hint`, `allowed-tools`, `model`.

### 17.5 Hazır Kullanılacak Üçüncü-Parti Bileşenler
- **Sub-agent kaynağı:** [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents) — `quant-analyst`, `fintech-engineer`, `risk-manager`, `data-engineer`, `ml-engineer`, `code-reviewer`, `debugger`, `docker-expert`, `fastapi-developer`, `react-specialist`, `typescript-pro`, `python-pro`.
- **Skill kaynağı:** [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills) — 47 skill. Bizim için seçilen 8: `backtest-expert`, `position-sizer`, `technical-analyst`, `market-news-analyst`, `signal-postmortem`, `strategy-pivot-designer`, `scenario-analyzer`, `exposure-coach`. (FMP API free tier 250 req/gün — bazıları gerektirir.)
- **MCP'ler:** `borsa-mcp`, `tradingview-mcp` (atilaahmettaner), `yahoo-finance-mcp` (Alex2Yang97 — yedek), opsiyonel `playwright-mcp` (isyatirim scraping yedek).
- **Şablon marketi:** [aitmpl.com](https://www.aitmpl.com/) — JS-rendered, alt-sayfaları doğrudan WebFetch ile okumadı; gerekirse claude-code-templates CLI ile çekilir.

### 17.6 Mimari Tek Cümle Özetleri
- **Veri akışı:** `Worker (yfinance/Binance/borsapy) → SpikeFilter (IQR + hacim) → SQLite cache → FastAPI gateway → (REST GET /api/chart) + (WS /ws/quotes) → TS DataEngine → ChartPanel`.
- **Backtest akışı:** `TS StrategyPanel → POST /api/backtest/run → Python BacktestEngine → BacktestResult → TS Chart.js equity curve`.
- **Sinyal akışı:** `Bar kapanışı → DecisionEngine + (sabah Claude API briefing) → /ws/signals → TS SignalFeed + Notifier (telegram/email/desktop/toast)`.
- **Paper trading akışı:** `/ws/signals → robot-executor sub-agent → SQLite paper_trades + paper_portfolio → canlı PnL hesabı (gateway fiyatı × açık miktar) → /ws/portfolio → PortfolioPanel`.
- **Always-on:** `docker-compose up -d` → api + workers + db + nginx + notifier; `restart: unless-stopped`; healthcheck'ler.

### 17.7 Memory Persistence Stratejisi (3 Katmanlı)
1. **`/Users/enes/AgentWorkspace/Backtest/CLAUDE.md`** — sabit bilgi: mimari, port haritası, çalışma kuralları. Her oturumda otomatik yüklenir.
2. **`/Users/enes/AgentWorkspace/Backtest/planlama.md`** — bu plan. Tick'ler her sprint sonunda güncellenir. Tek doğruluk kaynağı.
3. **`.claude/memory/session-recap.md`** — `Stop` hook'u her oturum sonunda otomatik yazar; `SessionStart` hook'u yeni oturumda systemMessage olarak inject eder. Böylece Claude sıfırdan keşfetmek zorunda kalmaz.

Globaldeki `~/.claude/projects/-Users-enes-AgentWorkspace-Backtest/memory/` (kullanıcı profili, geçmiş kararlar) zaten dolu ve aktif.

### 17.8 Şu Anki Durum (Snapshot — 2026-04-27)
- ✅ **Faz 1–4** tamam: keşif, planlama, kararlar, plan dosyası.
- ✅ **PR #1 merge edildi** (`08e7ae6`): v2 ön yüzü artık `/api/v2/candles` üzerinden lokal Python backend'e route oluyor.
  - 4 commit: `058d8b5` (route), `bef3eff` (testler), `cac192b` (delayed status), `5623733` (reconnect cap).
  - Pytest 16/16 yeşil; vite build temiz (39 modül).
- ✅ **Sprint 0 tamamlandı:** `planlama.md` proje köküne kopyalandı, `CLAUDE.md` yazıldı, `.claude/{agents,skills,commands,hooks,memory}/` iskeleti kuruldu.
- ⏳ **Sıradaki:** Sprint 1 — Backend Data Gateway (FastAPI, SQLite cache, IQR spike filter, Binance WS daemon, yfinance/borsapy poller).

### 17.9 Yeni Claude Penceresi Açıldığında — Yapılacaklar
1. `planlama.md` (proje köküne kopyalandıysa) ya da bu dosyayı oku.
2. Bölüm 17.8'deki "Şu Anki Durum" üzerinden nereye kalındığını anla.
3. `git log --oneline -20` ile son commit'leri ve cloud session'ından gelen PR'ı kontrol et.
4. Sprint listesinde ilk açık (`- [ ]`) tick'i bul, oradan başla.
5. Risk listesini (Bölüm 14) hatırla; her teknik karar bu çerçevede değerlendirilsin.

### 17.10 Önemli Linkler
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
