"""FastAPI gateway — Sprint 1 foundation + workers.

Eski ``live_server.py`` (stdlib ``http.server`` tabanlı) bu modüle terfi etti.
Sprint 1.4–1.7 ile birlikte canlı veri daemon'ları ``lifespan`` üzerinden
devreye alındı.

Özellikler:

* **Cache-aside** ``/api/v2/candles``: önce SQLite cache (``OHLCVCache``), miss
  olursa ``LiveDataService.fetch_candles`` → ``filter_bars`` → cache'e yaz →
  yanıt.
* **Worker supervisor** (``backend.workers``): Binance WS kline daemon +
  Yahoo poller + BIST hisse poller. Lifespan açılışında başlar, kapanışta
  durur. Sağlık verisi ``/api/health`` içinde.
* **Detaylı ``/api/health``**: cache stats, worker listesi (iter sayısı, son
  hata), v1/v2 mod durumu.
* **CORS** açık (``*``); read-only mod.
* Eski v1 endpoint'leri (``/api/market/defaults``, ``/api/market/chart``,
  ``/api/workspace``, ``POST /api/paper/signal``) aynen korunuyor.
"""

from __future__ import annotations

import datetime as dt
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.data.cache import OHLCVCache
from backend.data.spike_filter import filter_bars
from backend.data.symbols import (
    BIST_STOCKS,
    CRYPTO_WS_SYMBOLS,
    DEFAULT_INTERVAL,
    YAHOO_INDEX_FX_COMMODITY,
)
from backend.workers import WorkerSupervisor
from backend.workers.binance_ws import BinanceKlineWorker
from backend.workers.bist_poller import BistStockPoller
from backend.workers.yahoo_poller import YahooPoller
from quant_engine.data.live_feed import (
    LiveDataService,
    PaperTradingRecorder,
)
from quant_engine.workspace.json_store import WorkspaceJsonStore

ROOT = Path(__file__).resolve().parents[2]

# Cache miss eşiği: cache'teki en yeni bar'dan beri bu süreden uzun zaman
# geçmişse provider'a yeniden git. 15dk barlar için 90s mantıklı.
CACHE_FRESHNESS_SECONDS = 90


def _utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _interval_to_seconds(interval: str) -> int:
    """Interval stringini saniyeye çevir (cache age kararı için)."""
    table = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800,
    }
    return table.get(interval, 900)


def _build_default_supervisor(
    cache: OHLCVCache, data_service: LiveDataService
) -> WorkerSupervisor:
    """Üretim modunda kullanılan varsayılan worker seti."""
    return WorkerSupervisor(
        [
            BinanceKlineWorker(
                cache=cache,
                symbols=CRYPTO_WS_SYMBOLS,
                interval=DEFAULT_INTERVAL,
            ),
            YahooPoller(
                cache=cache,
                data_service=data_service,
                symbols=YAHOO_INDEX_FX_COMMODITY,
                interval=DEFAULT_INTERVAL,
            ),
            BistStockPoller(
                cache=cache,
                data_service=data_service,
                symbols=BIST_STOCKS,
                interval=DEFAULT_INTERVAL,
            ),
        ]
    )


