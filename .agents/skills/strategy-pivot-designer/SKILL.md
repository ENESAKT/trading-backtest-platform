# Strategy Pivot Designer

> Adapted from tradermonty/Codex-trading-skills

Mevcut strateji performansını değerlendirip iyileştirme / pivot önerileri sun.

## Görev

1. Mevcut stratejinin backtest sonuçlarını analiz et
2. Zayıf noktaları tespit et (düşük win rate, büyük drawdown, vb.)
3. Parametre ayarlama önerileri sun
4. Gerekirse tamamen farklı bir strateji pivot'u öner

## Pivot Karar Ağacı

```
Win rate < 40%?
  ├── Evet → Giriş sinyalini güçlendir (ek filtre ekle)
  └── Hayır → Profit factor < 1?
      ├── Evet → Çıkış mantığını iyileştir (trailing stop?)
      └── Hayır → Max DD > 20%?
          ├── Evet → Pozisyon büyüklüğünü azalt
          └── Hayır → Strateji çalışıyor, parametre optimize et
```

## Optimizasyon Önerileri

- **Time filter:** Sadece piyasa saatlerinde işlem (BIST 10:00-18:00)
- **Trend filter:** ADX > 25 iken trend stratejileri, ADX < 20 iken range
- **Volatility filter:** ATR bant genişliği ile pozisyon boyutu ayarla
- **Correlation filter:** Aynı sektörden çoklu pozisyon alma
