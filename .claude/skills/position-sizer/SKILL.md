# Position Sizer

> Adapted from tradermonty/claude-trading-skills

Her trade için optimal pozisyon büyüklüğü hesapla.

## Yöntemler

1. **Fixed Fractional:** Sermayenin sabit yüzdesi (mevcut: %10)
2. **Kelly Criterion:** f* = (bp - q) / b
   - b: ortalama kazanç/kayıp oranı
   - p: kazanma olasılığı
   - q: kaybetme olasılığı (1-p)
3. **Risk-Based:** ATR × pozisyon çarpanı
4. **Volatility Adjusted:** σ(returns) × hedef volatilite

## PiyasaPilot Entegrasyonu

Mevcut sabit değerler (`backend/paper/executor.py`):
- `POSITION_SIZE_PCT = 0.10` (sermayenin %10'u)
- `DAILY_LOSS_LIMIT_PCT = 0.10` (günlük max %10 zarar)

## Kullanım

```python
# Win rate ve profit factor'dan Kelly hesapla
win_rate = 0.55
avg_win = 150
avg_loss = 100
b = avg_win / avg_loss  # 1.5
p = win_rate
q = 1 - p
kelly = (b * p - q) / b  # optimal f*
half_kelly = kelly / 2   # konservatif yaklaşım
```
