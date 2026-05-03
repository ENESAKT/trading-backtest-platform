"""``BacktestEngine``'i HTTP/JSON katmanında tüketilebilir hale getir.

Sprint 3.2 + 3.3'ün motoru. Cache'ten OHLCV alır, ``StrategyRegistry``
üzerinden strateji oluşturur, ``BacktestEngine.run`` ile koşturur ve
JSON-serializable bir özet döndürür.

Akış (özet):

1. ``OHLCVCache.get_window`` → bar listesi (en yeni N).
2. ``pandas.DataFrame``'e dönüş → engine ``date`` sütununu bekler.
3. ``StrategyRegistry.create(strategy_id, params)`` → ``BaseStrategy``.
4. ``strategy.validate_params()`` → boş değilse 400.
5. ``strategy.prepare(df)`` indikatörleri önceden hesaplar.
6. ``BacktestEngine.run(df, strategy.as_signal_func(), symbol)`` → ``BacktestResult``.
7. JSON özeti üret: ``metrics``, ``equity_curve``, ``trades``, ``signals``.

Strateji listesi: ``backend.backtest.blueprints``.
"""

from __future__ import annotations

import datetime as dt
import io
import math
from dataclasses import asdict
from typing import Any

import pandas as pd

from backend.backtest import blueprints as _blueprints  # noqa: F401  (registry trigger)
from backend.data.cache import OHLCVCache
from backend.data.historical_store import HistoricalStore
from quant_engine.backtest.engine import BacktestConfig, BacktestEngine, QualityWarning
from quant_engine.research.monte_carlo import run_monte_carlo
from quant_engine.research.paper_ops import generate_preflight_checklist
from quant_engine.research.portfolio_lab import portfolio_metrics
from quant_engine.research.walk_forward import run_walk_forward_analysis
from quant_engine.strategy.registry import get_registry
from quant_engine.strategy.spec import FormulaError, StrategySpecSignal, validate_strategy_spec

MIN_BARS = 50
DEFAULT_SOURCE_MODE = "cache_only"


class BacktestRunError(Exception):
    """Generic backtest failure (invalid params, fill not produced, ...)."""


class UnknownStrategy(BacktestRunError):
    """Strategy id not in registry."""


class BacktestNotEnoughData(BacktestRunError):
    """Cache'te yeterli bar yok."""


def _bars_to_dataframe(bars: list[dict[str, Any]], symbol: str) -> pd.DataFrame:
    df = pd.DataFrame(bars)
    if df.empty:
        return df
    # Engine ``date`` sütununu bekler — cache UNIX saniye veriyor.
    df["date"] = pd.to_datetime(df["time"], unit="s", utc=True)
    df["symbol"] = symbol
    return df[["date", "symbol", "open", "high", "low", "close", "volume"]]


def _parse_date_boundary(value: str | None, *, end: bool = False) -> int | None:
    if not value:
        return None
    try:
        ts = pd.Timestamp(value)
    except Exception as exc:  # noqa: BLE001
        raise BacktestRunError(f"Geçersiz tarih: {value}") from exc
    if ts.tzinfo is None:
        ts = ts.tz_localize("UTC")
    else:
        ts = ts.tz_convert("UTC")
    if end and len(value) <= 10:
        ts = ts + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    return int(ts.timestamp())


def _interval_seconds(interval: str) -> int:
    table = {
        "1m": 60,
        "5m": 300,
        "15m": 900,
        "30m": 1800,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
        "1w": 604800,
    }
    return table.get(interval, 900)


