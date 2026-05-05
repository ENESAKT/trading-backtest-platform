# Sprint Arşivi — Sprint 0–12 (Tamamlananlar)

> Bu dosya referans arşividir. Aktif kodlama için `planlama-sprint-aktif.md`'yi oku.
> Tarih: 2026-05-01

---

## Sprint 0 — Bağlam ve Onay

- [x] 0.1 `planlama.md` proje köküne oluşturuldu
- [x] 0.2 `CLAUDE.md` yazıldı (mimari, port haritası, kurallar)
- [x] 0.3 `.claude/` iskelet klasörleri (agents/, skills/, commands/, hooks/, memory/)
- [x] 0.4 Açık kararlar — AI hibrit, izole sandık, Mac+Docker — onaylandı
- [x] 0.5 Seviye 2 (Planlayıcı) onaylandı; PR #1 merge edildi

---

## Sprint 1 — Backend Data Gateway

- [x] 1.1 FastAPI gateway: `backend/api/main.py`
- [x] 1.2 SQLite cache şeması (bars, quotes, meta) + Parquet dizini
- [x] 1.3 IQR + hacim ağırlıklı spike filter + pytest
- [x] 1.4–1.6 Worker iskelet + Binance WS + Yahoo Finance poller
- [x] 1.7 yfinance `.IS` poller (BIST hisse, 60s)
- [x] 1.8 `/api/v2/candles` endpoint (cache-aside)
- [x] 1.9 `/ws/quotes` WebSocket (canlı tick fan-out)
- [x] 1.10 Healthcheck endpoint
- [x] 1.11 Integration testleri geçiyor

---

## Sprint 2 — Frontend Birleşimi (TS Tek Terminal)

- [x] 2.1–2.3 Market Explorer, BIST 100 / Kripto / Forex kategorileri, çoklu pencere layout
- [x] 2.4 Fullscreen düğmesi (F kısayolu)
- [x] 2.5 Streamlit Strateji Lab → TS'e taşındı
- [x] 2.6 Veri İstasyonu → TS Sidebar ile karşılandı
- [x] 2.7 DataEngine yeni FastAPI gateway WS'ine bağlandı; CORS proxy sökündü
- [x] 2.7+ Backtest BUY/SELL marker'ları chart üstünde (lightweight-charts setMarkers)
- [x] 2.8 Streamlit söküldü (2856 satır + test + requirements temizlendi)

---

## Sprint 3 — Strateji & Backtest Birleşimi

- [x] 3.1 TS dahili backtest söküldü
- [x] 3.2 `POST /api/backtest/run` endpoint (Python BacktestEngine)
- [x] 3.3 Strateji blueprint formatı (parametre şeması + meta)
- [x] 3.4 TS `StrategyPanel` → API'ye POST, equity eğrisi Chart.js
- [x] 3.5 Live signal feed: `/ws/signals` (DecisionEngine her bar kapanışında)
- [x] 3.6 TS `SignalFeed` paneli (max 50 sinyal, WS, sekme 5)
- [x] 3.7 8 strateji → Sprint 11'de 9 strateji (lightgbm_probability)

---

## Sprint 4 — Paper Trading & Portföy

- [x] 4.1–4.2 SQLite şeması + strateji-bazlı sanal cüzdan (10.000 TL başlangıç)
- [x] 4.3 PaperExecutor: signal_bus'tan otomatik emir
- [x] 4.4 Canlı PnL hesabı
- [x] 4.5 TS PortfolioPanel v2: equity curve, drawdown, win rate, Sharpe
- [x] 4.6 Audit trail (SQLite paper_trades)
- [x] 4.7 Risk limitleri: günlük max %5 DD, pozisyon başı max %10

---

## Sprint 5 — Agent + Skill + MCP + Hook Kurulumu

