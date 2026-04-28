# Backtest + PiyasaPilot — Claude Çalışma Rehberi

> Bu dosya yeni bir Claude Code oturumunda **otomatik yüklenir**. Kalıcı bağlam.
> Detaylı sprint listesi ve karar geçmişi: `planlama.md`. Her zaman önce bu iki dosyayı oku.

---

## 1. Proje tek cümlede

`/Users/enes/AgentWorkspace/Backtest` — BIST, Kripto, Forex ve Emtia için **TradingView benzeri** tek bir trading terminali. Python backend (`quant_engine/`) + TypeScript SPA (`piyasapilot-v2/`). Hedef: canlı veri (15dk gecikmeli yeterli), 1 ay tarihsel cache, otomatik strateji + paper-trading, kesintisiz çalışan stack.

---

## 2. Mimari Snapshot

```
Tarayıcı (Vite SPA, lightweight-charts)
   │
   ▼  /api/v2/candles + WS  (vite dev proxy → :8000)
FastAPI / live_server (Python)  ← v1 endpoint'ler de korunuyor
   │
   ├─ LiveDataService.fetch_candles  (ccxt + yfinance)
   ├─ BacktestEngine                  (lookahead-free, testli)
   ├─ DecisionEngine                  (EMA200+BB+RSI, kural tabanlı)
   └─ Workspace JSON store            (paper trades + cache stub)
```

Detaylı mimari ve sprint planı: `planlama.md` (özellikle bölüm 4, 7, 11, 17).

---

## 3. Port Haritası

| Port | Servis | Komut |
|------|--------|-------|
| 8000 | FastAPI gateway | `python3 live_server.py` |
| 5173 | Vite dev (SPA) | `cd piyasapilot-v2 && npm run dev` |

Vite, `/api/v2/*` çağrılarını `127.0.0.1:8000`'a proxy eder (vite.config.ts).

---

## 4. Çalışma Kuralları (Enes'in Kuralları)

1. **6 seviyeli orkestratör akışı:** Komutçu → Planlayıcı → Bağlam Mühendisi → Araç Ustası → Yetenekli Usta → Orkestratör. Her seviye geçişinde "devam" onayı gerekli.
2. **Sub-agent maliyeti:** Düşük model (Haiku) tercih et; ana orkestratör için Sonnet/Opus.
3. **DOKUNMA listesi:**
   - `quant_engine/backtest/engine.py` — sağlam BacktestEngine
   - `quant_engine/data/providers/{binance,yfinance}_provider.py`
   - `quant_engine/data/live_feed.py` — `fetch_chart` v1 (paper trading bağımlı)
4. **Sıfır demo veri:** Provider veri vermezse "Bağlantı Hatası" döndür. Sahte veri yok.
5. **Tick takibi:** Her sprint görevi `planlama.md`'de checkbox. İş bitince `- [ ]` → `- [x]`.
6. **Sprint geçişi:** Bir sprint bitmeden sonrakine geçme. Enes açık onay verir.

---

## 5. Yeni Oturum Açıldığında — İlk 3 Adım

```bash
# 1. planlama.md oku → bölüm 17 (Öğrenilenler) + bölüm 11 (Sprint listesi)
# 2. .claude/memory/session-recap.md oku (varsa) → son oturumun özeti
# 3. git log --oneline -10 → son commit'lerden durumu doğrula
```

Sonra `planlama.md` Sprint listesinde ilk açık (`- [ ]`) tick'i bul, oradan başla.

---

## 6. Veri Sağlayıcıları (Kritik Sınırlar)

| Sağlayıcı | 15dk barlar | Notlar |
|-----------|-------------|--------|
| yfinance | sadece **5 gün** | `period="5d"` hardcoded; rate 60 req/dk |
| Binance public REST | ~**7 gün** | 1000 kline × 15dk; rate 1200 req/dk |
| borsapy (saidsurucu) | uzun geçmiş | BIST native; ~15dk gecikmeli |

**1 ay tarihsel için backend rolling cache şart** (Sprint 1).

---

## 7. Mevcut v2 API (Aktif)

```
GET /api/v2/candles?symbol=&interval=&limit=
```

Sembol formatları (frontend native, backend `_resolve_v2` ile yönlendirir):
- `BTCUSDT`, `ETHUSDT` → ccxt (Binance)
- `THYAO.IS`, `XU100` → yfinance BIST
- `USDTRY=X`, `EURTRY=X` → yfinance FX
- `GC=F`, `CL=F` → yfinance commodity
- `AAPL`, `MSFT` → yfinance US equity

Interval: `1m | 5m | 15m | 30m | 1h | 4h | 1d | 1w`. Limit clamp: 20 ≤ x ≤ 1000.

---

## 8. Test ve Build Komutları

```bash
# Python testler
source .venv/bin/activate && python -m pytest tests/ -v

# TS compile
cd piyasapilot-v2 && npx tsc --noEmit

# Vite production build
cd piyasapilot-v2 && npx vite build
```

---

## 9. Git Akışı

- Branch adı: `fix/...`, `feat/...`, `docs/...`, `chore/...`
- Commit mesajı: kısa imperative başlık + boş satır + ayrıntılar
- Co-author: `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>`
- PR body Türkçe, `## Summary`, `## Commits`, `## Test plan` başlıklı

---

## 10. Yapılmaması Gerekenler

- `git push --force` main'e — yasak.
- `--no-verify` ile hook bypass — yasak.
- Streamlit kullanma — Sprint 2.8'de söküldü (PR #9).
- TS tarafında bağımsız backtest mantığı — Sprint 3'te tek motor (Python) olacak.
- API'ye doğrudan erişim (corsproxy.io, api.binance.com fetch) — `/api/v2/candles` üzerinden.
