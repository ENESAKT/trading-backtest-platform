"""Async worker iskeleti — Sprint 1.4.

Bütün canlı veri daemon'ları (Binance WS, yfinance/BIST poller) bu temel
sınıfı genişletir. Ortak davranış:

* ``start()`` → ``run_forever`` task'ını ``asyncio.create_task`` ile başlatır.
* ``run_forever`` → ``while not stop_event``: ``run_once()`` + interrupt-able
  sleep. ``run_once`` istisna fırlatırsa logla ve devam et — daemon
  düşmesin (canlı yayında "her şey ölmesin" prensibi).
* ``stop()`` → stop_event tetikle, task'ı bekle (timeout ile).
* ``health()`` → snapshot dict (iter sayısı, son hata, son başarılı zaman).

Long-running stream worker'lar (örn. Binance WS) ``run_forever``'ı override
edip kendi backoff/reconnect loop'larını kurar — ``run_once`` semantiği
tüm worker'lara dayatılmıyor.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class WorkerHealth:
    name: str
    running: bool
    iterations: int
    failures: int
    last_run_ok: str | None
    last_error: str | None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AsyncWorker(ABC):
    """Periyodik async worker tabanı.

    Alt sınıflar ``run_once`` implement eder. ``interval_seconds`` iki çağrı
    arasındaki uyku süresidir (jitter dışarıdan uygulanabilir). ``0`` veya
    negatif verilirse uyku skip edilir → sürekli akış (örn. WS) için
    ``run_forever`` override edilir.
    """

    name: str
    interval_seconds: float

    def __init__(self, name: str, interval_seconds: float):
        self.name = name
        self.interval_seconds = float(interval_seconds)
        self._task: asyncio.Task[None] | None = None
        self._stop = asyncio.Event()
        self._iterations = 0
        self._failures = 0
        self._last_run_ok: str | None = None
        self._last_error: str | None = None

    # ── Lifecycle ────────────────────────────────────────────────────────
    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            return
        self._stop.clear()
        self._task = asyncio.create_task(self.run_forever(), name=f"worker:{self.name}")
        logger.info("worker started: %s", self.name)

    async def stop(self, timeout: float = 5.0) -> None:
        self._stop.set()
        task = self._task
        if task is None:
            return
        try:
            await asyncio.wait_for(task, timeout=timeout)
        except asyncio.TimeoutError:
            logger.warning("worker %s did not stop within %.1fs; cancelling", self.name, timeout)
            task.cancel()
            try:
                await task
            except (asyncio.CancelledError, Exception):
                pass
        finally:
            self._task = None
            logger.info("worker stopped: %s", self.name)

    @property
    def running(self) -> bool:
        return self._task is not None and not self._task.done()

    # ── Loop ─────────────────────────────────────────────────────────────
    async def run_forever(self) -> None:
        """Stop tetiklenene kadar ``run_once`` çağır + interrupt-able sleep."""
        while not self._stop.is_set():
            try:
                await self.run_once()
                self._iterations += 1
                self._last_run_ok = _utc_iso()
            except asyncio.CancelledError:
                raise
            except Exception as exc:  # noqa: BLE001 — daemon düşmesin
                self._failures += 1
                self._last_error = f"{type(exc).__name__}: {exc}"
                logger.warning("worker %s failed: %s", self.name, self._last_error)
            if self.interval_seconds > 0:
                await self._sleep(self.interval_seconds)

    async def _sleep(self, seconds: float) -> None:
        """Stop tetiklenirse erken çıkacak şekilde uyu."""
        try:
            await asyncio.wait_for(self._stop.wait(), timeout=seconds)
        except asyncio.TimeoutError:
            return

    @abstractmethod
    async def run_once(self) -> None:
        """Bir çevrim — alt sınıfta implement edilir."""

    # ── Sağlık ──────────────────────────────────────────────────────────
    def health(self) -> WorkerHealth:
        return WorkerHealth(
            name=self.name,
            running=self.running,
            iterations=self._iterations,
            failures=self._failures,
            last_run_ok=self._last_run_ok,
            last_error=self._last_error,
        )


class WorkerSupervisor:
    """Birden fazla worker'ı tek lifespan altında başlat/durdur.

    FastAPI ``lifespan`` context'i şu kalıbı kullanır::

        async with WorkerSupervisor(workers).run():
            yield  # uygulama açık

    Veya manuel: ``await sup.start_all()`` / ``await sup.stop_all()``.
    """

    def __init__(self, workers: list[AsyncWorker] | None = None):
        self.workers: list[AsyncWorker] = list(workers or [])

    def add(self, worker: AsyncWorker) -> None:
        self.workers.append(worker)

    async def start_all(self) -> None:
        for w in self.workers:
            await w.start()

    async def stop_all(self, timeout: float = 5.0) -> None:
        await asyncio.gather(
            *(w.stop(timeout=timeout) for w in self.workers),
            return_exceptions=True,
        )

    def health(self) -> list[dict[str, Any]]:
        return [w.health().to_dict() for w in self.workers]
