# Quant Engine

## Purpose

Quant engine, strateji, backtest, research, risk ve veri sağlayıcı çekirdeğini
taşır.

## Source Files

- `quant_engine/backtest/`
- `quant_engine/strategy/`
- `quant_engine/strategies/`
- `quant_engine/indicators/`
- `quant_engine/risk/`
- `quant_engine/research/`
- `quant_engine/data/`

## Current Facts

- Backtest engine dosyası `quant_engine/backtest/engine.py` koruma listesindedir.
- Strategy implementation ve registry `quant_engine/strategy/` altında mevcut.
- Yeni mimari iskelet için `quant_engine/strategies`, `quant_engine/indicators`,
  `quant_engine/risk`, `quant_engine/optimizer`, `quant_engine/metrics`,
  `quant_engine/data_feed` klasörleri bulunur.

## Related

- [[../01-maps/project-map]]
- [[../01-maps/data-map]]

