# Data Map

## Purpose

Veri katmanı canlı/önbellekli piyasa verisi, envanter, kalite kontrolleri ve
retention kurallarını kapsar.

## Source Files

- `backend/data/`
- `quant_engine/data/`
- `quant_engine/data_feed/`
- `data/cache/`
- `data/raw/`
- `data/processed/`
- `data/fixtures/`
- `infra/clickhouse/`
- `infra/mysql/`

## Current Facts

- SQLite cache dosyaları `data/cache/` altında bulunur.
- Ham, işlenmiş ve test fixture verileri için `data/raw`, `data/processed`,
  `data/fixtures` klasörleri ayrılmıştır.
- Provider dosyaları hassas kabul edilir ve onaysız değiştirilmez:
  `binance_provider.py`, `yfinance_provider.py`, `live_feed.py`.
- Veri mimarisi dokümanı: `docs/VERI_MIMARISI.md`.

## Related

- [[backend-map]]
- [[../04-modules/quant-engine]]

