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

# ── Python 3.10 uyumluluk yaması ─────────────────────────────────────────────
# datetime.UTC, Python 3.11'de eklendi. 3.10'da datetime.timezone.utc kullan.
import datetime as _dt_compat
if not hasattr(_dt_compat, "UTC"):
    _dt_compat.UTC = _dt_compat.timezone.utc  # type: ignore[attr-defined]
del _dt_compat
# ─────────────────────────────────────────────────────────────────────────────

import asyncio
import datetime as dt
import hashlib
import itertools
import logging
import math
import os
import re
import signal
import uuid
# NOT: sentry_sdk.init() burada çağrılmaz — create_app() içindeki _init_sentry() çağırır.
# Modül seviyesinde init yapmak .env yüklenmeden önce çalışır ve FastApiIntegration eklemez.
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any, AsyncIterator
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
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
from backend.auth.dependencies import get_current_user, get_optional_user, require_feature, require_quota, require_paper_trading
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
from backend.data.constants import VALID_INTERVALS_SET, validate_interval
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
_PRICE_ALERTS_DB_PATH = "data/cache/price_alerts.sqlite3"
_logger = logging.getLogger(__name__)

# Cache miss eşiği: cache'teki en yeni bar'dan beri bu süreden uzun zaman
# geçmişse provider'a yeniden git. 15dk barlar için 90s mantıklı.
CACHE_FRESHNESS_SECONDS = 90


def _bist_feed_configured() -> bool:
    return bool(getenv("BIST_HTTP_URL_TEMPLATE"))


def _viop_feed_configured() -> bool:
    return bool(getenv("VIOP_HTTP_URL_TEMPLATE"))


def _is_viop_market_symbol(symbol: str) -> bool:
    clean = symbol.strip().upper().replace(" ", "")
    return (
        clean.startswith("VIOP:")
        or clean.startswith("F_")
        or clean.startswith("O_")
        or clean.startswith("VIP-")
        or clean.startswith("VIOP_")
    )


def _is_bist_market_symbol(symbol: str) -> bool:
    clean = symbol.strip().upper().replace(" ", "")
    if not clean or clean.endswith("=X") or clean.endswith("=F"):
        return False
    if clean in {"XU100", "^XU100", "BIST100", "XU100.IS", "XU030.IS"}:
        return True
    if clean.endswith(".IS"):
        return True
    bist_codes = {item.replace(".IS", "") for item in BIST_STOCKS}
    return clean in bist_codes


def _license_blocked_payload(symbol: str, interval: str, market: str) -> dict[str, Any]:
    clean = symbol.strip().upper().replace(" ", "")
    if market == "viop":
        message = "VİOP verileri lisanslı veri sağlayıcı bağlantısı tamamlanana kadar kapalıdır."
        display = clean.replace("VIOP:", "")
    else:
        message = "BIST verileri lisanslı veri sağlayıcı bağlantısı tamamlanana kadar kapalıdır."
        display = "BIST 100" if clean in {"XU100", "^XU100", "BIST100", "XU100.IS"} else clean
    return {
        "symbol": clean,
        "display_name": display,
        "market": market,
        "interval": interval,
        "status": "not_configured",
        "message": message,
        "bars": [],
        "quote": None,
        "metadata": {
            "read_only": True,
            "cache": "blocked",
            "source": "license_pending",
            "is_real": False,
            "is_live": False,
            "is_delayed": False,
            "delay_minutes": None,
            "status": "not_configured",
            "fetched_at": _utc_iso(),
            "quality_status": "blocked",
            "coverage_pct": 0.0,
            "provider": "license_pending",
            "staleness_seconds": None,
            "license_note": message,
            "warnings": [
                "Lisanslı veri bağlantısı aktif olmadığından fiyat, grafik ve sinyal gösterimi kapalıdır.",
                "Yatırım tavsiyesi değildir.",
            ],
        },
    }


def _license_restricted_payload(symbol: str, interval: str) -> dict[str, Any] | None:
    if _is_viop_market_symbol(symbol) and not _viop_feed_configured():
        return _license_blocked_payload(symbol, interval, "viop")
    if _is_bist_market_symbol(symbol) and not _bist_feed_configured():
        return _license_blocked_payload(symbol, interval, "bist")
    return None


def _cors_origins() -> list[str]:
    raw = os.environ.get("CORS_ORIGINS", "http://localhost:5173")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["http://localhost:5173"]


def _require_ws_token(ws: WebSocket) -> bool:
    import hmac as _hmac
    if os.environ.get("REQUIRE_WS_API_KEY", "0") != "1":
        return True
    api_key = os.environ.get("API_KEY", "")
    if not api_key:
        return True
    token = ws.query_params.get("token", "")
    # sabit-zamanlı karşılaştırma (timing attack'e karşı)
    return _hmac.compare_digest(token, api_key)


def _rate_limiter() -> Any:
    if Limiter is None or get_remote_address is None:
        _logger.warning("[security] slowapi kurulu değil; rate limiting devre dışı.")
        return None
    return Limiter(key_func=get_remote_address)


def _limit(limiter: Any, rule: str) -> Any:
    if limiter is None:
        return lambda func: func
    return limiter.limit(rule)


async def _create_mysql_pool_from_env() -> Any | None:
    """Auth/payment metadata pool. Optional in local SQLite-only mode."""
    if os.environ.get("PIYASAPILOT_DISABLE_AUTH_DB") == "1":
        return None
    try:
        import aiomysql
    except ImportError:
        _logger.warning("[auth-db] aiomysql kurulu değil; auth DB devre dışı.")
        return None

    raw_url = os.environ.get("DATABASE_URL", "")
    parsed = urlparse(raw_url) if raw_url else None
    host = os.environ.get("MYSQL_HOST") or (parsed.hostname if parsed else None) or "localhost"
    port = int(os.environ.get("MYSQL_PORT") or (parsed.port if parsed else 3306))
    user = os.environ.get("MYSQL_USER") or (parsed.username if parsed else None) or "appuser"
    password = os.environ.get("MYSQL_PASSWORD") or (parsed.password if parsed else None) or "apppass"
    database = (
        os.environ.get("MYSQL_DATABASE")
        or ((parsed.path or "").lstrip("/") if parsed else "")
        or "metadata"
    )
    try:
        return await aiomysql.create_pool(
            host=host,
            port=port,
            user=user,
            password=password,
            db=database,
            autocommit=False,
            minsize=1,
            maxsize=int(os.environ.get("MYSQL_POOL_MAXSIZE", "10")),
        )
    except Exception as exc:  # noqa: BLE001
        _logger.warning("[auth-db] MySQL pool kurulamadı: %s", exc)
        return None


async def _create_async_redis_from_env() -> Any | None:
    """Redis is optional; used for OAuth state and login brute-force counters."""
    if os.environ.get("PIYASAPILOT_DISABLE_REDIS") == "1":
        return None
    try:
        import redis.asyncio as redis
    except ImportError:
        _logger.warning("[redis] redis paketi kurulu değil; Redis devre dışı.")
        return None
    try:
        client = redis.from_url(
            os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=0.5,
            socket_timeout=0.5,
        )
        await client.ping()
        return client
    except Exception as exc:  # noqa: BLE001
        _logger.warning("[redis] bağlantı kurulamadı: %s", exc)
        return None


