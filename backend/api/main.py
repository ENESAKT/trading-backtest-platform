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
* **CORS** env tabanlı; lokal geliştirmede Vite origin'i varsayılan.
* Eski v1 endpoint'leri (``/api/market/defaults``, ``/api/market/chart``,
  ``/api/workspace``, ``POST /api/paper/signal``) aynen korunuyor.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import itertools
import logging
import math
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

try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from slowapi.util import get_remote_address
except ImportError:  # pragma: no cover - dependency bootstrap fallback
    Limiter = None  # type: ignore[assignment]
    RateLimitExceeded = None  # type: ignore[assignment]
    _rate_limit_exceeded_handler = None  # type: ignore[assignment]
    get_remote_address = None  # type: ignore[assignment]

from backend.api.quote_bus import QuoteBus
from backend.signals.signal_bus import SignalBus
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
from backend.data.historical_store import HistoricalStore
from backend.data.repositories.market_data_facade import MarketDataFacade
from backend.data.spike_filter import filter_bars
from backend.data.symbols import (
    BIST_STOCKS,
    CRYPTO_WS_SYMBOLS,
    DEFAULT_INTERVAL,
    YAHOO_INDEX_FX_COMMODITY,
)
from backend.env_validator import validate_env
from backend.mali_analiz.cache import FinancialAnalysisCache
from backend.mali_analiz.harvester import harvest_if_stale, harvest_all, recompute_ratios_from_stored
from backend.mali_analiz.kap_provider import KapFinancialAnalysisProvider
from backend.mali_analiz.repository import FinancialStatementRepository
from backend.mali_analiz.service import FinancialAnalysisService
from backend.mali_analiz.symbols import BIST_30_SYMBOLS, BIST_100_SYMBOLS, SYMBOL_METADATA, normalize_symbol
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
from quant_engine.research.optimization_v2 import find_stable_region, generate_heatmap_data
from quant_engine.strategy.pack import export_strategy_pack, import_strategy_pack
from quant_engine.strategy.persistence import StrategyRecord, StrategyStore
from quant_engine.strategy.catalog import list_strategy_presets
from quant_engine.workspace.json_store import WorkspaceJsonStore

ROOT = Path(__file__).resolve().parents[2]
_PAPER_DB_PATH = "data/cache/ohlcv.sqlite3"
_BACKTEST_ARCHIVE_PATH = "data/strategy_lab/backtest_reports.sqlite3"
_STRATEGY_STORE_PATH = "data/strategy_lab/strategies.sqlite3"
_NEWS_DB_PATH = "data/cache/news.sqlite3"
_logger = logging.getLogger(__name__)

# Cache miss eşiği: cache'teki en yeni bar'dan beri bu süreden uzun zaman
# geçmişse provider'a yeniden git. 15dk barlar için 90s mantıklı.
CACHE_FRESHNESS_SECONDS = 90


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:5173"]


def _require_ws_token(ws: WebSocket) -> bool:
    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        return True
    token = ws.query_params.get("token", "")
    return token == api_key


def _rate_limiter() -> Any:
    if Limiter is None or get_remote_address is None:
        _logger.warning("[security] slowapi kurulu değil; rate limiting devre dışı.")
        return None
    return Limiter(key_func=get_remote_address)


def _limit(limiter: Any, rule: str) -> Any:
    if limiter is None:
        return lambda func: func
    return limiter.limit(rule)


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


