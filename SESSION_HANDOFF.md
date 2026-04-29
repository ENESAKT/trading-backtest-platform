# Oturum El Geçirme Notu — 2026-04-26

## Ne Yapıldı

Bu oturumda **Seviye 1 (Komutçu)** tamamlandı: repo derinlemesine incelendi ve özet sunuldu.
Enes "devam" demeden bir sonraki seviyeye GEÇİLMEDİ.

---

## Projenin Hikayesi (kısa)

`/Users/enes/AgentWorkspace/Backtest` — BIST/Kripto/Forex/Emtia için Python backtest sistemi + TypeScript trading terminali.

Hedef: AI tabanlı sinyal üretimi eklemek + arayüzü canlı veri ile kullanılabilir hale getirmek.

---

## Projenin Yapısı (ne var, ne yok)

### Çalışan parçalar
| Bileşen | Konum | Durum |
|---------|-------|-------|
| BacktestEngine | `quant_engine/backtest/engine.py` | Solid, lookahead-free, dokunma |
| BinanceProvider | `quant_engine/data/providers/binance_provider.py` | Çalışıyor |
| YFinanceProvider | `quant_engine/data/providers/yfinance_provider.py` | Çalışıyor |
| DecisionEngine (kural tabanlı) | `quant_engine/strategy/decision_engine.py` | EMA200+BB+RSI fusion, AI DEĞİL |
| Strateji örnekleri | `quant_engine/strategy/examples/` | SMA, RSI, Bollinger, Buy&Hold |
| Streamlit Terminal | `quant_engine/app/ui_streamlit/app.py` | Port 8502, ayrı çalışıyor |
| live_server.py | `live_server.py` | Port 8000, TS frontend köprüsü |
| TS Frontend | `piyasapilot-v2/src/` | lightweight-charts, WebSocket, polling |
| Strategy persistence | SQLite | `data/strategy_lab/strategies.sqlite3` |
| Paper trading | JSON store | `data/workspaces/workspace.json` (temel) |

### Eksikler (öncelik sırasıyla)
1. **AI sinyal motoru YOK** — Claude API veya ML entegrasyonu hiç yok
2. **Backend cache yok** — yfinance her request'te doğrudan çağrılıyor
3. **İki UI entegre değil** — Streamlit (port 8502) ve TS terminal (port 8000) birbirinden kopuk
4. **BacktestEngine API olarak expose edilmemiş** — TS frontend kendi TS backtest kodunu kullanıyor
5. **IQR spike filtresi yok** — MASTER_PLAN_v2.md'de tasarlanmış, implement edilmemiş
6. **SQLite paper trading tabloları yok** — `paper_trades` / `paper_portfolio` tabloları eksik
7. **Market Explorer yok** — sembol ağacı/accordion yok
8. **Fullscreen grafik yok**

### Mevcut mimari (sorun)
```
[Binance WS] → [WebSocketManager.ts] → [DataEngine.ts] → [ChartPanel.ts]
[yfinance/ccxt] → [live_server.py] → [PollingManager.ts] → [DataEngine.ts]
[Streamlit App port 8502] ←── tamamen ayrı, TS frontend'e bağlı değil
```

---

## 6 Seviyeli Plan (nereden devam edilecek)

| Seviye | Adı | Durum |
|--------|-----|-------|
| 1 | Komutçu — Repo inceleme | ✅ TAMAMLANDI |
| 2 | Planlayıcı — Mimari tasarım (`/plan` modu) | ⏳ BEKLIYOR (Enes onayı gerekiyor) |
| 3 | Bağlam Mühendisliği — CLAUDE.md dosyaları | Henüz başlanmadı |
| 4 | Araç Ustası — MCP listesi | Henüz başlanmadı |
| 5 | Yetenekli Usta — Skill üretimi | Henüz başlanmadı |
| 6 | Orkestratör — Sub-agent'lar | Henüz başlanmadı |

**Bir sonraki adım:** Enes "devam" dediğinde Seviye 2'ye geç — `/plan` modunda mimari çıkar.

---

## Yeni Ekrana Yapıştırılacak Mesaj

Aşağıdaki metni yeni Claude Code oturumunda ilk mesaj olarak yapıştır:

---

```
Merhaba. Önceki oturumdan devam ediyorum. 
Repo: /Users/enes/AgentWorkspace/Backtest

Seviye 1 (Komutçu - Repo İnceleme) tamamlandı. Özet şu:

- Python backend (quant_engine/) + TypeScript frontend (piyasapilot-v2/) olmak üzere iki katman var
- BacktestEngine sağlam, dokunma gerektirmiyor
- DecisionEngine var ama kural tabanlı, AI yok
- İki UI (Streamlit port 8502, TS terminal port 8000) birbirinden kopuk
- AI sinyal motoru, backend cache ve paper trading SQLite tabloları eksik
- IQR spike filtresi tasarlanmış ama implement edilmemiş

Şimdi Seviye 2'ye geçiyoruz: /plan modunda mimari tasarımını çıkar.
Frontend ne olacak, backend ne olacak, AI sinyal motoru nereye oturacak, 
canlı veri gateway nasıl kurulacak, mevcut grafik altyapısı nasıl korunacak.
Teknoloji seçimlerini sen yap, gerekçesini kısaca yaz. 
Sonra bana sun, onayımı aldıktan sonra koda geç.
```

---

## Önemli Dosyalar (okumaya değer)
- `MASTER_PLAN_v2.md` — mevcut sprint planı (4 sprint)
- `quant_engine/backtest/engine.py` — korunacak motor
- `piyasapilot-v2/src/app.ts` — TS frontend giriş noktası
- `quant_engine/data/live_feed.py` — LiveDataService (ccxt + yfinance)
- `quant_engine/strategy/decision_engine.py` — mevcut kural tabanlı sinyal motoru
