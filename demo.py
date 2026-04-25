#!/usr/bin/env python3
"""
Quant Engine — Demo & Test Betiği

Bu betik tüm sistemi uçtan uca gösterir:
1. Yapay veya gerçek (yfinance) veri
2. Strateji seçimi (SMA Crossover, RSI Reversion, Buy & Hold)
3. Backtest çalıştırma
4. Performans metrikleri hesaplama
5. Sonuç raporu + trade detayları

Kullanım:
    source .venv/bin/activate
    python demo.py                    # Yapay veri
    python demo.py --live             # yfinance ile gerçek veri
    python demo.py --symbol GARAN     # Belirli sembol
    python demo.py --optimize         # Grid search
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Proje kökünü Python path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from quant_engine.backtest.engine import (
    BacktestConfig,
    BacktestEngine,
)
from quant_engine.backtest.metrics import calculate_metrics


def setup_logging():
    """Loglama ayarları."""
    logger.remove()
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<level>{message}</level>"
        ),
        level="INFO",
    )


def generate_synthetic_data(
    n_bars: int = 500,
    seed: int = 42,
    symbol: str = "SYNTH",
) -> pd.DataFrame:
    """Yapay OHLCV verisi üret."""
    rng = np.random.default_rng(seed)
    trend = np.linspace(0, 0.3, n_bars)
    noise = rng.standard_normal(n_bars) * 0.02
    returns = trend / n_bars + noise
    prices = 100.0 * np.exp(np.cumsum(returns))
    close = prices
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (
        1 + rng.uniform(0, 0.02, n_bars)
    )
    low = np.minimum(open_, close) * (
        1 - rng.uniform(0, 0.02, n_bars)
    )
    volume = rng.integers(500_000, 5_000_000, n_bars)
    dates = pd.bdate_range(
        "2022-01-03", periods=n_bars, freq="B"
    )
    return pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "symbol": [symbol] * n_bars,
    })


def fetch_live_data(
    symbol: str, start: str = "2022-01-01"
) -> pd.DataFrame:
    """yfinance ile gerçek veri çek."""
    try:
        import yfinance as yf

        ticker = f"{symbol}.IS"
        logger.info(
            f"📡 {ticker} verisi çekiliyor "
            f"({start} → bugün)..."
        )
        df = yf.download(ticker, start=start, progress=False)

        if df.empty:
            logger.error(
                f"❌ {symbol} verisi çekilemedi!"
            )
            return pd.DataFrame()

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["symbol"] = symbol
        logger.info(
            f"✅ {len(df)} bar çekildi "
            f"({df['date'].min()} → {df['date'].max()})"
        )
        return df

    except Exception as e:
        logger.error(f"❌ Veri çekme hatası: {e}")
        return pd.DataFrame()


def run_strategy_comparison(
    data: pd.DataFrame, symbol: str
):
    """3 stratejiyi karşılaştır ve rapor ver."""
    from quant_engine.strategy.examples.buy_and_hold import (
        BuyAndHold,
    )
    from quant_engine.strategy.examples.rsi_reversion import (
        RsiReversion,
    )
    from quant_engine.strategy.examples.sma_crossover import (
        SmaCrossover,
    )

    config = BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,
        slippage_bps=5,
        max_position_pct=0.95,
        warm_up_bars=0,
    )

    strategies = [
        BuyAndHold(),
        SmaCrossover(
            params={
                "fast_period": 10,
                "slow_period": 30,
            }
        ),
        RsiReversion(
            params={
                "rsi_period": 14,
                "oversold": 30,
                "overbought": 70,
            }
        ),
    ]

    engine = BacktestEngine(config)

    print()
    print("═" * 80)
    print(
        "  🚀 QUANT ENGINE — "
        "STRATEJİ KARŞILAŞTIRMA RAPORU"
    )
    print(
        f"  📊 Sembol: {symbol} | "
        f"{len(data)} bar | "
        f"₺{config.initial_capital:,.0f} sermaye"
    )
    print(
        f"  📅 "
        f"{data['date'].min().strftime('%Y-%m-%d')} → "
        f"{data['date'].max().strftime('%Y-%m-%d')}"
    )
    print(
        f"  💰 Komisyon: "
        f"%{config.commission_rate * 100:.1f} | "
        f"Slippage: {config.slippage_bps} bps"
    )
    print("═" * 80)

    results = []

    for strategy in strategies:
        logger.info(
            f"\n🔄 {strategy.name} çalıştırılıyor..."
        )

        strategy.prepare(data)

        result = engine.run(
            data,
            strategy.as_signal_func(),
            symbol=symbol,
        )

        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            config.initial_capital,
            trades=result.trades,
        )

        results.append({
            "strategy": strategy,
            "result": result,
            "metrics": metrics,
        })

    # --- KARŞILAŞTIRMA TABLOSU ---
    print()
    print("─" * 80)
    print(
        f"  {'Strateji':<20} {'Getiri':>10} "
        f"{'CAGR':>8} {'Sharpe':>8} {'MaxDD':>8} "
        f"{'Win%':>7} {'PF':>6} "
        f"{'Trade':>6} {'Son₺':>14}"
    )
    print("─" * 80)

    for r in results:
        m = r["metrics"]
        name = r["strategy"].name
        print(
            f"  {name:<20} "
            f"{m.total_return_pct:>+9.2f}% "
            f"{m.cagr_pct:>+7.2f}% "
            f"{m.sharpe_ratio:>8.2f} "
            f"{m.max_drawdown_pct:>7.2f}% "
            f"{m.win_rate:>6.1f}% "
            f"{m.profit_factor:>6.2f} "
            f"{m.total_trades:>6d} "
            f"₺{m.final_equity:>12,.0f}"
        )

    print("─" * 80)

    # --- EN İYİ STRATEJİ ---
    best = max(
        results,
        key=lambda x: x["metrics"].sharpe_ratio,
    )
    print(
        f"\n  🏆 En iyi Sharpe: "
        f"{best['strategy'].name} "
        f"(Sharpe: {best['metrics'].sharpe_ratio:.2f})"
    )

    # --- DETAYLI METRİKLER ---
    print()
    print(best["metrics"].summary())

    # --- TRADE DETAYLARI ---
    best_result = best["result"]
    if best_result.trades:
        print()
        print("─" * 80)
        print(
            f"  📋 {best['strategy'].name} "
            f"— Son 10 Trade"
        )
        print("─" * 80)
        print(
            f"  {'Giriş':<12} {'Çıkış':<12} "
            f"{'Adet':>8} {'Giriş₺':>10} "
            f"{'Çıkış₺':>10} {'PnL₺':>10} "
            f"{'Sonuç':>5}"
        )
        print("  " + "─" * 70)

        for trade in best_result.trades[-10:]:
            entry = (
                trade.entry_date.strftime("%Y-%m-%d")
                if trade.entry_date
                else "N/A"
            )
            exit_ = (
                trade.exit_date.strftime("%Y-%m-%d")
                if trade.exit_date
                else "N/A"
            )
            icon = "✅" if trade.is_winner else "❌"
            print(
                f"  {entry:<12} {exit_:<12} "
                f"{trade.quantity:>8d} "
                f"₺{trade.entry_price:>9.2f} "
                f"₺{trade.exit_price:>9.2f} "
                f"₺{trade.net_pnl:>+9.0f} "
                f"{icon:>5}"
            )
    elif best_result.fills:
        print()
        print("─" * 80)
        print(
            f"  📋 {best['strategy'].name} "
            f"— Son 10 Fill"
        )
        print("─" * 80)
        for fill in best_result.fills[-10:]:
            ts = fill.fill_timestamp
            ds = (
                ts.strftime("%Y-%m-%d") if ts else "N/A"
            )
            side = (
                "AL"
                if fill.order.side.value == "buy"
                else "SAT"
            )
            print(
                f"  {ds:<12} {side:<5} "
                f"{fill.fill_quantity:>8d} "
                f"₺{fill.fill_price:>9.2f} "
                f"₺{fill.commission:>9.2f}"
            )

    # --- EQUITY CURVE ÖZETİ ---
    print()
    print("─" * 80)
    print(
        f"  📈 Equity Curve Özeti "
        f"({best['strategy'].name})"
    )
    print("─" * 80)

    curve = best_result.equity_curve
    n = len(curve)
    checkpoints = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    for i in checkpoints:
        ep = curve[i]
        ts = ep.timestamp
        ds = ts.strftime("%Y-%m-%d") if ts else "N/A"
        print(
            f"  {ds}  "
            f"₺{ep.total_equity:>12,.0f}  "
            f"DD: {ep.drawdown_pct:>5.1f}%  "
            f"Nakit: ₺{ep.cash:>12,.0f}"
        )

    # Uyarılar
    if best_result.warnings:
        print()
        print("─" * 80)
        print("  ⚠️ UYARILAR:")
        for w in best_result.warnings:
            print(f"    - {w}")

    print()
    print("═" * 80)
    print("  ✅ Demo tamamlandı!")
    print("═" * 80)
    print()


def run_optimization_demo(
    data: pd.DataFrame, symbol: str
):
    """Grid search demo."""
    from quant_engine.research.optimizer import (
        GridSearchOptimizer,
    )
    from quant_engine.strategy.examples.sma_crossover import (
        SmaCrossover,
    )

    config = BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,
        slippage_bps=5,
        max_position_pct=0.95,
    )

    optimizer = GridSearchOptimizer(
        config, data, symbol,
    )

    print()
    print("═" * 80)
    print("  🔍 GRID SEARCH OPTİMİZASYON")
    print("═" * 80)

    result = optimizer.run(
        SmaCrossover,
        {
            "fast_period": [5, 10, 15, 20],
            "slow_period": [20, 30, 40, 50, 60],
        },
        ranking_metric="sharpe_ratio",
    )

    df = result.top_n(10)
    if not df.empty:
        print()
        print("  🏆 En İyi 10 Sonuç:")
        print("─" * 80)
        print(
            df[
                [
                    "fast_period",
                    "slow_period",
                    "sharpe_ratio",
                    "total_return_pct",
                    "max_drawdown_pct",
                    "total_trades",
                ]
            ].to_string(index=False)
        )

    if result.warnings:
        print()
        for w in result.warnings:
            print(f"  {w}")

    print()
    print("═" * 80)
    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Quant Engine Demo — Strateji Karşılaştırma"
        )
    )
    parser.add_argument(
        "--symbol",
        "-s",
        default="THYAO",
        help="BIST sembolü (varsayılan: THYAO)",
    )
    parser.add_argument(
        "--start",
        default="2022-01-01",
        help="Başlangıç tarihi",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Gerçek veri kullan (yfinance)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Yapay veri bar sayısı",
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Grid search optimizasyonu çalıştır",
    )

    args = parser.parse_args()
    setup_logging()

    if args.live:
        data = fetch_live_data(args.symbol, args.start)
        if data.empty:
            logger.error(
                "Gerçek veri çekilemedi, "
                "yapay veriye geçiliyor..."
            )
            data = generate_synthetic_data(
                args.bars, symbol=args.symbol
            )
        symbol = args.symbol
    else:
        symbol = "SYNTH"
        data = generate_synthetic_data(
            args.bars, symbol=symbol
        )
        logger.info(
            f"📊 Yapay veri üretildi: {len(data)} bar "
            f"(gerçek veri için --live kullanın)"
        )

    run_strategy_comparison(data, symbol)

    if args.optimize:
        run_optimization_demo(data, symbol)


if __name__ == "__main__":
    main()