- [x] 5.1–5.8 8 sub-agent yazıldı: data-validator, quant-researcher, backtest-runner, frontend-builder, backend-builder, robot-executor, code-reviewer, devops-engineer
- [x] 5.9 borsa-mcp konfigürasyonu (.mcp.json)
- [x] 5.10 tradingview-mcp konfigürasyonu
- [x] 5.11 tradermonty'den 8 skill: backtest-expert, position-sizer, technical-analyst, market-news-analyst, signal-postmortem, strategy-pivot-designer, scenario-analyzer, risk-manager
- [x] 5.12 7 projeye özel skill: validate-spike-filter, run-backtest, health-check, morning-briefing, paper-trade-status, deploy-stack, session-recap
- [x] 5.13 Hook'lar: SessionStart, Stop, SubagentStop
- [x] 5.14 5 slash command: /devam, /backtest, /sinyal, /durum, /strateji-yeni
- [x] 5.15 Memory persistence: session-recap.md + hook'lar

---

## Sprint 6 — AI Sinyal Motoru (Hibrit)

- [x] 6.1 Kural motoru 8 sinyal tipine çıkarıldı; sinyal gücü (1-10) + konsensüs
- [x] 6.2–6.4 morning-briefing, scenario-analyzer, signal-postmortem skill'leri
- [x] 6.5 LightGBM readiness gate (veri yetersizse sahte model yok)
- [x] 6.6 AI sinyal feed /ws/signals'a fan-out

---

## Sprint 7 — Always-On & Bildirim

- [x] 7.1–7.3 Dockerfile'lar (api, workers, notifier) + docker-compose.yml + healthcheck'ler
- [x] 7.4 Telegram bot (httpx async, sinyal formatı, günlük rapor)
- [x] 7.5 Email (SMTP TLS, HTML rapor template)
- [x] 7.6 macOS desktop notification (AppleScript)
- [x] 7.7 In-app toast (STRONG sinyal, 5sn, slide-in)
- [x] 7.8 .env.example
- [x] 7.9 make up/down Makefile
- [x] 7.10 Stres testi: 470 istek / 0 altyapı hatası

---

## Sprint 8 — Test, Doküman, Hand-off

- [x] 8.1–8.5 README, docs/ mimari/agent/skill rehberleri, Playwright E2E, backtest pari test, memory testi
- [x] 8.6 Final demo doğrulama kapıları

---

## Sprint 9 — Polish & Production Hardening

- [x] 9.1 ILERLEME.md + ROADMAP.md güncellendi
- [x] 9.2–9.3 STRONG sinyal badge, gradient glow, konsensüs metadata
- [x] 9.4 Vite build: 0 hata (38 modül, 403ms)
- [x] 9.5 Backend API doğrulama: 9 strateji, PaperDB, SignalGenerator import başarılı
- [x] 9.6 Playwright smoke: 5 tab, açılış sekmesi persistence, Telegram tercih paneli
- [x] 9.7 292/292 test geçiyor
- [x] 9.8–9.13 ogrenilenler.md Sprint 9, workers standalone entrypoint, Docker fix

---

## Sprint 10 — Gerçek Veri Güven Kapısı ve MCP

- [x] 10.1–10.11 ProviderRouter, MarketDataResult/Health/Status, BIST/VİOP/kripto provider, SignalGenerator güven kapısı, Telegram komutları, testler (328 passed)
- [x] 10.12–10.13 borsa-mcp + tradingview-mcp Connected
- [x] 10.14–10.22 MCP smoke, lisanslı feed köprüsü, Binance WS reset dayanıklılığı, Telegram roundtrip check, Playwright E2E (4 test), Docker build/up/restart, stres smoke, LightGBM temeli

---

## Sprint 11 — Üretim Sertleştirme + Canlı Veri + ML