def _date_range_payload(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {"start": None, "end": None}
    start = pd.Timestamp(df.iloc[0]["date"])
    end = pd.Timestamp(df.iloc[-1]["date"])
    return {
        "start": int(start.timestamp()),
        "end": int(end.timestamp()),
        "start_iso": start.isoformat(),
        "end_iso": end.isoformat(),
    }


def _coverage_pct(
    bars: list[dict[str, Any]],
    interval: str,
    start_ts: int | None,
    end_ts: int | None,
) -> float:
    if not bars:
        return 0.0
    if start_ts is None or end_ts is None or end_ts <= start_ts:
        return 100.0
    expected = math.floor((end_ts - start_ts) / _interval_seconds(interval)) + 1
    if expected <= 0:
        return 100.0
    return min(100.0, (len(bars) / expected) * 100.0)


def _csv_text_to_bars(csv_text: str) -> list[dict[str, Any]]:
    if not csv_text.strip():
        raise BacktestRunError("CSV import için veri boş olamaz.")
    df = pd.read_csv(io.StringIO(csv_text))
    lower_cols = {str(c).lower(): c for c in df.columns}
    time_col = lower_cols.get("time") or lower_cols.get("date")
    required = ["open", "high", "low", "close", "volume"]
    missing = [c for c in required if c not in lower_cols]
    if time_col is None:
        missing.append("time/date")
    if missing:
        raise BacktestRunError(f"CSV kolonları eksik: {', '.join(missing)}")

    out: list[dict[str, Any]] = []
    for row_idx, row in df.iterrows():
        try:
            ts_raw = row[time_col]
            ts = (
                pd.to_datetime(float(ts_raw), unit="s", utc=True)
                if isinstance(ts_raw, (int, float)) or str(ts_raw).isdigit()
                else pd.to_datetime(ts_raw, utc=True)
            )
            out.append(
                {
                    "time": int(ts.timestamp()),
                    "open": float(row[lower_cols["open"]]),
                    "high": float(row[lower_cols["high"]]),
                    "low": float(row[lower_cols["low"]]),
                    "close": float(row[lower_cols["close"]]),
                    "volume": float(row[lower_cols["volume"]]),
                }
            )
        except Exception as exc:  # noqa: BLE001
            raise BacktestRunError(f"CSV satır {row_idx + 2} okunamadı: {exc}") from exc
    return out


def _validate_ohlcv_bars(bars: list[dict[str, Any]], *, source: str) -> list[str]:
    warnings: list[str] = []
    if not bars:
        raise BacktestNotEnoughData(f"{source} veri seti boş.")
    seen: set[int] = set()
    last_ts: int | None = None
    for idx, bar in enumerate(bars):
        ts = int(bar["time"])
        if ts in seen:
            raise BacktestRunError(f"{source}: duplicate bar timestamp: {ts}")
        seen.add(ts)
        if last_ts is not None and ts <= last_ts:
            raise BacktestRunError(f"{source}: tarih sırası bozuk (satır {idx + 1}).")
        last_ts = ts
        for key in ("open", "high", "low", "close"):
            value = float(bar[key])
            if not math.isfinite(value) or value <= 0:
                raise BacktestRunError(f"{source}: {key} sıfır/negatif olamaz (satır {idx + 1}).")
        if float(bar["volume"]) < 0:
            raise BacktestRunError(f"{source}: volume negatif olamaz (satır {idx + 1}).")
        high = float(bar["high"])
        low = float(bar["low"])
        open_ = float(bar["open"])
        close = float(bar["close"])
        if high < max(open_, close) or low > min(open_, close):
            raise BacktestRunError(f"{source}: OHLC tutarsızlığı (satır {idx + 1}).")
    returns = pd.Series([float(b["close"]) for b in bars]).pct_change().abs().dropna()
    if not returns.empty and float(returns.max()) > 0.25:
        warnings.append("Veride %25 üzeri tek bar hareketi var; spike/outlier olabilir.")
    return warnings


def _equity_curve_payload(curve: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for ep in curve:
        ts = getattr(ep, "timestamp", None)
        unix = int(ts.timestamp()) if ts is not None else 0
        out.append(
            {
                "time": unix,
                "bar_index": getattr(ep, "bar_index", 0),
                "cash": float(getattr(ep, "cash", 0.0)),
                "position_value": float(getattr(ep, "position_value", 0.0)),
                "total_equity": float(getattr(ep, "total_equity", 0.0)),
                "drawdown": float(getattr(ep, "drawdown", 0.0)),
            }
        )
    return out


def _trades_payload(trades: list[Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for t in trades:
        is_short = getattr(t, "side", None).value == "sell"
        out.append(
            {
                "symbol": t.symbol,
                "side": "SHORT" if is_short else "LONG",
                "entry_type": "SHORT" if is_short else "BUY",
                "exit_type": "COVER" if is_short else "SELL",
                "entry_time": int(t.entry_date.timestamp()) if t.entry_date else 0,
                "exit_time": int(t.exit_date.timestamp()) if t.exit_date else 0,
                "entry_price": float(t.entry_price),
                "exit_price": float(t.exit_price),
                "quantity": int(t.quantity),
                "net_pnl": float(t.net_pnl),
                "return_pct": float(t.pnl_pct),
                "is_winner": bool(t.is_winner),
                "commission": float(t.total_commission),
                "slippage_cost": float(t.total_slippage_cost),
                "entry_bar_index": int(t.entry_bar_index),
                "exit_bar_index": int(t.exit_bar_index),
            }
        )
    return out


def _signals_payload(
    fills: list[Any],
    trades: list[Any],
    equity_curve: list[Any],
) -> list[dict[str, Any]]:
    """Frontend ``ChartPanel.setSignals`` ile uyumlu ``Signal[]`` dizisi."""
    pnl_by_exit: dict[int, float] = {
        int(t.exit_bar_index): float(t.net_pnl)
        for t in trades
    }
    closed_entry_bars: set[int] = {
        int(t.entry_bar_index)
        for t in trades
    }
    equity_by_bar: dict[int, float] = {
        int(p.bar_index): float(p.total_equity)
        for p in equity_curve
    }
    out: list[dict[str, Any]] = []
    for fill in fills:
        intent = str(getattr(fill.order, "intent", "") or fill.order.side.value.upper())
        sig_type = {
            "BUY": "BUY",
            "SELL": "SELL",
            "SHORT": "SHORT",
            "COVER": "COVER",
        }.get(intent, "BUY" if fill.order.side.value == "buy" else "SELL")
        pnl = pnl_by_exit.get(int(fill.bar_index))
        is_open_position = (
            sig_type in {"BUY", "SHORT"}
            and int(fill.bar_index) not in closed_entry_bars
        )
        reason = f"{fill.order.symbol} {sig_type}"
        if pnl is not None:
            reason += f" · PnL {pnl:.2f}"
        if is_open_position:
            reason += " · Açık pozisyon"
        out.append(
            {
                "type": sig_type,
                "timestamp": int(fill.fill_timestamp.timestamp()) if fill.fill_timestamp else 0,
                "price": float(fill.fill_price),
                "quantity": int(fill.fill_quantity),
                "reason": reason,
                "strength": 5,
                "bar_index": int(fill.bar_index),
                "pnl": pnl,
                "equity": equity_by_bar.get(int(fill.bar_index)),
                "open_position": is_open_position,
            }
        )
    return out


def _profit_factor(trades: list[Any]) -> float:
    gross_profit = sum(float(t.net_pnl) for t in trades if t.net_pnl > 0)
    gross_loss = sum(abs(float(t.net_pnl)) for t in trades if t.net_pnl < 0)
    if gross_loss == 0:
        return 1_000_000.0 if gross_profit > 0 else 0.0
    return gross_profit / gross_loss


def _annualized_return_pct(final_equity: float, initial: float, df: pd.DataFrame) -> float:
    if df.empty or initial <= 0:
        return 0.0
    start = pd.Timestamp(df.iloc[0]["date"])
    end = pd.Timestamp(df.iloc[-1]["date"])
    days = max(1.0, (end - start).total_seconds() / 86400)
    years = days / 365.25
    if years <= 0:
        return 0.0
    return ((final_equity / initial) ** (1 / years) - 1) * 100


def _benchmark_return_pct(df: pd.DataFrame) -> float:
    if len(df) < 2:
        return 0.0
    first = float(df.iloc[0]["open"])
    last = float(df.iloc[-1]["close"])
    if first <= 0:
        return 0.0
    return (last / first - 1) * 100


def _make_engine_config(
    *,
    capital: float,
    commission_rate: float,
    slippage_bps: int,
    slippage_model: str,
    slippage_tick: float,
    volume_limit_pct: float,
    volume_window: int,
    max_position_pct: float,
    allow_short: bool,
) -> BacktestConfig:
    return BacktestConfig(
        initial_capital=float(capital),
        commission_rate=float(commission_rate),
        slippage_bps=int(slippage_bps),
        slippage_model=str(slippage_model),
        slippage_tick=float(slippage_tick),
        volume_limit_pct=float(volume_limit_pct),
        volume_window=int(volume_window),
        max_position_pct=float(max_position_pct),
        allow_short=bool(allow_short),
    )


def _walk_forward_payload(
    *,
    df: pd.DataFrame,
    run_slice: Any,
    params: dict[str, Any],
) -> dict[str, Any]:
    if len(df) < 120:
        return {
            "windows": [],
            "total_oos_return_pct": 0.0,
            "walk_forward_efficiency": 0.0,
            "passed": False,
            "warnings": [
                "Walk-forward analizi için en az 120 bar önerilir; mevcut veri yetersiz."
            ],
        }

    in_sample_bars = max(MIN_BARS, len(df) // 3)
    out_of_sample_bars = max(20, len(df) // 10)
    step_bars = out_of_sample_bars

    if in_sample_bars + out_of_sample_bars > len(df):
        return {
            "windows": [],
            "total_oos_return_pct": 0.0,
            "walk_forward_efficiency": 0.0,
            "passed": False,
            "warnings": ["Walk-forward pencereleri için yeterli bar yok."],
        }

    def score_func(_params: dict[str, Any], in_sample: pd.DataFrame) -> float:
        return float(run_slice(in_sample).total_return_pct)

    def out_of_sample_return_func(_params: dict[str, Any], out_of_sample: pd.DataFrame) -> float:
        return float(run_slice(out_of_sample).total_return_pct)

    try:
        report = run_walk_forward_analysis(
            df,
            [dict(params)],
            score_func,
            out_of_sample_return_func,
            in_sample_bars=in_sample_bars,
            out_of_sample_bars=out_of_sample_bars,
            step_bars=step_bars,
            min_window_efficiency=0.0,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "windows": [],
            "total_oos_return_pct": 0.0,
            "walk_forward_efficiency": 0.0,
            "passed": False,
            "warnings": [f"Walk-forward analizi üretilemedi: {exc}"],
        }

    payload = report.to_dict()
    payload["warnings"] = [
        "WFA mevcut parametrelerle doğrulama olarak çalışır; ayrı grid optimizasyonu henüz bağlı değil.",
        *payload.get("warnings", []),
    ]
    return payload


def _monte_carlo_payload(
    *,
    trades: list[Any],
    capital: float,
) -> dict[str, Any]:
    pnl_series = [float(getattr(trade, "net_pnl", 0.0)) for trade in trades]
    report = run_monte_carlo(
        pnl_series,
        initial_capital=float(capital),
        n_simulations=1000,
        method="bootstrap",
        seed=42,
    )
    warnings = list(report.warnings)
    if len(pnl_series) < 10:
        warnings.append(
            "Monte Carlo sonucu düşük işlem sayısı nedeniyle dikkatli yorumlanmalı."
        )
    return {
        "median_final_equity": report.median_final_equity,
        "p05_final_equity": report.p05_final_equity,
        "p95_final_equity": report.p95_final_equity,
        "probability_of_loss": report.probability_of_loss,
        "median_max_drawdown_pct": report.median_max_drawdown_pct,
        "p95_max_drawdown_pct": report.p95_max_drawdown_pct,
        "warnings": warnings,
    }


def _portfolio_lab_payload(result: Any) -> dict[str, Any]:
    equity_values = [
        float(getattr(point, "total_equity", 0.0))
        for point in getattr(result, "equity_curve", [])
    ]
    if len(equity_values) < 2:
        return {
            "metrics": portfolio_metrics(pd.Series([], dtype=float)),
            "strategy_count": 1,
            "warnings": ["Portföy özeti için yeterli equity verisi yok."],
        }
    index = [
        getattr(point, "timestamp", None) or idx
        for idx, point in enumerate(getattr(result, "equity_curve", []))
    ]
    curve = pd.Series(equity_values, index=index)
    return {
        "metrics": portfolio_metrics(curve),
        "strategy_count": 1,
        "warnings": [
            "Bu özet tek strateji equity curve'ünden üretilmiştir; çoklu strateji birleşimi Portfolio Lab helper'larıyla desteklenir."
        ],
    }


def _paper_operation_payload(
    *,
    payload: dict[str, Any],
    result: Any,
    df: pd.DataFrame,
    allow_short: bool,
) -> dict[str, Any]:
    data_source = payload.get("data_source") or {}
    assumptions = payload.get("assumptions") or {}
    wfa = payload.get("walk_forward_report") or {}
    mc = payload.get("monte_carlo_report") or {}
    checklist = generate_preflight_checklist(
        {
            "has_real_data": bool(data_source.get("is_real")),
            "bar_count": int(data_source.get("bar_count") or len(df)),
            "wfa_passed": bool(wfa.get("passed")),
            "monte_carlo_passed": float(mc.get("probability_of_loss", 1.0)) < 0.5,
            "has_slippage": float(assumptions.get("slippage_bps", 0) or 0) > 0,
            "avg_volume": float(df["volume"].tail(20).mean()) if "volume" in df else 0.0,
            "market": "BIST" if str(payload.get("symbol", "")).endswith(".IS") else "OTHER",
            "allows_short": bool(allow_short),
        }
    )
    return {
        "mode": "paper_only",
        "real_order_enabled": False,
        "preflight": checklist,
        "last_signal": (payload.get("signals") or [])[-1] if payload.get("signals") else None,
        "warnings": [
            "Gerçek emir gönderimi yoktur; bu özet yalnızca paper/alarm operasyon görünürlüğü sağlar."
        ],
    }


def _report_payload(
    *,
    result: Any,
    df: pd.DataFrame,
    symbol: str,
    interval: str,
    strategy_id: str,
    strategy_name: str,
    params: dict[str, Any],
    capital: float,
    source_mode: str,
    data_source: dict[str, Any],
    strategy_spec: dict[str, Any] | None = None,
) -> dict[str, Any]:
    trades = list(result.trades)
    net_pnl = float(result.final_equity) - float(capital)
    winners = [float(t.net_pnl) for t in trades if t.net_pnl > 0]
    losers = [float(t.net_pnl) for t in trades if t.net_pnl < 0]
    best = max([float(t.net_pnl) for t in trades], default=0.0)
    worst = min([float(t.net_pnl) for t in trades], default=0.0)
    total_slippage = sum(float(getattr(t, "total_slippage_cost", 0.0)) for t in trades)
    date_range = _date_range_payload(df)
    assumptions = asdict(result.assumptions)
    assumptions["allow_short"] = bool(strategy_spec) and any(
        str(strategy_spec.get("rules", {}).get(k, "")).strip()
        for k in ("short_entry", "short_exit")
    )
    return {
        "title": f"{strategy_name} · {symbol} · {interval}",
        "generated_at": dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat(),
        "symbol": symbol,
        "interval": interval,
        "last_price": float(df.iloc[-1]["close"]) if not df.empty else 0.0,
        "strategy_id": strategy_id,
        "strategy_name": strategy_name,
        "params": params,
        "strategy_spec": strategy_spec,
        "capital": float(capital),
        "source_mode": source_mode,
        "date_range": date_range,
        "data_source": data_source,
        "summary_text": (
            "Bu strateji seçilen tarih aralığında ve varsayımlarla test edilseydi "
            "yaklaşık sonuç budur; gelecek kazancı garanti etmez."
        ),
        "metrics": {
            "initial_capital": float(capital),
            "final_equity": float(result.final_equity),
            "net_pnl": net_pnl,
            "total_return_pct": float(result.total_return_pct),
            "annualized_return_pct": _annualized_return_pct(result.final_equity, capital, df),
            "max_drawdown_pct": float(result.max_drawdown_pct),
            "total_trades": int(result.total_trades),
            "total_commission": float(result.total_commission),
            "total_slippage": total_slippage,
            "sharpe_ratio": float(result.sharpe_ratio),
            "win_rate": float(result.win_rate),
            "profit_factor": _profit_factor(trades),
            "best_trade": best,
            "worst_trade": worst,
            "avg_win": sum(winners) / len(winners) if winners else 0.0,
            "avg_loss": sum(losers) / len(losers) if losers else 0.0,
            "benchmark_return_pct": _benchmark_return_pct(df),
            "has_open_position": bool(result.has_open_position),
        },
        "assumptions": assumptions,
        "quality_score": getattr(result, "quality_score", 100),
        "warnings": [
            {
                "code": getattr(w, "code", "UNKNOWN"),
                "severity": getattr(w, "severity", "low"),
                "message": getattr(w, "message", str(w))
            }
            for w in result.warnings
        ],
        "equity_curve": _equity_curve_payload(result.equity_curve),
        "trades": _trades_payload(result.trades),
        "signals": _signals_payload(result.fills, result.trades, result.equity_curve),
    }


def run_backtest(
    cache: OHLCVCache,
    symbol: str,
    interval: str,
    strategy_id: str = "",
    params: dict[str, Any] | None = None,
    capital: float = 100_000.0,
    lookback_bars: int = 500,
    start_date: str | None = None,
    end_date: str | None = None,
    commission_rate: float = 0.001,
    slippage_bps: int = 5,
    slippage_model: str = "fixed_bps",
    slippage_tick: float = 0.01,
    volume_limit_pct: float = 0.05,
    volume_window: int = 5,
    max_position_pct: float = 0.20,
    allow_short: bool = False,
    source_mode: str = DEFAULT_SOURCE_MODE,
    strategy_spec: dict[str, Any] | None = None,
    csv_text: str | None = None,
    csv_bars: list[dict[str, Any]] | None = None,
    data_service: Any | None = None,
    historical_store: HistoricalStore | None = None,
) -> dict[str, Any]:
    """Backtest çalıştır — JSON-uyumlu sonuç dict'i döndür.

    Hatalar:
      * ``UnknownStrategy`` — registry'de id yok.
      * ``BacktestNotEnoughData`` — cache'te < ``MIN_BARS`` satır.
      * ``BacktestRunError`` — parametre validasyonu / motor hatası.
    """
    canonical = symbol.strip().upper()
    source_mode = source_mode or DEFAULT_SOURCE_MODE
    start_ts = _parse_date_boundary(start_date)
    end_ts = _parse_date_boundary(end_date, end=True)
    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        raise BacktestRunError("Başlangıç tarihi bitiş tarihinden sonra olamaz.")

    data_warnings: list[str] = []
    provider_meta: dict[str, Any] = {}

    if source_mode == "csv_import":
        if csv_bars is not None:
            raw_bars = [
                {
                    "time": int(b["time"]),
                    "open": float(b["open"]),
                    "high": float(b["high"]),
                    "low": float(b["low"]),
                    "close": float(b["close"]),
                    "volume": float(b["volume"]),
                }
                for b in csv_bars
            ]
        else:
            raw_bars = _csv_text_to_bars(csv_text or "")
        raw_bars = [
            b for b in raw_bars
            if (start_ts is None or int(b["time"]) >= start_ts)
            and (end_ts is None or int(b["time"]) <= end_ts)
        ]
        data_warnings.extend(_validate_ohlcv_bars(raw_bars, source="CSV"))
        provider_meta = {
            "source": "csv_import",
            "provider_name": "CSV",
            "is_real": False,
            "status": "imported",
        }
    else:
        if source_mode not in {"cache_only", "cache_then_provider"}:
            raise BacktestRunError(
                "source_mode cache_only, cache_then_provider veya csv_import olmalı."
            )
        raw_bars = cache.get_window(
            canonical,
            interval,
            start_ts=start_ts,
            end_ts=end_ts,
            limit=None if start_ts or end_ts else int(lookback_bars),
        )
        if len(raw_bars) < MIN_BARS and historical_store is not None:
            historical = historical_store.read_bars(
                canonical,
                interval=interval,
                limit=None if start_date or end_date else int(lookback_bars),
                start=start_date,
                end=end_date,
            )
            if historical.bars:
                cache.upsert_bars(canonical, interval, historical.bars)
                raw_bars = historical.bars
                provider_meta = {
                    "source": "local_parquet",
                    "provider_name": "HistoricalStore",
                    "is_real": True,
                    "status": "ok",
                    "storage_symbol": historical.storage_symbol,
                }
        if (
            source_mode == "cache_then_provider"
            and len(raw_bars) < MIN_BARS
            and data_service is not None
        ):
            payload = data_service.fetch_candles(
                symbol=canonical,
                interval=interval,
                limit=int(lookback_bars),
            )
            provider_meta = dict(payload.get("metadata") or {})
            provider_meta.setdefault("source", "provider")
            provider_meta.setdefault("provider_name", data_service.__class__.__name__)
            provider_meta.setdefault("status", payload.get("status", "unknown"))
            provider_bars = payload.get("bars") or []
            if payload.get("status") == "ok" and provider_bars:
                cache.upsert_bars(canonical, interval, provider_bars)
                raw_bars = cache.get_window(
                    canonical,
                    interval,
                    start_ts=start_ts,
                    end_ts=end_ts,
                    limit=None if start_ts or end_ts else int(lookback_bars),
                )
        if not provider_meta:
            if (
                interval == "1d"
                and historical_store is not None
                and historical_store.has_symbol(canonical)
                and raw_bars
            ):
                provider_meta = {
                    "source": "local_parquet_cache",
                    "provider_name": "HistoricalStore/OHLCVCache",
                    "is_real": True,
                    "status": "ok",
                    "storage_symbol": historical_store.storage_symbol(canonical),
                }
            else:
                provider_meta = {
                    "source": "cache",
                    "provider_name": "OHLCVCache",
                    "is_real": False,
                    "status": "ok" if raw_bars else "empty",
                }
        if raw_bars:
            data_warnings.extend(_validate_ohlcv_bars(raw_bars, source="Cache"))

    if len(raw_bars) < MIN_BARS:
        raise BacktestNotEnoughData(
            f"Cache'te {symbol} {interval} için yetersiz bar "
            f"({len(raw_bars)} < {MIN_BARS}). Önce sembolü açıp veriyi "
            "doldurun (``/api/v2/candles``)."
        )

    df = _bars_to_dataframe(raw_bars, canonical)
    coverage = _coverage_pct(raw_bars, interval, start_ts, end_ts)
    if coverage < 99.0:
        data_warnings.append(
            "Bu test veri aralığının tamamını kapsamıyor "
            f"(yaklaşık %{coverage:.1f} kapsama)."
        )

    provider_meta.setdefault("data_coverage_pct", coverage)
    provider_meta.setdefault("bar_count", len(raw_bars))

    engine_config = _make_engine_config(
        capital=float(capital),
        commission_rate=float(commission_rate),
        slippage_bps=int(slippage_bps),
        slippage_model=str(slippage_model),
        slippage_tick=float(slippage_tick),
        volume_limit_pct=float(volume_limit_pct),
        volume_window=int(volume_window),
        max_position_pct=float(max_position_pct),
        allow_short=bool(allow_short),
    )
    engine = BacktestEngine(engine_config)
    normalized_spec: dict[str, Any] | None = None
    run_slice_for_wfa = None

    if strategy_spec:
        try:
            normalized_spec = validate_strategy_spec(strategy_spec)
        except FormulaError as exc:
            raise BacktestRunError(str(exc)) from exc
        strategy_name = str(normalized_spec.get("name") or "Kural Stratejisi")
        spec_signal = StrategySpecSignal(
            normalized_spec,
            df,
            allow_short=bool(allow_short),
        )
        result = engine.run_intents(df, spec_signal, symbol=canonical)
        if allow_short and normalized_spec["rules"].get("short_entry"):
            result.warnings.append(
                QualityWarning(
                    code="BIST_SHORT_SIMULATION",
                    severity="medium",
                    message="Short işlemler simülasyondur; gerçek emir uygunluğu ayrıca kontrol edilmelidir."
                )
            )
        strategy_key = strategy_id or "strategy_spec"
        out_params: dict[str, Any] = {}

        def run_slice_for_wfa(slice_df: pd.DataFrame) -> Any:
            slice_signal = StrategySpecSignal(
                normalized_spec or {},
                slice_df,
                allow_short=bool(allow_short),
            )
            return BacktestEngine(engine_config).run_intents(
                slice_df,
                slice_signal,
                symbol=canonical,
            )
    else:
        registry = get_registry()
        if strategy_id not in registry:
            raise UnknownStrategy(
                f"Bilinmeyen strateji: {strategy_id!r}. "
                f"Mevcut: {registry.get_names()}"
            )

        try:
            strategy = registry.create(strategy_id, params or {})
        except (KeyError, ValueError) as exc:
            raise BacktestRunError(str(exc)) from exc

        errors = strategy.validate_params()
        if errors:
            raise BacktestRunError("; ".join(errors))

        strategy.prepare(df)
        result = engine.run(df, strategy.as_signal_func(), symbol=canonical)
        strategy_name = getattr(strategy, "description", "") or strategy_id
        strategy_key = strategy_id
        out_params = dict(strategy.params)

        def run_slice_for_wfa(slice_df: pd.DataFrame) -> Any:
            slice_strategy = get_registry().create(strategy_id, out_params)
            slice_strategy.prepare(slice_df)
            return BacktestEngine(engine_config).run(
                slice_df,
                slice_strategy.as_signal_func(),
                symbol=canonical,
            )

    
    normalized_data_warnings = []
    for w in data_warnings:
        if isinstance(w, str):
            normalized_data_warnings.append(QualityWarning(code="DATA_ISSUE", severity="medium", message=w))
        else:
            normalized_data_warnings.append(w)
            
    result.warnings = [*normalized_data_warnings, *result.warnings]
    payload = _report_payload(
        result=result,
        df=df,
        symbol=canonical,
        interval=interval,
        strategy_id=strategy_key,
        strategy_name=strategy_name,
        params=out_params,
        capital=float(capital),
        source_mode=source_mode,
        data_source=provider_meta,
        strategy_spec=normalized_spec,
    )
    payload["lookback_bars"] = len(raw_bars)
    payload["walk_forward_report"] = _walk_forward_payload(
        df=df,
        run_slice=run_slice_for_wfa,
        params=out_params,
    )
    payload["monte_carlo_report"] = _monte_carlo_payload(
        trades=list(result.trades),
        capital=float(capital),
    )
    payload["portfolio_lab_summary"] = _portfolio_lab_payload(result)
    payload["paper_operation_summary"] = _paper_operation_payload(
        payload=payload,
        result=result,
        df=df,
        allow_short=bool(allow_short),
    )
    return payload
