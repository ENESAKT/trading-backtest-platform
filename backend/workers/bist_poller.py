"""BIST hisse poller — Sprint 1.7.

``YahooPoller``'ın .IS suffix'li hisseler için 60 saniyelik tarama varyantı.
Aynı pipeline (fetch_candles → filter_bars → upsert) kullanılır; ayrı sınıf
olması (a) supervisor sağlık raporunda ayrı satır göstermek, (b) Sprint 5'te
borsapy entegrasyonuna geçildiğinde noktasal değiştirme imkânı için.

> Not: planlama.md 1.7 başlangıçta ``borsapy`` öneriyordu; PyPI sürümü
> openai/onnxruntime/pymupdf gibi ağır transitif bağımlılıklar getiriyor.
> Foundation'da yfinance .IS yeterli; borsapy değerlendirmesi Sprint 5
> (MCP entegrasyonu) içinde yeniden ele alınacak.
"""

from __future__ import annotations

from typing import Any

from backend.data.cache import OHLCVCache
from backend.workers.yahoo_poller import BarHook, YahooPoller


class BistStockPoller(YahooPoller):
    DEFAULT_POLL_SECONDS = 60.0

    def __init__(
        self,
        cache: OHLCVCache,
        data_service: Any,
        symbols: list[str] | tuple[str, ...],
        interval: str = "15m",
        poll_seconds: float = DEFAULT_POLL_SECONDS,
        limit: int = YahooPoller.DEFAULT_LIMIT,
        on_bar: BarHook | None = None,
    ):
        super().__init__(
            cache=cache,
            data_service=data_service,
            symbols=symbols,
            interval=interval,
            poll_seconds=poll_seconds,
            limit=limit,
            name="bist_poller",
            on_bar=on_bar,
        )
