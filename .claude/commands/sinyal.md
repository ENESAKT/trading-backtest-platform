---
description: "Belirli bir sembol için teknik analiz sinyal raporu üret"
argument-hint: "<sembol>"
---

# /sinyal

Verilen sembol için teknik analiz tabanlı sinyal raporu üret.

## Kullanım

```
/sinyal THYAO.IS
/sinyal BTCUSDT
/sinyal GARAN.IS
```

## Adımlar

1. Sembolün tarihsel verisini çek: `GET /api/v2/candles?symbol=X&interval=15m&limit=500`
2. Tüm 8 stratejiyi bu sembol üzerinde koş (backtest-runner agent'ı ile)
3. Her stratejinin mevcut sinyalini (BUY/SELL/HOLD) belirle
4. Konsensüs oluştur:
   - 5+ strateji aynı yönde → **GÜÇLÜ SİNYAL**
   - 3–4 strateji aynı yönde → **ORTA SİNYAL**
   - 2 veya daha az → **ZAYIF SİNYAL**
5. Teknik gösterge özeti ekle (RSI, MACD, BB konumu, EMA trendi)

## Çıktı Formatı

```
## Sinyal Raporu: THYAO.IS — Türk Hava Yolları

### Konsensüs: 🟢 GÜÇLÜ AL (6/8 strateji)

| Strateji | Sinyal | Güven |
|----------|--------|-------|
| SMA Crossover | AL ▲ | %85 |
| RSI Reversion | TUT — | %40 |
| ... | ... | ... |

### Teknik Göstergeler
- RSI(14): 62.3 (nötr)
- MACD: pozitif, sinyal üstünde
- BB: orta bant üzerinde
- EMA(20): fiyat üzerinde (yükseliş)

### Yorum
[Kısa teknik analiz yorumu]
```
