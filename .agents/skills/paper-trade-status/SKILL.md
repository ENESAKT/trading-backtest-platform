# Paper Trade Status

Açık pozisyonlar, PnL ve equity eğrisi durumunu raporla.

## Kullanım

Paper trading sisteminin anlık durumunu görmek için çağrılır.

## Komutlar

```bash
# 1. Tüm cüzdanlar
curl -sf http://localhost:8000/api/paper/wallets | python3 -m json.tool

# 2. Son 20 trade
curl -sf http://localhost:8000/api/paper/trades?limit=20 | python3 -m json.tool

# 3. Belirli strateji equity curve
curl -sf "http://localhost:8000/api/paper/equity?strategy_id=sma_crossover&limit=50" | python3 -m json.tool

# 4. Tüm trade'leri export et
curl -sf http://localhost:8000/api/paper/trades/export | python3 -m json.tool
```

## Analiz

```python
import json, urllib.request

# Tüm trade'leri çek
data = json.loads(urllib.request.urlopen("http://localhost:8000/api/paper/trades?limit=1000").read())
trades = data["trades"]

# Tamamlanmış trade'ler
completed = [t for t in trades if t["closed_at"] is not None]
winners = [t for t in completed if (t["pnl"] or 0) > 0]

if completed:
    total_pnl = sum(t["pnl"] or 0 for t in completed)
    win_rate = len(winners) / len(completed) * 100
    avg_pnl = total_pnl / len(completed)
    print(f"Toplam trade: {len(completed)}")
    print(f"Win rate: {win_rate:.1f}%")
    print(f"Toplam PnL: {total_pnl:+.2f}₺")
    print(f"Ort. PnL: {avg_pnl:+.2f}₺")
```

## Yönetim Komutları

```bash
# Stratejiyi dondur
curl -X POST http://localhost:8000/api/paper/halt/sma_crossover

# Stratejiyi devam ettir
curl -X POST http://localhost:8000/api/paper/resume/sma_crossover

# Cüzdanı sıfırla
curl -X POST http://localhost:8000/api/paper/reset/sma_crossover
```
