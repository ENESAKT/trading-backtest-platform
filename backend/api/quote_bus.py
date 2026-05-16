"""In-memory pub/sub — Sprint 1.9 WS fan-out altyapısı.

Worker'lar cache'e bar yazdığında ``QuoteBus.publish`` çağrılır; bus mesajı
tüm bağlı WebSocket client'larının kuyruğuna iletir. Tek process içinde
çalışır (uvicorn worker'ları arası dağıtım Redis'e yükseltileceği zaman
Sprint 7'de gelecek).

Tasarım notları:

* Her client için kendi ``asyncio.Queue`` — yavaş bir client diğerlerini
  yavaşlatmasın. Kuyruk dolarsa eski mesajlar düşer (drop oldest).
* Subscribe sırasında client istediği ``symbols`` ve ``intervals`` filtresini
  belirtebilir. Boş liste = "hepsini al".
* Reentrant: ``publish`` hook'u worker'ın olay döngüsünden çağrılır; bus
  yalnızca ``Queue.put_nowait`` yapar, blocking yok.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

QUEUE_MAX = 256


@dataclass
class _Subscription:
    queue: asyncio.Queue[dict[str, Any]]
    symbols: frozenset[str] = field(default_factory=frozenset)
    intervals: frozenset[str] = field(default_factory=frozenset)
    dropped: int = 0

    def matches(self, symbol: str, interval: str) -> bool:
        if self.symbols and symbol not in self.symbols:
            return False
        if self.intervals and interval not in self.intervals:
            return False
        return True


class QuoteBus:
    """Tek process içinde fan-out pub/sub.

    ``publish`` worker thread/loop'undan çağrılabilir; bus iç state'i bir
    ``asyncio.Lock`` ile korunur, asıl payload teslimi non-blocking
    ``Queue.put_nowait`` ile yapılır.
    """

    def __init__(self, queue_max: int = QUEUE_MAX):
        self._subs: dict[str, _Subscription] = {}
        self._lock = asyncio.Lock()
        self.queue_max = int(queue_max)
        self.published_count = 0

    # ── Client lifecycle ─────────────────────────────────────────────────
    async def subscribe(
        self,
        symbols: list[str] | tuple[str, ...] | None = None,
        intervals: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[str, asyncio.Queue[dict[str, Any]]]:
        """Yeni client kaydı — (client_id, kuyruğu) döner."""
        client_id = uuid.uuid4().hex[:12]
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_max)
        sub = _Subscription(
            queue=queue,
            symbols=frozenset(s.upper() for s in (symbols or [])),
            intervals=frozenset(intervals or []),
        )
        async with self._lock:
            self._subs[client_id] = sub
        logger.info(
            "quote_bus subscribe: %s symbols=%s intervals=%s (total=%d)",
            client_id,
            sub.symbols or "ALL",
            sub.intervals or "ALL",
            len(self._subs),
        )
        return client_id, queue

    async def unsubscribe(self, client_id: str) -> None:
        async with self._lock:
            self._subs.pop(client_id, None)
        logger.info("quote_bus unsubscribe: %s (total=%d)", client_id, len(self._subs))

    # ── Publish ──────────────────────────────────────────────────────────
    async def publish(
        self, symbol: str, interval: str, bars: list[dict[str, Any]]
    ) -> None:
        """Worker'ın ``on_bar`` hook'undan çağrılır.

        Eşleşen subscriber'lara non-blocking push. Kuyruk doluysa en eski
        mesaj atılır ve yenisi yerine konur (drop-oldest).
        """
        if not bars:
            return
        message = {
            "type": "bars",
            "symbol": symbol.upper(),
            "interval": interval,
            "bars": bars,
            "ts": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        async with self._lock:
            targets = [
                sub for sub in self._subs.values()
                if sub.matches(message["symbol"], interval)
            ]
        for sub in targets:
            self._enqueue(sub, message)
        self.published_count += 1

    def _enqueue(self, sub: _Subscription, message: dict[str, Any]) -> None:
        try:
            sub.queue.put_nowait(message)
        except asyncio.QueueFull:
            try:
                _ = sub.queue.get_nowait()
                sub.dropped += 1
            except asyncio.QueueEmpty:
                pass
            try:
                sub.queue.put_nowait(message)
            except asyncio.QueueFull:  # pragma: no cover — unreachable
                pass

    # ── Stats ────────────────────────────────────────────────────────────
    def stats(self) -> dict[str, Any]:
        return {
            "subscribers": len(self._subs),
            "published": self.published_count,
            "dropped_total": sum(s.dropped for s in self._subs.values()),
        }
