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

import asyncio
import datetime as dt
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from backend.api.quote_bus import QuoteBus
from backend.api.signal_bus import SignalBus
from backend.backtest import (
    BacktestNotEnoughData,
    BacktestRunError,
    UnknownStrategy,
    list_blueprints,
    run_backtest,
)
from backend.data.cache import OHLCVCache
from backend.data.spike_filter import filter_bars
from backend.paper import PaperDB, PaperExecutor
from backend.signals import SignalGenerator
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
_PAPER_DB_PATH = "data/cache/ohlcv.sqlite3"

# Cache miss eşiği: cache'teki en yeni bar'dan beri bu süreden uzun zaman
# geçmişse provider'a yeniden git. 15dk barlar için 90s mantıklı.
CACHE_FRESHNESS_SECONDS = 90


def _utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


async def _drain_client_messages(ws: WebSocket) -> None:
    """Client-side mesajları boşaltarak disconnect tespitini sağla.

    Protokol bu PR'da sadece "subscribe" başlangıç kanalı; client'tan gelen
    diğer mesajlar şimdilik yutulur. Disconnect olunca ``WebSocketDisconnect``
    fırlar ve ana döngü ``recv_task.done()`` üzerinden çıkar.
    """
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        return
    except Exception:  # noqa: BLE001
        return


def _interval_to_seconds(interval: str) -> int:
    """Interval stringini saniyeye çevir (cache age kararı için)."""
    table = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "1d": 86400, "1w": 604800,
    }
    return table.get(interval, 900)


def _build_default_supervisor(
    cache: OHLCVCache,
    data_service: LiveDataService,
    quote_bus: QuoteBus | None = None,
    signal_generator: SignalGenerator | None = None,
    paper_executor: PaperExecutor | None = None,
) -> WorkerSupervisor:
    """Üretim modunda kullanılan varsayılan worker seti.

    Worker bar yazdığında iki ayrı fan-out tetiklenir:
      * ``quote_bus.publish`` → ``/ws/quotes`` (canlı bar)
      * ``signal_generator.evaluate`` → cache'ten son N barı çek,
        kayıtlı stratejileri koştur, AL/SAT varsa ``signal_bus`` →
        ``/ws/signals``.
    """
    async def _on_bar(symbol: str, interval: str, bars: list[dict[str, Any]]) -> None:
        if quote_bus is not None:
            await quote_bus.publish(symbol, interval, bars)
        if signal_generator is not None:
            await signal_generator.evaluate(symbol, interval, bars)
        if paper_executor is not None and bars:
            last_close = float(bars[-1].get("close", 0))
            if last_close > 0:
                paper_executor.update_prices({symbol.upper(): last_close})

    on_bar = _on_bar if (quote_bus is not None or signal_generator is not None or paper_executor is not None) else None
    return WorkerSupervisor(
        [
            BinanceKlineWorker(
                cache=cache,
                symbols=CRYPTO_WS_SYMBOLS,
                interval=DEFAULT_INTERVAL,
                on_bar=on_bar,
            ),
            YahooPoller(
                cache=cache,
                data_service=data_service,
                symbols=YAHOO_INDEX_FX_COMMODITY,
                interval=DEFAULT_INTERVAL,
                on_bar=on_bar,
            ),
            BistStockPoller(
                cache=cache,
                data_service=data_service,
                symbols=BIST_STOCKS,
                interval=DEFAULT_INTERVAL,
                on_bar=on_bar,
            ),
        ]
    )


