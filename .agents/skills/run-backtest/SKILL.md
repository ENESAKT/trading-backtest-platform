# Run Backtest

Hızlı backtest çalıştır ve sonuçları raporla.

## Kullanım

Sembol ve strateji vererek backtest çalıştır. Opsiyonel: sermaye, lookback bar sayısı.

## Hızlı Çalıştırma

```bash
# Gateway çalışıyor olmalı
curl -X POST http://localhost:8000/api/backtest/run \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "THYAO.IS",
    "strategy_id": "sma_crossover",
    "params": {"fast_period": 10, "slow_period": 30},
    "capital": 100000,
    "lookback_bars": 500
  }'
```

## Veya Python ile

```python
from backend.backtest import run_backtest
from backend.data.cache import OHLCVCache

cache = OHLCVCache()
result = run_backtest(
    cache=cache,
    symbol="THYAO.IS",
    interval="15m",
    strategy_id="sma_crossover",
    params={"fast_period": 10, "slow_period": 30},
    capital=100_000,
    lookback_bars=500,
)
print(f"Return: {result['metrics']['total_return_pct']:.2f}%")
print(f"Max DD: {result['metrics']['max_drawdown_pct']:.2f}%")
print(f"Trades: {result['metrics']['total_trades']}")
```

## Mevcut Stratejiler

`GET /api/backtest/strategies` ile güncel listeyi al.

| ID | Varsayılan Parametreler |
|----|------------------------|
| sma_crossover | fast_period=10, slow_period=30 |
| rsi_reversion | rsi_period=14, oversold=30, overbought=70 |
| bollinger_reversion | period=20, std_dev=2.0 |
| buy_and_hold | - |
| donchian_breakout | period=20 |
| macd_divergence | fast=12, slow=26, signal=9 |
| supertrend | period=10, multiplier=3.0 |
| mean_reversion_vwap | vwap_period=20, threshold=2.0 |
