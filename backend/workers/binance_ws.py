"""Binance public WebSocket kline stream daemon — Sprint 1.5.

Multiplexed stream URL'i (``/stream?streams=...``) ile birden fazla pariteyi
tek bağlantıdan dinler. Her bar **kapanışında** (``k.x == True``) cache'e
``upsert_bars`` ile yazar. Açık (form-on-the-fly) bar'lar yazılmaz —
final değer önce gelmeli (ileride Sprint 1.9 fan-out tarafında "ön-bar"
mesajı browser'a ayrı kanal üzerinden gidecek).

Reconnect: ``websockets.connect`` exception fırlatırsa exponential backoff
(``1s → 30s`` üst sınır). Stop tetiklenirse loop sessiz çıkar.

API anahtarı yok, public stream — ``stream.binance.com:9443``.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Awaitable, Callable

import websockets
from websockets.exceptions import ConnectionClosed

from backend.data.cache import OHLCVCache
from backend.workers.base import AsyncWorker, _utc_iso

logger = logging.getLogger(__name__)

# (symbol, interval, [bar]) — fan-out hook'u; testlerde mock'lanır.
BarHook = Callable[[str, str, list[dict[str, Any]]], Awaitable[None] | None]


class BinanceKlineWorker(AsyncWorker):
    """Binance combined kline stream → SQLite cache.

    Uzun ömürlü tek WS bağlantısı. ``run_once`` semantiği uygun değil; bu
    sınıf ``run_forever``'ı override eder.
    """

    BASE_URL = "wss://stream.binance.com:9443/stream"
    PING_INTERVAL = 20.0
    PING_TIMEOUT = 20.0
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 30.0

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
                ) as ws:
                    backoff = self.INITIAL_BACKOFF
                    await self._consume(ws)
            except asyncio.CancelledError:
                raise
            except (ConnectionClosed, OSError) as exc:
                self._failures += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("binance_ws disconnected: %s", self._last_error)
            except Exception as exc:  # noqa: BLE001
                self._failures += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("binance_ws unexpected: %s", self._last_error)

            if self._stop.is_set():
                break
            await self._sleep(backoff)
            backoff = min(backoff * 2.0, self.MAX_BACKOFF)

    async def _consume(self, ws: Any) -> None:
        async for raw in ws:
            if self._stop.is_set():
                break
            parsed = self.parse_kline_message(raw)
            if parsed is None:
                continue
            symbol, bar = parsed
            await self._persist(symbol, bar)

    async def _persist(self, symbol: str, bar: dict[str, Any]) -> None:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.cache.upsert_bars, symbol, self.interval, [bar]
        )
        self._iterations += 1
        self._last_run_ok = _utc_iso()
        if self.on_bar is not None:
            try:
                result = self.on_bar(symbol, self.interval, [bar])
                if asyncio.iscoroutine(result):
                    await result
            except Exception as exc:  # noqa: BLE001 — hook patladıysa stream durmasın
                logger.warning("binance_ws on_bar hook failed: %s", exc)
