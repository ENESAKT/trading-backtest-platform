---
description: "Backtest çalıştır ve sonucu raporla"
argument-hint: "<sembol> <strateji>"
---

# /backtest

Verilen sembol ve strateji için backtest çalıştır.

## Kullanım

```
/backtest THYAO.IS sma_crossover
/backtest BTCUSDT rsi_reversion
/backtest GARAN.IS bollinger_reversion --capital 50000
```

## Adımlar

1. Argümanları parse et: `sembol`, `strateji`, opsiyonel `--capital` (varsayılan 100.000₺)
2. Stratejinin var olduğunu doğrula: `GET /api/backtest/strategies`
3. Cache'te yeterli veri olduğunu kontrol et: `GET /api/v2/candles?symbol=X&limit=50`
4. Backtest çalıştır:
   ```bash
   curl -X POST http://localhost:8000/api/backtest/run \
     -H "Content-Type: application/json" \
     -d '{"symbol":"<sembol>","strategy_id":"<strateji>","capital":<sermaye>,"lookback_bars":500}'
   ```
5. Sonuçları tablo formatında raporla
6. Yorum ekle: strateji kârlı mı, risk kabul edilebilir mi

## Mevcut Stratejiler

| ID | Açıklama |
|----|----------|
| sma_crossover | SMA hızlı/yavaş çakışması |
| rsi_reversion | RSI aşırı alım/satım geri dönüşü |
| bollinger_reversion | Bollinger Bandı geri dönüşü |
| buy_and_hold | Al ve tut (benchmark) |
| donchian_breakout | Donchian kanal kırılımı |
| macd_divergence | MACD sinyal çizgisi kesişimi |
| supertrend | ATR tabanlı Supertrend |
| mean_reversion_vwap | VWAP sapma geri dönüşü |
