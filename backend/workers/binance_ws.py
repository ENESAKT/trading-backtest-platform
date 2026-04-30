"""Binance public WebSocket kline stream daemon — Sprint 1.5.

Multiplexed stream URL'i (``/stream?streams=...``) ile birden fazla pariteyi
tek bağlantıdan dinler. Her bar **kapanışında** (``k.x == True``) cache'e
``upsert_bars`` ile yazar. Açık (form-on-the-fly) bar'lar yazılmaz —
final değer önce gelmeli (ileride Sprint 1.9 fan-out tarafında "ön-bar"
mesajı browser'a ayrı kanal üzerinden gidecek).

Reconnect: ``websockets.connect`` exception fırlatırsa exponential backoff
(``1s → 30s`` üst sınır). Stop tetiklenirse loop sessiz çıkar.

API anahtarı yok, public market-data stream — ``data-stream.binance.vision``.
"""

from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, Awaitable, Callable

import websockets
from websockets.exceptions import ConnectionClosed

from backend.data.cache import OHLCVCache
from backend.workers.base import AsyncWorker, WorkerHealth, _utc_iso

logger = logging.getLogger(__name__)

# (symbol, interval, [bar]) — fan-out hook'u; testlerde mock'lanır.
BarHook = Callable[..., Awaitable[None] | None]


class BinanceKlineWorker(AsyncWorker):
    """Binance combined kline stream → SQLite cache.

    Uzun ömürlü tek WS bağlantısı. ``run_once`` semantiği uygun değil; bu
    sınıf ``run_forever``'ı override eder.
    """

    BASE_URL = "wss://data-stream.binance.vision/stream"
    PING_INTERVAL = 20.0
    PING_TIMEOUT = 20.0
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 30.0
    BACKOFF_JITTER_RATIO = 0.20
    OPEN_TIMEOUT = 10.0
    MAX_QUEUE = 512

    def __init__(
        self,
        cache: OHLCVCache,
        symbols: list[str] | tuple[str, ...],
        interval: str = "15m",
        on_bar: BarHook | None = None,
    ):
        super().__init__(name="binance_ws", interval_seconds=0.0)
        self.cache = cache
        self.symbols = [s.upper() for s in symbols]
        self.interval = interval
        self.on_bar = on_bar
        self._reconnects = 0
        self._last_connected_at: str | None = None
        self._last_disconnect_at: str | None = None
        self._last_message_at: str | None = None

    def _build_url(self) -> str:
        streams = "/".join(
            f"{s.lower()}@kline_{self.interval}" for s in self.symbols
        )
        return f"{self.BASE_URL}?streams={streams}"

    @staticmethod
    def parse_kline_message(raw: str | bytes) -> tuple[str, dict[str, Any]] | None:
        """WS mesajını (symbol, bar dict) tuple'ına çevir.

        Yalnızca **kapanmış** bar'lar (``k.x == True``) için döner. Açık bar
        veya başka tip mesaj geldiyse None.
        """
        try:
            msg = json.loads(raw)
        except (TypeError, ValueError):
            return None
        data = msg.get("data") if isinstance(msg, dict) else None
        if not isinstance(data, dict):
            return None
        k = data.get("k")
        if not isinstance(k, dict) or not k.get("x"):
            return None
        symbol = data.get("s") or k.get("s") or ""
        if not symbol:
            return None
        try:
            bar = {
                "time": int(k["t"]) // 1000,
                "open": float(k["o"]),
                "high": float(k["h"]),
                "low": float(k["l"]),
                "close": float(k["c"]),
                "volume": float(k["v"]),
            }
        except (KeyError, TypeError, ValueError):
            return None
        return symbol, bar

    async def run_once(self) -> None:
        # ``run_forever`` override edildiği için bu çağrılmaz; ama abstract
        # sözleşmesini karşılamak için no-op tanımı şart.
        return None

    async def run_forever(self) -> None:
        backoff = self.INITIAL_BACKOFF
        while not self._stop.is_set():
            url = self._build_url()
            try:
                async with websockets.connect(
                    url,
                    ping_interval=self.PING_INTERVAL,
                    ping_timeout=self.PING_TIMEOUT,
                    close_timeout=5.0,
                    open_timeout=self.OPEN_TIMEOUT,
                    max_queue=self.MAX_QUEUE,
                ) as ws:
                    self._last_connected_at = _utc_iso()
                    self._last_error = None
                    backoff = self.INITIAL_BACKOFF
                    await self._consume(ws)
            except asyncio.CancelledError:
                raise
            except (ConnectionClosed, OSError, TimeoutError) as exc:
                self._record_disconnect(exc, backoff)
            except Exception as exc:  # noqa: BLE001
                self._record_disconnect(exc, backoff, unexpected=True)

            if self._stop.is_set():
                break
            await self._sleep(self._with_jitter(backoff))
            backoff = min(backoff * 2.0, self.MAX_BACKOFF)

    async def _consume(self, ws: Any) -> None:
        async for raw in ws:
            if self._stop.is_set():
                break
            self._last_message_at = _utc_iso()
            parsed = self.parse_kline_message(raw)
            if parsed is None:
                continue
            symbol, bar = parsed
            await self._persist(symbol, bar)

    def _record_disconnect(
        self,
        exc: BaseException,
        next_backoff: float,
        unexpected: bool = False,
    ) -> None:
        self._failures += 1
        self._reconnects += 1
        self._last_disconnect_at = _utc_iso()
        self._last_error = f"{type(exc).__name__}: {exc}"
        kind = "unexpected" if unexpected else "disconnected"
        logger.warning(
            "binance_ws %s: %s; reconnect in %.1fs",
            kind,
            self._last_error,
            next_backoff,
        )

    def _with_jitter(self, seconds: float) -> float:
        if seconds <= 0:
            return 0
        spread = seconds * self.BACKOFF_JITTER_RATIO
        return max(0.1, seconds + random.uniform(-spread, spread))

    async def _persist(self, symbol: str, bar: dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.cache.upsert_bars, symbol, self.interval, [bar]
        )
        self._iterations += 1
        self._last_run_ok = _utc_iso()
        if self.on_bar is not None:
            try:
                metadata = {
                    "source": "Binance Spot Public WebSocket",
                    "is_real": True,
                    "status": "ok",
                    "provider_name": "binance_ws",
                }
                result = self.on_bar(symbol, self.interval, [bar], metadata)
                if asyncio.iscoroutine(result):
                    await result
            except TypeError:
                result = self.on_bar(symbol, self.interval, [bar])
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001 — hook patladıysa stream durmasın
                logger.warning("binance_ws on_bar hook failed: %s", exc)

    def health(self) -> WorkerHealth:
        base = super().health()
        base.metadata.update(
            {
                "reconnects": self._reconnects,
                "last_connected_at": self._last_connected_at,
                "last_disconnect_at": self._last_disconnect_at,
                "last_message_at": self._last_message_at,
                "backoff": {
                    "initial_seconds": self.INITIAL_BACKOFF,
                    "max_seconds": self.MAX_BACKOFF,
                    "jitter_ratio": self.BACKOFF_JITTER_RATIO,
                },
            }
        )
        return base