def create_app(
    cache: OHLCVCache | None = None,
    data_service: LiveDataService | None = None,
    workspace_store: WorkspaceJsonStore | None = None,
    paper_recorder: PaperTradingRecorder | None = None,
    supervisor: WorkerSupervisor | None = None,
    quote_bus: QuoteBus | None = None,
    signal_bus: SignalBus | None = None,
    signal_generator: SignalGenerator | None = None,
    paper_executor: PaperExecutor | None = None,
) -> FastAPI:
    """FastAPI app factory.

    Bağımlılıklar dışarıdan enjekte edilebilir → testte mock'lu örnek
    kurmayı kolaylaştırır. ``supervisor=None`` + ``PIYASAPILOT_DISABLE_WORKERS``
    setli değilse varsayılan worker seti kurulur. ``quote_bus`` verilmezse
    yeni bir tane yaratılır ve worker'lar buna ``on_bar`` ile bağlanır.
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
    quote_bus = quote_bus if quote_bus is not None else QuoteBus()
    signal_bus = signal_bus if signal_bus is not None else SignalBus()
    signal_generator = (
        signal_generator
        if signal_generator is not None
        else SignalGenerator(cache=cache, bus=signal_bus)
    )
    paper_db = PaperDB(ROOT / _PAPER_DB_PATH)
    paper_db.ensure_tables()
    paper_executor = paper_executor or PaperExecutor(db=paper_db)

    if supervisor is None:
        if os.environ.get("PIYASAPILOT_DISABLE_WORKERS") == "1":
            supervisor = WorkerSupervisor([])
        else:
            supervisor = _build_default_supervisor(
                cache, data_service, quote_bus, signal_generator, paper_executor,
            )

    async def _paper_executor_loop() -> None:
        client_id, queue = await signal_bus.subscribe()
        try:
            while True:
                msg = await queue.get()
                await paper_executor.process_signal(msg)
        except asyncio.CancelledError:
            pass
        finally:
            await signal_bus.unsubscribe(client_id)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        await supervisor.start_all()
        executor_task = asyncio.create_task(_paper_executor_loop())
        try:
            from backend.notifier.telegram import bildir_bot_basladi
            asyncio.create_task(bildir_bot_basladi())
        except Exception:  # noqa: BLE001
            pass
        try:
            yield
        finally:
            executor_task.cancel()
            await supervisor.stop_all()
            try:
                from backend.notifier.telegram import bildir_bot_durdu
                await bildir_bot_durdu()
            except Exception:  # noqa: BLE001
                pass

    app = FastAPI(
        title="PiyasaPilot Gateway",
        version="2.0.0",
        description="Read-only canlı/tarihsel piyasa veri kapısı. Emir motoru kapalı.",
        lifespan=lifespan,
    )
    app.state.supervisor = supervisor
    app.state.cache = cache
    app.state.quote_bus = quote_bus
    app.state.signal_bus = signal_bus
    app.state.signal_generator = signal_generator
    app.state.paper_db = paper_db
    app.state.paper_executor = paper_executor

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )

    # ── Assistant durumu ──────────────────────────────────────────────────
    @app.get("/api/assistant/status")
    def assistant_status() -> dict[str, Any]:
        """Telegram listener ve proje asistanının anlık durumu."""
        try:
            from backend.notifier.telegram_listener import get_listener_status
            listener = get_listener_status()
        except Exception:
            listener = {}
        return {
            "listener_aktif": listener.get("aktif", False),
            "islenen_mesaj": listener.get("islenen_mesaj", 0),
            "son_mesaj_ozet": listener.get("son_mesaj"),
            "son_hata": listener.get("son_hata"),
            "komutlar": [
                "/yardim", "/durum", "/fiyat", "/sinyal", "/strateji",
                "/ozet", "/son", "/hata", "/kontrol", "/gorev", "/duzelt",
            ],
            "llm_aktif": bool(os.getenv("ANTHROPIC_API_KEY")),
        }

    # ── Notifier durumu ───────────────────────────────────────────────────
    @app.get("/api/notifier/status")
    def notifier_status() -> dict[str, Any]:
        """Telegram bildirim servisinin anlık durumu."""
        import os
        token_var = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_var = os.getenv("TELEGRAM_CHAT_ID", "")
        telegram_configured = bool(token_var and chat_var)
        try:
            from backend.notifier.main import get_notifier_status
            durum = get_notifier_status()
        except Exception:
            durum = {}
        return {
            "telegram_yapilandirildi": telegram_configured,
            "token_son4": f"...{token_var[-4:]}" if token_var else None,
            "chat_id": chat_var if chat_var else None,
            "aktif": durum.get("aktif", False),
            "son_bildirim": durum.get("son_bildirim"),
            "son_hata": durum.get("son_hata"),
            "toplam_bildirim": durum.get("toplam_bildirim", 0),
        }

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
            "quote_bus": quote_bus.stats(),
            "signal_bus": signal_bus.stats(),
            "signal_generator": signal_generator.stats(),
            "paper_executor": paper_executor.stats(),
            "fetched_at": _utc_iso(),
            "message": "PiyasaPilot gateway çalışıyor. Emir motoru pasif.",
        }

    # ── Backtest API (Sprint 3.2 + 3.3) ──────────────────────────────────
    @app.get("/api/backtest/strategies")
    def backtest_strategies() -> dict[str, Any]:
        """Mevcut strateji blueprint'lerini listele (frontend form üretir)."""
        return {"strategies": list_blueprints()}

    @app.post("/api/backtest/run")
    def backtest_run(req: BacktestRequest) -> dict[str, Any]:
        try:
            return run_backtest(
                cache=cache,
                symbol=req.symbol,
                interval=req.interval,
                strategy_id=req.strategy_id,
                params=req.params,
                capital=req.capital,
                lookback_bars=req.lookback_bars,
            )
        except UnknownStrategy as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except BacktestNotEnoughData as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except BacktestRunError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    # ── Paper Trading API (Sprint 4) ─────────────────────────────────────

    @app.get("/api/paper/wallets")
    def paper_wallets() -> dict[str, Any]:
        return {"wallets": paper_db.all_wallets()}

    @app.get("/api/paper/trades")
    def paper_trades(strategy_id: str = "", limit: int = 50) -> dict[str, Any]:
        sid = strategy_id or None
        return {"trades": paper_db.get_trades(sid, limit=limit)}

    @app.get("/api/paper/trades/export")
    def paper_trades_export(strategy_id: str = "") -> dict[str, Any]:
        sid = strategy_id or None
        return {"trades": paper_db.export_trades(sid)}

    @app.get("/api/paper/equity")
    def paper_equity(strategy_id: str, limit: int = 200) -> dict[str, Any]:
        return {"equity_curve": paper_db.get_equity_curve(strategy_id, limit=limit)}

    @app.post("/api/paper/reset/{strategy_id}")
    def paper_reset(strategy_id: str) -> dict[str, Any]:
        paper_db.reset_wallet(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id}

    @app.post("/api/paper/halt/{strategy_id}")
    def paper_halt(strategy_id: str) -> dict[str, Any]:
        paper_db.halt_strategy(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id, "halted": True}

    @app.post("/api/paper/resume/{strategy_id}")
    def paper_resume(strategy_id: str) -> dict[str, Any]:
        paper_db.resume_strategy(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id, "halted": False}

    # ── WebSocket fan-out: signals (Sprint 3.5) ──────────────────────────
    @app.websocket("/ws/signals")
    async def ws_signals(ws: WebSocket) -> None:
        """Canlı sinyal fan-out kanalı (DecisionEngine + StrategyRegistry).

        Query params:
          * ``symbols=BTCUSDT,ETHUSDT`` (boş = hepsi)
          * ``types=BUY,SELL`` (boş = hepsi)
        """
        symbols_q = ws.query_params.get("symbols", "")
        types_q = ws.query_params.get("types", "")
        symbols = [s for s in symbols_q.split(",") if s] or None
        types = [s for s in types_q.split(",") if s] or None

        await ws.accept()
        client_id, queue = await signal_bus.subscribe(symbols=symbols, types=types)
        await ws.send_json({"type": "ready", "client_id": client_id})

        recv_task = asyncio.create_task(_drain_client_messages(ws))
        try:
            while True:
                msg = await queue.get()
                await ws.send_json(msg)
                if recv_task.done():
                    break
        except WebSocketDisconnect:
            pass
        except Exception:  # noqa: BLE001
            pass
        finally:
            recv_task.cancel()
            await signal_bus.unsubscribe(client_id)
            try:
                await ws.close()
            except Exception:  # noqa: BLE001
                pass

    # ── WebSocket fan-out: quotes ────────────────────────────────────────
    @app.websocket("/ws/quotes")
    async def ws_quotes(ws: WebSocket) -> None:
        """Canlı bar fan-out kanalı.

        Protokol:
          * Server bağlantı kabul eder, ``{"type": "ready", "client_id": ...}``
            yollar.
          * Client opsiyonel olarak ``{"type": "subscribe", "symbols": [...],
            "intervals": [...]}`` yollayabilir; boş listeler "hepsi" demek.
            Şu an PR #5 için subscribe **bağlantı sırasında bir kez** uygulanır
            (query param + ilk mesaj). Sembol/interval değiştirmek için
            yeniden bağlan.
          * Server worker'lardan gelen her bar paketini ``{"type": "bars",
            "symbol", "interval", "bars": [...], "ts"}`` formatında yollar.
        """
        symbols_q = ws.query_params.get("symbols", "")
        intervals_q = ws.query_params.get("intervals", "")
        symbols = [s for s in symbols_q.split(",") if s] or None
        intervals = [s for s in intervals_q.split(",") if s] or None

        await ws.accept()
        client_id, queue = await quote_bus.subscribe(
            symbols=symbols, intervals=intervals
        )
        await ws.send_json({"type": "ready", "client_id": client_id})

        recv_task = asyncio.create_task(_drain_client_messages(ws))
        try:
            while True:
                msg = await queue.get()
                await ws.send_json(msg)
                if recv_task.done():
                    break
        except WebSocketDisconnect:
            pass
        except Exception:  # noqa: BLE001
            # Sessizce kapat; daemon süreçleri etkilemesin.
            pass
        finally:
            recv_task.cancel()
            await quote_bus.unsubscribe(client_id)
            try:
                await ws.close()
            except Exception:  # noqa: BLE001
                pass

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


class BacktestRequest(BaseModel):
    """``POST /api/backtest/run`` gövdesi."""

    symbol: str = Field(..., description="Sembol — frontend native (örn. BTCUSDT, THYAO.IS)")
    interval: str = Field("15m", description="Timeframe — 1m..1w")
    strategy_id: str = Field(..., description="Blueprint id (sma_crossover, rsi_reversion, ...)")
    params: dict[str, Any] = Field(default_factory=dict)
    capital: float = Field(100_000.0, gt=0, description="Başlangıç sermayesi (TL)")
    lookback_bars: int = Field(500, ge=50, le=5000, description="Cache'ten alınacak son bar sayısı")


# Uvicorn entry point: `uvicorn backend.api.main:app`
app = create_app()
