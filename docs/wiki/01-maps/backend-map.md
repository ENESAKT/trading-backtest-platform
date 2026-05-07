# Backend Map

## Purpose

Backend, FastAPI gateway ve canlı veri/sinyal fan-out işlerini taşır.

## Source Files

- `backend/api/main.py`
- `backend/api/quote_bus.py`
- `backend/signals/signal_bus.py`
- `backend/signals/generator.py`
- `backend/workers/`
- `backend/services/`
- `backend/data/`
- `backend/paper/`

## Current Facts

- FastAPI entrypoint `backend/api/main.py`.
- Quote websocket yolu `/ws/quotes`.
- Signal websocket yolu `/ws/signals`.
- Signal bus canonical import yolu `backend.signals.signal_bus`.
- Worker supervisor API lifespan içinde Binance, Yahoo ve BIST poller başlatır.
- Paper executor simülasyon modundadır; sağlık çıktısında açık pozisyon ve işlem sayaçları görünür.

## Related

- [[data-map]]
- [[../04-modules/deployment]]
- [[../04-modules/quant-engine]]

