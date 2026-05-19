"""Async worker daemon'ları (Sprint 1.4–1.7).

* ``base.AsyncWorker`` — periyodik / sürekli çalışan worker'lar için ortak iskelet.
* ``base.WorkerSupervisor`` — birden fazla worker'ı tek lifespan altında yönet.
* ``binance_ws.BinanceKlineWorker`` — Binance public WS kline stream → cache.
* ``yahoo_poller.YahooPoller`` — yfinance üzerinden BIST endeks + FX + emtia.
* ``bist_poller.BistStockPoller`` — yfinance ``.IS`` ile BIST 100 hisseler.

Workers ``OHLCVCache.upsert_bars`` ile yazar; üst katman bunu ``filter_bars``
sonrasında yapar (fonksiyon işbirlikleri ``main.lifespan`` tarafında kurulur).
"""

from backend.workers.base import AsyncWorker, WorkerHealth, WorkerSupervisor

__all__ = ["AsyncWorker", "WorkerHealth", "WorkerSupervisor"]
