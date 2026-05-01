# PLANLAMA — PiyasaPilot Trading Terminali (Ana Index)

> Bu dosya index'tir. Sıra ve öncelik için önce `genelplanlama.md`, kodlama için ilgili alt plan dosyasını oku.
> Tarih: 2026-05-01 · Branch: codex/education-feature-planning

---

## 1. Proje Özeti

`/Users/enes/AgentWorkspace/Backtest` — Python backend (`quant_engine/`, `backend/`) ve TypeScript/Vite SPA (`piyasapilot-v2/`) içeren trading terminali.

**Hedef:** TradingView benzeri tek SPA; strateji fikri → kural → backtest → optimizasyon → paper robot zincirini tek ekranda yöneten algoritmik trade laboratuvarı.

**Durum (2026-05-01):** Sprint 0–12 tamamlandı. Aktif fazlar: Eğitimler sekmesi, Grafik Lab (G2+), Backtest Lab kalan işleri ve Mali Analiz için ön okuma.

---

## 2. Çalışan Servisler

| Servis | Port | Dosya |
|--------|------|-------|
| FastAPI gateway | 8000 | `backend/api/main.py` |
| Frontend SPA | 5173 | `piyasapilot-v2/` |
| Veri workers | — | `backend/workers/` |
| Paper executor | — | `backend/paper/` |
| Notifier | — | `backend/notifier/` |

**Dokunma listesi:** `quant_engine/backtest/engine.py`, `quant_engine/data/providers/binance_provider.py`, `quant_engine/data/providers/yfinance_provider.py`, `quant_engine/data/live_feed.py`

---

## 3. Enes'in Kesin Kararları

- [x] Frontend: TS terminali ana arayüz (Streamlit Sprint 2.8'de söküldü)
- [x] Backend rolling cache: SQLite/Parquet, kayar pencere
- [x] Sembol kapsamı: BIST 100 + 20 kripto + FX/emtia (~130 sembol)
- [x] Always-on: Docker Compose (lokal Mac, taşınabilir)
- [x] Backtest motoru: Python BacktestEngine tek kaynak; TS sadece görüntüler
- [x] AI sinyal: kural motoru (8 tip) + Claude API sabah brifing + LightGBM (≥3 ay cache)
- [x] Paper trading: strateji-bazlı izole sandık (10.000 TL), günlük %5 DD limiti
- [x] Bildirim: Telegram + Email + In-app + macOS desktop
- [x] Gerçek emir gönderimi kapsam dışı
- [x] Eğitim içerikleri: telifsiz, PiyasaPilot'a özgü iş akışına dönüştürülecek

---

## 4. Mimari (Tek Cümle Özetler)

- **Veri:** Worker → SpikeFilter → SQLite cache → FastAPI → REST/WS → TS DataEngine → ChartPanel
- **Backtest:** StrategyPanel → POST /api/backtest/run → BacktestEngine → sonuç → Chart.js
- **Sinyal:** Bar kapanışı → DecisionEngine → /ws/signals → SignalFeed + Notifier
- **Paper:** /ws/signals → PaperExecutor → SQLite → PnL → PortfolioPanel

---

## 5. Dosya Haritası

| Dosya | İçerik |
|-------|--------|
| `genelplanlama.md` | Tek yürütme haritası ve uygulama sırası |
| `planlama.md` | Bu index |
| `planlama-sprint-gecmis.md` | Sprint 0–12 arşiv (tamamlananlar, referans) |
| `planlama-sprint-aktif.md` | Aktif geliştirme fazları ve sıraları |
| `planlama-grafik.md` | Grafik Lab — Sprint G2–G10 |
| `planlama-backtest.md` | Backtest Lab — Sprint B1–B13 (Borfin) |
| `planlama-egitimler.md` | Eğitimler sekmesi + Blog içerik planı |
| `planlama-mali-analiz.md` | Mali Analiz sekmesi planı |
| `egitimplanlama.md` | BORFİN kurs okuma süreci ve OCR kayıtları |

---

## 6. Geliştirme Faz Sırası

```
Faz 1 — Eğitim kaynak modeli ve yeni sekmeler
  ├── Eğitimler sekmesi  → planlama-egitimler.md (klavye: 6)
  └── Mali Analiz ön okuma → planlama-mali-analiz.md (klavye hedefi: 7)

Faz 2 — Grafik iyileştirmeleri (ChartPanel.ts'e dikkatli dokunma)
  └── Sprint G2–G10 → planlama-grafik.md

Faz 3 — Strateji Lab kalan işleri (quant_engine + StrategySpec değişiklikler)
  └── Sprint B1–B6 → planlama-backtest.md

Faz 4 — İleri analitik (WFA, Monte Carlo, Portföy Lab)
  └── Sprint B6–B13 → planlama-backtest.md
```

---

## 7. Veri Sağlayıcı Özeti

| Sembol | Birincil | İkincil |
|--------|----------|---------|
| BIST hisse | borsapy | yfinance `.IS` |
| BIST endeks | yfinance | borsapy |
| Kripto | Binance REST+WS | ccxt |
| Forex/Emtia | yfinance | borsapy |
| Fundamentals | borsa-mcp | borsapy |

Cache: Worker 60s'de bir çağırır → SQLite INSERT OR IGNORE → zamanla 1 ay+ birikir.

---

## 8. Kaynak Linkler

- [saidsurucu/borsa-mcp](https://github.com/saidsurucu/borsa-mcp)
- [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp)
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills)
