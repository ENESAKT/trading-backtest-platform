#!/usr/bin/env python3
"""
Quant Engine — Demo & Test Betiği

Bu betik tüm sistemi uçtan uca gösterir:
1. Yapay veya gerçek (yfinance) veri
2. Strateji seçimi (SMA Crossover, RSI Reversion, Buy & Hold)
3. Backtest çalıştırma
4. Performans metrikleri hesaplama
5. Sonuç raporu

Kullanım:
    source .venv/bin/activate
    python demo.py                    # Yapay veri + 3 strateji karşılaştırması
    python demo.py --live             # yfinance ile gerçek veri
    python demo.py --symbol GARAN     # Belirli sembol (internet gerekli)
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Proje kökünü Python path'e ekle
sys.path.insert(0, str(Path(__file__).resolve().parent))

from loguru import logger

from quant_engine.backtest.engine import BacktestConfig, BacktestEngine
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
    """
    Yapay OHLCV verisi üret — internet gerektirmez.

    Trend + mean reversion + volatilite rejimi ile
    gerçekçi fiyat hareketi simüle eder.
    """
    rng = np.random.default_rng(seed)

    # Trend + noise
    trend = np.linspace(0, 0.3, n_bars)  # hafif yükseliş trendi
    noise = rng.standard_normal(n_bars) * 0.02
    returns = trend / n_bars + noise

    # Fiyat serisi
    prices = 100.0 * np.exp(np.cumsum(returns))

    # OHLCV
    close = prices
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * (1 + rng.uniform(0, 0.02, n_bars))
    low = np.minimum(open_, close) * (1 - rng.uniform(0, 0.02, n_bars))
    volume = rng.integers(500_000, 5_000_000, n_bars)

    dates = pd.bdate_range("2022-01-03", periods=n_bars, freq="B")

    return pd.DataFrame({
        "date": dates,
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": volume,
        "symbol": [symbol] * n_bars,
    })


def fetch_live_data(symbol: str, start: str = "2022-01-01") -> pd.DataFrame:
    """yfinance ile gerçek veri çek."""
    try:
        import yfinance as yf

        ticker = f"{symbol}.IS"
        logger.info(f"📡 {ticker} verisi çekiliyor ({start} → bugün)...")
        df = yf.download(ticker, start=start, progress=False)

        if df.empty:
            logger.error(f"❌ {symbol} verisi çekilemedi!")
            return pd.DataFrame()

        df = df.reset_index()
        df.columns = [c.lower() for c in df.columns]
        df["symbol"] = symbol
        logger.info(f"✅ {len(df)} bar çekildi ({df['date'].min()} → {df['date'].max()})")
        return df

    except Exception as e:
        logger.error(f"❌ Veri çekme hatası: {e}")
        return pd.DataFrame()


def run_strategy_comparison(data: pd.DataFrame, symbol: str):
    """3 stratejiyi karşılaştır ve rapor ver."""

    # İmportlar
    from quant_engine.strategy.examples.buy_and_hold import BuyAndHold
    from quant_engine.strategy.examples.rsi_reversion import RsiReversion
    from quant_engine.strategy.examples.sma_crossover import SmaCrossover

    config = BacktestConfig(
        initial_capital=100_000.0,
        commission_rate=0.001,  # %0.1
        slippage_bps=5,         # 5 baz puan
        max_position_pct=0.95,  # Sermayenin %95'i
        warm_up_bars=0,
    )

    strategies = [
        BuyAndHold(),
        SmaCrossover(params={"fast_period": 10, "slow_period": 30}),
        RsiReversion(params={"rsi_period": 14, "oversold": 30, "overbought": 70}),
    ]

    engine = BacktestEngine(config)

    print()
    print("═" * 80)
    print("  🚀 QUANT ENGINE — STRATEJİ KARŞILAŞTIRMA RAPORU")
    print(f"  📊 Sembol: {symbol} | {len(data)} bar | "
          f"₺{config.initial_capital:,.0f} sermaye")
    print(f"  📅 {data['date'].min().strftime('%Y-%m-%d')} → "
          f"{data['date'].max().strftime('%Y-%m-%d')}")
    print(f"  💰 Komisyon: %{config.commission_rate * 100:.1f} | "
          f"Slippage: {config.slippage_bps} bps")
    print("═" * 80)

    results = []

    for strategy in strategies:
        logger.info(f"\n🔄 {strategy.name} çalıştırılıyor...")

        result = engine.run(
            data,
            strategy.as_signal_func(),
            symbol=symbol,
        )

        metrics = calculate_metrics(
            result.equity_curve,
            result.fills,
            config.initial_capital,
        )

        results.append({
            "strategy": strategy,
            "result": result,
            "metrics": metrics,
        })

    # --- KARŞILAŞTIRMA TABLOSU ---
    print()
    print("─" * 80)
    print(f"  {'Strateji':<20} {'Getiri':>10} {'CAGR':>8} "
          f"{'Sharpe':>8} {'MaxDD':>8} {'Win%':>7} "
          f"{'PF':>6} {'Trade':>6} {'Son₺':>14}")
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
    best = max(results, key=lambda x: x["metrics"].sharpe_ratio)
    print(f"\n  🏆 En iyi Sharpe: {best['strategy'].name} "
          f"(Sharpe: {best['metrics'].sharpe_ratio:.2f})")

    # --- DETAYLI METRİKLER (en iyi strateji) ---
    print()
    print(best["metrics"].summary())

    # --- TRADE DETAYLARI ---
    best_result = best["result"]
    if best_result.fills:
        print()
        print("─" * 80)
        print(f"  📋 {best['strategy'].name} — Son 10 İşlem")
        print("─" * 80)
        print(f"  {'Tarih':<12} {'Yön':<5} {'Adet':>8} "
              f"{'Fiyat':>10} {'Komisyon':>10}")
        print("  " + "─" * 55)

        for fill in best_result.fills[-10:]:
            ts = fill.fill_timestamp
            date_str = ts.strftime("%Y-%m-%d") if ts else "N/A"
            print(
                f"  {date_str:<12} "
                f"{'AL' if fill.order.side.value == 'buy' else 'SAT':<5} "
                f"{fill.fill_quantity:>8d} "
                f"₺{fill.fill_price:>9.2f} "
                f"₺{fill.commission:>9.2f}"
            )

    # --- EQUİTY CURVE ÖZETİ ---
    print()
    print("─" * 80)
    print(f"  📈 Equity Curve Özeti ({best['strategy'].name})")
    print("─" * 80)

    curve = best_result.equity_curve
    n = len(curve)
    checkpoints = [0, n // 4, n // 2, 3 * n // 4, n - 1]
    for i in checkpoints:
        ep = curve[i]
        ts = ep.timestamp
        date_str = ts.strftime("%Y-%m-%d") if ts else "N/A"
        print(
            f"  {date_str}  "
            f"₺{ep.total_equity:>12,.0f}  "
            f"DD: {ep.drawdown_pct:>5.1f}%  "
            f"Nakit: ₺{ep.cash:>12,.0f}"
        )

    print()
    print("═" * 80)
    print("  ✅ Demo tamamlandı!")
    print("═" * 80)
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Quant Engine Demo — Strateji Karşılaştırma"
    )
    parser.add_argument(
        "--symbol", "-s",
        default="THYAO",
        help="BIST sembolü (varsayılan: THYAO)"
    )
    parser.add_argument(
        "--start",
        default="2022-01-01",
        help="Başlangıç tarihi (varsayılan: 2022-01-01)"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Gerçek veri kullan (yfinance, internet gerekli)"
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=500,
        help="Yapay veri bar sayısı (varsayılan: 500)"
    )

    args = parser.parse_args()
    setup_logging()

    if args.live:
        data = fetch_live_data(args.symbol, args.start)
        if data.empty:
            logger.error("Gerçek veri çekilemedi, yapay veriye geçiliyor...")
            data = generate_synthetic_data(args.bars, symbol=args.symbol)
        symbol = args.symbol
    else:
        symbol = "SYNTH"
        data = generate_synthetic_data(args.bars, symbol=symbol)
        logger.info(
            f"📊 Yapay veri üretildi: {len(data)} bar "
            f"(gerçek veri için --live kullanın)"
        )

    run_strategy_comparison(data, symbol)


if __name__ == "__main__":
    main()
