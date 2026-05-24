"""In-memory signal pub/sub — Sprint 3.5 ``/ws/signals`` fan-out altyapısı.

``QuoteBus``'ın yapısal ikizi; ayrı tutuldu çünkü:

* Filtre semantiği farklı (sembol + ``strategy_id`` veya ``BUY``/``SELL``).
* Yayın hızı çok daha düşük (her bar kapanışında 0–N sinyal); burada
  drop-oldest eşiği daha uzun olabilir ama davranış aynı tutuldu.
* Sprint 6'da AI sinyal feed (``/ws/signals/ai``) ayrı bir bus olur;
  hibrit ayrımı temiz kalsın.
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
    types: frozenset[str] = field(default_factory=frozenset)
    dropped: int = 0

    def matches(self, symbol: str, signal_type: str) -> bool:
        if self.symbols and symbol not in self.symbols:
            return False
        if self.types and signal_type not in self.types:
            return False
        return True


class SignalBus:
    """Tek process içinde signal fan-out pub/sub."""

    def __init__(self, queue_max: int = QUEUE_MAX):
        self._subs: dict[str, _Subscription] = {}
        self._lock = asyncio.Lock()
        self.queue_max = int(queue_max)
        self.published_count = 0

    async def subscribe(
        self,
        symbols: list[str] | tuple[str, ...] | None = None,
        types: list[str] | tuple[str, ...] | None = None,
    ) -> tuple[str, asyncio.Queue[dict[str, Any]]]:
        client_id = uuid.uuid4().hex[:12]
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self.queue_max)
        sub = _Subscription(
            queue=queue,
            symbols=frozenset(s.upper() for s in (symbols or [])),
            types=frozenset(t.upper() for t in (types or [])),
        )
        async with self._lock:
            self._subs[client_id] = sub
        logger.info(
            "signal_bus subscribe: %s symbols=%s types=%s (total=%d)",
            client_id, sub.symbols or "ALL", sub.types or "ALL", len(self._subs),
        )
        return client_id, queue

    async def unsubscribe(self, client_id: str) -> None:
        async with self._lock:
            self._subs.pop(client_id, None)
        logger.info("signal_bus unsubscribe: %s (total=%d)", client_id, len(self._subs))

    async def publish(
        self,
        symbol: str,
        signal_type: str,
        price: float,
        strategy_id: str,
        reason: str = "",
        strength: int = 5,
        interval: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> None:
        message = {
            "type": "signal",
            "symbol": symbol.upper(),
            "signal_type": signal_type.upper(),
            "price": float(price),
            "strategy_id": strategy_id,
            "reason": reason,
            "strength": int(strength),
            "interval": interval,
            "ts": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        }
        if metadata:
            message["metadata"] = metadata
        async with self._lock:
            targets = [
                sub for sub in self._subs.values()
                if sub.matches(message["symbol"], message["signal_type"])
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
            except asyncio.QueueFull:  # pragma: no cover
                pass

    def stats(self) -> dict[str, Any]:
        return {
            "subscribers": len(self._subs),
            "published": self.published_count,
            "dropped_total": sum(s.dropped for s in self._subs.values()),
        }
