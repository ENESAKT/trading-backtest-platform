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

from dataclasses import asdict
from typing import Any

import pandas as pd

from backend.backtest import blueprints as _blueprints  # noqa: F401  (registry trigger)
from backend.data.cache import OHLCVCache
from quant_engine.backtest.engine import BacktestConfig, BacktestEngine
from quant_engine.strategy.registry import get_registry

MIN_BARS = 50


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
        out.append(
            {
                "symbol": t.symbol,
                "entry_time": int(t.entry_date.timestamp()) if t.entry_date else 0,
                "exit_time": int(t.exit_date.timestamp()) if t.exit_date else 0,
                "entry_price": float(t.entry_price),
                "exit_price": float(t.exit_price),
                "quantity": int(t.quantity),
                "net_pnl": float(t.net_pnl),
                "return_pct": float(t.pnl_pct),
                "is_winner": bool(t.is_winner),
            }
        )
    return out


def _signals_payload(trades: list[Any]) -> list[dict[str, Any]]:
    """Frontend ``ChartPanel.setSignals`` ile uyumlu ``Signal[]`` dizisi.

    Her tamamlanmış trade için (BUY giriş, SELL çıkış) iki kayıt yayınlar.
    Açık pozisyonun girişi de eklenir; çıkışı yoktur.
    """
    out: list[dict[str, Any]] = []
    for t in trades:
        out.append(
            {
                "type": "BUY",
                "timestamp": int(t.entry_date.timestamp()) if t.entry_date else 0,
                "price": float(t.entry_price),
                "reason": f"{t.symbol} giriş",
                "strength": 5,
            }
        )
        out.append(
            {
                "type": "SELL",
                "timestamp": int(t.exit_date.timestamp()) if t.exit_date else 0,
                "price": float(t.exit_price),
                "reason": f"{t.symbol} çıkış · PnL {t.net_pnl:.2f}",
                "strength": 5,
            }
        )
    return out


def run_backtest(
    cache: OHLCVCache,
    symbol: str,
    interval: str,
    strategy_id: str,
    params: dict[str, Any] | None = None,
    capital: float = 100_000.0,
    lookback_bars: int = 500,
) -> dict[str, Any]:
    """Backtest çalıştır — JSON-uyumlu sonuç dict'i döndür.

    Hatalar:
      * ``UnknownStrategy`` — registry'de id yok.
      * ``BacktestNotEnoughData`` — cache'te < ``MIN_BARS`` satır.
      * ``BacktestRunError`` — parametre validasyonu / motor hatası.
    """
    registry = get_registry()
    if strategy_id not in registry:
        raise UnknownStrategy(
            f"Bilinmeyen strateji: {strategy_id!r}. "
            f"Mevcut: {registry.get_names()}"
        )

    canonical = symbol.strip().upper()
    raw_bars = cache.get_window(canonical, interval, limit=int(lookback_bars))
    if len(raw_bars) < MIN_BARS:
        raise BacktestNotEnoughData(
            f"Cache'te {symbol} {interval} için yetersiz bar "
            f"({len(raw_bars)} < {MIN_BARS}). Önce sembolü açıp veriyi "
            "doldurun (``/api/v2/candles``)."
        )

    df = _bars_to_dataframe(raw_bars, canonical)

    try:
        strategy = registry.create(strategy_id, params or {})
    except (KeyError, ValueError) as exc:
        raise BacktestRunError(str(exc)) from exc

    errors = strategy.validate_params()
    if errors:
        raise BacktestRunError("; ".join(errors))

    strategy.prepare(df)

    engine = BacktestEngine(
        BacktestConfig(initial_capital=float(capital))
    )
    result = engine.run(df, strategy.as_signal_func(), symbol=canonical)

    return {
        "symbol": canonical,
        "interval": interval,
        "strategy_id": strategy_id,
        "params": dict(strategy.params),
        "capital": float(capital),
        "lookback_bars": len(raw_bars),
        "metrics": {
            "final_equity": float(result.final_equity),
            "total_return_pct": float(result.total_return_pct),
            "max_drawdown_pct": float(result.max_drawdown_pct),
            "total_trades": int(result.total_trades),
            "total_commission": float(result.total_commission),
            "sharpe_ratio": float(result.sharpe_ratio),
            "win_rate": float(result.win_rate),
            "has_open_position": bool(result.has_open_position),
        },
        "assumptions": asdict(result.assumptions),
        "warnings": list(result.warnings),
        "equity_curve": _equity_curve_payload(result.equity_curve),
        "trades": _trades_payload(result.trades),
        "signals": _signals_payload(result.trades),
    }