def _sanitize_floats(obj: Any) -> Any:
    """Recursively replace NaN/Inf with None so JSON serialization never fails."""
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return obj
    if isinstance(obj, dict):
        return {k: _sanitize_floats(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize_floats(v) for v in obj]
    return obj


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
    mali_analiz_service: FinancialAnalysisService | None = None,
    historical_store: HistoricalStore | None = None,
    market_data_facade: MarketDataFacade | None = None,
) -> FastAPI:
    """FastAPI app factory.

    Bağımlılıklar dışarıdan enjekte edilebilir → testte mock'lu örnek
    kurmayı kolaylaştırır. ``supervisor=None`` + ``PIYASAPILOT_DISABLE_WORKERS``
    setli değilse varsayılan worker seti kurulur. ``quote_bus`` verilmezse
    yeni bir tane yaratılır ve worker'lar buna ``on_bar`` ile bağlanır.
    """
    injected_data_service = data_service is not None
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
    historical_store = historical_store or HistoricalStore()
    if (
        market_data_facade is None
        and not injected_data_service
        and os.environ.get("PIYASAPILOT_DISABLE_DB_FACADE") != "1"
    ):
        market_data_facade = MarketDataFacade.from_env()

    financial_repository = None  # her yolda tanımlı olsun
    if mali_analiz_service is None:
        ma_cache = FinancialAnalysisCache(ROOT / "data" / "cache" / "mali_analiz.sqlite3")
        if os.environ.get("PIYASAPILOT_DISABLE_FINANCIAL_REPOSITORY") != "1":
            financial_repository = FinancialStatementRepository()
            try:
                financial_repository.ensure_tables()
            except Exception:
                pass
        mali_analiz_service = FinancialAnalysisService(
            cache=ma_cache,
            provider=KapFinancialAnalysisProvider(),
            repository=financial_repository,
        )

    # Startup finansal veri kontrolü — bayat semboller arka planda güncellenir
    _financial_repository_ref = financial_repository

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

        # Finansal veri startup kontrolü — bayat semboller arka planda güncellenir
        if _financial_repository_ref is not None and os.environ.get("PIYASAPILOT_DISABLE_FINANCIAL_HARVEST") != "1":
            import asyncio as _aio
            def _bg_harvest():
                try:
                    harvest_if_stale(_financial_repository_ref, max_workers=1)
                except Exception as _e:
                    _logger.warning("[mali-analiz] Startup harvest hatası: %s", _e)
            _aio.get_event_loop().run_in_executor(None, _bg_harvest)

        # Worker sağlık izleyici — çöküşlerde Telegram uyarısı
        from backend.workers.health_monitor import WorkerHealthMonitor
        health_monitor = WorkerHealthMonitor(supervisor)
        await health_monitor.start()

        # Haber arka plan worker — her 30 dakikada BIST30 haberlerini günceller
        async def _news_background_worker():
            from backend.news.news_store import NewsStore
            from backend.news.news_fetcher import fetch_news_for_symbol
            store = NewsStore(_NEWS_DB_PATH)
            while True:
                try:
                    for sym in BIST_30_SYMBOLS[:15]:  # İlk 15 sembol — rate-limit dostu
                        try:
                            items = fetch_news_for_symbol(sym, limit=10)
                            if items:
                                store.upsert(items)
                        except Exception as _e:
                            _logger.debug("[news-worker] %s hatası: %s", sym, _e)
                        await asyncio.sleep(2)  # Semboller arası bekleme
                except asyncio.CancelledError:
                    break
                except Exception as _e:
                    _logger.warning("[news-worker] Döngü hatası: %s", _e)
                await asyncio.sleep(30 * 60)  # 30 dakika bekle

        news_worker_task = asyncio.create_task(_news_background_worker())

        try:
            yield
        finally:
            await health_monitor.stop()
            news_worker_task.cancel()
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
    app.state.market_data_facade = market_data_facade

    limiter = _rate_limiter()
    if limiter is not None:
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins(),
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
        return {
            "strategies": list_blueprints(),
            "presets": list_strategy_presets(include_spec=True)
        }

    @app.post("/api/backtest/run")
    @_limit(limiter, "30/minute")
    def backtest_run(request: Request, req: BacktestRequest) -> dict[str, Any]:
        del request
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
                slippage_model=req.slippage_model,
                slippage_tick=req.slippage_tick,
                volume_limit_pct=req.volume_limit_pct,
                volume_window=req.volume_window,
                max_position_pct=req.max_position_pct,
                allow_short=req.allow_short,
                source_mode=req.source_mode,
                strategy_spec=req.strategy_spec,
                csv_text=req.csv_text,
                csv_bars=req.csv_bars,
                historical_store=historical_store,
            )
            result = _sanitize_floats(result)
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
                    slippage_model=req.slippage_model,
                    slippage_tick=req.slippage_tick,
                    volume_limit_pct=req.volume_limit_pct,
                    volume_window=req.volume_window,
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
        stability_report: dict[str, Any] = {}
        heatmap: dict[str, Any] = {"x_axis": [], "y_axis": [], "z_matrix": []}
        if len(keys) >= 2 and rows:
            p1_key, p2_key = keys[0], keys[1]
            grid_results = [
                {
                    "params": row["params"],
                    "score": float(row["score"]),
                    "total_return_pct": float(row["metrics"]["total_return_pct"]),
                }
                for row in rows
            ]
            heatmap = generate_heatmap_data(grid_results, p1_key, p2_key, metric="score")
            stable = find_stable_region(grid_results, p1_key, p2_key, metric="score", threshold=0.75)
            if stable:
                stability_report = {
                    "param_keys": [p1_key, p2_key],
                    "best_params": {
                        p1_key: stable.get("best_p1"),
                        p2_key: stable.get("best_p2"),
                    },
                    "stable_score": stable.get("stable_score", 0.0),
                    "metric_value": stable.get("metric_value", 0.0),
                    "global_max": stable.get("global_max", 0.0),
                    "heatmap": heatmap,
                    "warnings": [],
                }
            else:
                stability_report = {
                    "param_keys": [p1_key, p2_key],
                    "best_params": {},
                    "stable_score": 0.0,
                    "metric_value": 0.0,
                    "global_max": 0.0,
                    "heatmap": heatmap,
                    "warnings": ["Stabil bölge hesaplanamadı."],
                }
        return {
            "symbol": req.symbol.upper(),
            "interval": req.interval,
            "results": rows,
            "errors": errors,
            "best": rows[0] if rows else None,
            "stability_report": stability_report,
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
        return {"scanner_version": "v3", "results": rows, "errors": errors}

    # ── Walk-Forward Analizi ──────────────────────────────────────────────
    @app.post("/api/backtest/walk-forward")
    def backtest_walk_forward(req: WalkForwardRequest) -> dict[str, Any]:
        """Kayan pencere walk-forward analizi.

        Her pencerede en iyi parametre kombinasyonu in-sample'da seçilir,
        ardından out-of-sample döneminde değerlendirilir.
        """
        from quant_engine.research.walk_forward import generate_windows

        canonical = req.symbol.strip().upper()
        total_bars_needed = req.in_sample_bars + req.out_of_sample_bars
        bars = cache.get_window(canonical, req.interval, req.lookback_bars)
        if not bars or len(bars) < total_bars_needed:
            have = len(bars) if bars else 0
            raise HTTPException(
                status_code=409,
                detail=f"Walk-forward için yeterli bar yok (gerekli: {total_bars_needed}, mevcut: {have}).",
            )

        # Param grid'den kombinasyon listesi oluştur
        grid = req.param_grid or {}
        if grid:
            keys = list(grid.keys())
            combos = [
                dict(zip(keys, combo, strict=False))
                for combo in itertools.product(*[grid[k] for k in keys])
            ]
        else:
            combos = [dict(req.params)]

        if not combos:
            raise HTTPException(status_code=400, detail="param_grid veya params boş olamaz.")

        windows = generate_windows(
            len(bars),
            in_sample_bars=req.in_sample_bars,
            out_of_sample_bars=req.out_of_sample_bars,
            step_bars=req.step_bars,
        )
        if not windows:
            raise HTTPException(
                status_code=409,
                detail="Verilen bar sayısı ile pencere üretilemedi. in_sample_bars + out_of_sample_bars toplamını küçültün.",
            )

        def _run_slice(params: dict[str, Any], bar_slice: list[dict[str, Any]]) -> dict[str, Any]:
            try:
                return run_backtest(
                    cache=cache,
                    data_service=data_service,
                    symbol=canonical,
                    interval=req.interval,
                    strategy_id=req.strategy_id,
                    params=params,
                    capital=req.capital,
                    commission_rate=req.commission_rate,
                    slippage_bps=req.slippage_bps,
                    allow_short=req.allow_short,
                    source_mode="csv_import",
                    strategy_spec=req.strategy_spec,
                    csv_bars=bar_slice,
                )
            except Exception:  # noqa: BLE001
                return {}

        def _score(result: dict[str, Any]) -> float:
            m = result.get("metrics") or {}
            if not m:
                return -999.0
            ret = float(m.get("total_return_pct", 0))
            dd = float(m.get("max_drawdown_pct", 0))
            trades = int(m.get("total_trades", 0))
            s = ret - dd * 0.7 + min(trades, 20) * 0.1
            if trades < 2:
                s -= 10
            return s

        fold_results: list[dict[str, Any]] = []
        all_oos_returns: list[float] = []
        all_efficiencies: list[float] = []

        for window in windows:
            in_bars = bars[window.in_sample_start : window.in_sample_end]
            oos_bars = bars[window.out_of_sample_start : window.out_of_sample_end]

            best_score = -float("inf")
            best_params: dict[str, Any] = combos[0]
            for combo in combos:
                res = _run_slice(combo, in_bars)
                s = _score(res)
                if s > best_score:
                    best_score = s
                    best_params = combo

            oos_result = _run_slice(best_params, oos_bars)
            oos_metrics = oos_result.get("metrics") or {}
            oos_return = float(oos_metrics.get("total_return_pct", 0))
            efficiency = oos_return / abs(best_score) if best_score not in (0, -999.0) else 0.0

            all_oos_returns.append(oos_return)
            all_efficiencies.append(efficiency)

            # Tarih bilgisi (bar zaman damgaları)
            in_start_ts = in_bars[0]["time"] if in_bars else 0
            in_end_ts = in_bars[-1]["time"] if in_bars else 0
            oos_start_ts = oos_bars[0]["time"] if oos_bars else 0
            oos_end_ts = oos_bars[-1]["time"] if oos_bars else 0

            fold_results.append({
                "fold": window.index,
                "in_sample": {
                    "start_ts": in_start_ts,
                    "end_ts": in_end_ts,
                    "bars": len(in_bars),
                    "score": best_score,
                },
                "out_of_sample": {
                    "start_ts": oos_start_ts,
                    "end_ts": oos_end_ts,
                    "bars": len(oos_bars),
                    "return_pct": oos_return,
                    "total_trades": int(oos_metrics.get("total_trades", 0)),
                    "max_drawdown_pct": float(oos_metrics.get("max_drawdown_pct", 0)),
                },
                "best_params": best_params,
                "walk_forward_efficiency": efficiency,
            })

        # Bileşik OOS getiri
        compound = 1.0
        for r in all_oos_returns:
            compound *= 1 + r / 100.0
        total_oos_return = (compound - 1) * 100.0
        avg_efficiency = sum(all_efficiencies) / len(all_efficiencies) if all_efficiencies else 0.0
        avg_oos = sum(all_oos_returns) / len(all_oos_returns) if all_oos_returns else 0.0

        return _sanitize_floats({
            "symbol": canonical,
            "interval": req.interval,
            "n_folds": len(windows),
            "in_sample_bars": req.in_sample_bars,
            "out_of_sample_bars": req.out_of_sample_bars,
            "step_bars": req.step_bars,
            "folds": fold_results,
            "aggregate": {
                "avg_oos_return_pct": avg_oos,
                "total_oos_return_pct": total_oos_return,
                "avg_walk_forward_efficiency": avg_efficiency,
                "passed": avg_oos > 0,
                "n_folds": len(windows),
            },
        })

    # ── Monte Carlo Simülasyonu ───────────────────────────────────────────
    @app.post("/api/backtest/monte-carlo")
    def backtest_monte_carlo(req: MonteCarloRequest) -> dict[str, Any]:
        """Arşivlenmiş backtest PnL serisinden Monte Carlo simülasyonu.

        ``run_id`` ile bir backtest raporu belirtilir; trade PnL'leri
        bootstrap/permütasyon yöntemiyle yeniden örneklenerek N simülasyon
        koşturulur.
        """
        from quant_engine.research.monte_carlo import run_monte_carlo

        report = backtest_archive.get(req.run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")

        trades = report.get("trades") or []
        pnl_series = [
            float(t.get("net_pnl", 0))
            for t in trades
            if t.get("net_pnl") is not None
        ]

        if not pnl_series:
            raise HTTPException(
                status_code=409,
                detail="Backtest raporunda işlem PnL verisi bulunamadı. Önce backtest çalıştırın.",
            )

        capital = float(report.get("capital", 100_000.0))
        mc = run_monte_carlo(
            pnl_series=pnl_series,
            initial_capital=capital,
            n_simulations=min(req.n_simulations, 2000),
            method=req.method,
            seed=req.seed,
        )

        # 50 örnek path döndür (tüm simülasyonlar çok büyük olur)
        sample_count = min(50, len(mc.simulations))
        sample_sims = mc.simulations[:sample_count]

        # Percentil bantları için tüm son değerleri hesapla (frontend için)
        import numpy as np
        final_equities = [path[-1] for path in mc.simulations if path]
        pct_values: dict[str, float] = {}
        if final_equities:
            arr = np.array(final_equities)
            pct_values = {
                "p5":  float(np.percentile(arr, 5)),
                "p25": float(np.percentile(arr, 25)),
                "p50": float(np.percentile(arr, 50)),
                "p75": float(np.percentile(arr, 75)),
                "p95": float(np.percentile(arr, 95)),
            }

        return _sanitize_floats({
            "run_id": req.run_id,
            "symbol": str(report.get("symbol", "")),
            "interval": str(report.get("interval", "")),
            "n_simulations": req.n_simulations,
            "method": req.method,
            "n_trades": len(pnl_series),
            "initial_capital": capital,
            "results": {
                "median_final_equity": mc.median_final_equity,
                "p05_final_equity": mc.p05_final_equity,
                "p95_final_equity": mc.p95_final_equity,
                "probability_of_loss": mc.probability_of_loss,
                "median_max_drawdown_pct": mc.median_max_drawdown_pct,
                "p95_max_drawdown_pct": mc.p95_max_drawdown_pct,
                "percentiles": pct_values,
            },
            "sample_simulations": sample_sims,
            "warnings": mc.warnings,
        })

    # ── Backtest Karşılaştırma ────────────────────────────────────────────────
    @app.post("/api/backtest/compare")
    def backtest_compare(body: dict[str, Any]) -> dict[str, Any]:
        """İki backtest raporunu yan yana karşılaştır.

        Body: {run_id_a: str, run_id_b: str}
        """
        run_id_a = str(body.get("run_id_a", ""))
        run_id_b = str(body.get("run_id_b", ""))
        if not run_id_a or not run_id_b:
            raise HTTPException(status_code=400, detail="run_id_a ve run_id_b zorunlu.")

        report_a = backtest_archive.get(run_id_a)
        report_b = backtest_archive.get(run_id_b)
        if report_a is None:
            raise HTTPException(status_code=404, detail=f"Rapor bulunamadı: {run_id_a}")
        if report_b is None:
            raise HTTPException(status_code=404, detail=f"Rapor bulunamadı: {run_id_b}")

        COMPARE_KEYS = [
            "total_return_pct", "annualized_return_pct", "max_drawdown_pct",
            "sharpe_ratio", "win_rate", "profit_factor", "total_trades",
            "final_equity", "total_commission", "total_slippage",
        ]

        def _metrics(r: dict[str, Any]) -> dict[str, Any]:
            return r.get("metrics") or {}

        ma = _metrics(report_a)
        mb = _metrics(report_b)

        diffs: list[dict[str, Any]] = []
        for key in COMPARE_KEYS:
            va = ma.get(key)
            vb = mb.get(key)
            if va is None and vb is None:
                continue
            winner: str | None = None
            if va is not None and vb is not None:
                better_higher = key not in ("max_drawdown_pct", "total_commission", "total_slippage")
                winner = "a" if (float(va) > float(vb)) == better_higher else "b"
            diffs.append({"key": key, "a": va, "b": vb, "winner": winner})

        def _summary(r: dict[str, Any]) -> dict[str, Any]:
            return {
                "run_id": r.get("run_id", ""),
                "symbol": r.get("symbol", ""),
                "interval": r.get("interval", ""),
                "strategy_name": r.get("strategy_name", ""),
                "created_at": r.get("created_at", ""),
            }

        return {
            "a": _summary(report_a),
            "b": _summary(report_b),
            "diffs": diffs,
            "winner_counts": {
                "a": sum(1 for d in diffs if d["winner"] == "a"),
                "b": sum(1 for d in diffs if d["winner"] == "b"),
            },
        }

    # ── Teknik Analiz Özet ────────────────────────────────────────────────────
    @app.get("/api/technical/{symbol}")
    def get_technical_analysis(symbol: str, interval: str = "1d") -> dict[str, Any]:
        """Son N bar üzerinden teknik göstergeler ve sinyal özetleri.

        Yanıt: {symbol, interval, indicators: {...}, signals: {...}}
        """
        import pandas as pd
        from quant_engine.strategy.indicators import (
            rsi as calc_rsi, ema, bollinger_bands, atr as calc_atr, macd,
        )

        sym_upper = symbol.upper()
        bars = cache.get_window(sym_upper, interval, limit=200)
        if not bars:
            raise HTTPException(status_code=404, detail=f"{sym_upper}/{interval} için veri bulunamadı.")

        closes = pd.Series([float(b["close"]) for b in bars])
        highs  = pd.Series([float(b["high"])  for b in bars])
        lows   = pd.Series([float(b["low"])   for b in bars])

        def _last(s: pd.Series) -> float | None:
            if len(s) == 0:
                return None
            v = s.iloc[-1]
            return None if (v != v) else round(float(v), 4)

        rsi14  = calc_rsi(closes, 14)
        ema9   = ema(closes, 9)
        ema21  = ema(closes, 21)
        ema50  = ema(closes, 50)
        ema200 = ema(closes, 200)
        bb_upper, _bb_mid, bb_lower = bollinger_bands(closes, 20, 2.0)
        atr14  = calc_atr(highs, lows, closes, 14)
        macd_line, macd_sig, macd_hist = macd(closes, 12, 26, 9)

        last_close  = _last(closes)
        last_rsi    = _last(rsi14)
        last_ema9   = _last(ema9)
        last_ema21  = _last(ema21)
        last_ema50  = _last(ema50)
        last_ema200 = _last(ema200)
        last_bb_u   = _last(bb_upper)
        last_bb_l   = _last(bb_lower)
        last_macd   = _last(macd_line)
        last_msig   = _last(macd_sig)
        last_mhist  = _last(macd_hist)

        rsi_signal = (
            "oversold"  if (last_rsi is not None and last_rsi < 30) else
            "overbought" if (last_rsi is not None and last_rsi > 70) else "neutral"
        )
        trend_signal = (
            "bullish" if (last_ema9 and last_ema21 and last_ema9 > last_ema21) else
            "bearish" if (last_ema9 and last_ema21 and last_ema9 < last_ema21) else "neutral"
        )
        above_200 = bool(last_close and last_ema200 and last_close > last_ema200)
        bb_signal = (
            "at_upper" if (last_close and last_bb_u and last_close >= last_bb_u * 0.99) else
            "at_lower" if (last_close and last_bb_l and last_close <= last_bb_l * 1.01) else "inside"
        )
        macd_cross = (
            "bullish" if (last_mhist is not None and last_mhist > 0) else
            "bearish" if (last_mhist is not None and last_mhist < 0) else "neutral"
        )

        return {
            "symbol": sym_upper,
            "interval": interval,
            "last_close": last_close,
            "bars_used": len(bars),
            "indicators": {
                "close":       last_close,
                "rsi14":       last_rsi,
                "ema9":        last_ema9,
                "ema21":       last_ema21,
                "ema50":       last_ema50,
                "ema200":      last_ema200,
                "bb_upper":    last_bb_u,
                "bb_lower":    last_bb_l,
                "atr14":       _last(atr14),
                "macd":        last_macd,
                "macd_signal": last_msig,
                "macd_hist":   last_mhist,
            },
            "signals": {
                "rsi":       rsi_signal,
                "trend":     trend_signal,
                "above_200": above_200,
                "bb":        bb_signal,
                "macd":      macd_cross,
            },
        }

    # ── Haber Akışı ──────────────────────────────────────────────────────────
    _news_store_instance = None

    def _get_news_store():
        nonlocal _news_store_instance
        if _news_store_instance is None:
            from backend.news.news_store import NewsStore
            _news_store_instance = NewsStore(_NEWS_DB_PATH)
        return _news_store_instance

    @app.get("/api/news")
    def get_news(
        symbol: str | None = None,
        limit: int = 30,
        fresh: bool = False,
        keyword: str | None = None,
    ) -> dict[str, Any]:
        """Haber listesi döndür.

        ``fresh=true`` ile yfinance'den çekip cache'e yaz.
        ``fresh=false`` (varsayılan) ile SQLite'tan oku.
        """
        store = _get_news_store()
        if fresh and symbol:
            from backend.news.news_fetcher import fetch_news_for_symbol
            items = fetch_news_for_symbol(symbol, limit=min(limit, 40))
            if items:
                store.upsert(items)
        news = store.query(symbol=symbol, limit=limit, keyword=keyword)
        unread = store.count_unread(symbol=symbol)
        return {"news": news, "total": len(news), "unread_24h": unread}

    @app.get("/api/news/unread-count")
    def get_news_unread_count(symbol: str | None = None) -> dict[str, Any]:
        """Son 24 saatteki haber sayısı (sidebar rozeti için)."""
        store = _get_news_store()
        return {"count": store.count_unread(symbol=symbol)}

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

    @app.post("/api/strategy-lab/pack/export")
    def strategy_pack_export(req: StrategyPackExportRequest) -> dict[str, Any]:
        try:
            pack = export_strategy_pack(
                req.strategy_spec,
                params=req.params,
                indicator_set=req.indicator_set,
                risk_settings=req.risk_settings,
                description=req.description,
                example_backtest_metadata=req.example_backtest_metadata,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"filename": ".piyasapilot-strategy.json", "pack": pack}

    @app.post("/api/strategy-lab/pack/import")
    def strategy_pack_import(req: StrategyPackImportRequest) -> dict[str, Any]:
        try:
            pack = import_strategy_pack(req.pack)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        return {"pack": pack}

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
          * ``token=...`` (API_KEY tanımlıysa zorunlu)
        """
        if not _require_ws_token(ws):
            await ws.close(code=1008)
            return

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
          * ``token=...`` query param'ı API_KEY tanımlıysa zorunludur.
        """
        if not _require_ws_token(ws):
            await ws.close(code=1008)
            return

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
        try:
            safe_limit = max(1, min(int(limit), 5000))
        except (TypeError, ValueError):
            safe_limit = 500

        if market_data_facade is not None and symbol.strip():
            repo_result = market_data_facade.read_candles(symbol, interval, safe_limit)
            if repo_result is not None:
                canonical_symbol = symbol.strip().upper()
                return JSONResponse({
                    "symbol": canonical_symbol,
                    "display_name": canonical_symbol,
                    "market": "",
                    "interval": interval,
                    "status": "ok",
                    "bars": repo_result.bars,
                    "quote": {
                        "last": repo_result.bars[-1]["close"],
                        "timestamp": _utc_iso(),
                    },
                    "metadata": {
                        "read_only": True,
                        "cache": repo_result.source,
                        "source": repo_result.source,
                        "is_real": True,
                        "status": "ok",
                        "fetched_at": _utc_iso(),
                    },
                })

        if interval == "1d":
            try:
                local_limit = max(20, min(int(limit), 5000))
            except (TypeError, ValueError):
                local_limit = 500
            local_payload = historical_store.payload(
                symbol=symbol,
                interval=interval,
                limit=local_limit,
            )
            if local_payload is not None:
                canonical_symbol = local_payload["symbol"]
                cleaned, report = filter_bars(local_payload["bars"])
                cache.upsert_bars(canonical_symbol, interval, cleaned)
                local_payload["bars"] = cleaned
                local_payload["metadata"]["spike_filter"] = {
                    "total": report.total_bars,
                    "winsorized": report.winsorized,
                    "untouched_high_volume": report.untouched_high_volume,
                }
                local_payload["metadata"]["cache"] = "local_parquet_then_write"
                return JSONResponse(local_payload)

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
            if market_data_facade is not None:
                market_data_facade.write_candles(
                    canonical_symbol,
                    interval,
                    cleaned,
                    source=provider_payload.get("metadata", {}).get("provider", "provider"),
                    limit=safe_limit,
                )
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

    # ── Mali Analiz API v2 — gerçek borsapy verisi ──────────────────────────
    @app.get("/api/mali-analiz/universe")
    def get_mali_analiz_universe(scope: str = "bist30") -> dict[str, Any]:
        """BIST 30 / BIST 100 sembol listesini fetch durumu ile döndürür."""
        target_list = BIST_100_SYMBOLS if scope == "bist100" else BIST_30_SYMBOLS
        fetch_status: dict[str, dict] = {}
        if _financial_repository_ref:
            for row in _financial_repository_ref.get_all_fetch_status():
                fetch_status[row["symbol"]] = {
                    "last_period": row.get("last_period"),
                    "fetched_at": str(row["fetched_at"]) if row.get("fetched_at") else None,
                    "status": row.get("status", "unknown"),
                    "periods_fetched": row.get("periods_fetched", 0),
                }
        symbols = [
            {
                "symbol": sym,
                "ticker": f"{sym}.IS",
                "name": SYMBOL_METADATA.get(sym, sym),
                "fetch_status": fetch_status.get(sym, {"status": "no_data"}),
            }
            for sym in target_list
        ]
        return {"scope": scope, "symbols": symbols, "source": "borsapy"}

    @app.get("/api/mali-analiz/alerts")
    def get_mali_analiz_alerts(
        symbol: str | None = None,
        limit: int = 50,
        unread_only: bool = False,
    ) -> dict[str, Any]:
        """Direktif ve uyarıları döndürür."""
        if not _financial_repository_ref:
            return {"alerts": [], "source": "no_db"}
        rows = _financial_repository_ref.get_alerts(symbol=symbol, limit=limit, unread_only=unread_only)
        return {"alerts": _serialize_rows(rows), "total": len(rows)}

    @app.post("/api/mali-analiz/alerts/mark-read")
    def mark_mali_analiz_alerts_read(body: dict[str, Any]) -> dict[str, Any]:
        """Belirtilen uyarıları okundu olarak işaretle."""
        ids = [int(i) for i in body.get("ids", [])]
        if _financial_repository_ref and ids:
            _financial_repository_ref.mark_alerts_read(ids)
        return {"marked": len(ids)}

    @app.post("/api/mali-analiz/refresh")
    async def refresh_mali_analiz_all(
        symbols: list[str] | None = None,
    ) -> dict[str, Any]:
        """Tüm BIST 30/100 (veya belirtilen semboller) için veri yenileme tetikler."""
        if not _financial_repository_ref:
            raise HTTPException(status_code=503, detail="Finansal repository hazır değil")
        import asyncio as _aio
        targets = symbols or BIST_30_SYMBOLS
        def _run():
            return harvest_all(
                symbols=targets,
                repository=_financial_repository_ref,
                max_workers=4,
            )
        results = await _aio.get_event_loop().run_in_executor(None, _run)
        ok = sum(1 for v in results.values() if v == "ok")
        return {"triggered": len(targets), "ok": ok, "results": results}

    @app.post("/api/mali-analiz/recompute")
    async def recompute_mali_analiz_all() -> dict[str, Any]:
        """Mevcut stored raw data'dan tüm BIST 30 için oranları yeniden hesaplar.

        borsapy'ye gitmez — sadece MySQL'deki ham satırları kullanır.
        """
        if not _financial_repository_ref:
            raise HTTPException(status_code=503, detail="Finansal repository hazır değil")
        import asyncio as _aio
        def _run():
            results = {}
            for sym in BIST_30_SYMBOLS:
                results[sym] = recompute_ratios_from_stored(sym, _financial_repository_ref)
            return results
        results = await _aio.get_event_loop().run_in_executor(None, _run)
        ok = sum(1 for v in results.values() if v == "ok")
        return {"triggered": len(BIST_30_SYMBOLS), "ok": ok, "results": results}

    @app.post("/api/mali-analiz/{symbol}/recompute")
    async def recompute_mali_analiz_symbol(symbol: str) -> dict[str, Any]:
        """Tek sembol için stored data'dan oran yeniden hesaplama."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            raise HTTPException(status_code=503, detail="Finansal repository hazır değil")
        import asyncio as _aio
        result = await _aio.get_event_loop().run_in_executor(
            None, recompute_ratios_from_stored, normalized, _financial_repository_ref
        )
        return {"symbol": normalized, "status": result}

    @app.post("/api/mali-analiz/{symbol}/refresh")
    async def refresh_mali_analiz_symbol(symbol: str) -> dict[str, Any]:
        """Tek sembol için veri yenileme tetikler."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            raise HTTPException(status_code=503, detail="Finansal repository hazır değil")
        import asyncio as _aio
        def _run():
            return harvest_all(
                symbols=[normalized],
                repository=_financial_repository_ref,
                max_workers=1,
            )
        results = await _aio.get_event_loop().run_in_executor(None, _run)
        return {"symbol": normalized, "status": results.get(normalized, "unknown")}

    @app.get("/api/mali-analiz/{symbol}/balance-sheet")
    def get_balance_sheet(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Bilanço verisi — satır × dönem pivot tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "rows": [], "periods": [], "source": "no_db"}
        periods = _financial_repository_ref.get_available_periods(normalized, period_type)[:limit]
        rows = _financial_repository_ref.get_raw_rows(normalized, "balance_sheet", period_type, periods)
        return {
            "symbol": normalized,
            "periods": periods,
            "rows": _pivot_rows(rows, periods),
            "source": "borsapy",
        }

    @app.get("/api/mali-analiz/{symbol}/income-stmt")
    def get_income_stmt(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Gelir tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "rows": [], "periods": [], "source": "no_db"}
        periods = _financial_repository_ref.get_available_periods(normalized, period_type)[:limit]
        rows = _financial_repository_ref.get_raw_rows(normalized, "income_stmt", period_type, periods)
        return {
            "symbol": normalized,
            "periods": periods,
            "rows": _pivot_rows(rows, periods),
            "source": "borsapy",
        }

    @app.get("/api/mali-analiz/{symbol}/cashflow")
    def get_cashflow(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
    ) -> dict[str, Any]:
        """Nakit akışı tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "rows": [], "periods": [], "source": "no_db"}
        periods = _financial_repository_ref.get_available_periods(normalized, period_type)[:limit]
        rows = _financial_repository_ref.get_raw_rows(normalized, "cashflow", period_type, periods)
        return {
            "symbol": normalized,
            "periods": periods,
            "rows": _pivot_rows(rows, periods),
            "source": "borsapy",
        }

    @app.get("/api/mali-analiz/{symbol}/ratios")
    def get_symbol_ratios(
        symbol: str,
        limit: int = 12,
    ) -> dict[str, Any]:
        """Hesaplanmış finansal oranlar."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "ratios": [], "source": "no_db"}
        periods = _financial_repository_ref.get_available_periods(normalized, "quarterly")[:limit]
        rows = _financial_repository_ref.get_computed_ratios(normalized, periods=periods)
        return {
            "symbol": normalized,
            "periods": periods,
            "ratios": _serialize_rows(rows),
            "source": "borsapy",
        }

    @app.get("/api/mali-analiz/{symbol}/summary")
    def get_symbol_summary(symbol: str) -> dict[str, Any]:
        """Özet + direktifler."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "alerts": [], "ratios": [], "source": "no_db"}
        alerts = _financial_repository_ref.get_alerts(symbol=normalized, limit=10)
        periods = _financial_repository_ref.get_available_periods(normalized, "quarterly")[:4]
        ratios = _financial_repository_ref.get_computed_ratios(
            normalized, periods=periods[:1],
            ratio_keys=["fk", "pd_dd", "ev_ebitda", "roe", "net_kar_marji", "net_borc_ebitda", "ciro_buyume"]
        )
        return {
            "symbol": normalized,
            "name": SYMBOL_METADATA.get(normalized, normalized),
            "latest_period": periods[0] if periods else None,
            "alerts": _serialize_rows(alerts),
            "key_ratios": _serialize_rows(ratios),
            "source": "borsapy",
        }

    # Eski endpoint'ler — geriye dönük uyumluluk
    @app.get("/api/mali-analiz/{symbol}/reports")
    def get_mali_analiz_reports(symbol: str) -> dict[str, Any]:
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        periods = []
        if _financial_repository_ref:
            periods = _financial_repository_ref.get_available_periods(normalized, "quarterly")
        return {"symbol": normalized, "periods": periods, "source": "borsapy"}

    @app.get("/api/mali-analiz/{symbol}/events")
    def get_mali_analiz_events(symbol: str) -> dict[str, Any]:
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        alerts = []
        if _financial_repository_ref:
            alerts = _financial_repository_ref.get_alerts(symbol=normalized, limit=20)
        return {"symbol": normalized, "events": _serialize_rows(alerts), "source": "borsapy"}

    @app.get("/api/mali-analiz/{symbol}/metric-history")
    def get_mali_analiz_metric_history(
        symbol: str,
        metric: str = "net_income",
    ) -> dict[str, Any]:
        """Metrik geçmişi kontratı; finansal seri bağlanana kadar boş döner."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
        if not _financial_repository_ref:
            return {"symbol": normalized, "metric": metric, "points": [], "source": "no_db"}
        ratios = _financial_repository_ref.get_computed_ratios(normalized, ratio_keys=[metric])
        points = [
            {"period": r["period"], "value": float(r["value"]) if r["value"] is not None else None}
            for r in ratios
        ]
        return {"symbol": normalized, "metric": metric, "points": points, "source": "borsapy"}

    @app.get("/api/mali-analiz/{symbol}/chart-data")
    def get_mali_analiz_chart_data(
        symbol: str,
        limit: int = 16,
    ) -> dict[str, Any]:
        """Lightweight-charts için finansal zaman serisi döner.

        Her metrik: [{period, time_iso, value}] (kronolojik, eskiden yeniye)
        time_iso: lightweight-charts'ın kabul ettiği 'YYYY-MM-DD' formatında.
        """
        try:
            normalized = normalize_symbol(symbol)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        if not _financial_repository_ref:
            return {"symbol": normalized, "metrics": {}, "source": "no_db"}

        # Çekilen oranlar (son limit çeyrek)
        CHART_METRICS = [
            "net_kar_marji", "brut_kar_marji", "ebitda_marji",
            "roe", "roa",
            "ciro_buyume", "net_kar_buyume",
            "net_borc_ebitda", "borc_ozkaynak",
            "cari_oran",
        ]
        ratio_rows = _financial_repository_ref.get_computed_ratios(normalized, ratio_keys=CHART_METRICS)

        # Ham gelir tablosu — ciro ve net kar absolute değerler için
        income_rows = _financial_repository_ref.get_raw_rows(normalized, "income_stmt", "quarterly")

        def _period_to_iso(period: str) -> str | None:
            """'2023Q1' → '2023-01-01', '2023/12' → '2023-12-01'"""
            import re
            m = re.match(r"(\d{4})Q(\d)", period)
            if m:
                quarter_month = {"1": "01", "2": "04", "3": "07", "4": "10"}
                return f"{m.group(1)}-{quarter_month.get(m.group(2), '01')}-01"
            m2 = re.match(r"(\d{4})/(\d{2})", period)
            if m2:
                return f"{m2.group(1)}-{m2.group(2)}-01"
            return None

        # Oran serileri
        metrics: dict[str, list[dict]] = {k: [] for k in CHART_METRICS}
        seen: dict[str, set] = {k: set() for k in CHART_METRICS}
        for row in ratio_rows:
            key = row.get("ratio_key", "")
            if key not in metrics:
                continue
            period = row.get("period", "")
            if period in seen[key]:
                continue
            seen[key].add(period)
            iso = _period_to_iso(period)
            if iso and row.get("value") is not None:
                metrics[key].append({"period": period, "time": iso, "value": float(row["value"])})

        for key in metrics:
            metrics[key].sort(key=lambda x: x["time"])
            metrics[key] = metrics[key][-limit:]

        # Ciro (revenue) ve Net Kar ham değerleri — row_index 1 ve 35
        rev_series: list[dict] = []
        ni_series: list[dict] = []
        rev_by_period: dict[str, float] = {}
        ni_by_period: dict[str, float] = {}
        for row in income_rows:
            period = row.get("period", "")
            idx = row.get("row_index")
            val = row.get("value")
            if val is None:
                continue
            fval = float(val)
            if idx == 1:
                rev_by_period[period] = fval
            elif idx == 35:
                ni_by_period[period] = fval

        for period, val in sorted(rev_by_period.items())[-limit:]:
            iso = _period_to_iso(period)
            if iso:
                rev_series.append({"period": period, "time": iso, "value": val})
        for period, val in sorted(ni_by_period.items())[-limit:]:
            iso = _period_to_iso(period)
            if iso:
                ni_series.append({"period": period, "time": iso, "value": val})

        metrics["revenue"] = rev_series
        metrics["net_income"] = ni_series

        return {"symbol": normalized, "metrics": metrics, "source": "borsapy"}

    @app.get("/api/mali-analiz/comparison")
    def get_mali_analiz_comparison() -> dict[str, Any]:
        """BIST 30 karşılaştırma tablosu — tüm semboller için son dönem oranları.

        Dönüş:
          comparison_keys: gösterilecek oran sırası
          symbols: [{symbol, name, period, ratios:{key:{value,unit}}}]
        """
        COMPARISON_KEYS = [
            "fk", "pd_dd", "ev_ebitda",
            "roe", "net_kar_marji", "brut_kar_marji",
            "ciro_buyume", "net_kar_buyume",
            "net_borc_ebitda", "borc_ozkaynak",
            "cari_oran", "fcf_marji",
        ]
        KEY_META = {
            "fk":             ("F/K",         "x"),
            "pd_dd":          ("PD/DD",        "x"),
            "ev_ebitda":      ("EV/EBITDA",    "x"),
            "roe":            ("ROE",          "%"),
            "net_kar_marji":  ("NK Marjı",     "%"),
            "brut_kar_marji": ("Brüt Marj",    "%"),
            "ciro_buyume":    ("Ciro Büy.",    "%"),
            "net_kar_buyume": ("NK Büy.",      "%"),
            "net_borc_ebitda":("ND/EBITDA",    "x"),
            "borc_ozkaynak":  ("Borç/ÖK",      "x"),
            "cari_oran":      ("Cari Oran",    "x"),
            "fcf_marji":      ("FCF Marjı",    "%"),
        }

        if not _financial_repository_ref:
            return {"comparison_keys": COMPARISON_KEYS, "key_meta": KEY_META, "symbols": [], "source": "no_db"}

        rows = _financial_repository_ref.get_latest_ratios_all_symbols(
            BIST_30_SYMBOLS, COMPARISON_KEYS
        )

        # {symbol: {period, ratios:{key:{value,unit}}}}
        by_symbol: dict[str, dict] = {}
        for row in rows:
            sym = row["symbol"]
            if sym not in by_symbol:
                by_symbol[sym] = {"period": row.get("period", ""), "ratios": {}}
            key = row["ratio_key"]
            if key in KEY_META:
                by_symbol[sym]["ratios"][key] = {
                    "value": float(row["value"]) if row["value"] is not None else None,
                    "unit":  KEY_META[key][1],
                }

        symbols_out = []
        for sym in BIST_30_SYMBOLS:
            entry = by_symbol.get(sym, {})
            symbols_out.append({
                "symbol":  sym,
                "name":    SYMBOL_METADATA.get(sym, sym),
                "period":  entry.get("period", ""),
                "ratios":  entry.get("ratios", {}),
                "has_data": sym in by_symbol,
            })

        return {
            "comparison_keys": COMPARISON_KEYS,
            "key_meta": {k: {"label": v[0], "unit": v[1]} for k, v in KEY_META.items()},
            "symbols": symbols_out,
            "source": "borsapy",
        }

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


# ── Mali analiz yardımcıları ────────────────────────────────────────────────

def _serialize_rows(rows: list[dict]) -> list[dict]:
    """datetime/Decimal → JSON serileştirilebilir."""
    import decimal
    result = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if isinstance(v, decimal.Decimal):
                clean[k] = float(v)
            elif hasattr(v, "isoformat"):
                clean[k] = v.isoformat()
            else:
                clean[k] = v
        result.append(clean)
    return result


def _pivot_rows(rows: list[dict], periods: list[str]) -> list[dict]:
    """Satır bazlı DB sonucunu {label, row_index, {period: value}} pivotuna çevirir."""
    import decimal
    # row_index bazında grupla
    index_map: dict[int, dict] = {}
    for row in rows:
        idx = row["row_index"]
        if idx not in index_map:
            index_map[idx] = {"row_index": idx, "label": row["label"], "values": {}}
        raw_val = row["value"]
        val = float(raw_val) if isinstance(raw_val, decimal.Decimal) else raw_val
        index_map[idx]["values"][row["period"]] = val

    # Sıralı döndür
    result = []
    for idx in sorted(index_map.keys()):
        entry = index_map[idx]
        # Tüm değerler 0 veya None ise atla
        vals = [v for v in entry["values"].values() if v is not None and v != 0]
        if not vals:
            continue
        result.append({
            "row_index": entry["row_index"],
            "label": entry["label"],
            "values": {p: entry["values"].get(p) for p in periods},
        })
    return result


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
    slippage_model: str = Field("fixed_bps", description="Slippage modeli (fixed_bps, fixed_tick)")
    slippage_tick: float = Field(0.01, description="Tick bazlı slippage için tick değeri")
    volume_limit_pct: float = Field(0.05, description="Likidite limiti (son X bar ortalamasının yüzdesi)")
    volume_window: int = Field(5, description="Ortalama hacim hesaplama için pencere boyutu")
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
    slippage_model: str = Field("fixed_bps")
    slippage_tick: float = Field(0.01)
    volume_limit_pct: float = Field(0.05)
    volume_window: int = Field(5)
    max_position_pct: float = Field(0.20, gt=0, le=1.0)
    allow_short: bool = False
    source_mode: str = "cache_only"


class StrategyPackExportRequest(BaseModel):
    strategy_spec: dict[str, Any]
    params: dict[str, Any] = Field(default_factory=dict)
    indicator_set: dict[str, Any] | list[Any] = Field(default_factory=dict)
    risk_settings: dict[str, Any] = Field(default_factory=dict)
    description: str = ""
    example_backtest_metadata: dict[str, Any] = Field(default_factory=dict)


class StrategyPackImportRequest(BaseModel):
    pack: dict[str, Any] | str


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
    slippage_model: str = Field("fixed_bps")
    slippage_tick: float = Field(0.01)
    volume_limit_pct: float = Field(0.05)
    volume_window: int = Field(5)
    max_position_pct: float = Field(0.20, gt=0, le=1.0)
    allow_short: bool = False
    source_mode: str = "cache_only"


class WalkForwardRequest(BaseModel):
    """``POST /api/backtest/walk-forward`` gövdesi."""

    symbol: str = Field(..., description="Sembol")
    interval: str = Field("1d", description="Timeframe")
    strategy_id: str = Field("", description="Blueprint id veya strategy_spec için boş")
    strategy_spec: dict[str, Any] | None = Field(None)
    params: dict[str, Any] = Field(default_factory=dict, description="Sabit parametreler")
    param_grid: dict[str, list[Any]] = Field(
        default_factory=dict,
        description="Optimizasyon grid'i — boş ise params kullanılır",
    )
    in_sample_bars: int = Field(200, ge=50, le=2000, description="Her penceredeki in-sample bar sayısı")
    out_of_sample_bars: int = Field(50, ge=10, le=500, description="Her penceredeki out-of-sample bar sayısı")
    step_bars: int = Field(50, ge=10, le=500, description="Pencere kayma adımı (bar)")
    lookback_bars: int = Field(1000, ge=100, le=5000, description="Cache'ten alınacak toplam bar")
    capital: float = Field(100_000.0, gt=0)
    commission_rate: float = Field(0.001, ge=0, le=0.10)
    slippage_bps: int = Field(5, ge=0, le=500)
    allow_short: bool = False


class MonteCarloRequest(BaseModel):
    """``POST /api/backtest/monte-carlo`` gövdesi."""

    run_id: str = Field(..., description="Arşivlenmiş backtest rapor ID'si")
    n_simulations: int = Field(500, ge=100, le=2000, description="Simülasyon tekrar sayısı")
    method: str = Field("bootstrap", description="bootstrap veya permutation")
    seed: int | None = Field(None, description="Tekrarlanabilirlik için rastgele tohum")


# Uvicorn entry point: `uvicorn backend.api.main:app`
app = create_app()