def _utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def _init_sentry() -> None:
    dsn = getenv("SENTRY_DSN", "")
    if not dsn:
        return
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        sentry_sdk.init(
            dsn=dsn,
            environment=getenv("SENTRY_ENVIRONMENT", getenv("APP_ENV", "development")),
            integrations=[FastApiIntegration()],
            traces_sample_rate=float(getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            send_default_pii=False,
        )
        _logger.info("[sentry] Sentry aktif.")
    except Exception as exc:  # noqa: BLE001
        _logger.warning("[sentry] Sentry başlatılamadı: %s", exc)


def _check_optional_env() -> None:
    """Başlangıçta opsiyonel çevre değişkenlerini kontrol et; eksikse uyar."""
    checks = [
        ("TELEGRAM_BOT_TOKEN", "Telegram bildirimleri devre dışı"),
        ("TELEGRAM_CHAT_ID", "Telegram bildirimleri devre dışı"),
        ("SMTP_HOST", "E-posta bildirimleri devre dışı"),
        ("BIST_HTTP_URL_TEMPLATE", "Lisanslı BIST feed bağlı değil — BIST fiyat/grafik akışı kapalı"),
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
    workers = [
        BinanceKlineWorker(
            cache=cache,
            symbols=CRYPTO_WS_SYMBOLS,
            interval=DEFAULT_INTERVAL,
            on_bar=on_bar,
        ),
        YahooPoller(
            cache=cache,
            data_service=data_service,
            symbols=tuple(
                symbol for symbol in YAHOO_INDEX_FX_COMMODITY
                if not _is_bist_market_symbol(symbol) or _bist_feed_configured()
            ),
            interval=DEFAULT_INTERVAL,
            on_bar=on_bar,
        ),
    ]
    if _bist_feed_configured():
        workers.append(
            BistStockPoller(
                cache=cache,
                data_service=data_service,
                symbols=BIST_STOCKS,
                interval=DEFAULT_INTERVAL,
                on_bar=on_bar,
            )
        )
    else:
        _logger.info("[workers] BIST poller lisanslı feed beklediği için başlatılmadı.")
    return WorkerSupervisor(workers)


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
    _init_sentry()
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
        app.state.db_pool = await _create_mysql_pool_from_env()
        app.state.redis = await _create_async_redis_from_env()

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

        # Fiyat uyarısı worker — her 15 saniyede cache'ten son fiyatı kontrol eder
        async def _price_alert_worker():
            import sqlite3 as _sqlite3
            from pathlib import Path as _Path
            _pa_path = _Path(_PRICE_ALERTS_DB_PATH)
            _pa_path.parent.mkdir(parents=True, exist_ok=True)
            _pa_ddl = """
            CREATE TABLE IF NOT EXISTS price_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol     TEXT NOT NULL,
                target     REAL NOT NULL,
                direction  TEXT NOT NULL,
                triggered  INTEGER NOT NULL DEFAULT 0,
                note       TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );"""
            with _sqlite3.connect(str(_pa_path)) as _c:
                _c.executescript(_pa_ddl)
            while True:
                try:
                    with _sqlite3.connect(str(_pa_path)) as _c:
                        _c.row_factory = _sqlite3.Row
                        active = _c.execute(
                            "SELECT * FROM price_alerts WHERE triggered=0"
                        ).fetchall()
                    for row in active:
                        sym = str(row["symbol"])
                        target = float(row["target"])
                        direction = str(row["direction"])
                        last = cache.get_last_price(sym) if hasattr(cache, "get_last_price") else None
                        if last is None:
                            continue
                        hit = (direction == "above" and last >= target) or \
                              (direction == "below" and last <= target)
                        if hit:
                            with _sqlite3.connect(str(_pa_path)) as _c:
                                _c.execute(
                                    "UPDATE price_alerts SET triggered=1 WHERE id=?",
                                    (row["id"],),
                                )
                            msg = f"🔔 Fiyat uyarısı: {sym} {'≥' if direction=='above' else '≤'} {target:.2f} (şu an: {last:.2f})"
                            _logger.info("[price-alert] %s", msg)
                            try:
                                from backend.notifier.telegram import send_telegram
                                send_telegram(msg)
                            except Exception:
                                pass
                except asyncio.CancelledError:
                    break
                except Exception as _e:
                    _logger.debug("[price-alert-worker] hata: %s", _e)
                await asyncio.sleep(15)

        price_alert_task = asyncio.create_task(_price_alert_worker())

        try:
            yield
        finally:
            redis_client = getattr(app.state, "redis", None)
            if redis_client is not None:
                await redis_client.aclose()
            db_pool = getattr(app.state, "db_pool", None)
            if db_pool is not None:
                db_pool.close()
                await db_pool.wait_closed()
            await health_monitor.stop()
            news_worker_task.cancel()
            price_alert_task.cancel()
            executor_task.cancel()
            await supervisor.stop_all()
            try:
                paper_db.checkpoint()
                _logger.info("[shutdown] SQLite WAL checkpoint tamamlandı.")
            except Exception as exc:
                _logger.warning("[shutdown] WAL checkpoint başarısız: %s", exc)

    app = FastAPI(
        title="PiyasaPilot API",
        version="1.0.0",
        description=(
            "PiyasaPilot — Gerçek zamanlı piyasa verisi, sinyal üretimi, backtest motoru "
            "ve paper trading simülasyonu API'si.\n\n"
            "**Not:** Emir motoru pasiftir. Gerçek emir gönderimi desteklenmez.\n\n"
            "## Kimlik Doğrulama\n"
            "Korumalı endpoint'ler `access_token` HTTP-only cookie gerektirir. "
            "`POST /api/auth/login` ile oturum açın."
        ),
        contact={
            "name": "PiyasaPilot Destek",
            "url": "https://piyasapilotu.com",
            "email": "destek@piyasapilotu.com",
        },
        openapi_tags=[
            {"name": "auth", "description": "Kimlik doğrulama — kayıt, giriş, OAuth, 2FA"},
            {"name": "backtest", "description": "Backtest motoru — strateji çalıştırma, optimizasyon, tarama"},
            {"name": "paper-trading", "description": "Paper trading simülasyonu — sanal portföy yönetimi"},
            {"name": "strategy-lab", "description": "Strateji laboratuvarı — kaydetme, dışa/içe aktarma"},
            {"name": "billing", "description": "Ödeme sistemi — Stripe checkout, portal, webhook"},
            {"name": "payments", "description": "Ödeme yönetimi — abonelik durumu, iptal"},
            {"name": "news", "description": "Haber akışı — KAP, RSS kaynakları"},
            {"name": "financials", "description": "Mali analiz — bilanço, gelir tablosu, oranlar"},
            {"name": "alerts", "description": "Fiyat uyarıları"},
            {"name": "admin", "description": "Yönetici paneli"},
        ],
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
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
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*", "X-API-Key"],
    )
    app.add_middleware(APIKeyMiddleware)

    # ── Auth Router ───────────────────────────────────────────────────────
    try:
        from backend.api.auth_router import router as auth_router
        app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
        _logger.info("[auth] Auth router yüklendi → /api/auth/*")
    except Exception as _auth_err:
        _logger.warning("[auth] Auth router yüklenemedi: %s", _auth_err)

    # ── Payments Router ───────────────────────────────────────────────────
    try:
        from backend.api.payments_router import router as payments_router
        app.include_router(payments_router, prefix="/api/payments", tags=["payments"])
        _logger.info("[payments] Payments router yüklendi → /api/payments/*")
    except Exception as _pay_err:
        _logger.warning("[payments] Payments router yüklenemedi: %s", _pay_err)

    # ── Billing Router (devre dışı — payments_router tek yetkili Stripe handler) ──
    # billing_router SQLite idempotency kullanıyordu; payments_router MySQL kullanıyor.
    # İki router aynı Stripe event'larını işleyemez; billing_router kaldırıldı.

    # ── Admin Router ──────────────────────────────────────────────────────
    try:
        from backend.api.admin_router import router as admin_router
        app.include_router(admin_router, prefix="/api/admin", tags=["admin"])
        _logger.info("[admin] Admin router yüklendi → /api/admin/*")
    except Exception as _admin_err:
        _logger.warning("[admin] Admin router yüklenemedi: %s", _admin_err)

    # ── Growth Router ─────────────────────────────────────────────────────
    try:
        from backend.api.growth_router import router as growth_router
        app.include_router(growth_router, prefix="/api", tags=["growth"])
        _logger.info("[growth] Growth router yüklendi → /api/waitlist, /api/backtest/share")
    except Exception as _growth_err:
        _logger.warning("[growth] Growth router yüklenemedi: %s", _growth_err)

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
        # SQLite pool istatistikleri
        db_pools = {}
        try:
            from backend.db.pool import SQLitePool
            for attr_name in ("paper_db",):
                obj = getattr(app.state, attr_name, None)
                if obj and hasattr(obj, "db") and hasattr(obj.db, "stats_dict"):
                    db_pools[attr_name] = obj.db.stats_dict()
        except Exception:
            pass
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
            "db_pools": db_pools,
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

    # ── Sembol Evreni API ────────────────────────────────────────────────
    @app.get("/api/symbols", tags=["symbols"])
    def get_symbol_universe(
        group: str | None = None,
        asset_type: str | None = None,
        active_only: bool = True,
    ) -> dict[str, Any]:
        """Sembol evrenini döndürür.

        Query params:
            group:       'BIST 30' | 'BIST 100' | 'Kripto' | 'Döviz / Emtia' | 'VİOP' | 'ABD Piyasaları'
            asset_type:  'equity' | 'crypto' | 'fx' | 'commodity' | 'index' | 'futures'
            active_only: True (varsayılan) → sadece aktif semboller
        """
        from backend.data.symbols import (
            BIST_STOCKS,
            CRYPTO_WS_SYMBOLS,
            YAHOO_INDEX_FX_COMMODITY,
        )

        # Statik sembol kaydını SymbolInfo formatına dönüştür
        raw: list[dict[str, Any]] = []
        bist_licensed = _bist_feed_configured()

        # BIST hisseler
        for sym in BIST_STOCKS:
            ticker = sym.replace(".IS", "")
            grp = "BIST 30" if ticker in {
                "AKBNK","ARCLK","ASELS","BIMAS","DOHOL","EREGL","FROTO","GARAN",
                "HALKB","ISCTR","KCHOL","KOZAL","KRDMD","MAVI","PGSUS","SAHOL",
                "SASA","SISE","TAVHL","TCELL","THYAO","TOASO","TTKOM","TUPRS",
                "VAKBN","VESTL","YKBNK","PETKM","EKGYO","ENKAI",
            } else "BIST 100"
            raw.append({
                "symbol":     sym,
                "name":       ticker,
                "asset_type": "equity",
                "group":      grp,
                "currency":   "TRY",
                "active":     bist_licensed,
                "market":     "BIST",
                "provider":   "bist_http" if bist_licensed else "license_pending",
            })

        # Kripto
        for sym in CRYPTO_WS_SYMBOLS:
            raw.append({
                "symbol":     sym,
                "name":       sym.replace("USDT", "/USDT"),
                "asset_type": "crypto",
                "group":      "Kripto",
                "currency":   "USDT",
                "active":     True,
                "market":     "CRYPTO",
                "provider":   "binance",
            })

        # Endeks / FX / Emtia
        _FX_META: dict[str, dict[str, str]] = {
            "XU100":   {"name": "BIST 100 Endeksi",  "asset_type": "index",     "group": "BIST 30",       "currency": "TRY"},
            "USDTRY=X":{"name": "USD/TRY",           "asset_type": "fx",        "group": "Döviz / Emtia", "currency": "TRY"},
            "EURTRY=X":{"name": "EUR/TRY",           "asset_type": "fx",        "group": "Döviz / Emtia", "currency": "TRY"},
            "GC=F":    {"name": "Altın (USD/oz)",    "asset_type": "commodity", "group": "Döviz / Emtia", "currency": "USD"},
            "CL=F":    {"name": "Brent Petrol",      "asset_type": "commodity", "group": "Döviz / Emtia", "currency": "USD"},
            "SI=F":    {"name": "Gümüş (USD/oz)",    "asset_type": "commodity", "group": "Döviz / Emtia", "currency": "USD"},
        }
        for sym, meta in _FX_META.items():
            is_bist_index = sym == "XU100"
            raw.append({
                "symbol":     sym,
                "name":       meta["name"],
                "asset_type": meta["asset_type"],
                "group":      meta["group"],
                "currency":   meta["currency"],
                "active":     bist_licensed if is_bist_index else True,
                "market":     "BIST" if is_bist_index else "GLOBAL",
                "provider":   (
                    "bist_http" if is_bist_index and bist_licensed
                    else ("license_pending" if is_bist_index else "yfinance")
                ),
            })

        # Filtrele
        result = raw
        if active_only:
            result = [s for s in result if s["active"]]
        if group:
            result = [s for s in result if s["group"] == group]
        if asset_type:
            result = [s for s in result if s["asset_type"] == asset_type]

        return {
            "symbols": result,
            "total": len(result),
            "fetched_at": _utc_iso(),
        }

    # ── Backtest API (Sprint 3.2 + 3.3) ──────────────────────────────────
    @app.get("/api/backtest/strategies", tags=["backtest"])
    def backtest_strategies(user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Mevcut strateji blueprint'lerini listele (frontend form üretir)."""
        return {
            "strategies": list_blueprints(),
            "presets": list_strategy_presets(include_spec=True)
        }

    @app.post("/api/backtest/run", tags=["backtest"])
    @_limit(limiter, "30/minute")
    def backtest_run(request: Request, req: BacktestRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
            uid = str(user.get("id", "")) or None
            uemail = str(user.get("email", "")) or None
            run_id = backtest_archive.save(result, user_id=uid, user_email=uemail)
            result["run_id"] = run_id
            # ── Audit log ─────────────────────────────────────────────────────
            try:
                from backend.audit import audit_logger, AuditEvent, AuditAction
                import asyncio
                asyncio.get_event_loop().run_until_complete(audit_logger.log(AuditEvent(
                    action=AuditAction.BACKTEST_RUN,
                    user_id=int(user.get("id", 0)) or None,
                    resource=f"{req.symbol}/{req.interval}",
                    metadata={
                        "run_id": run_id,
                        "strategy": req.strategy_id,
                        "bars": req.lookback_bars,
                        "capital": req.capital,
                    },
                )))
            except Exception:
                pass  # audit hatası backtest'i engellemesin
            return result
        except UnknownStrategy:
            raise HTTPException(status_code=400, detail="Bilinmeyen strateji.")
        except BacktestNotEnoughData:
            raise HTTPException(status_code=409, detail="Backtest için yeterli veri yok.")
        except BacktestRunError:
            raise HTTPException(status_code=400, detail="Backtest çalıştırılamadı.")

    @app.post("/api/backtest/batch", tags=["backtest"])
    @_limit(limiter, "5/minute")
    def backtest_batch(request: Request, body: dict[str, Any], user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Aynı stratejiyi birden fazla sembole uygula, sonuçları getiriye göre sırala.

        Body: {symbols: [str], strategy_id: str, params: {}, interval: str,
               capital: float, start_date?: str, end_date?: str, max_symbols: int}
        """
        del request
        symbols: list[str] = [str(s) for s in body.get("symbols", []) if isinstance(s, str)][:50]
        if not symbols:
            raise HTTPException(400, detail="symbols listesi boş.")

        strategy_id = str(body.get("strategy_id", "sma_cross"))
        params      = body.get("params", {})
        interval    = str(body.get("interval", "1d"))
        capital     = float(body.get("capital", 100_000.0))
        start_date  = body.get("start_date")
        end_date    = body.get("end_date")
        commission  = float(body.get("commission_rate", 0.001))
        max_symbols = min(int(body.get("max_symbols", 30)), 50)
        symbols     = symbols[:max_symbols]

        results = []
        errors  = []
        uid = str(user.get("id", "")) or None
        uemail = str(user.get("email", "")) or None

        for sym in symbols:
            try:
                result = run_backtest(
                    cache=cache,
                    data_service=data_service,
                    symbol=sym,
                    interval=interval,
                    strategy_id=strategy_id,
                    params=params,
                    capital=capital,
                    lookback_bars=500,
                    start_date=start_date,
                    end_date=end_date,
                    commission_rate=commission,
                    slippage_bps=5,
                    slippage_model="fixed_bps",
                    slippage_tick=0.01,
                    volume_limit_pct=0.05,
                    volume_window=5,
                    max_position_pct=0.20,
                    allow_short=False,
                    source_mode="cache_only",
                    strategy_spec=None,
                    csv_text=None,
                    csv_bars=None,
                    historical_store=historical_store,
                )
                result = _sanitize_floats(result)
                run_id = backtest_archive.save(result, user_id=uid, user_email=uemail)
                m = result.get("metrics", {})
                results.append({
                    "symbol":        sym,
                    "run_id":        run_id,
                    "total_return_pct":   m.get("total_return_pct", 0),
                    "sharpe_ratio":       m.get("sharpe_ratio"),
                    "max_drawdown_pct":   m.get("max_drawdown_pct"),
                    "win_rate":           m.get("win_rate"),
                    "total_trades":       m.get("total_trades", 0),
                    "final_equity":       m.get("final_equity", capital),
                    "profit_factor":      m.get("profit_factor"),
                })
            except (UnknownStrategy, BacktestRunError):
                errors.append({"symbol": sym, "error": "Backtest çalıştırılamadı."})
            except Exception:  # noqa: BLE001
                errors.append({"symbol": sym, "error": "Backtest çalıştırılamadı."})

        results.sort(key=lambda r: r.get("total_return_pct", 0), reverse=True)
        return {"results": results, "errors": errors, "total": len(results), "failed": len(errors)}

    @app.get("/api/backtest/reports", tags=["backtest"])
    def backtest_reports(limit: int = 50, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        return {"reports": backtest_archive.list(limit=limit)}

    @app.get("/api/backtest/reports/{run_id}", tags=["backtest"])
    def backtest_report(run_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        report = backtest_archive.get(run_id)
        if report is None:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")
        return report

    @app.get("/api/backtest/reports/{run_id}/export", tags=["backtest"])
    def backtest_report_export(run_id: str, format: str = "json", user: dict = Depends(get_current_user)) -> Any:
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

    @app.delete("/api/backtest/reports/{run_id}", tags=["backtest"])
    def backtest_report_delete(run_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        deleted = backtest_archive.delete(run_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Backtest raporu bulunamadı.")
        return {"deleted": run_id}

    @app.post("/api/backtest/optimize", tags=["backtest"])
    def backtest_optimize(req: OptimizeRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
            except Exception:  # noqa: BLE001
                errors.append({"params": combo, "error": "Optimizasyon denemesi çalıştırılamadı."})

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

    @app.post("/api/backtest/scan", tags=["backtest"])
    def backtest_scan(req: ScanRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
            except Exception:  # noqa: BLE001
                errors.append({"symbol": symbol, "error": "Backtest taraması çalıştırılamadı."})
        rows.sort(key=lambda row: float(row["score"]), reverse=True)
        return {"scanner_version": "v3", "results": rows, "errors": errors}

    # ── Walk-Forward Analizi ──────────────────────────────────────────────
    @app.post("/api/backtest/walk-forward", tags=["backtest"])
    def backtest_walk_forward(req: WalkForwardRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
    @app.post("/api/backtest/monte-carlo", tags=["backtest"])
    def backtest_monte_carlo(req: MonteCarloRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
    @app.post("/api/backtest/compare", tags=["backtest"])
    def backtest_compare(body: dict[str, Any], user: dict = Depends(get_current_user)) -> dict[str, Any]:
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
    @app.get("/api/technical/{symbol}", tags=["backtest"])
    def get_technical_analysis(symbol: str, interval: str = "1d", user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.get("/api/news", tags=["news"])
    def get_news(
        symbol: str | None = None,
        limit: int = 30,
        fresh: bool = False,
        keyword: str | None = None,
        user: dict | None = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """Haber listesi döndür.

        Plan kapısı:
          - guest (giriş yok): son 5 haber, fresh=false zorlanır
          - free: 20 haber
          - pro/ultra/admin: 100 habere kadar

        ``fresh=true`` ile KAP RSS/borsapy/yfinance zincirinden çekip cache'e yaz.
        ``fresh=false`` (varsayılan) ile SQLite'tan oku.
        """
        # Plan bazlı limit ve fresh kısıtı
        if user is None:
            # Guest — giriş yok; sınırlı erişim, fresh kapalı
            effective_limit = min(limit, 5)
            allow_fresh = False
            plan_note = "guest"
        else:
            role = user.get("role", "free")
            if role in ("pro", "ultra", "admin"):
                effective_limit = min(limit, 100)
            else:
                effective_limit = min(limit, 20)
            allow_fresh = fresh
            plan_note = role

        store = _get_news_store()
        if allow_fresh and symbol:
            from backend.news.news_fetcher import fetch_news_for_symbol
            items = fetch_news_for_symbol(symbol, limit=min(effective_limit, 40))
            if items:
                store.upsert(items)
        news = store.query(symbol=symbol, limit=effective_limit, keyword=keyword)
        unread = store.count_unread(symbol=symbol) if user else 0
        result: dict[str, Any] = {
            "news": news,
            "total": len(news),
            "unread_24h": unread,
            "plan_note": plan_note,
        }
        if not news:
            result["message"] = "Bu sembol için haber bulunamadı." if symbol else "Haber bulunamadı."
        if user is None:
            result["guest_limit_note"] = "Tüm haberleri görmek için giriş yapın."
        return result

    @app.get("/api/news/unread-count", tags=["news"])
    def get_news_unread_count(symbol: str | None = None, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        store = _get_news_store()
        return {"count": store.count_unread(symbol=symbol)}

    @app.post("/api/news/mark-read", tags=["news"])
    def mark_news_read(body: dict[str, Any], user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Haber id listesini okundu olarak işaretle."""
        ids = body.get("ids", [])
        if not isinstance(ids, list):
            raise HTTPException(status_code=422, detail="ids must be a list")
        store = _get_news_store()
        store.mark_read([int(i) for i in ids])
        return {"marked": len(ids), "unread": store.count_unread()}

    @app.get("/api/news/impact/{symbol}", tags=["news"])
    def get_news_impact(
        symbol: str,
        days_before: int = 2,
        days_after: int = 5,
        limit: int = 20,
        user: dict | None = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """
        Haber/KAP olay anı etrafındaki fiyat/hacim hareketi analizi.

        Her olay için:
          - Olay öncesi N bar getirisi
          - Olay sonrası N bar getirisi
          - Etki skoru (sonrası / öncesi oranı)

        Gerçek fiyat verisi yoksa boş event_impacts döndürür.
        Veri mevcut olduğunda event_impacts dolacak.
        """
        import math

        store = _get_news_store()
        news = store.query(symbol=symbol.upper(), limit=limit)
        if not news:
            return {
                "symbol": symbol.upper(),
                "event_impacts": [],
                "note": "Bu sembol için haber verisi yok.",
            }

        # Yfinance'dan son fiyat verisi çek
        price_map: dict[str, float] = {}
        try:
            import yfinance as yf  # type: ignore[import-untyped]
            import datetime as dt
            ticker_sym = f"{symbol.upper()}.IS" if not symbol.upper().endswith(".IS") and len(symbol) <= 7 else symbol.upper()
            ticker = yf.Ticker(ticker_sym)
            hist = ticker.history(period="2y", interval="1d")
            if hist is not None and not hist.empty:
                for ts, row in hist.iterrows():
                    date_str = str(ts)[:10]
                    price_map[date_str] = float(row.get("Close") or 0.0)
        except Exception:
            pass

        impacts = []
        for item in news:
            event_date = item.get("published_at") or item.get("fetched_at") or ""
            event_date = event_date[:10]
            if not event_date or not price_map:
                impacts.append({
                    "news_id": item.get("id"),
                    "event_date": event_date,
                    "headline": item.get("headline", "")[:80],
                    "pre_return_pct": None,
                    "post_return_pct": None,
                    "impact_score": None,
                    "note": "Fiyat verisi yok",
                })
                continue

            # Tarih bazlı fiyat arama
            sorted_dates = sorted(price_map.keys())

            def find_price_n_days(anchor: str, n: int) -> float | None:
                """anchor tarihinden n gün önceki/sonraki ilk mevcut fiyat."""
                try:
                    anchor_dt = dt.date.fromisoformat(anchor)
                    target = (anchor_dt + dt.timedelta(days=n)).isoformat()
                    # En yakın mevcut tarihi bul
                    if n >= 0:
                        candidates = [d for d in sorted_dates if d >= target]
                    else:
                        candidates = [d for d in sorted_dates if d <= target]
                    if candidates:
                        return price_map[candidates[0] if n >= 0 else candidates[-1]]
                    return None
                except Exception:
                    return None

            p_before = find_price_n_days(event_date, -days_before)
            p_event  = find_price_n_days(event_date, 0)
            p_after  = find_price_n_days(event_date, days_after)

            pre_ret: float | None = None
            post_ret: float | None = None
            impact_score: float | None = None

            if p_before and p_event and p_before > 0:
                pre_ret = round((p_event - p_before) / p_before * 100, 3)
            if p_event and p_after and p_event > 0:
                post_ret = round((p_after - p_event) / p_event * 100, 3)
            if pre_ret is not None and post_ret is not None:
                # Etki skoru: haber sonrası hareket büyüklüğü / öncesi hareket
                pre_abs = abs(pre_ret) if pre_ret else 0.001
                impact_score = round(abs(post_ret) / pre_abs, 2)

            impacts.append({
                "news_id":       item.get("id"),
                "event_date":    event_date,
                "headline":      item.get("headline", "")[:80],
                "pre_return_pct": pre_ret,
                "post_return_pct": post_ret,
                "impact_score":  impact_score,
                "price_before":  round(p_before, 4) if p_before else None,
                "price_event":   round(p_event, 4) if p_event else None,
                "price_after":   round(p_after, 4) if p_after else None,
            })

        return {
            "symbol": symbol.upper(),
            "event_impacts": impacts,
            "days_before": days_before,
            "days_after": days_after,
        }

    # ── Piyasa Olayları (events) ──────────────────────────────────────────────

    _event_store_instance = None

    def _get_event_store():
        nonlocal _event_store_instance
        if _event_store_instance is None:
            from backend.events.event_store import EventStore
            import os
            db_path = os.environ.get("EVENT_DB_PATH", "db/market_events.db")
            _event_store_instance = EventStore(db_path)
        return _event_store_instance

    @app.get("/api/events", tags=["events"])
    def get_events(
        symbol: str | None = None,
        event_types: str | None = None,      # virgülle ayrılmış: kap,earnings,dividend
        from_date: str | None = None,        # YYYY-MM-DD
        to_date: str | None = None,          # YYYY-MM-DD
        limit: int = 50,
        fresh: bool = False,
        confirmed_only: bool = False,
        user: dict | None = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """
        Piyasa olaylarını döndür: KAP bildirimleri, bilanço, temettü, ekonomik takvim.

        Plan kapısı:
          - guest: yalnızca ekonomik takvim (global)
          - free: sembol bazlı 20 olay
          - pro/ultra/admin: 200 olaya kadar, fresh destekli
        """
        # Plan bazlı kısıt
        if user is None:
            # Guest — yalnızca ekonomik takvim
            et_list = ["economic"]
            effective_limit = 20
            allow_fresh = False
            symbol = None  # Sembol bazlı filtreleme yok
        else:
            role = user.get("role", "free")
            et_list = [t.strip() for t in event_types.split(",")] if event_types else []
            effective_limit = min(limit, 200 if role in ("pro", "ultra", "admin") else 50)
            allow_fresh = fresh and role in ("pro", "ultra", "admin")

        store = _get_event_store()

        # Fresh mod: verilen sembol için kaynaktan çek
        if allow_fresh and symbol:
            from backend.events.event_fetcher import fetch_events_for_symbol
            fetched = fetch_events_for_symbol(symbol, limit=min(effective_limit, 50))
            if fetched:
                store.upsert(fetched)

        events = store.query(
            symbol=symbol,
            event_types=et_list if et_list else None,
            from_date=from_date,
            to_date=to_date,
            limit=effective_limit,
            confirmed_only=confirmed_only,
        )

        result: dict[str, Any] = {
            "events": events,
            "total": len(events),
        }
        if not events:
            result["message"] = (
                "Bu sembol için olay bulunamadı." if symbol
                else "Belirtilen tarih aralığında olay yok."
            )
        if user is None:
            result["guest_note"] = "Hisse olaylarını görmek için giriş yapın."

        return result

    @app.get("/api/events/upcoming", tags=["events"])
    def get_upcoming_events(
        days: int = 30,
        limit: int = 20,
        user: dict | None = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """Önümüzdeki N günün olaylarını döndür (ekonomik takvim dahil)."""
        store = _get_event_store()
        events = store.upcoming(days=days, limit=limit)
        return {"events": events, "total": len(events), "days": days}

    @app.post("/api/events/fetch", tags=["events"])
    def fetch_symbol_events(
        body: dict[str, Any],
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Sembol için olay verisi çek ve depoya yaz (Pro+ planı gerekli)."""
        role = user.get("role", "free")
        if role not in ("pro", "ultra", "admin"):
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "PLAN_LIMIT",
                    "tr": "Olay veri çekimi Pro veya Ultra planında mevcut.",
                    "en": "Event data fetch requires Pro or Ultra plan.",
                },
            )
        symbol = str(body.get("symbol") or "").upper().strip()
        if not symbol:
            raise HTTPException(status_code=422, detail="symbol gerekli")

        from backend.events.event_fetcher import fetch_events_for_symbol
        store = _get_event_store()
        fetched = fetch_events_for_symbol(symbol, limit=100)
        count = store.upsert(fetched) if fetched else 0
        return {"symbol": symbol, "fetched": len(fetched), "upserted": count}

    @app.get("/api/strategy-lab/strategies", tags=["strategy-lab"])
    def strategy_lab_list(user: dict = Depends(get_current_user)) -> dict[str, Any]:
        records = strategy_store.list_strategies()
        return {"strategies": [_strategy_record_payload(r) for r in records]}

    @app.get("/api/strategy-lab/strategies/{record_id}", tags=["strategy-lab"])
    def strategy_lab_get(record_id: int, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        record = strategy_store.get_strategy(record_id)
        if record is None:
            raise HTTPException(status_code=404, detail="Strateji kaydı bulunamadı.")
        return _strategy_record_payload(record)

    @app.post("/api/strategy-lab/strategies", tags=["strategy-lab"])
    def strategy_lab_save(req: StrategySaveRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.post("/api/strategy-lab/pack/export", tags=["strategy-lab"])
    def strategy_pack_export(req: StrategyPackExportRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        try:
            pack = export_strategy_pack(
                req.strategy_spec,
                params=req.params,
                indicator_set=req.indicator_set,
                risk_settings=req.risk_settings,
                description=req.description,
                example_backtest_metadata=req.example_backtest_metadata,
            )
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz strateji paketi.")
        return {"filename": ".piyasapilot-strategy.json", "pack": pack}

    @app.post("/api/strategy-lab/pack/import", tags=["strategy-lab"])
    def strategy_pack_import(req: StrategyPackImportRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        try:
            pack = import_strategy_pack(req.pack)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz strateji paketi.")
        return {"pack": pack}

    @app.post("/api/strategy-lab/strategies/{record_id}/paper/activate", tags=["strategy-lab"])
    def strategy_lab_activate_paper(record_id: int, req: PaperActivateRequest, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.delete("/api/strategy-lab/strategies/{record_id}", tags=["strategy-lab"])
    def strategy_lab_delete_strategy(record_id: int, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        ok = strategy_store.delete_strategy(record_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Strateji kaydı bulunamadı.")
        return {"status": "ok", "id": record_id}

    @app.post("/api/strategy-lab/paper/{activation_id}/deactivate", tags=["strategy-lab"])
    def strategy_lab_deactivate_paper(activation_id: int, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        ok = strategy_store.deactivate_paper(activation_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Paper aktivasyonu bulunamadı.")
        return {"status": "ok", "activation_id": activation_id, "active": False}

    @app.get("/api/strategy-lab/paper", tags=["strategy-lab"])
    def strategy_lab_paper_activations(active_only: bool = False, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        return {
            "activations": [
                asdict(a) for a in strategy_store.list_paper_activations(active_only=active_only)
            ]
        }

    @app.post("/api/backtest/reports/{run_id}/paper/activate", tags=["paper-trading"])
    def backtest_report_activate_paper(run_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.get("/api/paper/wallets", tags=["paper-trading"])
    def paper_wallets(user: dict = Depends(get_current_user)) -> dict[str, Any]:
        return {"wallets": paper_db.all_wallets()}

    @app.get("/api/paper/trades", tags=["paper-trading"])
    def paper_trades(strategy_id: str = "", limit: int = 50, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        sid = strategy_id or None
        return {"trades": paper_db.get_trades(sid, limit=limit)}

    @app.get("/api/paper/positions", tags=["paper-trading"])
    def paper_positions(strategy_id: str = "", user: dict = Depends(get_current_user)) -> dict[str, Any]:
        sid = strategy_id or None
        return {"positions": paper_db.get_positions(sid)}

    @app.get("/api/paper/trades/export", tags=["paper-trading"])
    def paper_trades_export(strategy_id: str = "", user: dict = Depends(get_current_user)) -> dict[str, Any]:
        sid = strategy_id or None
        return {"trades": paper_db.export_trades(sid)}

    @app.get("/api/paper/equity", tags=["paper-trading"])
    def paper_equity(strategy_id: str, limit: int = 200, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        return {"equity_curve": paper_db.get_equity_curve(strategy_id, limit=limit)}

    @app.post("/api/paper/reset/{strategy_id}", tags=["paper-trading"], dependencies=[Depends(require_paper_trading)])
    def paper_reset(strategy_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        paper_db.reset_wallet(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id}

    @app.post("/api/paper/halt/{strategy_id}", tags=["paper-trading"], dependencies=[Depends(require_paper_trading)])
    def paper_halt(strategy_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        paper_db.halt_strategy(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id, "halted": True}

    @app.post("/api/paper/resume/{strategy_id}", tags=["paper-trading"], dependencies=[Depends(require_paper_trading)])
    def paper_resume(strategy_id: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        paper_db.resume_strategy(strategy_id)
        return {"status": "ok", "strategy_id": strategy_id, "halted": False}

    @app.get("/api/paper/mtm", tags=["paper-trading"])
    def paper_mtm(strategy_id: str = "", user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Açık pozisyonları mark-to-market değeriyle döndürür.

        Her pozisyon için:
        - entry_price, quantity, opened_at
        - current_price: cache'ten son 1d kapanış fiyatı (yoksa entry_price)
        - unrealized_pnl: (current_price - entry_price) * quantity
        - unrealized_pnl_pct: % fark
        """
        sid = strategy_id or None
        positions = paper_db.get_positions(sid)

        result = []
        for pos in positions:
            sym         = str(pos["symbol"]).upper()
            entry_price = float(pos["entry_price"])
            quantity    = float(pos["quantity"])

            # En güncel fiyat: cache'ten son bar
            bar = cache.latest_bar(sym, "1d") or cache.latest_bar(sym, "1h")
            if bar:
                current_price = float(bar["close"])
            else:
                current_price = entry_price

            unrealized_pnl = (current_price - entry_price) * quantity
            unrealized_pnl_pct = (
                ((current_price - entry_price) / entry_price * 100)
                if entry_price > 0 else 0.0
            )

            result.append({
                "strategy_id":        pos["strategy_id"],
                "symbol":             sym,
                "trade_id":           pos["trade_id"],
                "entry_price":        round(entry_price, 6),
                "current_price":      round(current_price, 6),
                "quantity":           round(quantity, 6),
                "position_value":     round(current_price * quantity, 4),
                "cost_basis":         round(entry_price * quantity, 4),
                "unrealized_pnl":     round(unrealized_pnl, 4),
                "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
                "opened_at":          pos["opened_at"],
                "updated_at":         pos.get("updated_at"),
            })

        total_unrealized = round(sum(r["unrealized_pnl"] for r in result), 4)
        total_value      = round(sum(r["position_value"]  for r in result), 4)

        return {
            "positions":       result,
            "total_unrealized_pnl": total_unrealized,
            "total_position_value": total_value,
            "position_count":  len(result),
            "fetched_at":      _utc_iso(),
        }

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


    # ── Piyasa Genel Görünümü ─────────────────────────────────────────────────
    @app.get("/api/market/overview", tags=["market"])
    def market_overview() -> dict:
        """BIST, döviz, kripto, emtia genel görünümü. Auth gerekmez."""
        _GROUPS: list[tuple[str, str, str]] = [
            # (group, symbol, label)
            ("bist",        "XU100.IS",  "BIST 100"),
            ("bist",        "XU030.IS",  "BIST 30"),
            ("forex",       "USDTRY=X",  "USD/TRY"),
            ("forex",       "EURTRY=X",  "EUR/TRY"),
            ("commodities", "GC=F",      "Altın"),
            ("commodities", "BZ=F",      "Brent"),
            ("crypto",      "BTCUSDT",   "BTC/USDT"),
            ("crypto",      "ETHUSDT",   "ETH/USDT"),
            ("global",      "SPY",       "S&P 500 (SPY)"),
        ]

        now_ts = dt.datetime.now(dt.timezone.utc)
        result: dict[str, Any] = {
            "bist": [],
            "forex": [],
            "crypto": [],
            "commodities": [],
            "global": [],
            "fetched_at": _utc_iso(),
            "data_note": "Veriler gecikmeli olabilir — yatırım tavsiyesi değildir",
        }

        for group, symbol, label in _GROUPS:
            if group == "bist" and not _bist_feed_configured():
                result[group].append({
                    "symbol": symbol,
                    "label": label,
                    "last": None,
                    "change_pct": None,
                    "fetched_at": None,
                    "quality": "license_pending",
                    "message": "BIST verileri lisanslı sağlayıcı bağlantısı tamamlanana kadar kapalıdır.",
                })
                continue
            bar = cache.latest_bar(symbol, "1d")
            if bar is None:
                entry: dict[str, Any] = {
                    "symbol": symbol,
                    "label": label,
                    "last": None,
                    "change_pct": None,
                    "fetched_at": None,
                    "quality": "unknown",
                }
            else:
                bar_time = dt.datetime.fromtimestamp(int(bar["time"]), tz=dt.timezone.utc)
                age_hours = (now_ts - bar_time).total_seconds() / 3600
                quality = "stale" if age_hours > 24 else "ok"

                # change_pct: son 2 bar gerekir
                prev_bars = cache.get_window(symbol, "1d", limit=2)
                change_pct: float | None = None
                if prev_bars and len(prev_bars) >= 2:
                    prev_close = float(prev_bars[-2]["close"])
                    last_close = float(bar["close"])
                    if prev_close > 0:
                        change_pct = round((last_close - prev_close) / prev_close * 100, 4)

                entry = {
                    "symbol": symbol,
                    "label": label,
                    "last": round(float(bar["close"]), 4),
                    "change_pct": change_pct,
                    "fetched_at": bar_time.isoformat(),
                    "quality": quality,
                }
            result[group].append(entry)

        return result

    @app.get("/api/market/regime", tags=["market"])
    def market_regime() -> dict[str, Any]:
        """Piyasa rejim skoru — BIST 100 + kripto benchmark.

        Skor 0–100 arası:  0=güçlü düşüş, 100=güçlü yükseliş.
        Bileşenler:
          - RSI(14) konumu (30→ 50→ 70 bandı)
          - EMA trend (fiyat>EMA200)
          - ADX güç (>25 = trend var)
          - Volatilite (ATR/fiyat — yüksek vol skor azaltır)
          - BIST30 breadth (% of stocks > SMA50)
        """
        import numpy as np
        from backend.data.constants import VALID_INTERVALS_SET  # noqa: F401

        def _calc_rsi(arr: list[float], p: int = 14) -> float | None:
            if len(arr) < p + 1:
                return None
            a = np.array(arr, dtype=float)
            d = np.diff(a)
            g = np.where(d > 0, d, 0.0)
            l_ = np.where(d < 0, -d, 0.0)
            ag = float(np.mean(g[:p])); al = float(np.mean(l_[:p]))
            for i in range(p, len(d)):
                ag = (ag * (p - 1) + g[i]) / p
                al = (al * (p - 1) + l_[i]) / p
            return round(100 - 100 / (1 + ag / al), 2) if al > 0 else 100.0

        def _calc_ema(arr: list[float], p: int) -> float | None:
            if len(arr) < p:
                return None
            k = 2 / (p + 1)
            ema = sum(arr[:p]) / p
            for v in arr[p:]:
                ema = v * k + ema * (1 - k)
            return ema

        def _calc_atr(bars: list[dict], p: int = 14) -> float | None:
            if len(bars) < p + 1:
                return None
            trs = []
            for i in range(1, len(bars)):
                h = float(bars[i]["high"]); l = float(bars[i]["low"]); pc = float(bars[i - 1]["close"])
                trs.append(max(h - l, abs(h - pc), abs(l - pc)))
            atr = sum(trs[:p]) / p
            for tr in trs[p:]:
                atr = (atr * (p - 1) + tr) / p
            return atr

        BENCHMARK = "BTCUSDT"  # BIST'e lisans olmadığında kripto benchmark
        bars = cache.get_window(BENCHMARK, "1d", limit=300) or []
        scores: dict[str, int] = {}
        details: dict[str, Any] = {}

        if bars and len(bars) >= 20:
            closes = [float(b["close"]) for b in bars]
            last   = closes[-1]

            # RSI bileşeni (0-30)
            rsi = _calc_rsi(closes, 14)
            if rsi is not None:
                rsi_score = max(0, min(30, int((rsi - 30) / 40 * 30))) if rsi > 30 else 0
                scores["rsi"] = rsi_score
                details["rsi_14"] = round(rsi, 1)

            # EMA200 trendi (0-25)
            ema200 = _calc_ema(closes, 200)
            if ema200:
                scores["ema_trend"] = 25 if last > ema200 else 0
                details["ema_200"] = round(ema200, 4)
                details["above_ema200"] = last > ema200

            # EMA50 (0-15)
            ema50 = _calc_ema(closes, 50)
            if ema50:
                scores["ema_50_trend"] = 15 if last > ema50 else 0
                details["ema_50"] = round(ema50, 4)

            # ATR volatilite baskısı (0-15 ters)
            atr = _calc_atr(bars, 14)
            if atr and last > 0:
                atr_pct = (atr / last) * 100
                vol_score = max(0, 15 - int(atr_pct * 1.5))
                scores["volatility"] = vol_score
                details["atr_pct"] = round(atr_pct, 2)

            # SMA50 üstünde fiyat trendi — son 5/20 bar momentum (0-15)
            if len(closes) >= 20:
                momentum = (closes[-1] - closes[-20]) / closes[-20] * 100 if closes[-20] > 0 else 0
                scores["momentum"] = max(0, min(15, int(momentum * 3 + 7.5)))
                details["momentum_20d_pct"] = round(momentum, 2)
        else:
            details["note"] = "Yeterli bar verisi yok"

        total_score = min(100, max(0, sum(scores.values())))
        if total_score >= 70:
            regime = "güçlü_yükseliş"
            regime_en = "strong_bull"
        elif total_score >= 55:
            regime = "yükseliş"
            regime_en = "bull"
        elif total_score >= 45:
            regime = "yatay"
            regime_en = "sideways"
        elif total_score >= 30:
            regime = "düşüş"
            regime_en = "bear"
        else:
            regime = "güçlü_düşüş"
            regime_en = "strong_bear"

        return {
            "score":          total_score,
            "regime":         regime,
            "regime_en":      regime_en,
            "benchmark":      BENCHMARK,
            "components":     scores,
            "details":        details,
            "max_score":      100,
            "interpretation": {
                "0-30":   "Güçlü düşüş trendi — riskten kaçınma yüksek",
                "30-45":  "Düşüş trendi — savunmacı pozisyon",
                "45-55":  "Yatay / belirsiz piyasa",
                "55-70":  "Yükseliş trendi — seçici fırsatlar",
                "70-100": "Güçlü yükseliş trendi — risk iştahı yüksek",
            },
            "disclaimer": "Rejim skoru geçmiş fiyat verisine dayalı teknik analizdir; yatırım tavsiyesi değildir.",
            "fetched_at": _utc_iso(),
        }

    # ── Sinyal Güven Durumu ───────────────────────────────────────────────────
    @app.get("/api/signals/trust-status", tags=["signals"])
    def signals_trust_status(user: dict = Depends(get_current_user)) -> dict:
        """BIST veri güven engelinin kullanıcıya gösterilmesi."""
        stats = signal_generator.stats()
        skipped = int(stats.get("skipped_untrusted", 0))
        emitted = int(stats.get("signals_emitted", 0))
        last_skip = stats.get("last_skip_reason")
        trust_blocked = skipped > 0
        return {
            "signals_emitted": emitted,
            "skipped_untrusted": skipped,
            "trust_blocked": trust_blocked,
            "block_reason": (
                last_skip
                if last_skip
                else ("Yahoo Finance BIST verisi güvenilir işaretlenmedi" if trust_blocked else None)
            ),
            "provider": "yahoo_finance",
            "suggestion": (
                "Lisanslı veri sağlayıcısı bağlanmadığında BIST sinyalleri bloklanır."
                if trust_blocked
                else "Sinyal akışı normal."
            ),
            "fetched_at": _utc_iso(),
        }

    @app.get("/api/workspace")
    def workspace() -> dict[str, Any]:
        return workspace_store.load()

    # ── Veri Lisansı Matrisi ─────────────────────────────────────────────────
    @app.get("/api/data/license-matrix", tags=["data"])
    def data_license_matrix(user: dict = Depends(get_current_user)) -> dict:
        """
        Provider/piyasa/veri tipi kombinasyonları için lisans matrisini döner.
        Redistribution, export, cache süresi ve kullanıcı planı kısıtlarını içerir.
        """
        from backend.data.license_matrix import license_matrix
        return {
            "entries": license_matrix.as_dict(),
            "principles": [
                "Lisansı olmayan veri ücretli özellik gibi paketlenemez.",
                "Export/paylaşım lisans matrisine göre sınırlandırılır.",
                "Bilinmeyen lisans kombinasyonlarında kısıtlayıcı varsayılan uygulanır.",
                "Redis cache kayıtları orijinal provider lisansına tabidir.",
            ],
            "fetched_at": _utc_iso(),
        }

    # ── Depolama Katmanı Politikası ──────────────────────────────────────────
    @app.get("/api/data/storage-policy", tags=["data"])
    def storage_policy(user: dict = Depends(get_current_user)) -> dict:
        """
        ClickHouse / MySQL / Redis katman ayrımı politikasını döner.
        Her kategorinin hangi storage'a yazılabileceğini gösterir.
        """
        from backend.data.storage_layer_guard import StorageLayerGuard
        return {
            "policy": StorageLayerGuard.policy_summary(),
            "description": {
                "clickhouse": "OHLCV bar, tick, büyük zaman serisi, kalite olayları",
                "mysql":      "Sembol metadata, kullanıcı, plan, alarm, envanter, lisans",
                "redis":      "Sıcak cache, pub/sub, distributed lock, kısa ömürlü snapshot",
            },
            "rules": [
                "Zaman serisi (OHLCV) hiçbir zaman MySQL'e yazılmaz",
                "Kullanıcı/plan bilgisi hiçbir zaman ClickHouse'a yazılmaz",
                "Redis kalıcı truth source olarak kullanılamaz — her key TTL taşımalı",
                "Provider sessizce değişemez — her geçiş loglanır ve UI'ya iletilir",
            ],
            "fetched_at": _utc_iso(),
        }

    # ── Fiyat Uyarıları ──────────────────────────────────────────────────────

    def _pa_connect() -> "sqlite3.Connection":
        import sqlite3 as _sq3
        from pathlib import Path as _P
        p = _P(_PRICE_ALERTS_DB_PATH)
        p.parent.mkdir(parents=True, exist_ok=True)
        conn = _sq3.connect(str(p))
        conn.row_factory = _sq3.Row
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS price_alerts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol     TEXT NOT NULL,
                target     REAL NOT NULL,
                direction  TEXT NOT NULL,
                triggered  INTEGER NOT NULL DEFAULT 0,
                note       TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );""")
        return conn

    @app.get("/api/alerts/price", tags=["alerts"])
    def list_price_alerts(symbol: str | None = None, active_only: bool = True, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        with _pa_connect() as conn:
            q = "SELECT * FROM price_alerts"
            args: list[Any] = []
            clauses: list[str] = []
            if active_only:
                clauses.append("triggered=0")
            if symbol:
                clauses.append("symbol=?")
                args.append(symbol.upper())
            if clauses:
                q += " WHERE " + " AND ".join(clauses)
            q += " ORDER BY created_at DESC LIMIT 100"
            rows = conn.execute(q, args).fetchall()
        return {"alerts": [dict(r) for r in rows]}

    @app.post("/api/alerts/price", tags=["alerts"])
    def create_price_alert(body: dict[str, Any], user: dict = Depends(get_current_user)) -> dict[str, Any]:
        symbol = str(body.get("symbol", "")).upper()
        target = body.get("target")
        direction = str(body.get("direction", "above"))
        note = str(body.get("note", ""))
        if not symbol or target is None:
            raise HTTPException(status_code=422, detail="symbol ve target zorunludur.")
        if direction not in ("above", "below"):
            raise HTTPException(status_code=422, detail="direction 'above' veya 'below' olmalı.")
        with _pa_connect() as conn:
            cur = conn.execute(
                "INSERT INTO price_alerts (symbol, target, direction, note) VALUES (?,?,?,?)",
                (symbol, float(target), direction, note),
            )
            conn.commit()
            alert_id = cur.lastrowid
        return {"id": alert_id, "symbol": symbol, "target": target, "direction": direction}

    @app.delete("/api/alerts/price/{alert_id}", tags=["alerts"])
    def delete_price_alert(alert_id: int, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        with _pa_connect() as conn:
            conn.execute("DELETE FROM price_alerts WHERE id=?", (alert_id,))
            deleted = conn.execute("SELECT changes()").fetchone()[0]
            conn.commit()
        if not deleted:
            raise HTTPException(status_code=404, detail="Uyarı bulunamadı.")
        return {"deleted": alert_id}

    @app.post("/api/paper/signal", tags=["paper-trading"], dependencies=[Depends(require_paper_trading)])
    async def paper_signal(request: Request, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        try:
            trade = paper_recorder.record_signal(payload)
            # ── Audit log ──────────────────────────────────────────────────
            try:
                from backend.audit import audit_logger, AuditEvent, AuditAction
                await audit_logger.log(AuditEvent(
                    action=AuditAction.PAPER_ORDER_SUBMIT,
                    user_id=int(user.get("id", 0)) or None,
                    resource=str(payload.get("symbol", "")),
                    metadata={
                        "direction": payload.get("direction"),
                        "strategy": payload.get("strategy_id"),
                        "price": payload.get("price"),
                    },
                ))
            except Exception:
                pass
            return {
                "status": "ok",
                "message": "Sanal paper trade gerçek son fiyatla kaydedildi.",
                "trade": trade,
            }
        except Exception:
            raise HTTPException(status_code=400, detail="Paper trade kaydedilemedi.")

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
        canonical_input = symbol.strip().upper()
        if not re.fullmatch(r"[A-Z0-9][A-Z0-9._:=-]{0,63}", canonical_input):
            raise HTTPException(
                status_code=400,
                detail={"code": "invalid_symbol", "message": "Geçersiz veya boş sembol."},
            )
        symbol = canonical_input

        try:
            safe_limit = max(1, min(int(limit), 5000))
        except (TypeError, ValueError):
            safe_limit = 500

        # Interval doğrulaması — merkezi VALID_INTERVALS_SET kullanılır
        if interval.strip().lower() not in VALID_INTERVALS_SET:
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "invalid_interval",
                    "message": f"Geçersiz zaman dilimi: '{interval}'. "
                               f"Desteklenenler: 1m, 5m, 15m, 30m, 1h, 2h, 4h, 1d, 1w, 1mo",
                },
            )

        if symbol.strip():
            restricted_payload = _license_restricted_payload(symbol, interval)
            if restricted_payload is not None:
                return JSONResponse(
                    restricted_payload,
                    headers={"X-Data-Source": "license_pending"},
                )

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
                        "is_live": False,
                        "is_delayed": True,
                        "delay_minutes": 15,
                        "status": "ok",
                        "fetched_at": _utc_iso(),
                        "quality_status": "ok",
                        "coverage_pct": 100.0,
                        "provider": repo_result.source,
                        "staleness_seconds": 0,
                        "license_note": "Gecikmeli veri — yatırım tavsiyesi değildir",
                        "warnings": [],
                    },
                }, headers={"X-Data-Source": repo_result.source})

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
                local_payload["metadata"].setdefault("source", "local_parquet")
                local_payload["metadata"].update({
                    "is_real": True,
                    "is_live": False,
                    "is_delayed": True,
                    "delay_minutes": 15,
                    "fetched_at": _utc_iso(),
                    "quality_status": "ok",
                    "coverage_pct": 100.0,
                    "provider": local_payload["metadata"].get("source", "local_parquet"),
                    "staleness_seconds": 0,
                    "license_note": "Gecikmeli veri — yatırım tavsiyesi değildir",
                    "warnings": [],
                })
                return JSONResponse(local_payload, headers={"X-Data-Source": "local_parquet"})

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
            metadata = provider_payload.setdefault("metadata", {})
            provider_source = metadata.get("provider") or metadata.get("provider_name") or "provider"
            is_real_provider = bool(metadata.get("is_real", False))
            if market_data_facade is not None:
                market_data_facade.write_candles(
                    canonical_symbol,
                    interval,
                    cleaned,
                    source=str(provider_source),
                    limit=safe_limit,
                )
            provider_payload["bars"] = cleaned
            metadata["spike_filter"] = {
                "total": report.total_bars,
                "winsorized": report.winsorized,
                "untouched_high_volume": report.untouched_high_volume,
            }
            metadata["cache"] = "miss_then_write"
            metadata.update({
                "is_real": is_real_provider,
                "is_live": False,
                "is_delayed": True,
                "delay_minutes": 15,
                "fetched_at": _utc_iso(),
                "quality_status": "ok" if is_real_provider else "warning",
                "coverage_pct": 100.0,
                "provider": str(provider_source),
                "staleness_seconds": 0,
                "source_type": "licensed" if is_real_provider else "public_unverified",
                "license_note": (
                    "Lisanslı/kaynaktan veri — yatırım tavsiyesi değildir"
                    if is_real_provider
                    else "Lisans bilgisi doğrulanmadı; yatırım tavsiyesi değildir"
                ),
                "warnings": [] if is_real_provider else ["Veri lisansı doğrulanmadı"],
            })
            return JSONResponse(provider_payload, headers={"X-Data-Source": str(provider_source)})

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
                    "source": "cache-legacy",
                    "is_real": False,
                    "is_live": False,
                    "is_delayed": True,
                    "delay_minutes": 15,
                    "status": "stale",
                    "fetched_at": _utc_iso(),
                    "quality_status": "warning",
                    "coverage_pct": 100.0,
                    "provider": "cache-legacy",
                    "staleness_seconds": -1,
                    "license_note": "Gecikmeli veri — yatırım tavsiyesi değildir",
                    "warnings": ["Provider gecikmeli yanıt"],
                    "provider_error": provider_payload.get("metadata", {}).get("error", ""),
                },
            }, headers={"X-Data-Source": "cache-legacy"})

        # Veri yok / lisanslı kaynak yok durumları gateway hatası değildir.
        # Payload status alanı üst katmana nedeni taşır; HTTP 200 canlılık
        # ve stres testlerinde altyapı hatasıyla veri yokluğunu ayırır.
        if provider_payload.get("status") in {"no_data", "not_configured"}:
            return JSONResponse(provider_payload)

        # Hem provider hem cache boş ve gerçek provider hatası var.
        return JSONResponse(provider_payload, status_code=502)

    # ── Mali Analiz API v2 — gerçek borsapy verisi ──────────────────────────
    @app.get("/api/mali-analiz/universe", tags=["financials"])
    def get_mali_analiz_universe(scope: str = "bist30", user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.get("/api/mali-analiz/alerts", tags=["financials"])
    def get_mali_analiz_alerts(
        symbol: str | None = None,
        limit: int = 50,
        unread_only: bool = False,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Direktif ve uyarıları döndürür."""
        if not _financial_repository_ref:
            return {"alerts": [], "source": "no_db"}
        rows = _financial_repository_ref.get_alerts(symbol=symbol, limit=limit, unread_only=unread_only)
        return {"alerts": _serialize_rows(rows), "total": len(rows)}

    @app.post("/api/mali-analiz/alerts/mark-read", tags=["financials"])
    def mark_mali_analiz_alerts_read(body: dict[str, Any], user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Belirtilen uyarıları okundu olarak işaretle."""
        ids = [int(i) for i in body.get("ids", [])]
        if _financial_repository_ref and ids:
            _financial_repository_ref.mark_alerts_read(ids)
        return {"marked": len(ids)}

    @app.post("/api/mali-analiz/refresh", tags=["financials"])
    async def refresh_mali_analiz_all(
        symbols: list[str] | None = None,
        user: dict = Depends(get_current_user),
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

    @app.post("/api/mali-analiz/recompute", tags=["financials"])
    async def recompute_mali_analiz_all(user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    @app.post("/api/mali-analiz/{symbol}/recompute", tags=["financials"])
    async def recompute_mali_analiz_symbol(symbol: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Tek sembol için stored data'dan oran yeniden hesaplama."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
        if not _financial_repository_ref:
            raise HTTPException(status_code=503, detail="Finansal repository hazır değil")
        import asyncio as _aio
        result = await _aio.get_event_loop().run_in_executor(
            None, recompute_ratios_from_stored, normalized, _financial_repository_ref
        )
        return {"symbol": normalized, "status": result}

    @app.post("/api/mali-analiz/{symbol}/refresh", tags=["financials"])
    async def refresh_mali_analiz_symbol(symbol: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Tek sembol için veri yenileme tetikler."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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

    @app.get("/api/mali-analiz/{symbol}/balance-sheet", tags=["financials"])
    def get_balance_sheet(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Bilanço verisi — satır × dönem pivot tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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

    @app.get("/api/mali-analiz/{symbol}/income-stmt", tags=["financials"])
    def get_income_stmt(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Gelir tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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

    @app.get("/api/mali-analiz/{symbol}/cashflow", tags=["financials"])
    def get_cashflow(
        symbol: str,
        period_type: str = "quarterly",
        limit: int = 20,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Nakit akışı tablosu."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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

    @app.get("/api/mali-analiz/{symbol}/ratios", tags=["financials"])
    def get_symbol_ratios(
        symbol: str,
        limit: int = 12,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Hesaplanmış finansal oranlar."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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

    @app.get("/api/mali-analiz/{symbol}/summary", tags=["financials"])
    def get_symbol_summary(symbol: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """Özet + direktifler."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
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
    @app.get("/api/mali-analiz/{symbol}/reports", tags=["financials"])
    def get_mali_analiz_reports(symbol: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
        periods: list[str] = []
        if _financial_repository_ref:
            periods = _financial_repository_ref.get_available_periods(normalized, "quarterly")
        # Convert available periods to report-style entries for the frontend
        reports = [
            {
                "title": f"{normalized} — {p} Çeyreklik Finansal Rapor",
                "period": p,
                "published_at": None,
                "url": None,
                "source": "borsapy / isyatirim.com",
            }
            for p in periods
        ]
        return {
            "symbol": normalized,
            "periods": periods,
            "reports": reports,
            "source": "borsapy",
        }

    @app.get("/api/mali-analiz/{symbol}/events", tags=["financials"])
    def get_mali_analiz_events(symbol: str, user: dict = Depends(get_current_user)) -> dict[str, Any]:
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
        alerts: list[Any] = []
        if _financial_repository_ref:
            alerts = _financial_repository_ref.get_alerts(symbol=normalized, limit=100)
        # Deduplicate: keep only the most recent alert per (alert_type, period) combination
        seen: set[tuple[str, str]] = set()
        deduped: list[Any] = []
        for a in _serialize_rows(alerts):
            key = (str(a.get("alert_type", "")), str(a.get("period", "")))
            if key not in seen:
                seen.add(key)
                deduped.append(a)
        return {"symbol": normalized, "events": deduped, "source": "borsapy"}

    @app.get("/api/mali-analiz/{symbol}/metric-history", tags=["financials"])
    def get_mali_analiz_metric_history(
        symbol: str,
        metric: str = "net_income",
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Metrik geçmişi kontratı; finansal seri bağlanana kadar boş döner."""
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")
        if not _financial_repository_ref:
            return {"symbol": normalized, "metric": metric, "points": [], "source": "no_db"}
        ratios = _financial_repository_ref.get_computed_ratios(normalized, ratio_keys=[metric])
        points = [
            {"period": r["period"], "value": float(r["value"]) if r["value"] is not None else None}
            for r in ratios
        ]
        return {"symbol": normalized, "metric": metric, "points": points, "source": "borsapy"}

    @app.get("/api/mali-analiz/{symbol}/chart-data", tags=["financials"])
    def get_mali_analiz_chart_data(
        symbol: str,
        limit: int = 16,
        user: dict = Depends(get_current_user),
    ) -> dict[str, Any]:
        """Lightweight-charts için finansal zaman serisi döner.

        Her metrik: [{period, time_iso, value}] (kronolojik, eskiden yeniye)
        time_iso: lightweight-charts'ın kabul ettiği 'YYYY-MM-DD' formatında.
        """
        try:
            normalized = normalize_symbol(symbol)
        except ValueError:
            raise HTTPException(status_code=400, detail="Geçersiz sembol.")

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

    @app.get("/api/mali-analiz/comparison", tags=["financials"])
    def get_mali_analiz_comparison(user: dict = Depends(get_current_user)) -> dict[str, Any]:
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

    # ── Kullanıcı plan limitleri ──────────────────────────────────────────
    @app.get("/api/me/limits", tags=["auth"])
    def get_user_limits(user: dict = Depends(get_current_user)) -> dict:
        """Kullanıcının plan limitlerini döndür — frontend tek kaynaktan okur."""
        from backend.auth.feature_gate import get_quota, can_access
        role = user.get("role", "free")
        return {
            "role": role,
            "limits": {
                "backtest_runs_per_day": get_quota(role, "backtest_runs_per_day"),
                "screener_runs_per_day": get_quota(role, "signals_per_day"),
                "watchlist_symbols": get_quota(role, "max_watchlist_symbols"),
                "news_access": can_access(role, "terminal_access"),
                "signals_access": can_access(role, "signals_per_day"),
                "paper_trading": get_quota(role, "max_paper_accounts") != 0,
                "scanner": can_access(role, "scanner"),
                "backtest_pro": can_access(role, "backtest_pro"),
                "multi_chart": can_access(role, "multi_chart"),
                "mali_analiz_scope": get_quota(role, "mali_analiz_scope"),
            },
        }

    # ── Screener ──────────────────────────────────────────────────────────────
    @app.post("/api/screener/run", tags=["screener"])
    def screener_run(
        req: ScreenerRunRequest,
        user: dict = Depends(get_current_user),
    ) -> ScreenerRunResponse:
        """Sembol evrenini filtrele, sırala ve döndür.

        Cache'ten son 1d barı çeker; RSI varsa hesaplar.
        Erişilemeyen alanlar None olarak döner.
        """
        import numpy as np

        run_id = str(uuid.uuid4())
        created_at = _utc_iso()

        # filters_hash
        filters_raw = req.model_dump_json(include={"filters"}).encode()
        filters_hash = hashlib.md5(filters_raw).hexdigest()

        # Evren seçimi
        universe_upper = req.universe.upper()
        if universe_upper == "BIST30":
            symbols = list(BIST_30_SYMBOLS)
        elif universe_upper == "BIST100":
            symbols = list(BIST_100_SYMBOLS)
        elif universe_upper == "CRYPTO":
            symbols = [s.replace("USDT", "") + "USDT" for s in CRYPTO_WS_SYMBOLS[:50]]
        else:
            # ALL: BIST100 + crypto
            symbols = list(BIST_100_SYMBOLS) + [s.replace("USDT", "") + "USDT" for s in CRYPTO_WS_SYMBOLS[:20]]

        def _calc_rsi(closes: list[float], period: int = 14) -> float | None:
            if len(closes) < period + 1:
                return None
            arr = np.array(closes, dtype=float)
            deltas = np.diff(arr)
            gains = np.where(deltas > 0, deltas, 0.0)
            losses = np.where(deltas < 0, -deltas, 0.0)
            avg_gain = float(np.mean(gains[:period]))
            avg_loss = float(np.mean(losses[:period]))
            for i in range(period, len(deltas)):
                avg_gain = (avg_gain * (period - 1) + gains[i]) / period
                avg_loss = (avg_loss * (period - 1) + losses[i]) / period
            if avg_loss == 0:
                return 100.0
            rs = avg_gain / avg_loss
            return round(100.0 - 100.0 / (1.0 + rs), 2)

        def _apply_filter(row_val: Any, op: str, threshold: Any) -> bool:
            if row_val is None:
                return False
            try:
                rv = float(row_val)
                tv = float(threshold)
            except (TypeError, ValueError):
                # string eq/neq
                if op == "eq":
                    return str(row_val) == str(threshold)
                if op == "neq":
                    return str(row_val) != str(threshold)
                return False
            if op == "gt":
                return rv > tv
            if op == "lt":
                return rv < tv
            if op == "gte":
                return rv >= tv
            if op == "lte":
                return rv <= tv
            if op == "eq":
                return rv == tv
            if op == "neq":
                return rv != tv
            return True

        rows: list[ScreenerRow] = []
        for sym in symbols:
            sym_upper = sym.upper()
            bar_now = cache.latest_bar(sym_upper, "1d")
            if bar_now is None:
                last_price = None
                volume = None
            else:
                last_price = round(float(bar_now["close"]), 4)
                volume = round(float(bar_now["volume"]), 2)

            # Önceki bar — change_pct için
            prev_bars = cache.get_window(sym_upper, "1d", limit=2)
            change_pct: float | None = None
            if prev_bars and len(prev_bars) >= 2 and last_price is not None:
                prev_close = float(prev_bars[-2]["close"])
                if prev_close > 0:
                    change_pct = round((last_price - prev_close) / prev_close * 100, 2)

            # Son 252 bar — RSI + 52w high + volume_avg_20d
            hist_bars = cache.get_window(sym_upper, "1d", limit=252)
            rsi_14: float | None = None
            volume_avg_20d: float | None = None
            distance_from_52w_high: float | None = None
            if hist_bars and len(hist_bars) >= 15:
                closes_list = [float(b["close"]) for b in hist_bars]
                rsi_14 = _calc_rsi(closes_list, 14)
                # Volume avg 20d
                volumes = [float(b["volume"]) for b in hist_bars if b.get("volume") is not None]
                if len(volumes) >= 20:
                    volume_avg_20d = round(float(np.mean(volumes[-20:])), 2)
                # 52w high (son 252 bar)
                highs = [float(b["high"]) for b in hist_bars if b.get("high") is not None]
                if highs and last_price is not None:
                    high_52w = max(highs)
                    if high_52w > 0:
                        distance_from_52w_high = round((last_price - high_52w) / high_52w * 100, 2)

            name = SYMBOL_METADATA.get(sym_upper, "")

            row = ScreenerRow(
                symbol=sym_upper,
                name=name,
                last_price=last_price,
                change_pct=change_pct,
                volume=volume,
                market_cap=None,
                pe_ratio=None,
                rsi_14=rsi_14,
                volume_avg_20d=volume_avg_20d,
                distance_from_52w_high=distance_from_52w_high,
                sector="",
            )
            rows.append(row)

        # Filtrele
        if req.filters:
            filtered: list[ScreenerRow] = []
            for row in rows:
                passes = True
                for f in req.filters:
                    col_val = getattr(row, f.column, None)
                    if not _apply_filter(col_val, f.op, f.value):
                        passes = False
                        break
                if passes:
                    filtered.append(row)
            rows = filtered

        # Sırala
        sort_key = req.sort_by
        reverse = req.sort_dir.lower() == "desc"

        def _sort_key(r: ScreenerRow) -> tuple[int, float]:
            v = getattr(r, sort_key, None)
            if v is None:
                return (1, 0.0)
            return (0, float(v))

        rows.sort(key=_sort_key, reverse=reverse)

        # Limit uygula
        rows = rows[: req.limit]

        # data_snapshot_hash — satır verisinin MD5'i (tekrar üretilebilirlik)
        rows_raw = "".join(
            f"{r.symbol}:{r.last_price}:{r.change_pct}:{r.rsi_14}"
            for r in rows
        ).encode()
        data_snapshot_hash = hashlib.md5(rows_raw).hexdigest()

        # ── Audit log ──────────────────────────────────────────────────────────
        try:
            from backend.audit import audit_logger, AuditEvent, AuditAction
            import asyncio
            asyncio.get_event_loop().run_until_complete(audit_logger.log(AuditEvent(
                action=AuditAction.SCREENER_RUN,
                user_id=int(user.get("id", 0)) or None,
                resource=f"{req.market}/{req.universe}",
                metadata={
                    "run_id": run_id,
                    "filters": len(req.filters),
                    "row_count": len(rows),
                    "filters_hash": filters_hash,
                },
            )))
        except Exception:
            pass

        return ScreenerRunResponse(
            run_id=run_id,
            created_at=created_at,
            market=req.market,
            universe=req.universe,
            filters_hash=filters_hash,
            data_snapshot_hash=data_snapshot_hash,
            row_count=len(rows),
            rows=rows,
            metadata={
                "universe_size": len(symbols),
                "sort_by": sort_key,
                "sort_dir": req.sort_dir,
                "filters_applied": len(req.filters),
            },
        )

    @app.get("/api/screener/presets", tags=["screener"])
    def screener_presets() -> dict[str, Any]:
        """Hazır screener preset listesi.

        Her preset: id, name, description, universe, filters[], sort_by, sort_dir, limit.
        """
        presets = [
            {
                "id": "top_volume",
                "name": "En Yüksek Hacim",
                "description": "Günlük hacme göre sıralanmış en likit semboller.",
                "universe": "BIST100",
                "filters": [],
                "sort_by": "volume",
                "sort_dir": "desc",
                "limit": 20,
            },
            {
                "id": "top_gainers",
                "name": "Günün En Çok Yükselenleri",
                "description": "Günlük değişim yüzdesine göre en çok artan semboller.",
                "universe": "BIST100",
                "filters": [{"column": "change_pct", "op": "gt", "value": 0}],
                "sort_by": "change_pct",
                "sort_dir": "desc",
                "limit": 20,
            },
            {
                "id": "top_losers",
                "name": "Günün En Çok Düşenleri",
                "description": "Günlük değişim yüzdesine göre en çok düşen semboller.",
                "universe": "BIST100",
                "filters": [{"column": "change_pct", "op": "lt", "value": 0}],
                "sort_by": "change_pct",
                "sort_dir": "asc",
                "limit": 20,
            },
            {
                "id": "rsi_oversold",
                "name": "RSI Aşırı Satım",
                "description": "RSI(14) < 30 olan semboller — potansiyel dönüş adayları.",
                "universe": "BIST100",
                "filters": [{"column": "rsi_14", "op": "lt", "value": 30}],
                "sort_by": "rsi_14",
                "sort_dir": "asc",
                "limit": 20,
            },
            {
                "id": "rsi_overbought",
                "name": "RSI Aşırı Alım",
                "description": "RSI(14) > 70 olan semboller — momentum devam edebilir veya düzeltme gelebilir.",
                "universe": "BIST100",
                "filters": [{"column": "rsi_14", "op": "gt", "value": 70}],
                "sort_by": "rsi_14",
                "sort_dir": "desc",
                "limit": 20,
            },
            {
                "id": "near_52w_high",
                "name": "52 Haftalık Zirveye Yakın",
                "description": "52 haftalık zirvesinden en az %5 uzakta olan ve yükselen semboller.",
                "universe": "BIST100",
                "filters": [
                    {"column": "distance_from_52w_high", "op": "gte", "value": -5},
                    {"column": "change_pct", "op": "gt", "value": 0},
                ],
                "sort_by": "distance_from_52w_high",
                "sort_dir": "desc",
                "limit": 20,
            },
            {
                "id": "crypto_momentum",
                "name": "Kripto Momentum",
                "description": "Günlük pozitif değişim gösteren kripto pariteler.",
                "universe": "CRYPTO",
                "filters": [{"column": "change_pct", "op": "gt", "value": 0}],
                "sort_by": "change_pct",
                "sort_dir": "desc",
                "limit": 20,
            },
            {
                "id": "relative_volume_spike",
                "name": "Hacim Patlaması",
                "description": "Son hacmi 20 günlük ortalama hacmin 2 katından fazla olan semboller.",
                "universe": "BIST100",
                "filters": [],   # volume_avg_20d karşılaştırması row-level yapılıyor
                "sort_by": "volume",
                "sort_dir": "desc",
                "limit": 20,
                "_note": "Relative volume filtresi şu an sadece volume sort ile yaklaşık uygulanıyor. Tam relative volume filtresi bir sonraki sürümde.",
            },
        ]
        return {
            "presets": presets,
            "count": len(presets),
            "fetched_at": _utc_iso(),
        }

    # ── Technical Summary ─────────────────────────────────────────────────────
    @app.get("/api/technical/summary", tags=["technical"])
    def technical_summary(
        symbol: str,
        market: str = "BIST",
        timeframe: str = "1d",
        user: dict = Depends(get_current_user),
    ) -> dict:
        """Sembol için teknik özet: RSI, SMA, EMA, MACD, ATR + overall_rating."""
        import numpy as np

        sym_upper = symbol.strip().upper()
        fetched_at = _utc_iso()

        bars = cache.get_window(sym_upper, timeframe, limit=200)
        if not bars:
            raise HTTPException(
                status_code=404,
                detail=f"{sym_upper}/{timeframe} için cache verisi bulunamadı.",
            )

        closes_arr  = np.array([float(b["close"])  for b in bars], dtype=float)
        highs_arr   = np.array([float(b["high"])   for b in bars], dtype=float)
        lows_arr    = np.array([float(b["low"])    for b in bars], dtype=float)
        volumes_arr = np.array([float(b.get("volume", 0) or 0) for b in bars], dtype=float)
        n = len(closes_arr)

        def _round(v: float | None, d: int = 4) -> float | None:
            if v is None or math.isnan(v):
                return None
            return round(v, d)

        # ── RSI(14) ──
        def _rsi(arr: np.ndarray, period: int = 14) -> float | None:
            if len(arr) < period + 1:
                return None
            deltas = np.diff(arr)
            gains  = np.where(deltas > 0, deltas, 0.0)
            losses = np.where(deltas < 0, -deltas, 0.0)
            avg_g = float(np.mean(gains[:period]))
            avg_l = float(np.mean(losses[:period]))
            for i in range(period, len(deltas)):
                avg_g = (avg_g * (period - 1) + gains[i]) / period
                avg_l = (avg_l * (period - 1) + losses[i]) / period
            if avg_l == 0:
                return 100.0
            return round(100.0 - 100.0 / (1.0 + avg_g / avg_l), 2)

        # ── SMA ──
        def _sma(arr: np.ndarray, period: int) -> float | None:
            if len(arr) < period:
                return None
            return float(np.mean(arr[-period:]))

        # ── EMA ──
        def _ema(arr: np.ndarray, period: int) -> float | None:
            if len(arr) < period:
                return None
            k = 2.0 / (period + 1)
            val = float(np.mean(arr[:period]))
            for v in arr[period:]:
                val = v * k + val * (1 - k)
            return val

        # ── MACD(12,26,9) ──
        def _macd(arr: np.ndarray) -> tuple[float | None, float | None, float | None]:
            if len(arr) < 26:
                return None, None, None
            k12 = 2.0 / (12 + 1)
            k26 = 2.0 / (26 + 1)
            ema12 = float(np.mean(arr[:12]))
            ema26 = float(np.mean(arr[:26]))
            for v in arr[12:]:
                ema12 = v * k12 + ema12 * (1 - k12)
            for v in arr[26:]:
                ema26 = v * k26 + ema26 * (1 - k26)
            line = ema12 - ema26
            # MACD signal: EMA(9) of MACD line over last 26+ bars
            macd_series: list[float] = []
            e12 = float(np.mean(arr[:12]))
            e26 = float(np.mean(arr[:26]))
            for v in arr[12:]:
                e12 = v * k12 + e12 * (1 - k12)
            for idx in range(26, len(arr)):
                e26 = arr[idx] * k26 + e26 * (1 - k26)
                macd_series.append(e12 - e26)
                e12 = arr[idx] * k12 + e12 * (1 - k12)
            if len(macd_series) < 9:
                return round(line, 4), None, None
            k9 = 2.0 / (9 + 1)
            sig = float(np.mean(macd_series[:9]))
            for mv in macd_series[9:]:
                sig = mv * k9 + sig * (1 - k9)
            hist = macd_series[-1] - sig if macd_series else None
            return round(line, 4), round(sig, 4), (round(hist, 4) if hist is not None else None)

        # ── ATR(14) ──
        def _atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float | None:
            if len(close) < period + 1:
                return None
            trs = []
            for i in range(1, len(close)):
                tr = max(
                    high[i] - low[i],
                    abs(high[i] - close[i - 1]),
                    abs(low[i]  - close[i - 1]),
                )
                trs.append(tr)
            if len(trs) < period:
                return None
            atr_val = float(np.mean(trs[:period]))
            for tr in trs[period:]:
                atr_val = (atr_val * (period - 1) + tr) / period
            return round(atr_val, 4)

        # ── Bollinger Bands(20,2) ──
        def _bollinger(arr: np.ndarray, period: int = 20, std_dev: float = 2.0) -> tuple[float | None, float | None, float | None]:
            if len(arr) < period:
                return None, None, None
            sma_val = float(np.mean(arr[-period:]))
            std_val = float(np.std(arr[-period:], ddof=1))
            return round(sma_val + std_dev * std_val, 4), round(sma_val, 4), round(sma_val - std_dev * std_val, 4)

        # ── Stochastic(14,3) ──
        def _stochastic(high: np.ndarray, low: np.ndarray, close: np.ndarray, k_period: int = 14, d_period: int = 3) -> tuple[float | None, float | None]:
            if len(close) < k_period + d_period:
                return None, None
            k_series: list[float] = []
            for i in range(k_period - 1, len(close)):
                period_high = float(np.max(high[i - k_period + 1:i + 1]))
                period_low  = float(np.min(low[i  - k_period + 1:i + 1]))
                if period_high - period_low == 0:
                    k_series.append(50.0)
                else:
                    k_series.append((close[i] - period_low) / (period_high - period_low) * 100)
            if len(k_series) < d_period:
                return None, None
            k_val = round(k_series[-1], 2)
            d_val = round(float(np.mean(k_series[-d_period:])), 2)
            return k_val, d_val

        # ── ADX(14) ──
        def _adx(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float | None:
            if len(close) < period * 2:
                return None
            tr_list, plus_dm_list, minus_dm_list = [], [], []
            for i in range(1, len(close)):
                h, l, pc = float(high[i]), float(low[i]), float(close[i - 1])
                tr_list.append(max(h - l, abs(h - pc), abs(l - pc)))
                hd = float(high[i]) - float(high[i - 1])
                ld = float(low[i - 1]) - float(low[i])
                plus_dm_list.append(hd if hd > ld and hd > 0 else 0.0)
                minus_dm_list.append(ld if ld > hd and ld > 0 else 0.0)
            # Wilder smoothing
            smooth = lambda lst: [sum(lst[:period])] + [
                s - s / period + lst[i] for i, s in zip(range(period, len(lst)), [sum(lst[:period])] + [None] * len(lst))
                if s is not None
            ]
            def _wilder(lst: list[float]) -> list[float]:
                result = [sum(lst[:period])]
                for v in lst[period:]:
                    result.append(result[-1] - result[-1] / period + v)
                return result
            atr_s = _wilder(tr_list)
            plus_s  = _wilder(plus_dm_list)
            minus_s = _wilder(minus_dm_list)
            dx_list = []
            for a, p, m in zip(atr_s, plus_s, minus_s):
                plus_di  = 100.0 * p / a if a != 0 else 0.0
                minus_di = 100.0 * m / a if a != 0 else 0.0
                denom = plus_di + minus_di
                dx_list.append(100.0 * abs(plus_di - minus_di) / denom if denom != 0 else 0.0)
            if len(dx_list) < period:
                return None
            adx_val = float(np.mean(dx_list[:period]))
            for dx in dx_list[period:]:
                adx_val = (adx_val * (period - 1) + dx) / period
            return round(adx_val, 2)

        # ── CCI(20) — Commodity Channel Index ──
        def _cci(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 20) -> float | None:
            if len(close) < period:
                return None
            tp = (high + low + close) / 3.0
            tp_slice = tp[-period:]
            mean_tp = float(np.mean(tp_slice))
            mean_dev = float(np.mean(np.abs(tp_slice - mean_tp)))
            if mean_dev == 0:
                return 0.0
            return round((float(tp_slice[-1]) - mean_tp) / (0.015 * mean_dev), 2)

        # ── Momentum(10) ──
        def _momentum(arr: np.ndarray, period: int = 10) -> float | None:
            if len(arr) < period + 1:
                return None
            return round(float(arr[-1]) - float(arr[-period - 1]), 4)

        # ── Williams %R(14) ──
        def _williams_r(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> float | None:
            if len(close) < period:
                return None
            h = float(np.max(high[-period:]))
            l = float(np.min(low[-period:]))
            if h - l == 0:
                return -50.0
            return round((h - float(close[-1])) / (h - l) * -100.0, 2)

        # ── Stochastic RSI(14,14,3,3) ──
        def _stoch_rsi(arr: np.ndarray, rsi_period: int = 14, stoch_period: int = 14, k_period: int = 3, d_period: int = 3) -> tuple[float | None, float | None]:
            if len(arr) < rsi_period + stoch_period + k_period + d_period:
                return None, None
            # Build RSI series
            rsi_series: list[float] = []
            for i in range(rsi_period, len(arr) + 1):
                sub = arr[i - rsi_period - 1:i]
                if len(sub) < rsi_period + 1:
                    continue
                v = _rsi(sub, rsi_period)
                if v is not None:
                    rsi_series.append(v)
            if len(rsi_series) < stoch_period + k_period + d_period:
                return None, None
            rsi_arr = np.array(rsi_series, dtype=float)
            k_raw: list[float] = []
            for i in range(stoch_period - 1, len(rsi_arr)):
                sl = rsi_arr[i - stoch_period + 1:i + 1]
                r_h, r_l = float(np.max(sl)), float(np.min(sl))
                k_raw.append((rsi_arr[i] - r_l) / (r_h - r_l) * 100 if r_h - r_l != 0 else 50.0)
            if len(k_raw) < k_period + d_period:
                return None, None
            k_smooth: list[float] = [float(np.mean(k_raw[i:i + k_period])) for i in range(len(k_raw) - k_period + 1)]
            d_smooth: list[float] = [float(np.mean(k_smooth[i:i + d_period])) for i in range(len(k_smooth) - d_period + 1)]
            return round(k_smooth[-1], 2) if k_smooth else None, round(d_smooth[-1], 2) if d_smooth else None

        # ── Hull MA(9) ──
        def _hma(arr: np.ndarray, period: int = 9) -> float | None:
            half = max(2, period // 2)
            sqrt_p = max(2, int(period ** 0.5))
            if len(arr) < period:
                return None
            wma1 = _wma(arr, half)
            wma2 = _wma(arr, period)
            if wma1 is None or wma2 is None:
                return None
            # Hull raw series: 2*WMA(n/2) - WMA(n)
            hull_series: list[float] = []
            for i in range(period - 1, len(arr)):
                sub = arr[: i + 1]
                w1 = _wma(sub, half)
                w2 = _wma(sub, period)
                if w1 is not None and w2 is not None:
                    hull_series.append(2 * w1 - w2)
            if len(hull_series) < sqrt_p:
                return None
            return _round(_wma(np.array(hull_series, dtype=float), sqrt_p))

        # ── WMA(n) — Weighted Moving Average (yardımcı) ──
        def _wma(arr: np.ndarray, period: int) -> float | None:
            if len(arr) < period:
                return None
            weights = np.arange(1, period + 1, dtype=float)
            return float(np.dot(arr[-period:], weights) / weights.sum())

        # ── VWMA(20) — Volume Weighted MA ──
        def _vwma(close: np.ndarray, volume: np.ndarray, period: int = 20) -> float | None:
            if len(close) < period or volume is None or len(volume) < period:
                return None
            v_slice = volume[-period:]
            c_slice = close[-period:]
            vol_sum = float(np.sum(v_slice))
            if vol_sum == 0:
                return None
            return _round(float(np.dot(c_slice, v_slice) / vol_sum))

        # ── Ichimoku — Tenkan-sen(9), Kijun-sen(26), Chikou ──
        def _ichimoku(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, float | None]:
            def _mid(h: np.ndarray, l: np.ndarray, p: int) -> float | None:
                if len(h) < p:
                    return None
                return round((float(np.max(h[-p:])) + float(np.min(l[-p:]))) / 2, 4)
            tenkan  = _mid(high, low, 9)
            kijun   = _mid(high, low, 26)
            senkou_a = round((tenkan + kijun) / 2, 4) if tenkan and kijun else None
            senkou_b = _mid(high, low, 52)
            chikou  = _round(float(close[-1])) if len(close) > 0 else None
            above_cloud: str | None = None
            if close[-1] is not None and senkou_a is not None and senkou_b is not None:
                cloud_top = max(senkou_a, senkou_b)
                cloud_bot = min(senkou_a, senkou_b)
                if float(close[-1]) > cloud_top:
                    above_cloud = "above"
                elif float(close[-1]) < cloud_bot:
                    above_cloud = "below"
                else:
                    above_cloud = "inside"
            return {
                "tenkan_sen":  tenkan,
                "kijun_sen":   kijun,
                "senkou_a":    senkou_a,
                "senkou_b":    senkou_b,
                "chikou_span": chikou,
                "cloud_position": above_cloud,
            }

        # ── Awesome Oscillator (AO = SMA5 of midpoints - SMA34 of midpoints) ──
        def _awesome_oscillator(high: np.ndarray, low: np.ndarray) -> float | None:
            if len(high) < 34:
                return None
            mids = (high + low) / 2.0
            sma5  = float(np.mean(mids[-5:]))
            sma34 = float(np.mean(mids[-34:]))
            return _round(sma5 - sma34)

        # ── Bull/Bear Power ──
        def _bull_bear_power(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 13) -> tuple[float | None, float | None]:
            ema_val = _ema(close, period)
            if ema_val is None:
                return None, None
            bull = _round(float(high[-1]) - ema_val)
            bear = _round(float(low[-1]) - ema_val)
            return bull, bear

        # ── Ultimate Oscillator (7,14,28) ──
        def _ultimate_oscillator(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> float | None:
            if len(close) < 29:
                return None
            bp_list, tr_list = [], []
            for i in range(1, len(close)):
                true_low  = min(float(low[i]),  float(close[i-1]))
                true_high = max(float(high[i]), float(close[i-1]))
                bp = float(close[i]) - true_low
                tr = true_high - true_low
                bp_list.append(bp)
                tr_list.append(tr if tr > 0 else 1e-9)
            def _avg(bp, tr, n):
                if len(bp) < n:
                    return 0.0
                return sum(bp[-n:]) / (sum(tr[-n:]) or 1e-9)
            avg7  = _avg(bp_list, tr_list, 7)
            avg14 = _avg(bp_list, tr_list, 14)
            avg28 = _avg(bp_list, tr_list, 28)
            uo = 100.0 * (4 * avg7 + 2 * avg14 + avg28) / 7.0
            return _round(uo)

        def _uo_signal(v: float | None) -> str:
            if v is None:
                return "neutral"
            if v < 30:
                return "oversold"
            if v > 70:
                return "overbought"
            return "neutral"

        # ── Fibonacci pivot seviyeleri ──
        def _fib_pivots(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, float | None]:
            if len(close) < 2:
                return {}
            h, l, c = float(high[-2]), float(low[-2]), float(close[-2])
            pp  = (h + l + c) / 3.0
            rng = h - l
            return {
                "PP":  round(pp, 4),
                "R1":  round(pp + 0.382 * rng, 4),
                "R2":  round(pp + 0.618 * rng, 4),
                "R3":  round(pp + 1.000 * rng, 4),
                "S1":  round(pp - 0.382 * rng, 4),
                "S2":  round(pp - 0.618 * rng, 4),
                "S3":  round(pp - 1.000 * rng, 4),
            }

        # ── Pivot seviyeleri (Classic) ──
        def _pivots(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, float | None]:
            if len(close) < 2:
                return {}
            # Önceki tam bar kullan
            h, l, c = float(high[-2]), float(low[-2]), float(close[-2])
            pp = (h + l + c) / 3.0
            r1 = 2 * pp - l
            s1 = 2 * pp - h
            r2 = pp + (h - l)
            s2 = pp - (h - l)
            r3 = h + 2 * (pp - l)
            s3 = l - 2 * (h - pp)
            return {
                "PP": round(pp, 4), "R1": round(r1, 4), "R2": round(r2, 4), "R3": round(r3, 4),
                "S1": round(s1, 4), "S2": round(s2, 4), "S3": round(s3, 4),
            }

        # ── Camarilla pivot seviyeleri ──
        def _camarilla_pivots(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, float | None]:
            if len(close) < 2:
                return {}
            h, l, c = float(high[-2]), float(low[-2]), float(close[-2])
            rng = h - l
            return {
                "PP": round((h + l + c) / 3.0, 4),
                "R1": round(c + rng * 1.1 / 12, 4),
                "R2": round(c + rng * 1.1 / 6,  4),
                "R3": round(c + rng * 1.1 / 4,  4),
                "R4": round(c + rng * 1.1 / 2,  4),
                "S1": round(c - rng * 1.1 / 12, 4),
                "S2": round(c - rng * 1.1 / 6,  4),
                "S3": round(c - rng * 1.1 / 4,  4),
                "S4": round(c - rng * 1.1 / 2,  4),
            }

        # ── Woodie pivot seviyeleri ──
        def _woodie_pivots(high: np.ndarray, low: np.ndarray, close: np.ndarray) -> dict[str, float | None]:
            if len(close) < 2:
                return {}
            h, l, c = float(high[-2]), float(low[-2]), float(close[-2])
            # Woodie: PP = (H + L + 2*Open) / 4; Open yaklaşımı = previous close
            pp = (h + l + 2 * c) / 4.0
            r1 = 2 * pp - l
            s1 = 2 * pp - h
            r2 = pp + (h - l)
            s2 = pp - (h - l)
            return {
                "PP": round(pp, 4),
                "R1": round(r1, 4), "R2": round(r2, 4),
                "S1": round(s1, 4), "S2": round(s2, 4),
            }

        # ── DeMark pivot seviyeleri ──
        def _demark_pivots(high: np.ndarray, low: np.ndarray, close: np.ndarray, open_arr: np.ndarray | None = None) -> dict[str, float | None]:
            if len(close) < 2:
                return {}
            h, l, c = float(high[-2]), float(low[-2]), float(close[-2])
            o = float(open_arr[-2]) if open_arr is not None and len(open_arr) >= 2 else c
            if c < o:
                x = h + 2 * l + c
            elif c > o:
                x = 2 * h + l + c
            else:
                x = h + l + 2 * c
            pp = x / 4.0
            r1 = x / 2.0 - l
            s1 = x / 2.0 - h
            return {
                "PP": round(pp, 4),
                "R1": round(r1, 4),
                "S1": round(s1, 4),
            }

        last_close = _round(float(closes_arr[-1]))
        prev_close = float(closes_arr[-2]) if n >= 2 else None
        change_pct: float | None = None
        if prev_close and prev_close > 0 and last_close is not None:
            change_pct = _round((last_close - prev_close) / prev_close * 100, 2)

        rsi_val   = _rsi(closes_arr, 14)
        sma_10    = _round(_sma(closes_arr, 10))
        sma_20    = _round(_sma(closes_arr, 20))
        sma_30    = _round(_sma(closes_arr, 30))
        sma_50    = _round(_sma(closes_arr, 50))
        sma_100   = _round(_sma(closes_arr, 100))
        sma_200   = _round(_sma(closes_arr, 200))
        ema_10    = _round(_ema(closes_arr, 10))
        ema_20    = _round(_ema(closes_arr, 20))
        ema_50    = _round(_ema(closes_arr, 50))
        ema_100   = _round(_ema(closes_arr, 100))
        ema_200   = _round(_ema(closes_arr, 200))
        macd_v, macd_sig_v, macd_hist_v = _macd(closes_arr)
        atr_val   = _atr(highs_arr, lows_arr, closes_arr, 14)
        bb_upper, bb_mid, bb_lower = _bollinger(closes_arr, 20, 2.0)
        stoch_k, stoch_d   = _stochastic(highs_arr, lows_arr, closes_arr, 14, 3)
        adx_val            = _adx(highs_arr, lows_arr, closes_arr, 14)
        cci_val            = _cci(highs_arr, lows_arr, closes_arr, 20)
        momentum_val       = _momentum(closes_arr, 10)
        williams_r_val     = _williams_r(highs_arr, lows_arr, closes_arr, 14)
        srsi_k, srsi_d     = _stoch_rsi(closes_arr, 14, 14, 3, 3)
        hma_9              = _hma(closes_arr, 9)
        vwma_20            = _vwma(closes_arr, volumes_arr, 20)
        ichimoku           = _ichimoku(highs_arr, lows_arr, closes_arr)
        pivots             = _pivots(highs_arr, lows_arr, closes_arr)
        fib_pivots         = _fib_pivots(highs_arr, lows_arr, closes_arr)
        # Ek göstergeler
        ao_val             = _awesome_oscillator(highs_arr, lows_arr)
        bull_power, bear_power = _bull_bear_power(highs_arr, lows_arr, closes_arr, 13)
        uo_val             = _ultimate_oscillator(highs_arr, lows_arr, closes_arr)
        # Ek pivot türleri
        camarilla_pivots   = _camarilla_pivots(highs_arr, lows_arr, closes_arr)
        woodie_pivots      = _woodie_pivots(highs_arr, lows_arr, closes_arr)
        # bars'dan open dizisi çıkar (varsa)
        _opens_arr = np.array([float(b.get("open", b["close"])) for b in bars], dtype=float)
        demark_pivots      = _demark_pivots(highs_arr, lows_arr, closes_arr, _opens_arr)

        # Signal mantığı
        def _ma_signal(ma_val: float | None) -> str:
            if ma_val is None or last_close is None:
                return "neutral"
            diff_pct = abs(last_close - ma_val) / ma_val if ma_val else 0
            if diff_pct < 0.005:
                return "neutral"
            return "buy" if last_close > ma_val else "sell"

        def _rsi_signal(v: float | None) -> str:
            if v is None:
                return "neutral"
            if v < 30:
                return "oversold"
            if v > 70:
                return "overbought"
            return "neutral"

        def _macd_signal(hist: float | None) -> str:
            if hist is None:
                return "neutral"
            if hist > 0:
                return "buy"
            if hist < 0:
                return "sell"
            return "neutral"

        def _stoch_signal(k: float | None, d: float | None) -> str:
            if k is None or d is None:
                return "neutral"
            if k < 20 and d < 20:
                return "oversold"
            if k > 80 and d > 80:
                return "overbought"
            if k > d:
                return "buy"
            if k < d:
                return "sell"
            return "neutral"

        def _bb_signal(close: float | None, upper: float | None, lower: float | None, mid: float | None) -> str:
            if close is None or upper is None or lower is None:
                return "neutral"
            if close > upper:
                return "overbought"
            if close < lower:
                return "oversold"
            if mid is not None and close > mid:
                return "buy"
            return "sell"

        def _cci_signal(v: float | None) -> str:
            if v is None:
                return "neutral"
            if v < -100:
                return "oversold"
            if v > 100:
                return "overbought"
            return "neutral"

        def _momentum_signal(v: float | None) -> str:
            if v is None:
                return "neutral"
            return "buy" if v > 0 else "sell"

        def _williams_r_signal(v: float | None) -> str:
            if v is None:
                return "neutral"
            if v < -80:
                return "oversold"
            if v > -20:
                return "overbought"
            return "neutral"

        def _srsi_signal(k: float | None, d: float | None) -> str:
            if k is None or d is None:
                return "neutral"
            if k < 20 and d < 20:
                return "oversold"
            if k > 80 and d > 80:
                return "overbought"
            if k > d:
                return "buy"
            if k < d:
                return "sell"
            return "neutral"

        ma_signals = {
            "sma_10":  _ma_signal(sma_10),
            "sma_20":  _ma_signal(sma_20),
            "sma_30":  _ma_signal(sma_30),
            "sma_50":  _ma_signal(sma_50),
            "sma_100": _ma_signal(sma_100),
            "sma_200": _ma_signal(sma_200),
            "ema_10":  _ma_signal(ema_10),
            "ema_20":  _ma_signal(ema_20),
            "ema_50":  _ma_signal(ema_50),
            "ema_100": _ma_signal(ema_100),
            "ema_200": _ma_signal(ema_200),
            "hma_9":   _ma_signal(hma_9),
            "vwma_20": _ma_signal(vwma_20),
        }
        osc_macd_signal     = _macd_signal(macd_hist_v)
        osc_rsi_signal      = _rsi_signal(rsi_val)
        osc_stoch_signal    = _stoch_signal(stoch_k, stoch_d)
        osc_bb_signal       = _bb_signal(last_close, bb_upper, bb_lower, bb_mid)
        osc_cci_signal      = _cci_signal(cci_val)
        osc_momentum_signal = _momentum_signal(momentum_val)
        osc_wr_signal       = _williams_r_signal(williams_r_val)
        osc_srsi_signal     = _srsi_signal(srsi_k, srsi_d)
        osc_ao_signal       = "buy" if ao_val and ao_val > 0 else ("sell" if ao_val and ao_val < 0 else "neutral")
        osc_uo_signal       = _uo_signal(uo_val)

        # overall_rating: oscillators + MA sinyallerini say
        osc_signals_all = [
            osc_macd_signal, osc_rsi_signal, osc_stoch_signal, osc_bb_signal,
            osc_cci_signal, osc_momentum_signal, osc_wr_signal, osc_srsi_signal,
            osc_ao_signal, osc_uo_signal,
        ]
        ma_signals_all  = list(ma_signals.values())

        def _count_rating(signals: list[str]) -> dict[str, int]:
            buy  = sum(1 for s in signals if s in ("buy", "oversold"))
            sell = sum(1 for s in signals if s in ("sell", "overbought"))
            return {"buy": buy, "sell": sell, "neutral": len(signals) - buy - sell}

        osc_rating = _count_rating(osc_signals_all)
        ma_rating  = _count_rating(ma_signals_all)
        all_signals_list = osc_signals_all + ma_signals_all
        total_rating = _count_rating(all_signals_list)

        if total_rating["buy"] > total_rating["sell"]:
            overall = "buy"
        elif total_rating["sell"] > total_rating["buy"]:
            overall = "sell"
        else:
            overall = "neutral"

        return {
            "symbol": sym_upper,
            "market": market.upper(),
            "timeframe": timeframe,
            "bars_used": n,
            "fetched_at": fetched_at,
            "calculation_version": "2.0",
            "price": {
                "last": last_close,
                "change_pct": change_pct,
            },
            "oscillators": {
                "rsi_14": {
                    "value": rsi_val,
                    "signal": osc_rsi_signal,
                },
                "macd": {
                    "value": macd_v,
                    "signal_line": macd_sig_v,
                    "histogram": macd_hist_v,
                    "signal": osc_macd_signal,
                },
                "stochastic": {
                    "k": stoch_k,
                    "d": stoch_d,
                    "signal": osc_stoch_signal,
                },
                "atr_14": {
                    "value": atr_val,
                    "atr_pct": _round(atr_val / float(closes_arr[-1]) * 100 if atr_val and float(closes_arr[-1]) > 0 else None, 2),
                },
                "bollinger": {
                    "upper": bb_upper,
                    "middle": bb_mid,
                    "lower": bb_lower,
                    "signal": osc_bb_signal,
                    "bandwidth_pct": _round((bb_upper - bb_lower) / bb_mid * 100 if bb_upper and bb_lower and bb_mid and bb_mid != 0 else None, 2),
                },
                "adx_14": {
                    "value": adx_val,
                    "trend_strength": (
                        "güçlü" if adx_val and adx_val > 25
                        else "zayıf" if adx_val and adx_val < 20
                        else "orta" if adx_val else None
                    ),
                },
                "cci_20": {
                    "value": _round(cci_val, 2),
                    "signal": osc_cci_signal,
                },
                "momentum_10": {
                    "value": _round(momentum_val, 4),
                    "signal": osc_momentum_signal,
                },
                "williams_r_14": {
                    "value": _round(williams_r_val, 2),
                    "signal": osc_wr_signal,
                },
                "stoch_rsi": {
                    "k": _round(srsi_k, 2),
                    "d": _round(srsi_d, 2),
                    "signal": osc_srsi_signal,
                },
                "awesome_oscillator": {
                    "value": ao_val,
                    "signal": osc_ao_signal,
                    "description": "SMA5(midpoint) - SMA34(midpoint); pozitif = momentum yukarı",
                },
                "bull_bear_power": {
                    "bull": bull_power,
                    "bear": bear_power,
                    "signal": (
                        "buy" if (bull_power or 0) > 0 and (bear_power or 0) > -abs(bull_power or 0) * 0.5
                        else "sell" if (bear_power or 0) < 0 else "neutral"
                    ),
                    "description": "Bull=High-EMA13, Bear=Low-EMA13",
                },
                "ultimate_oscillator": {
                    "value": uo_val,
                    "signal": osc_uo_signal,
                    "description": "7/14/28 periyotlu ağırlıklı ortalama; 30 altı aşırı satım, 70 üstü aşırı alım",
                },
                "rating": osc_rating,
            },
            "moving_averages": {
                "sma_10":  {"value": sma_10,  "signal": ma_signals["sma_10"],  "distance_pct": _round((last_close - sma_10) / sma_10 * 100 if sma_10 and last_close else None, 2)},
                "sma_20":  {"value": sma_20,  "signal": ma_signals["sma_20"],  "distance_pct": _round((last_close - sma_20) / sma_20 * 100 if sma_20 and last_close else None, 2)},
                "sma_30":  {"value": sma_30,  "signal": ma_signals["sma_30"],  "distance_pct": _round((last_close - sma_30) / sma_30 * 100 if sma_30 and last_close else None, 2)},
                "sma_50":  {"value": sma_50,  "signal": ma_signals["sma_50"],  "distance_pct": _round((last_close - sma_50) / sma_50 * 100 if sma_50 and last_close else None, 2)},
                "sma_100": {"value": sma_100, "signal": ma_signals["sma_100"], "distance_pct": _round((last_close - sma_100) / sma_100 * 100 if sma_100 and last_close else None, 2)},
                "sma_200": {"value": sma_200, "signal": ma_signals["sma_200"], "distance_pct": _round((last_close - sma_200) / sma_200 * 100 if sma_200 and last_close else None, 2)},
                "ema_10":  {"value": ema_10,  "signal": ma_signals["ema_10"],  "distance_pct": _round((last_close - ema_10) / ema_10 * 100 if ema_10 and last_close else None, 2)},
                "ema_20":  {"value": ema_20,  "signal": ma_signals["ema_20"],  "distance_pct": _round((last_close - ema_20) / ema_20 * 100 if ema_20 and last_close else None, 2)},
                "ema_50":  {"value": ema_50,  "signal": ma_signals["ema_50"],  "distance_pct": _round((last_close - ema_50) / ema_50 * 100 if ema_50 and last_close else None, 2)},
                "ema_100": {"value": ema_100, "signal": ma_signals["ema_100"], "distance_pct": _round((last_close - ema_100) / ema_100 * 100 if ema_100 and last_close else None, 2)},
                "ema_200": {"value": ema_200, "signal": ma_signals["ema_200"], "distance_pct": _round((last_close - ema_200) / ema_200 * 100 if ema_200 and last_close else None, 2)},
                "hma_9":   {"value": hma_9,   "signal": ma_signals["hma_9"],   "distance_pct": _round((last_close - hma_9) / hma_9 * 100 if hma_9 and last_close else None, 2)},
                "vwma_20": {"value": vwma_20, "signal": ma_signals["vwma_20"], "distance_pct": _round((last_close - vwma_20) / vwma_20 * 100 if vwma_20 and last_close else None, 2)},
                "ichimoku": ichimoku,
                "rating": ma_rating,
            },
            "pivots": {
                "classic": {
                    "method": "classic",
                    "note": "Önceki tam bar OHLC verisiyle hesaplandı.",
                    "levels": pivots,
                },
                "fibonacci": {
                    "method": "fibonacci",
                    "note": "Fibonacci oranlı pivot seviyeleri.",
                    "levels": fib_pivots,
                },
                "camarilla": {
                    "method": "camarilla",
                    "note": "Camarilla: Close + range × 1.1/12…1.1/2 oranları.",
                    "levels": camarilla_pivots,
                },
                "woodie": {
                    "method": "woodie",
                    "note": "Woodie: PP = (H+L+2C)/4; open yerine önceki kapanış kullanılır.",
                    "levels": woodie_pivots,
                },
                "demark": {
                    "method": "demark",
                    "note": "DeMark: X değeri kapanış/açılış ilişkisine göre seçilir.",
                    "levels": demark_pivots,
                },
                "period_note": "Tüm pivotlar önceki tamamlanmış bar (n-1) verisiyle hesaplandı.",
            },
            "overall_rating": overall,
            "overall_counts": total_rating,
            "data_truth": {
                "quality_status": "ok",
                "provider": "cache",
                "fetched_at": fetched_at,
                "warning": "Bu teknik özet cache verisinden hesaplanmıştır; yatırım tavsiyesi değildir.",
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # 18.4 · Finansallar sekmesi — mali özet + değerleme oranları
    # ─────────────────────────────────────────────────────────────────────
    @app.get("/api/financials/{symbol}", tags=["symbol360"])
    def get_financials(
        symbol: str,
        user: dict = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """
        Sembol için finansal özet: gelir tablosu, bilanço, değerleme oranları.

        Plan kısıtı: guest → temel oranlar; free → TTM + yıllık; pro/ultra → çeyreklik.

        Veri kaynağı: yfinance (gecikimli, lisansına göre).
        Uyarı: Bu veriler yatırım tavsiyesi değildir.
        """
        sym = symbol.strip().upper().replace(".IS", "")
        plan = (user or {}).get("plan", "guest")
        fetched_at = _utc_iso()

        disclaimer = (
            "Bu finansal veriler bilgilendirme amaçlıdır; yatırım tavsiyesi değildir. "
            "Veriler gecikimli olabilir. Kaynak: yfinance (Yahoo Finance lisansı)."
        )

        result: dict[str, Any] = {
            "symbol": sym,
            "plan": plan,
            "fetched_at": fetched_at,
            "disclaimer": disclaimer,
            "data_truth": {
                "provider": "yfinance",
                "delayed": True,
                "license_note": "Yahoo Finance verisi; yeniden dağıtım ve ticari kullanım kısıtlıdır.",
            },
        }

        try:
            import yfinance as yf
            ticker_sym = f"{sym}.IS" if len(sym) <= 7 and not sym.endswith(".IS") else sym
            ticker = yf.Ticker(ticker_sym)
            info = ticker.info or {}

            def _safe(key: str, default: Any = None) -> Any:
                v = info.get(key, default)
                if v == "Infinity" or v != v:  # NaN check
                    return None
                return v

            # Temel oranlar (tüm planlar)
            result["valuation"] = {
                "pe_ratio":         _safe("trailingPE"),
                "forward_pe":       _safe("forwardPE"),
                "pb_ratio":         _safe("priceToBook"),
                "ps_ratio":         _safe("priceToSalesTrailing12Months"),
                "ev_ebitda":        _safe("enterpriseToEbitda"),
                "ev_revenue":       _safe("enterpriseToRevenue"),
                "peg_ratio":        _safe("pegRatio"),
                "market_cap":       _safe("marketCap"),
                "enterprise_value": _safe("enterpriseValue"),
            }

            result["profitability"] = {
                "return_on_equity":   _safe("returnOnEquity"),
                "return_on_assets":   _safe("returnOnAssets"),
                "profit_margin":      _safe("profitMargins"),
                "operating_margin":   _safe("operatingMargins"),
                "gross_margin":       _safe("grossMargins"),
                "ebitda_margin":      _safe("ebitdaMargins"),
            }

            result["growth"] = {
                "revenue_growth":   _safe("revenueGrowth"),
                "earnings_growth":  _safe("earningsGrowth"),
                "earnings_quarterly_growth": _safe("earningsQuarterlyGrowth"),
            }

            result["financial_health"] = {
                "total_cash":         _safe("totalCash"),
                "total_debt":         _safe("totalDebt"),
                "net_debt":           (_safe("totalDebt") or 0) - (_safe("totalCash") or 0) if _safe("totalDebt") and _safe("totalCash") else None,
                "current_ratio":      _safe("currentRatio"),
                "quick_ratio":        _safe("quickRatio"),
                "debt_to_equity":     _safe("debtToEquity"),
                "free_cashflow":      _safe("freeCashflow"),
                "operating_cashflow": _safe("operatingCashflow"),
            }

            if plan not in ("guest",):
                # TTM gelir tablosu
                result["income_statement_ttm"] = {
                    "revenue":          _safe("totalRevenue"),
                    "gross_profit":     _safe("grossProfits"),
                    "ebitda":           _safe("ebitda"),
                    "net_income":       _safe("netIncomeToCommon"),
                    "eps_trailing":     _safe("trailingEps"),
                    "eps_forward":      _safe("forwardEps"),
                }

        except ImportError:
            result["error"] = "yfinance kurulu değil (pip install yfinance)."
        except Exception:
            result["error"] = "Veri alınamadı."

        return result

    # ─────────────────────────────────────────────────────────────────────
    # 18.4 · Takvim sekmesi — sembol için tüm gelecek/geçmiş olaylar
    # ─────────────────────────────────────────────────────────────────────
    @app.get("/api/symbol/{symbol}/calendar", tags=["symbol360"])
    def get_symbol_calendar(
        symbol: str,
        from_date: str | None = None,
        to_date: str | None = None,
        limit: int = 50,
        user: dict = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """
        Sembol için takvim olayları: bilanço, temettü, GMYK, sermaye artırımı, ekonomik takvim.

        Geçmiş ve gelecek olaylar ayrımı ile "tahmini" etiketi zorunludur.
        """
        import datetime as dt_cal
        sym = symbol.strip().upper().replace(".IS", "")
        plan = (user or {}).get("plan", "guest")
        today = dt_cal.date.today().isoformat()

        store = _get_event_store()
        # Sembol olayları
        events = store.query(symbol=sym, from_date=from_date, to_date=to_date, limit=limit)
        # Ekonomik olaylar (global)
        econ = store.query(event_types=["economic"], from_date=from_date or today, limit=20)

        def _classify(ev: dict) -> str:
            return "past" if ev["event_date"] < today else "upcoming"

        result_events = []
        for ev in events + econ:
            ev["when"] = _classify(ev)
            ev["confirmed_label"] = "kesin" if ev["is_confirmed"] else "tahmini"
            result_events.append(ev)

        # Tarihe göre sırala: yakın gelecek önce, sonra geçmiş
        result_events.sort(key=lambda e: (e["event_date"], e.get("event_type", "")))

        return {
            "symbol":    sym,
            "fetched_at": _utc_iso(),
            "plan":      plan,
            "count":     len(result_events),
            "events":    result_events,
            "note":      "Tarih kesin değilse 'tahmini' etiketi görünür. Geçmiş olaylar arşiv amaçlıdır.",
            "disclaimer": "Bu takvim verileri bilgilendirme amaçlıdır; yatırım tavsiyesi değildir.",
        }

    # ─────────────────────────────────────────────────────────────────────
    # 18.11 · Sağ yan panel — quick-view: izleme, alarm, haber, takvim
    # ─────────────────────────────────────────────────────────────────────
    @app.get("/api/quick-view", tags=["panel"])
    def get_quick_view(
        symbols: str = "",
        user: dict = Depends(get_optional_user),
    ) -> dict[str, Any]:
        """
        Sağ yan panel için özet veri:
        - Son fiyatlar (izleme listesi)
        - Yaklaşan olaylar (30 gün)
        - Son haberler (5 adet)
        - Veri kalitesi özeti

        Kullanım: GET /api/quick-view?symbols=THYAO,GARAN,AKBNK
        """
        import datetime as dt_qv
        plan = (user or {}).get("plan", "guest")
        sym_list = [s.strip().upper() for s in symbols.split(",") if s.strip()] if symbols else []

        # Son fiyatlar — cache'ten
        quotes: list[dict] = []
        for sym in sym_list[:20]:  # maksimum 20 sembol
            bars = cache.get_window(sym, "1d", limit=2)
            if bars:
                last = bars[-1]
                prev = bars[-2] if len(bars) >= 2 else None
                chg = None
                if prev and float(prev.get("close", 0)) > 0:
                    chg = round((float(last["close"]) - float(prev["close"])) / float(prev["close"]) * 100, 2)
                quotes.append({
                    "symbol": sym,
                    "close":  float(last.get("close", 0)),
                    "change_pct": chg,
                    "volume": float(last.get("volume", 0) or 0),
                    "bar_time": last.get("time"),
                })

        # Yaklaşan olaylar
        store = _get_event_store()
        upcoming = store.upcoming(days=30, limit=15)

        # Son haberler
        news_limit = 5 if plan == "guest" else 10
        latest_news: list[dict] = []
        for sym in (sym_list[:3] if sym_list else []):
            try:
                from backend.news.news_fetcher import fetch_news_for_symbol
                items = fetch_news_for_symbol(sym, limit=3)
                for it in items[:2]:
                    it["_for_symbol"] = sym
                    latest_news.append(it)
            except Exception:
                pass
        latest_news = latest_news[:news_limit]

        return {
            "fetched_at": _utc_iso(),
            "plan":       plan,
            "quotes":     quotes,
            "upcoming_events": upcoming,
            "latest_news": latest_news,
            "disclaimer":  "Bu özet bilgilendirme amaçlıdır; yatırım tavsiyesi değildir.",
        }

    # ─────────────────────────────────────────────────────────────────────
    # 18.13 · Monitoring — genişletilmiş sağlık metrikleri
    # ─────────────────────────────────────────────────────────────────────
    @app.get("/api/health/detailed", tags=["ops"])
    def health_detailed(user: dict = Depends(get_current_user)) -> dict[str, Any]:
        """
        Üretim izleme için genişletilmiş sağlık metrikleri.

        Yalnızca admin kullanıcılar görebilir; CI/Grafana scrape için de kullanılabilir.
        """
        import time as _time

        if (user or {}).get("role") not in ("admin", "superadmin"):
            raise HTTPException(status_code=403, detail="Admin yetkisi gereklidir.")

        # Cache metrikleri
        cache_stats = cache.stats()
        cache_ok = cache_stats.get("rows", 0) > 0

        # Worker durumları
        worker_errors = {w["name"]: w.get("failures", 0) for w in supervisor.status().get("workers", [])}
        high_failure_workers = [k for k, v in worker_errors.items() if v > 5]

        # Event store
        try:
            store = _get_event_store()
            event_count = store.count()
            event_store_ok = True
        except Exception:
            event_count = 0
            event_store_ok = False

        return {
            "fetched_at": _utc_iso(),
            "overall_health": "degraded" if high_failure_workers else "ok",
            "cache": {
                "rows": cache_stats.get("rows", 0),
                "symbols": cache_stats.get("distinct_symbols", 0),
                "healthy": cache_ok,
                "alert": "cache boş veya stale" if not cache_ok else None,
            },
            "workers": {
                "all":   [w["name"] for w in supervisor.status().get("workers", [])],
                "high_failure": high_failure_workers,
                "alert": f"Worker hatalar yüksek: {high_failure_workers}" if high_failure_workers else None,
            },
            "event_store": {
                "total_events": event_count,
                "healthy": event_store_ok,
                "alert": "Event store erişilemiyor" if not event_store_ok else None,
            },
            "alerts": [
                alert for alert in [
                    "cache boş" if not cache_ok else None,
                    f"Worker hata: {high_failure_workers}" if high_failure_workers else None,
                    "Event store erişilemiyor" if not event_store_ok else None,
                ]
                if alert
            ],
            "monitoring_note": (
                "Bu endpoint Prometheus/Grafana veya cron alarm için tasarlanmıştır. "
                "alerts[] doluysa PagerDuty/Telegram alarm tetiklenmelidir."
            ),
        }

    # ── Statik dosyalar (SPA / index.html) ───────────────────────────────
    # Mount en sona; daha spesifik /api/* route'larını gölgelemesin diye.
    # Önce ROOT/index.html'e bak, yoksa frontend/dist/index.html'e düş.
    _spa_root = ROOT / "index.html"
    _spa_dist = ROOT / "frontend" / "dist"
    if _spa_root.exists():
        @app.get("/")
        def root_index() -> FileResponse:
            return FileResponse(ROOT / "index.html")
    elif (_spa_dist / "index.html").exists():
        # Vite build çıktısı frontend/dist altında
        app.mount("/assets", StaticFiles(directory=_spa_dist / "assets"), name="spa_assets")

        @app.get("/")
        def root_index() -> FileResponse:
            return FileResponse(_spa_dist / "index.html")

        @app.get("/{full_path:path}")
        def spa_fallback(full_path: str) -> FileResponse:
            """SPA client-side routing — bilinmeyen path'leri index.html'e yönlendir."""
            if full_path.startswith("api/") or full_path.startswith("ws/"):
                from fastapi import HTTPException
                raise HTTPException(status_code=404)
            return FileResponse(_spa_dist / "index.html")

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


# ── Screener modelleri ──────────────────────────────────────────────────────

class ScreenerFilter(BaseModel):
    column: str
    op: str  # gt, lt, gte, lte, eq, neq
    value: float | str


class ScreenerRunRequest(BaseModel):
    market: str = "BIST"
    universe: str = "BIST100"  # BIST100 | BIST30 | ALL | CRYPTO
    filters: list[ScreenerFilter] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    sort_by: str = "volume"
    sort_dir: str = "desc"  # asc | desc
    limit: int = Field(50, ge=1, le=500)


class ScreenerRow(BaseModel):
    symbol: str
    name: str = ""
    last_price: float | None = None
    change_pct: float | None = None
    volume: float | None = None
    market_cap: float | None = None
    pe_ratio: float | None = None         # Harici veri gerektiriyor; şimdilik None
    rsi_14: float | None = None
    volume_avg_20d: float | None = None   # Son 20 günlük ortalama hacim
    distance_from_52w_high: float | None = None  # 52-haftalık zirveye mesafe (%)
    sector: str = ""


class ScreenerRunResponse(BaseModel):
    run_id: str
    created_at: str
    market: str
    universe: str
    filters_hash: str
    data_snapshot_hash: str = ""   # row verisinin MD5'i — tekrar üretilebilirlik için
    row_count: int
    rows: list[ScreenerRow]
    metadata: dict


# Uvicorn entry point: `uvicorn backend.api.main:app`
app = create_app()
