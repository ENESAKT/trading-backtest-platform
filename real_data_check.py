"""
Quant Engine — Gerçek Veri Kontrol Betiği.

Bu betik yalnızca Yahoo Finance üzerinden alınan gerçek OHLCV verisiyle çalışır.
Veri sağlayıcı boş dönerse veya veri kalite kontrolünden geçmezse backtest başlatmaz.
"""

from __future__ import annotations

import argparse
import datetime as dt
from typing import Any

import pandas as pd

from quant_engine.backtest.engine import BacktestConfig, BacktestEngine
from quant_engine.backtest.metrics import calculate_metrics
from quant_engine.core.protocols import BarRequest, Market, Timeframe
from quant_engine.data.providers.yfinance_provider import YFinanceProvider
from quant_engine.data_pipeline.data_validator import DataValidator
from quant_engine.strategy.base import BaseStrategy
from quant_engine.strategy.examples.bollinger_reversion import BollingerReversion
from quant_engine.strategy.examples.buy_and_hold import BuyAndHold
from quant_engine.strategy.examples.rsi_reversion import RsiReversion
from quant_engine.strategy.examples.sma_crossover import SmaCrossover

STRATEGIES: dict[str, type[BaseStrategy]] = {
    "sma": SmaCrossover,
    "rsi": RsiReversion,
    "bollinger": BollingerReversion,
    "buy_hold": BuyAndHold,
}


def fetch_real_data(symbol: str, start: dt.date, timeframe: Timeframe) -> pd.DataFrame:
    provider = YFinanceProvider(timeout=15)
    result = provider.fetch_bars(
        BarRequest(
            symbol=symbol,
            market=Market.BIST,
            timeframe=timeframe,
            start=start,
            end=dt.date.today(),
        )
    )
    if not result.success or result.data.empty:
        errors = "; ".join(result.errors or ["Geçerli piyasa verisi bulunamadı."])
        raise RuntimeError(errors)
    return result.data


def build_strategy(name: str, params: dict[str, Any]) -> BaseStrategy:
    strategy_cls = STRATEGIES[name]
    strategy = strategy_cls(params=params or None)
    errors = strategy.validate_params()
    if errors:
        raise ValueError("; ".join(errors))
    return strategy


def run_real_backtest(
    data: pd.DataFrame,
    symbol: str,
    strategy_name: str,
    params: dict[str, Any],
    config: BacktestConfig,
):
    strategy = build_strategy(strategy_name, params)
    strategy.prepare(data)
    result = BacktestEngine(config).run(data, strategy.as_signal_func(), symbol=symbol)
    metrics = calculate_metrics(
        result.equity_curve,
        result.fills,
        config.initial_capital,
        timeframe="1d",
        trades=result.trades,
    )
    return result, metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Quant Engine gerçek veri kontrolü")
    parser.add_argument("--symbol", default="THYAO", help="BIST sembolü, örn: THYAO")
    parser.add_argument("--start", default="2022-01-01", help="Başlangıç tarihi: YYYY-AA-GG")
    parser.add_argument(
        "--strategy",
        choices=sorted(STRATEGIES),
        default="sma",
        help="Çalıştırılacak strateji",
    )
    parser.add_argument("--capital", type=float, default=100_000.0, help="Başlangıç sermayesi")
    parser.add_argument("--commission", type=float, default=0.001, help="Komisyon oranı")
    parser.add_argument("--slippage-bps", type=int, default=5, help="Kayma maliyeti bps")
    args = parser.parse_args()

    symbol = args.symbol.upper().replace(".IS", "")
    start = dt.date.fromisoformat(args.start)
    data = fetch_real_data(symbol, start, Timeframe.D1)
    validation = DataValidator(min_rows=60).validate(data, symbol=symbol)
    if not validation.can_run_backtest:
        raise RuntimeError("Veri kalite kontrolü başarısız: " + "; ".join(validation.errors))

    config = BacktestConfig(
        initial_capital=float(args.capital),
        commission_rate=float(args.commission),
        slippage_bps=int(args.slippage_bps),
        max_position_pct=0.95,
    )
    result, metrics = run_real_backtest(data, symbol, args.strategy, {}, config)

    print(f"{symbol}: {len(data)} gerçek bar alındı. Kaynak: yfinance")
    print(f"Strateji: {args.strategy}")
    print(f"Net getiri: {metrics.total_return_pct:.2f}%")
    print(f"Maksimum düşüş: {metrics.max_drawdown_pct:.2f}%")
    print(f"Sharpe: {metrics.sharpe_ratio:.2f}")
    print(f"Trade: {metrics.total_trades}")
    print(f"Açık pozisyon: {'Var' if result.has_open_position else 'Yok'}")


if __name__ == "__main__":
    main()