- [x] 16.1 BIST/VİOP lisanslı feed köprüsü (is_real etiketi, Yahoo fallback uyarısı)
- [x] 16.2 LightGBM: readiness gate, retrain cron, SignalGenerator lgbm_prob, 9. strateji
- [x] 16.3 Frontend: lazy-load sidebar, mobil layout, indikatör toggle, sinyal localStorage kalıcılığı, 4 Playwright testi
- [x] 16.4 Prometheus /metrics, Grafana dashboard, worker çöküş Telegram uyarısı, daily health report
- [x] 16.5 .env validation, SIGTERM graceful shutdown, API key auth, WAL checkpoint testi

---

## Sprint 12 — Kodsuz Strateji Lab + Long/Short Backtest

- [x] 12.1 DSL sözlüğü, parser, strategy_spec şeması
- [x] 12.2 Backtest request/response v2 + rapor şeması
- [x] 12.3 Long/short trade intent motoru (BUY/SELL/SHORT/COVER/HOLD)
- [x] 12.4 Backtest rapor arşivi (SQLite)
- [x] 12.5 CSV import + veri doğrulama
- [x] 12.6 Strateji Lab frontend ekranı (Kural Lab + Hazır Strateji modları)
- [x] 12.7 Grafik marker + tooltip + işlem tablosu senkronu
- [x] 12.8 Export endpoints (JSON, CSV işlem, CSV equity, CSV optimizasyon)
- [x] 12.9 Grid optimizasyon v1 (comma-list grid, skor tablosu)
- [x] 12.10 Piyasa Tarayıcı v2 (sembol listesi tarama, sonuçtan grafik)
- [x] 12.11 Paper robot + alarm bağlantısı (signal bus + notifier WebSocket)
- [x] Enes görsel kurucuyla strateji oluşturabiliyor
- [x] Enes güvenli formül diliyle strateji yazabiliyor
- [x] Rapor arşive kaydoluyor, JSON/CSV dışa aktarılıyor
- [x] Long/short PnL ve timing testleri geçiyor (328 passed)

---

## Sprint G1 — Grafik Fiyat Skalası Düzeltmesi

- [x] Sembol değişiminde fiyat skalası eski aralığı taşımıyor; yeni sembol dikeyde otomatik ortalanıyor
- [x] Ana seri, hacim, RSI, MACD scale resetleniyor
- [x] Oto fiyat ve manuel yeniden ortala toolbar kontrolleri eklendi
- [x] Playwright: düşük fiyatlı → yüksek fiyatlı sembol geçişinde grafik boş kalmıyor
- [x] Playwright: yüksek → düşük geçişte mumlar görünür, son fiyat çizgisi ölçek içinde
- [x] Son fiyat yatay çizgisi ve sağ skalada renkli etiketi standart hale getirildi
- [x] Önceki kapanış kesik çizgisi toolbar toggle ile açılıp kapatılabiliyor

---

## Öğrenilenler (2026-04-30 Snapshot)

**Kritik sınırlar:**
- yfinance 15dk: sadece 5 gün geriye gider
- Binance 15dk: ~7 gün (1000 kline × 15dk)
- borsapy: BIST için `period="max"` destekler, ~15dk gecikmeli
- Backend rolling cache zorunlu; worker 60s'de bir INSERT OR IGNORE

**Sağlam, dokunulmayacak:**
- `quant_engine/backtest/engine.py` — lookahead-free, signal bar[t] close, execution bar[t+1] open
- `quant_engine/data/providers/binance_provider.py` — public REST, rate limit 1200 req/dk
- `quant_engine/data/providers/yfinance_provider.py` — .IS suffix, fallback period="5d"
- `quant_engine/data/live_feed.py` — USDT → ccxt, TRY → yfinance resolve_symbol()

**Memory persistence (3 katman):**
1. `CLAUDE.md` — sabit bilgi, her oturumda otomatik yüklenir
2. `planlama.md` (index) — dosya haritası, kararlar
3. `.claude/memory/session-recap.md` — Stop hook otomatik yazar, SessionStart inject eder
