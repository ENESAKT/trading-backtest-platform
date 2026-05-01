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
import itertools
import logging
import os
import signal
from contextlib import asynccontextmanager
from dataclasses import asdict
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
    BacktestArchive,
    BacktestNotEnoughData,
    BacktestRunError,
    UnknownStrategy,
    equity_csv,
    list_blueprints,
    run_backtest,
    trades_csv,
)
from backend.config import getenv, llm_configured, mask_sensitive, telegram_configured
from backend.data.cache import OHLCVCache
from backend.data.spike_filter import filter_bars
from backend.data.symbols import (
    BIST_STOCKS,
    CRYPTO_WS_SYMBOLS,
    DEFAULT_INTERVAL,
    YAHOO_INDEX_FX_COMMODITY,
)
from backend.env_validator import validate_env
from backend.middleware.api_key_auth import APIKeyMiddleware
from backend.paper import PaperDB, PaperExecutor
from backend.signals import SignalGenerator
from backend.workers import WorkerSupervisor
from backend.workers.binance_ws import BinanceKlineWorker
from backend.workers.bist_poller import BistStockPoller
from backend.workers.yahoo_poller import YahooPoller
from quant_engine.data.live_feed import (
    LiveDataService,
    PaperTradingRecorder,
)
from quant_engine.strategy.persistence import StrategyRecord, StrategyStore
from quant_engine.workspace.json_store import WorkspaceJsonStore

ROOT = Path(__file__).resolve().parents[2]
_PAPER_DB_PATH = "data/cache/ohlcv.sqlite3"
_BACKTEST_ARCHIVE_PATH = "data/strategy_lab/backtest_reports.sqlite3"
_STRATEGY_STORE_PATH = "data/strategy_lab/strategies.sqlite3"
_logger = logging.getLogger(__name__)

# Cache miss eşiği: cache'teki en yeni bar'dan beri bu süreden uzun zaman
# geçmişse provider'a yeniden git. 15dk barlar için 90s mantıklı.
CACHE_FRESHNESS_SECONDS = 90


def _utc_iso() -> str:
    return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()


def _check_optional_env() -> None:
    """Başlangıçta opsiyonel çevre değişkenlerini kontrol et; eksikse uyar."""
    checks = [
        ("TELEGRAM_BOT_TOKEN", "Telegram bildirimleri devre dışı"),
        ("TELEGRAM_CHAT_ID", "Telegram bildirimleri devre dışı"),
        ("SMTP_HOST", "E-posta bildirimleri devre dışı"),
        ("BIST_HTTP_URL_TEMPLATE", "Lisanslı BIST feed bağlı değil — Yahoo fallback aktif"),
        ("VIOP_HTTP_URL_TEMPLATE", "Lisanslı VİOP feed bağlı değil"),
    ]
    for key, note in checks:
        if not getenv(key):
            _logger.warning("[env] Eksik opsiyonel değişken: %s — %s", key, note)


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


def _replace_placeholders(value: Any, replacements: dict[str, Any]) -> Any:
    """Optimizasyon grid değerlerini ``{fast}`` gibi formül placeholder'larına bas."""
    if isinstance(value, str):
        out = value
        for key, replacement in replacements.items():
            out = out.replace("{" + str(key) + "}", str(replacement))
        return out
    if isinstance(value, dict):
        return {k: _replace_placeholders(v, replacements) for k, v in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(v, replacements) for v in value]
    return value


def _extract_spec_indicators(strategy_spec: dict[str, Any] | None) -> list[str]:
    if not strategy_spec:
        return []
    known = [
        "SMA", "EMA", "RSI", "MACD_LINE", "MACD_SIGNAL", "MACD_HIST",
        "BB_UPPER", "BB_MID", "BB_LOWER", "ATR", "VWAP", "HIGHEST",
        "LOWEST", "CROSS_UP", "CROSS_DOWN", "BARS_SINCE",
    ]
    text = " ".join(
        str(v)
        for v in (strategy_spec.get("rules") or {}).values()
    ).upper()
    return [name for name in known if name in text]


def _strategy_record_payload(record: StrategyRecord) -> dict[str, Any]:
    payload = asdict(record)
    payload["strategy_spec"] = record.params.get("strategy_spec")
    payload["settings"] = record.params.get("settings", {})
    return payload


