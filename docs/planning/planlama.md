# PLANLAMA — PiyasaPilot Trading Terminali (Ana Index)

> Bu dosya index'tir. Sıra ve öncelik için önce `genelplanlama.md`, kodlama için ilgili alt plan dosyasını oku.
> Tarih: 2026-05-03 · Branch: codex/financials-ui-api-v1

---

## 1. Proje Özeti

`/Users/enes/AgentWorkspace/Backtest` — Python backend (`quant_engine/`, `backend/`) ve TypeScript/Vite SPA (`piyasapilot-v2/`) içeren trading terminali.

**Hedef:** TradingView benzeri tek SPA; strateji fikri → kural → backtest → optimizasyon → paper robot zincirini tek ekranda yöneten algoritmik trade laboratuvarı.

**Durum (2026-05-03):** Veri platformu, repo temizliği/canlıya çıkış hazırlığı, denetim skill/script katmanı, Eğitimler, Grafik Lab G1-G10 ve Backtest Lab B1-B13 ürün entegrasyonu tamamlandı. Mali Analiz tarafında metadata-only API/UI v1, universe sidebar ve boş kontratlar hazır; gerçek KAP/provider bağlantısı ve finansal tablo store'u henüz bağlanmadı.

---

## 2. Çalışan Servisler

| Servis | Port | Dosya |
|--------|------|-------|
| FastAPI gateway | 8000 | `backend/api/main.py` |
| Frontend SPA | 5173 | `piyasapilot-v2/` |
| Veri workers | — | `backend/workers/` |
| Paper executor | — | `backend/paper/` |
| Notifier | — | `backend/notifier/` |
| Gelecek ClickHouse | 8123/9000 | `infra/clickhouse/` |
| Gelecek MySQL | 3306 | `infra/mysql/` |
| Gelecek Redis | 6379 | `infra/docker-compose.*.yml` |

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
- [x] Yeni veri hedefi: önce BIST 100 + VIOP; sonra tüm BIST; sonra diğer piyasalar
- [x] Production veri omurgası: ClickHouse + MySQL + Redis
- [x] BIST hisse `1m` veri yalnızca son 1 yıl tutulacak
- [x] VIOP `1m` veri 10 yıl hedefleyecek
- [x] BIST hisse `5m` ve üstü timeframe'ler 10 yıl hedefleyecek
- [x] Günlükten dakikalık sahte veri üretilmeyecek
- [x] Borfin OCR/frame/video artifact'leri production paketine girmeyecek
- [x] Veri/deploy/repo temizliği için kontrol skill'leri ve mentor agent planlanacak

---

## 4. Mimari (Tek Cümle Özetler)

- **Mevcut Veri:** Worker → SpikeFilter → SQLite/Parquet cache → FastAPI → REST/WS → TS DataEngine → ChartPanel
- **Hedef Veri:** Provider/Ingestor → Validate/Quality → ClickHouse `market_bars` → Repository → API/Backtest/Screener; MySQL metadata/job/inventory, Redis quote/cache/lock/pub-sub
- **Backtest:** StrategyPanel → POST /api/backtest/run → BacktestEngine → sonuç → Chart.js
- **Sinyal:** Bar kapanışı → DecisionEngine → /ws/signals → SignalFeed + Notifier
- **Paper:** /ws/signals → PaperExecutor → SQLite → PnL → PortfolioPanel
- **Production:** nginx → frontend/API/WS; Docker Compose prod → api/ingestor/scheduler/clickhouse/mysql/redis/backup

---

## 5. Dosya Haritası

| Dosya | İçerik |
|-------|--------|
| `YAPILANLAR.md` | Teknik envanter — tüm yapılanlar, modüller, teknolojiler |
| `YAPILACAKLAR.md` | Kalan işler, sunucu çıkış, güvenlik, MySQL entegrasyon adımları |
| `genelplanlama.md` | Tek yürütme haritası ve uygulama sırası |
| `planlama.md` | Bu index |
| `planlama-sprint-gecmis.md` | Sprint 0–12 arşiv (tamamlananlar, referans) |
| `planlama-sprint-aktif.md` | Aktif geliştirme fazları ve sıraları |
| `planlama-veri-platformu.md` | BIST/VIOP veri platformu, ClickHouse/MySQL/Redis, retention, inventory |
| `planlama-agent-skill-mentor.md` | Veri/deploy/temizlik skill'leri ve mentor/data/release agent planı |
| `planlama-mali-analiz.md` | Mali Analiz sekmesi planı |
| `egitimplanlama.md` | BORFİN kurs okuma süreci ve OCR kayıtları |
| `docs/DEPLOYMENT.md` | Sunucu kurulum rehberi (adım adım) |
| `docs/archive/` | Tarihsel snapshot'lar (ROADMAP, ILERLEME, PROJE_DURUM_OZET) |

---

## 6. Geliştirme Faz Sırası

```
Faz 0 — Veri platformu ve production hazırlığı
  ├── Veri platformu → planlama-veri-platformu.md
  ├── Repo temizlik/canlıya çıkış → planlama-temizlik-canliya-cikis.md
  └── Denetim skill'leri + mentor agent → planlama-agent-skill-mentor.md

Faz 1 — Eğitim kaynak modeli ve yeni sekmeler
  ├── Eğitimler sekmesi  → planlama-egitimler.md (klavye: 6)
  └── Mali Analiz metadata/API/UI v1 → planlama-mali-analiz.md (klavye: 7)

Faz 2 — Grafik iyileştirmeleri (ChartPanel.ts'e dikkatli dokunma)
  └── Sprint G2–G10 → planlama-grafik.md

Faz 3 — Strateji Lab ürün entegrasyonu (quant_engine + StrategySpec değişiklikler)
  └── Sprint B1–B13 → planlama-backtest.md

Faz 4 — Mali Analiz gerçek veri fazı
  └── KAP/provider + finansal tablo store'u → planlama-mali-analiz.md
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

Yeni veri platformu hedefi:

| Katman | Sorumluluk |
|--------|------------|
| ClickHouse | OHLCV, raw/derived bar, hızlı backtest/screener |
| MySQL | Sembol, VIOP kontrat, provider, ingest job, data inventory, retention policy |
| Redis | Son quote, kısa candle cache, WebSocket pub/sub, ingest lock |
| Parquet/DuckDB | Lokal yedek, cold archive, fallback |

Retention özeti:

| Market | Timeframe | Saklama |
|--------|-----------|---------|
| BIST hisse | `1m` | 1 yıl |
| BIST hisse | `5m` ve üstü | 10 yıl |
| VIOP | `1m` ve üstü | 10 yıl |

---

## 8. Kaynak Linkler

- [saidsurucu/borsa-mcp](https://github.com/saidsurucu/borsa-mcp)
- [atilaahmettaner/tradingview-mcp](https://github.com/atilaahmettaner/tradingview-mcp)
- [VoltAgent/awesome-claude-code-subagents](https://github.com/VoltAgent/awesome-claude-code-subagents)
- [tradermonty/claude-trading-skills](https://github.com/tradermonty/claude-trading-skills)