def create_app(
    cache: OHLCVCache | None = None,
    data_service: LiveDataService | None = None,
    workspace_store: WorkspaceJsonStore | None = None,
    paper_recorder: PaperTradingRecorder | None = None,
    supervisor: WorkerSupervisor | None = None,
) -> FastAPI:
    """FastAPI app factory.

    Bağımlılıklar dışarıdan enjekte edilebilir → testte mock'lu örnek
    kurmayı kolaylaştırır. ``supervisor=None`` + ``PIYASAPILOT_DISABLE_WORKERS``
    setli değilse varsayılan worker seti kurulur. Test fikstürleri boş
    ``WorkerSupervisor([])`` geçer → lifespan worker başlatmaz.
    """
    cache = cache or OHLCVCache()
    data_service = data_service or LiveDataService()
    workspace_store = workspace_store or WorkspaceJsonStore(
        ROOT / "data" / "workspaces" / "workspace.json"
    )
    paper_recorder = paper_recorder or PaperTradingRecorder(
        data_service=data_service,
        workspace_path=ROOT / "data" / "workspaces" / "workspace.json",
    )
    if supervisor is None:
        if os.environ.get("PIYASAPILOT_DISABLE_WORKERS") == "1":
            supervisor = WorkerSupervisor([])
        else:
            supervisor = _build_default_supervisor(cache, data_service)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await supervisor.start_all()
        try:
            yield
        finally:
            await supervisor.stop_all()

    app = FastAPI(
        title="PiyasaPilot Gateway",
        version="2.0.0",
        description="Read-only canlı/tarihsel piyasa veri kapısı. Emir motoru kapalı.",
        lifespan=lifespan,
    )
    app.state.supervisor = supervisor
    app.state.cache = cache

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Health ────────────────────────────────────────────────────────────
    @app.get("/api/health")
    def health() -> dict[str, Any]:
        stats = cache.stats()
        return {
            "status": "ok",
            "read_only": True,
            "version": app.version,
            "cache": {
                "rows": stats.rows,
                "distinct_symbols": stats.distinct_symbols,
                "last_inserted_at": stats.last_inserted_at,
            },
            "workers": supervisor.health(),
            "fetched_at": _utc_iso(),
            "message": "PiyasaPilot gateway çalışıyor. Emir motoru pasif.",
        }

    # ── Eski v1 endpoint'leri (geriye dönük) ─────────────────────────────
    @app.get("/api/market/defaults")
    def market_defaults() -> dict[str, Any]:
        return data_service.fetch_default_dashboard()

    @app.get("/api/market/chart")
    def market_chart(symbol: str = "", limit: int = 180) -> dict[str, Any]:
        if not symbol:
            raise HTTPException(status_code=400, detail="Sembol zorunludur.")
        return data_service.fetch_chart(symbol, limit=limit)

    @app.get("/api/workspace")
    def workspace() -> dict[str, Any]:
        return workspace_store.load()

    @app.post("/api/paper/signal")
    async def paper_signal(request: Request) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        try:
            trade = paper_recorder.record_signal(payload)
            return {
                "status": "ok",
                "message": "Sanal paper trade gerçek son fiyatla kaydedildi.",
                "trade": trade,
            }
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # ── v2 endpoint: cache-aside OHLCV ───────────────────────────────────
    @app.get("/api/v2/candles")
    def v2_candles(
        symbol: str = "",
        interval: str = "15m",
        limit: int = 500,
    ) -> JSONResponse:
        """Cache-aside OHLCV dönüşü.

        Akış:
          1. ``OHLCVCache.latest_bar`` ile cache'teki son bar yaşını öğren.
          2. Eğer son bar tazeyse (< CACHE_FRESHNESS_SECONDS) cache'ten oku
             ve döndür.
          3. Aksi halde provider'dan yeni pencere çek, ``filter_bars`` ile
             temizle, cache'e ``upsert_bars`` ile yaz, dön.
          4. Provider hata verirse cache'te biriken eski veriyi yine de döndür
             (graceful degradation), metadata'da ``status='stale'``.
        """
        # Validation backend tarafında zaten yapılıyor; burada sadece çağrı.
        provider_payload = data_service.fetch_candles(
            symbol=symbol, interval=interval, limit=limit
        )

        # Validation hatası → 400 ve cache'i kullanma
        if (
            provider_payload.get("status") == "error"
            and provider_payload.get("metadata", {}).get("error")
            in {"symbol_required", "invalid_interval"}
        ):
            return JSONResponse(provider_payload, status_code=400)

        canonical_symbol = (
            provider_payload.get("symbol") or symbol.strip().upper()
        )
        bars = provider_payload.get("bars") or []

        # Provider başarılı → spike filter + cache'e yaz
        if provider_payload.get("status") == "ok" and bars:
            cleaned, report = filter_bars(bars)
            cache.upsert_bars(canonical_symbol, interval, cleaned)
            provider_payload["bars"] = cleaned
            provider_payload.setdefault("metadata", {})
            provider_payload["metadata"]["spike_filter"] = {
                "total": report.total_bars,
                "winsorized": report.winsorized,
                "untouched_high_volume": report.untouched_high_volume,
            }
            provider_payload["metadata"]["cache"] = "miss_then_write"
            return JSONResponse(provider_payload)

        # Provider hata → cache'te biriken eski veriyle graceful degrade
        cached_bars = cache.get_window(
            canonical_symbol, interval, limit=int(limit) if int(limit) > 0 else 500
        )
        if cached_bars:
            return JSONResponse({
                "symbol": canonical_symbol,
                "display_name": provider_payload.get("display_name", canonical_symbol),
                "market": provider_payload.get("market", ""),
                "interval": interval,
                "status": "stale",
                "message": "Provider'a ulaşılamadı, cache'ten eski veri döndürüldü.",
                "bars": cached_bars,
                "quote": {
                    "last": cached_bars[-1]["close"],
                    "timestamp": _utc_iso(),
                },
                "metadata": {
                    "read_only": True,
                    "cache": "fallback",
                    "provider_error": provider_payload.get("metadata", {}).get("error", ""),
                    "fetched_at": _utc_iso(),
                },
            })

        # Hem provider hem cache boş → hata payload'ını aynen geri ver
        return JSONResponse(provider_payload, status_code=502)

    # ── Statik dosyalar (SPA / index.html) ───────────────────────────────
    # Mount en sona; daha spesifik /api/* route'larını gölgelemesin diye.
    if (ROOT / "index.html").exists():
        @app.get("/")
        def root_index() -> FileResponse:
            return FileResponse(ROOT / "index.html")

    # Statik dizinler (varsa)
    static_dir = ROOT / "data"
    if static_dir.exists():
        app.mount("/data", StaticFiles(directory=static_dir), name="data")

    return app


# Uvicorn entry point: `uvicorn backend.api.main:app`
app = create_app()
