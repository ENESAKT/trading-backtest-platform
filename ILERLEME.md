# İlerleme Raporu — Backtest + PiyasaPilot

> **Tarih:** 2026-04-27
> **Branch:** `feat/sprint-1-ws-fanout` (review için açık — PR #5)
> **Tek doğruluk kaynağı:** `planlama.md`.

---

## 1. PR Tablosu

| # | Branch | Konu | Durum |
|---|--------|------|-------|
| 1 | `fix/v2-api-route-via-local-backend` | v2 API → lokal backend route + WS reconnect cap | ✅ MERGED |
| 2 | `chore/sprint-0-skeleton` | Sprint-0 iskelet (`planlama.md`, `CLAUDE.md`, `.claude/`) | ✅ MERGED |
| 3 | `feat/sprint-1-gateway-foundation` | Sprint-1 foundation: FastAPI + SQLite cache + IQR spike filter | ✅ MERGED |
| 4 | `feat/sprint-1-workers` | Sprint-1 workers: Binance WS + Yahoo + BIST poller + lifespan | ✅ MERGED |
| 5 | `feat/sprint-1-ws-fanout` | Sprint-1.9: QuoteBus + `/ws/quotes` + frontend QuoteStream | ⏳ REVIEW (https://github.com/ENESAKT/Backtest/pull/5) |

## 2. Sprint Durumu

### Sprint 1 — Backend Data Gateway ✅ TAMAMLANDI (PR #5 merge sonrası)
- [x] 1.1 FastAPI gateway _PR #3_
- [x] 1.2 SQLite OHLCV cache _PR #3_
- [x] 1.3 IQR + hacim spike filter _PR #3_
- [x] 1.4 Worker iskeleti _PR #4_
- [x] 1.5 Binance WS daemon _PR #4_
- [x] 1.6 Yahoo Finance poller _PR #4_
- [x] 1.7 BIST hisse poller _PR #4_
- [x] 1.8 `/api/v2/candles` cache-aside _PR #3_
- [x] 1.9 `/ws/quotes` fan-out _PR #5_
- [x] 1.10 `/api/health` (cache + workers + quote_bus) _PR #3 + #4 + #5_
- [x] 1.11 Integration testleri _PR #3 + #4 + #5_

**Sprint 1 ilerleme:** 11/11 (✅ %100, PR #5 merge'i bekliyor).

### Sprint 2 — Frontend Birleşimi (sıradaki)
- [ ] 2.1 Market Explorer (sol panel tree/accordion)
- [ ] 2.2 BIST 100 / Kripto / FX-Emtia kategorileri (tam katalog)
- [ ] 2.3 Çoklu pencere layout
- [ ] 2.4 Fullscreen butonu
- [ ] 2.5–2.6 Streamlit Strateji Lab + Veri İstasyonu özelliklerini TS'e taşı
- [ ] 2.7 `DataEngine` → `QuoteStream`'e bağla; eski Binance direct WS sökülecek
- [ ] 2.8 Streamlit söküm

## 3. Hızlı Sayılar

| Metrik | Değer |
|--------|-------|
| Açık PR | **1** (#5) |
| Merged PR | **4** (#1–4) |
| `feat/sprint-1-ws-fanout` commit sayısı | **5** |
| Test (pytest) | **277 passed**, 1 deprecation warning (pre-existing) |
| TS compile | clean |

## 4. Sıradaki Adım

1. **PR #5 manuel doğrulama (Enes):**
   - `python live_server.py`
   - `wscat -c ws://localhost:8000/ws/quotes` → `ready` mesajı
   - 15 dk içinde Binance kapanan kline geldiğinde `bars` mesajı görmeli
   - `curl localhost:8000/api/health` → `quote_bus.subscribers >= 1` (wscat açıkken)
2. PR #5 merge.
3. Sprint 2 başlat: Market Explorer (PR #6).
