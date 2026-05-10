# PiyasaPilot — API Referansı

> Sürüm: 2.0 · Backend: FastAPI (port 8000) · Tüm endpoint'ler `/api/` prefix'i ile başlar.

---

## Temel Kavramlar

- **Sembol formatı:** BIST için `THYAO.IS`, Binance için `BTCUSDT`, USD/TRY için `USDTRY=X`
- **Interval:** `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `1d`, `1wk`
- **Kimlik doğrulama:** Yok (lokal/iç ağ kullanımı)
- **Hata formatı:** `{"detail": "mesaj"}` HTTP 4xx/5xx ile

---

## 1. Altyapı

### `GET /api/health`
Sistem sağlık durumu — worker listesi, cache istatistikleri.

```json
{
  "status": "ok",
  "cache": {"bar_count": 71737, "symbol_count": 57},
  "workers": [{"name": "BistStockPoller", "iter_count": 12, "last_error": null}]
}
```

### `GET /metrics`
Prometheus formatında metrikler.

### `GET /api/data/providers/health`
Veri sağlayıcı sağlık kontrolü (yfinance, ClickHouse, Redis).

---

## 2. Piyasa Verisi

### `GET /api/v2/candles`
OHLCV mum verisi. Cache-aside: SQLite → LiveDataService.

**Parametreler:**
| Parametre | Tip | Açıklama |
|-----------|-----|---------|
| `symbol` | string | Sembol (THYAO.IS, BTCUSDT) |
| `interval` | string | Zaman dilimi (1d, 1h, vs.) |
| `limit` | int | Maksimum bar sayısı (varsayılan: 500) |
| `start` | int? | Unix timestamp başlangıç |
| `end` | int? | Unix timestamp bitiş |

**Yanıt:**
```json
{"status": "ok", "bars": [{"time": 1714521600, "open": 234.1, "high": 238.5, "low": 231.0, "close": 236.7, "volume": 5000000}]}
```

### `GET /api/market/defaults`
Varsayılan sembol ve interval listesi.

### `GET /api/market/chart`
v1 uyumluluk — mum verisi (eski format).

### `GET /api/workspace`
Çalışma alanı ayarları.

---

## 3. Teknik Analiz

### `GET /api/technical/{symbol}`
RSI, MACD, Bollinger, ATR, EMA9/21/50/200 hesapla; sinyal özeti döndür.

**Parametreler:**
| Parametre | Tip | Açıklama |
|-----------|-----|---------|
| `interval` | string | Zaman dilimi (varsayılan: 1d) |
| `limit` | int | Bar sayısı (varsayılan: 200) |

**Yanıt:**
```json
{
  "symbol": "THYAO",
  "interval": "1d",
  "last_close": 236.7,
  "indicators": {"rsi14": 58.2, "ema9": 232.1, "ema21": 228.5, "ema50": 215.0, "ema200": 198.3, "bb_upper": 245.0, "bb_lower": 220.0, "atr14": 8.2, "macd": 3.1, "macd_signal": 2.8, "macd_hist": 0.3},
  "signal": {"rsi": "neutral", "trend": "bullish", "above_200": true, "bb": "inside", "macd": "bullish"}
}
```

---

## 4. Backtest

### `POST /api/backtest/run`
Tek sembol backtest çalıştır.

**Body:**
```json
{
  "symbol": "THYAO.IS", "interval": "1d",
  "strategy_id": "sma_crossover",
  "params": {"fast_period": 10, "slow_period": 30},
  "capital": 100000,
  "commission_pct": 0.1,
  "lookback_bars": 500
}
```

**Yanıt:** `BacktestResult` — metrics, equity_curve, trades, signals.

### `GET /api/backtest/strategies`
Kullanılabilir strateji listesi (blueprint ID + parametre şeması).

### `GET /api/backtest/reports`
Arşivlenmiş tüm backtest sonuçları (son 50).

### `GET /api/backtest/reports/{run_id}`
Belirli bir backtest sonucunu getir.

### `GET /api/backtest/reports/{run_id}/export`
Backtest sonucu dışa aktar.

**Parametreler:** `format=json|csv`

### `POST /api/backtest/optimize`
Parametre grid optimizasyonu.

**Body:**
```json
{
  "symbol": "THYAO.IS", "interval": "1d", "strategy_id": "sma_crossover",
  "param_grid": {"fast_period": [5, 10, 15], "slow_period": [20, 30, 50]},
  "capital": 100000, "lookback_bars": 500
}
```

**Yanıt:** En iyi parametreler + tüm kombinasyon sonuçları + `heatmap` (2D matris).

### `POST /api/backtest/scan`
Çoklu sembol tarama — her sembol için backtest çalıştır.

**Body:**
```json
{
  "symbols": ["THYAO.IS", "AKBNK.IS"],
  "interval": "1d", "strategy_id": "rsi_oversold",
  "params": {}, "capital": 100000
}
```

### `POST /api/backtest/walk-forward`
Walk-forward analizi — zaman pencereleri boyunca parametre stabilitesi testi.

**Body:**
```json
{
  "run_id": "abc123",
  "n_windows": 5,
  "in_sample_pct": 0.7,
  "param_grid": {"period": [10, 14, 21]}
}
```

### `POST /api/backtest/monte-carlo`
Monte Carlo simülasyonu — trade sırası karıştırarak risk analizi.

**Body:**
```json
{"run_id": "abc123", "n_simulations": 500, "resample_trades": true}
```

**Yanıt:** `{median_final_equity, p05_final_equity, p95_final_equity, probability_of_loss, sample_simulations}`

### `POST /api/backtest/compare`
İki backtest sonucunu karşılaştır — metrik farkı + kazanan sayacı.

**Body:** `{"run_id_a": "abc", "run_id_b": "xyz"}`

---

## 5. Strateji Lab

### `GET /api/strategy-lab/strategies`
Kayıtlı strateji listesi.

### `GET /api/strategy-lab/strategies/{record_id}`
Tekil strateji getir.

### `POST /api/strategy-lab/strategies`
Strateji kaydet.

### `POST /api/strategy-lab/pack/export`
Strateji pack'ini dışa aktar (JSON).

### `POST /api/strategy-lab/pack/import`
Strateji pack'ini içe aktar.

### `POST /api/strategy-lab/strategies/{record_id}/paper/activate`
Paper trading'e strateji aktive et.

### `POST /api/strategy-lab/paper/{activation_id}/deactivate`
Paper trading stratejisini devre dışı bırak.

### `GET /api/strategy-lab/paper`
Aktif paper trading stratejileri.

---

## 6. Paper Trading

### `GET /api/paper/wallets`
Tüm paper cüzdanları.

### `GET /api/paper/trades`
Paper işlem geçmişi.

**Parametreler:** `strategy_id`, `limit`, `offset`

### `GET /api/paper/trades/export`
Paper işlemleri CSV/JSON olarak dışa aktar.

### `GET /api/paper/equity`
Paper strateji equity curve'ü.

**Parametreler:** `strategy_id` (zorunlu)

### `POST /api/paper/reset/{strategy_id}`
Paper stratejiyi sıfırla (tüm pozisyon ve geçmiş silinir).

### `POST /api/paper/halt/{strategy_id}` / `POST /api/paper/resume/{strategy_id}`
Paper stratejiyi durdur / devam ettir.

### `POST /api/backtest/reports/{run_id}/paper/activate`
Backtest sonucundan paper trading stratejisi oluştur.

---

## 7. Haber Akışı

### `GET /api/news`
Haber listesi döndür.

**Parametreler:**
| Parametre | Tip | Açıklama |
|-----------|-----|---------|
| `symbol` | string? | Sembol filtresi (THYAO) |
| `limit` | int | Maksimum haber sayısı (varsayılan: 30) |
| `fresh` | bool | `true` → yfinance'den çek + kaydet |
| `keyword` | string? | Anahtar kelime filtresi |

**Yanıt:**
```json
{"news": [{"id": 1, "symbol": "THYAO", "headline": "...", "body": null, "source": "Reuters", "published_at": "2024-01-15T10:00:00Z", "url": "https://..."}], "total": 10, "unread_24h": 3}
```

### `GET /api/news/unread-count`
Son 24 saatteki okunmamış haber sayısı (sidebar rozeti için).

**Parametreler:** `symbol?`

---

## 8. Mali Analiz (BIST)

### `GET /api/mali-analiz/universe`
Takip edilen sembol evreni.

**Parametreler:** `scope=bist30|bist100` (varsayılan: bist30)

### `GET /api/mali-analiz/comparison`
BIST 30 karşılaştırma tablosu — tüm semboller için oran karşılaştırması.

### `GET /api/mali-analiz/{symbol}/summary`
Sembol özet — ratios + alerts.

### `GET /api/mali-analiz/{symbol}/balance-sheet`
Bilanço tablosu (son N dönem).

### `GET /api/mali-analiz/{symbol}/income-stmt`
Gelir tablosu.

### `GET /api/mali-analiz/{symbol}/cashflow`
Nakit akış tablosu.

### `GET /api/mali-analiz/{symbol}/ratios`
Hesaplanmış oranlar (F/K, PD/DD, ROE, ROA, vs.).

### `GET /api/mali-analiz/{symbol}/chart-data`
Grafik için finansal zaman serisi (ciro, net kar, marjlar, vs.).

**Parametreler:** `limit=20`

### `GET /api/mali-analiz/{symbol}/reports`
Sembol için kayıtlı raporlar.

### `GET /api/mali-analiz/{symbol}/events`
KAP bildirimleri / finansal takvim olayları.

### `GET /api/mali-analiz/{symbol}/metric-history`
Belirli bir metriğin tarihsel seyri.

### `GET /api/mali-analiz/alerts`
Tüm finansal uyarılar.

### `POST /api/mali-analiz/alerts/mark-read`
Uyarıları okundu olarak işaretle.

### `POST /api/mali-analiz/refresh`
Tüm BIST30 verilerini yenile (arka planda).

### `POST /api/mali-analiz/recompute`
Tüm oranları yeniden hesapla.

### `POST /api/mali-analiz/{symbol}/refresh`
Belirli sembol verisini yenile.

### `POST /api/mali-analiz/{symbol}/recompute`
Belirli sembol oranlarını yeniden hesapla.

---

## 9. Bildirimler & Asistan

### `GET /api/notifier/status`
Telegram bildirim durumu.

### `GET /api/notifier/preferences`
Bildirim tercihleri.

### `PUT /api/notifier/preferences`
Bildirim tercihlerini güncelle.

### `GET /api/assistant/status`
AI asistan durumu.

---

## 10. WebSocket

### `WS /ws/quotes`
Canlı fiyat akışı (OHLCV bar'ları).

**Subscribe:** `{"action": "subscribe", "symbol": "THYAO.IS", "interval": "1d"}`

**Mesaj formatı:**
```json
{"type": "bar", "symbol": "THYAO.IS", "bar": {"time": 1714521600, "open": 234.1, "high": 238.5, "low": 231.0, "close": 236.7, "volume": 5000000}}
```

### `WS /ws/signals`
Canlı sinyal akışı (backtest + ML sinyalleri).

**Mesaj formatı:**
```json
{"type": "signal", "symbol": "THYAO.IS", "signal_type": "STRONG_BUY", "price": 236.7, "strength": 8, "reason": "RSI+MACD bullish crossover", "interval": "1d", "ts": "2024-01-15T10:00:00Z"}
```