def _paper_activation_warnings(record: StrategyRecord) -> list[str]:
    spec = record.params.get("strategy_spec")
    if not isinstance(spec, dict):
        return ["Paper aktivasyonu hazır blueprint kayıtları için canlı spec sinyali üretmez."]
    rules = spec.get("rules") or {}
    warnings: list[str] = []
    if rules.get("short_entry") or rules.get("short_exit"):
        warnings.append(
            "Paper executor güvenlik nedeniyle short emri üretmez; short kuralları "
            "yalnızca backtest simülasyonunda kullanılır."
        )
    warnings.append("Paper mode simülasyondur; gerçek emir göndermez.")
    return warnings


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
    async def _on_bar(
        symbol: str,
        interval: str,
        bars: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if quote_bus is not None:
            await quote_bus.publish(symbol, interval, bars)
        if signal_generator is not None:
            await signal_generator.evaluate(symbol, interval, bars, metadata=metadata)
        if paper_executor is not None and bars:
            last_close = float(bars[-1].get("close", 0))
            if last_close > 0:
                paper_executor.update_prices({symbol.upper(): last_close})

    has_live_hooks = (
        quote_bus is not None or signal_generator is not None or paper_executor is not None
    )
    on_bar = _on_bar if has_live_hooks else None
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
    backtest_archive: BacktestArchive | None = None,
    strategy_store: StrategyStore | None = None,
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
    backtest_archive = backtest_archive or BacktestArchive(ROOT / _BACKTEST_ARCHIVE_PATH)
    strategy_store = strategy_store or StrategyStore(ROOT / _STRATEGY_STORE_PATH)

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
        validate_env()

        # SIGTERM graceful shutdown hook
        loop = asyncio.get_event_loop()
        try:
            loop.add_signal_handler(
                signal.SIGTERM,
                lambda: _logger.info("[shutdown] SIGTERM alındı"),
            )
        except (NotImplementedError, RuntimeError):
            pass  # Windows / test ortamı

        await supervisor.start_all()
        executor_task = asyncio.create_task(_paper_executor_loop())

        # Worker sağlık izleyici — çöküşlerde Telegram uyarısı
        from backend.workers.health_monitor import WorkerHealthMonitor
        health_monitor = WorkerHealthMonitor(supervisor)
        await health_monitor.start()

        try:
            yield
        finally:
            await health_monitor.stop()
            executor_task.cancel()
            await supervisor.stop_all()
            try:
                paper_db.checkpoint()
                _logger.info("[shutdown] SQLite WAL checkpoint tamamlandı.")
            except Exception as exc:
                _logger.warning("[shutdown] WAL checkpoint başarısız: %s", exc)

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
    app.state.backtest_archive = backtest_archive
    app.state.strategy_store = strategy_store

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*", "X-API-Key"],
    )
    app.add_middleware(APIKeyMiddleware)

    # ── Assistant durumu ──────────────────────────────────────────────────
    @app.get("/api/assistant/status")
    def assistant_status() -> dict[str, Any]:
        """Telegram listener ve proje asistanının anlık durumu."""
        try:
            from backend.notifier.telegram_listener import get_listener_status
            listener = get_listener_status()
        except Exception:
            listener = {}
        try:
            from backend.notifier.listener_status import read_listener_status
            shared_listener = read_listener_status()
            listener = {**listener, **shared_listener}
        except Exception:
            pass
        return {
            "listener_aktif": listener.get("aktif", False),
            "islenen_mesaj": listener.get("islenen_mesaj", 0),
            "son_mesaj_ozet": mask_sensitive(listener.get("son_mesaj")),
            "son_hata": mask_sensitive(listener.get("son_hata")),
            "komutlar": [
                "/yardim", "/durum", "/fiyat", "/sinyal", "/strateji",
                "/ozet", "/son", "/hata", "/kontrol", "/gorev", "/duzelt",
            ],
            "llm_aktif": llm_configured(),
        }

    # ── Notifier durumu ───────────────────────────────────────────────────
    @app.get("/api/notifier/status")
    def notifier_status() -> dict[str, Any]:
        """Telegram bildirim servisinin anlık durumu."""
        try:
            from backend.notifier.main import get_notifier_status
            durum = get_notifier_status()
        except Exception:
            durum = {}
        try:
            from backend.notifier.service_status import read_notifier_status
            shared_durum = read_notifier_status()
            durum = {**durum, **shared_durum}
        except Exception:
            pass
        try:
            from backend.notifier.email import email_status
            email = email_status()
        except Exception:
            email = {"smtp_yapilandirildi": False}
        return {
            "telegram_yapilandirildi": telegram_configured(),
            "yetkili_kullanici_yapilandirildi": bool(getenv("TELEGRAM_CHAT_ID")),
            "email": email,
            "aktif": durum.get("aktif", False),
            "son_bildirim": durum.get("son_bildirim"),
            "son_hata": mask_sensitive(durum.get("son_hata")),
            "toplam_bildirim": durum.get("toplam_bildirim", 0),
        }

    @app.get("/api/notifier/preferences")
    def notifier_preferences() -> dict[str, Any]:
        """Telegram bildirim filtrelerini döndür; gizli bilgi içermez."""
        from backend.notifier.preferences import public_preferences

        return public_preferences()

    @app.put("/api/notifier/preferences")
    async def update_notifier_preferences(request: Request) -> dict[str, Any]:
        """Telegram bildirim filtrelerini güncelle; token/chat_id kabul etmez."""
        from backend.notifier.preferences import public_preferences, write_preferences

        payload = await request.json()
        if not isinstance(payload, dict):
            payload = {}
        write_preferences(payload)
        return public_preferences()

    # ── Prometheus metrics ────────────────────────────────────────────────
    from fastapi.responses import PlainTextResponse

    @app.get("/metrics", response_class=PlainTextResponse)
    def prometheus_metrics() -> str:
        """Prometheus exposition format — stdlib, dış bağımlılık yok."""
        stats = cache.stats()
        worker_health = supervisor.health()
        lines = [
            "# HELP gateway_cache_bars_total Cached OHLCV bar sayısı",
            "# TYPE gateway_cache_bars_total gauge",
            f"gateway_cache_bars_total {stats.rows}",
            "# HELP gateway_cache_symbols_total Distinct sembol sayısı",
            "# TYPE gateway_cache_symbols_total gauge",
            f"gateway_cache_symbols_total {stats.distinct_symbols}",
            "# HELP gateway_worker_up Worker çalışıyor mu (1=evet 0=hayır)",
            "# TYPE gateway_worker_up gauge",
        ]
        for w in worker_health:
            name = w.get("name", "unknown").replace(" ", "_").replace("-", "_")
            up = 1 if w.get("running") else 0
            lines.append(f'gateway_worker_up{{worker="{name}"}} {up}')
        lines.append("# HELP gateway_signal_bus_subscribers Aktif WS sinyal subscriber sayısı")
        lines.append("# TYPE gateway_signal_bus_subscribers gauge")
        bus_stats = signal_bus.stats()
        lines.append(f"gateway_signal_bus_subscribers {bus_stats.get('subscribers', 0)}")
        lines.append("")
        return "\n".join(lines)

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

    @app.get("/api/data/providers/health")
    def data_providers_health() -> dict[str, Any]:
        """BIST/VİOP/kripto veri sağlayıcılarının güvenli sağlık özeti."""
        if hasattr(data_service, "provider_health"):
            return data_service.provider_health()
        return {
            "status": "ok",
            "fetched_at": _utc_iso(),
            "providers": [],
            "message": "Veri sağlayıcı sağlık bilgisi bu servis için raporlanmadı.",
        }

    # ── Backtest API (Sprint 3.2 + 3.3) ──────────────────────────────────
    @app.get("/api/backtest/strategies")
    def backtest_strategies() -> dict[str, Any]:
        """Mevcut strateji blueprint'lerini listele (frontend form üretir)."""
        return {"strategies": list_blueprints()}

    @app.post("/api/backtest/run")
    def backtest_run(req: BacktestRequest) -> dict[str, Any]:
        try:
            result = run_backtest(
                cache=cache,
                data_service=data_service,
                symbol=req.symbol,
                interval=req.interval,
                strategy_id=req.strategy_id,
                params=req.params,
                capital=req.capital,
                lookback_bars=req.lookback_bars,
                start_date=req.start_date,
                end_date=req.end_date,
                commission_rate=req.commission_rate,
                slippage_bps=req.slippage_bps,
                max_position_pct=req.max_position_pct,
                allow_short=req.allow_short,
                source_mode=req.source_mode,
                strategy_spec=req.strategy_spec,
                csv_text=req.csv_text,
                csv_bars=req.csv_bars,
            )
            run_id = backtest_archive.save(result)
            result["run_id"] = run_id
            return result
        except UnknownStrategy as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        except BacktestNotEnoughData as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        except BacktestRunError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.get("/api/backtest/reports")
    def backtest_reports(limit: int = 50) -> dict[str, Any]:
        return {"reports": backtest_archive.list(limit=limit)}

    @app.get("/api/backtest/reports/{run_id}")
    def backtest_report(run_id: str) -> dict[str, Any]:
        report = backtest_archive.get(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")
        return report

    @app.get("/api/backtest/reports/{run_id}/export")
    def backtest_report_export(run_id: str, format: str = "json") -> Any:
        report = backtest_archive.get(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")
        if format == "json":
            return report
        if format == "trades_csv":
            return PlainTextResponse(trades_csv(report), media_type="text/csv")
        if format == "equity_csv":
            return PlainTextResponse(equity_csv(report), media_type="text/csv")
        raise HTTPException(
            status_code=400,
            detail="format json, trades_csv veya equity_csv olmalı.",
        )

    @app.post("/api/backtest/optimize")
    def backtest_optimize(req: OptimizeRequest) -> dict[str, Any]:
        grid = req.param_grid or {}
        if not grid:
            raise HTTPException(status_code=400, detail="param_grid boş olamaz.")
        keys = list(grid.keys())
        values = [list(v) for v in grid.values()]
        combos = [dict(zip(keys, combo, strict=False)) for combo in itertools.product(*values)]
        if len(combos) > req.max_combinations:
            raise HTTPException(
                status_code=400,
                detail=f"Kombinasyon sayısı {req.max_combinations} üst sınırını aşıyor.",
            )

        rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for combo in combos:
            try:
                params = dict(req.params)
                params.update(combo)
                spec = (
                    _replace_placeholders(req.strategy_spec, combo)
                    if req.strategy_spec
                    else None
                )
                result = run_backtest(
                    cache=cache,
                    data_service=data_service,
                    symbol=req.symbol,
                    interval=req.interval,
                    strategy_id=req.strategy_id,
                    params=params,
                    capital=req.capital,
                    lookback_bars=req.lookback_bars,
                    start_date=req.start_date,
                    end_date=req.end_date,
                    commission_rate=req.commission_rate,
                    slippage_bps=req.slippage_bps,
                    max_position_pct=req.max_position_pct,
                    allow_short=req.allow_short,
                    source_mode=req.source_mode,
                    strategy_spec=spec,
                )
                metrics = result["metrics"]
                score = (
                    float(metrics["total_return_pct"])
                    - float(metrics["max_drawdown_pct"]) * 0.7
                    + min(int(metrics["total_trades"]), 20) * 0.1
                )
                warnings = list(result.get("warnings") or [])
                if int(metrics["total_trades"]) < 2:
                    warnings.append("Az işlem üretti; sonuç istatistiksel olarak zayıf olabilir.")
                    score -= 10
                rows.append({
                    "params": combo,
                    "metrics": metrics,
                    "score": score,
                    "warnings": warnings,
                })
            except Exception as exc:  # noqa: BLE001
                errors.append({"params": combo, "error": str(exc)})

        rows.sort(key=lambda row: float(row["score"]), reverse=True)
        return {
            "symbol": req.symbol.upper(),
            "interval": req.interval,
            "results": rows,
            "errors": errors,
            "best": rows[0] if rows else None,
        }

    @app.post("/api/backtest/scan")
    def backtest_scan(req: ScanRequest) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        errors: list[dict[str, Any]] = []
        for symbol in req.symbols[: req.limit]:
            try:
                result = run_backtest(
                    cache=cache,
                    data_service=data_service,
                    symbol=symbol,
                    interval=req.interval,
                    strategy_id=req.strategy_id,
                    params=req.params,
                    capital=req.capital,
                    lookback_bars=req.lookback_bars,
                    start_date=req.start_date,
                    end_date=req.end_date,
                    commission_rate=req.commission_rate,
                    slippage_bps=req.slippage_bps,
                    max_position_pct=req.max_position_pct,
                    allow_short=req.allow_short,
                    source_mode=req.source_mode,
                    strategy_spec=req.strategy_spec,
                )
                signals = result.get("signals") or []
                last_signal = signals[-1] if signals else None
                metrics = result["metrics"]
                rows.append({
                    "symbol": result["symbol"],
                    "last_price": result.get("last_price"),
                    "last_signal": last_signal,
                    "total_return_pct": metrics["total_return_pct"],
                    "max_drawdown_pct": metrics["max_drawdown_pct"],
                    "total_trades": metrics["total_trades"],
                    "score": (
                        float(metrics["total_return_pct"])
                        - float(metrics["max_drawdown_pct"]) * 0.7
                    ),
                })
            except Exception as exc:  # noqa: BLE001
                errors.append({"symbol": symbol, "error": str(exc)})
        rows.sort(key=lambda row: float(row["score"]), reverse=True)
        return {"results": rows, "errors": errors}

    @app.get("/api/strategy-lab/strategies")
    def strategy_lab_list() -> dict[str, Any]:
        records = strategy_store.list_strategies()
        return {"strategies": [_strategy_record_payload(r) for r in records]}

    @app.get("/api/strategy-lab/strategies/{record_id}")
    def strategy_lab_get(record_id: int) -> dict[str, Any]:
        record = strategy_store.get_strategy(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Strateji kaydı bulunamadı.")
        return _strategy_record_payload(record)

    @app.post("/api/strategy-lab/strategies")
    def strategy_lab_save(req: StrategySaveRequest) -> dict[str, Any]:
        params = dict(req.params)
        if req.strategy_spec is not None:
            params["strategy_spec"] = req.strategy_spec
        params["settings"] = req.settings
        record = strategy_store.save_strategy(
            name=req.name,
            base_strategy=req.strategy_id or "strategy_spec",
            params=params,
            indicators=_extract_spec_indicators(req.strategy_spec),
            symbol=req.symbol,
            market=req.market,
            timeframe=req.interval,
            notes=req.notes,
        )
        return _strategy_record_payload(record)

    @app.post("/api/strategy-lab/strategies/{record_id}/paper/activate")
    def strategy_lab_activate_paper(record_id: int, req: PaperActivateRequest) -> dict[str, Any]:
        record = strategy_store.get_strategy(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Strateji kaydı bulunamadı.")
        warnings = _paper_activation_warnings(record)
        activation = strategy_store.activate_paper(
            strategy_record_id=record_id,
            report_id=req.report_id,
            symbol=req.symbol or record.symbol,
            interval=req.interval or record.timeframe,
            warnings=warnings,
        )
        return {"activation": asdict(activation), "warnings": warnings}

    @app.post("/api/strategy-lab/paper/{activation_id}/deactivate")
    def strategy_lab_deactivate_paper(activation_id: int) -> dict[str, Any]:
        ok = strategy_store.deactivate_paper(activation_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Paper aktivasyonu bulunamadı.")
        return {"status": "ok", "activation_id": activation_id, "active": False}

    @app.get("/api/strategy-lab/paper")
    def strategy_lab_paper_activations(active_only: bool = False) -> dict[str, Any]:
        return {
            "activations": [
                asdict(a) for a in strategy_store.list_paper_activations(active_only=active_only)
            ]
        }

    @app.post("/api/backtest/reports/{run_id}/paper/activate")
    def backtest_report_activate_paper(run_id: str) -> dict[str, Any]:
        report = backtest_archive.get(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")
        spec = report.get("strategy_spec")
        if not isinstance(spec, dict):
            raise HTTPException(
                status_code=400,
                detail=(
                    "Hazır blueprint raporu paper'a alınmadan önce "
                    "strategy_spec olarak kaydedilmeli."
                ),
            )
        record = strategy_store.save_strategy(
            name=str(spec.get("name") or report.get("strategy_name") or "Paper strateji"),
            base_strategy="strategy_spec",
            params={
                "strategy_spec": spec,
                "settings": {
                    "capital": report.get("capital"),
                    "source_mode": report.get("source_mode"),
                    "assumptions": report.get("assumptions"),
                },
            },
            indicators=_extract_spec_indicators(spec),
            symbol=str(report.get("symbol", "")),
            market="",
            timeframe=str(report.get("interval", "")),
            notes=f"Backtest raporundan paper'a alındı: {run_id}",
        )
        warnings = _paper_activation_warnings(record)
        activation = strategy_store.activate_paper(
            strategy_record_id=record.id,
            report_id=run_id,
            symbol=record.symbol,
            interval=record.timeframe,
            warnings=warnings,
        )
        return {
            "strategy": _strategy_record_payload(record),
            "activation": asdict(activation),
            "warnings": warnings,
        }

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
        except asyncio.CancelledError:
            pass
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
        except asyncio.CancelledError:
            pass
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
                    "is_real": False,
                    "status": "stale",
                    "provider_error": provider_payload.get("metadata", {}).get("error", ""),
                    "fetched_at": _utc_iso(),
                },
            })

        # Veri yok / lisanslı kaynak yok durumları gateway hatası değildir.
        # Payload status alanı üst katmana nedeni taşır; HTTP 200 canlılık
        # ve stres testlerinde altyapı hatasıyla veri yokluğunu ayırır.
        if provider_payload.get("status") in {"no_data", "not_configured"}:
            return JSONResponse(provider_payload)

        # Hem provider hem cache boş ve gerçek provider hatası var.
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
    strategy_id: str = Field(
        "",
        description="Blueprint id veya strategy_spec için boş/strategy_spec",
    )
    params: dict[str, Any] = Field(default_factory=dict)
    capital: float = Field(100_000.0, gt=0, description="Başlangıç sermayesi (TL)")
    lookback_bars: int = Field(500, ge=50, le=5000, description="Cache'ten alınacak son bar sayısı")
    start_date: str | None = Field(None, description="Backtest başlangıç tarihi")
    end_date: str | None = Field(None, description="Backtest bitiş tarihi")
    commission_rate: float = Field(0.001, ge=0, le=0.10, description="Komisyon oranı")
    slippage_bps: int = Field(5, ge=0, le=500, description="Slippage baz puan")
    max_position_pct: float = Field(0.20, gt=0, le=1.0, description="Maksimum pozisyon oranı")
    allow_short: bool = Field(False, description="Short simülasyonuna izin ver")
    source_mode: str = Field(
        "cache_only",
        description="cache_only, cache_then_provider, csv_import",
    )
    strategy_spec: dict[str, Any] | None = Field(None, description="Güvenli DSL strategy_spec")
    csv_text: str | None = Field(None, description="CSV import içeriği")
    csv_bars: list[dict[str, Any]] | None = Field(
        None,
        description="CSV yerine doğrudan OHLCV bar listesi",
    )


class StrategySaveRequest(BaseModel):
    name: str = Field(..., min_length=1)
    symbol: str = Field(..., min_length=1)
    interval: str = Field("1d")
    market: str = Field("")
    strategy_id: str = Field("strategy_spec")
    strategy_spec: dict[str, Any] | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    settings: dict[str, Any] = Field(default_factory=dict)
    source_mode: str = Field("cache_only")
    notes: str = Field("")


class PaperActivateRequest(BaseModel):
    report_id: str = Field("")
    symbol: str = Field("")
    interval: str = Field("")


class OptimizeRequest(BaseModel):
    symbol: str
    interval: str = "1d"
    strategy_id: str = "strategy_spec"
    params: dict[str, Any] = Field(default_factory=dict)
    strategy_spec: dict[str, Any] | None = None
    param_grid: dict[str, list[Any]] = Field(default_factory=dict)
    max_combinations: int = Field(80, ge=1, le=200)
    capital: float = Field(100_000.0, gt=0)
    lookback_bars: int = Field(500, ge=50, le=5000)
    start_date: str | None = None
    end_date: str | None = None
    commission_rate: float = Field(0.001, ge=0, le=0.10)
    slippage_bps: int = Field(5, ge=0, le=500)
    max_position_pct: float = Field(0.20, gt=0, le=1.0)
    allow_short: bool = False
    source_mode: str = "cache_only"


class ScanRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    interval: str = "1d"
    strategy_id: str = "strategy_spec"
    params: dict[str, Any] = Field(default_factory=dict)
    strategy_spec: dict[str, Any] | None = None
    limit: int = Field(30, ge=1, le=150)
    capital: float = Field(100_000.0, gt=0)
    lookback_bars: int = Field(500, ge=50, le=5000)
    start_date: str | None = None
    end_date: str | None = None
    commission_rate: float = Field(0.001, ge=0, le=0.10)
    slippage_bps: int = Field(5, ge=0, le=500)
    max_position_pct: float = Field(0.20, gt=0, le=1.0)
    allow_short: bool = False
    source_mode: str = "cache_only"


# Uvicorn entry point: `uvicorn backend.api.main:app`
app = create_app()
