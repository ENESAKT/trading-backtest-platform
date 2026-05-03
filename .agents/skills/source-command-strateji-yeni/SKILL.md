---
name: "source-command-strateji-yeni"
description: "Yeni strateji önerisi al (quant-researcher agent'ını başlat)"
---

# source-command-strateji-yeni

Use this skill when the user asks to run the migrated source command `strateji-yeni`.

## Command Template

# /strateji-yeni

Quant researcher agent'ını başlatarak yeni strateji önerisi al.

## Kullanım

```
/strateji-yeni
/strateji-yeni momentum
/strateji-yeni mean-reversion BIST
/strateji-yeni seasonality
```

## Adımlar

1. Opsiyonel odak alanını parse et (momentum, mean-reversion, breakout, seasonality, hybrid)
2. Mevcut 8 stratejiyi listele → yeni strateji bu 8'den farklı olmalı
3. `quant-researcher` agent'ını başlat:
   - Strateji fikri üret
   - Giriş/çıkış kurallarını formal tanımla
   - Test edilecek parametreleri öner
   - Beklenen edge'i açıkla
4. Önerilen strateji için basit backtest koş (3 farklı sembol üzerinde)
5. Sonuçları raporla ve implementasyonu öner

## Mevcut Stratejiler (tekrarı önlemek için)

1. `sma_crossover` — SMA hızlı/yavaş çakışması
2. `rsi_reversion` — RSI aşırı alım/satım
3. `bollinger_reversion` — BB geri dönüş
4. `buy_and_hold` — Al ve tut
5. `donchian_breakout` — Donchian kanal kırılımı
6. `macd_divergence` — MACD kesişim
7. `supertrend` — ATR Supertrend
8. `mean_reversion_vwap` — VWAP sapma

## Yeni Strateji Adayları

- Ichimoku Cloud breakout
- ADX trend gücü filtreli momentum
- Williams %R oversold bounce
- Volume Profile (POC/VA) tabanlı
- Keltner Channel squeeze breakout
- Stochastic divergence
- Parabolic SAR trend reversal
