# Signal Postmortem

> Adapted from tradermonty/Codex-trading-skills

Kapanan trade'leri analiz et ve öğrenme çıkar.

## Görev

1. Son kapanan trade'leri çek (`/api/paper/trades?limit=20`)
2. Her trade için:
   - Giriş/çıkış zamanlaması doğru muydu?
   - Stop-loss veya take-profit tetiklendi mi?
   - Strateji sinyalinin kalitesi nasıldı?
3. Pattern tespiti:
   - Hangi stratejiler daha iyi çalışıyor?
   - Belirli saatlerde performans farkı var mı?
   - Sembol bazlı eğilimler (BIST hisseleri vs kripto)

## Analiz Şablonu

```markdown
## Trade Postmortem — [trade_id]

### Detaylar
- Strateji: sma_crossover
- Sembol: THYAO.IS
- Yön: BUY → SELL
- Giriş: ₺185.50 @ 09:30
- Çıkış: ₺188.20 @ 14:15
- PnL: +₺270 (+1.46%)

### Zamanlama Analizi
- Giriş: [Erken/Zamanında/Geç]
- Çıkış: [Erken/Zamanında/Geç]

### Öğrenilen
- [Teknik bulgu]
- [Strateji iyileştirme önerisi]
```

## PiyasaPilot API

```bash
# Son trade'leri çek
curl -sf http://localhost:8000/api/paper/trades?limit=20

# Belirli strateji trade'leri
curl -sf "http://localhost:8000/api/paper/trades?strategy_id=sma_crossover&limit=20"
```
