from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pandas as pd

from quant_engine.app.ui_streamlit.app import (
    _date_window_start,
    _parse_bist_catalog_html,
    build_strategy_leaderboard,
    build_trade_overlay,
    run_backtest,
)
from quant_engine.backtest.engine import BacktestConfig


def _fixture_ohlcv(n_bars: int = 500, symbol: str = "TEST") -> pd.DataFrame:
    trend = np.linspace(0, 0.35, n_bars)
    wave = np.sin(np.arange(n_bars) / 8) * 0.035
    close = 100 * np.exp(np.cumsum(trend / n_bars + wave / 8))
    open_ = np.roll(close, 1)
    open_[0] = close[0]
    high = np.maximum(open_, close) * 1.012
    low = np.minimum(open_, close) * 0.988
    return pd.DataFrame(
        {
            "date": pd.bdate_range("2022-01-03", periods=n_bars, freq="B"),
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": np.full(n_bars, 1_500_000),
            "symbol": [symbol] * n_bars,
        }
    )


def test_trade_overlay_pairs_completed_trades():
    data = _fixture_ohlcv(n_bars=500, symbol="THYAO")
    config = BacktestConfig(
        initial_capital=100_000,
        commission_rate=0.001,
        slippage_bps=5,
        max_position_pct=0.95,
    )
    _, result, _ = run_backtest(
        data,
        "THYAO",
        "SMA Kesişimi",
        {"fast_period": 10, "slow_period": 30},
        config,
    )

    overlay = build_trade_overlay(result, data)

    assert len(overlay.segments) == len(result.trades)
    assert set(overlay.markers["side"]).issuperset({"AL", "SAT"})
    assert set(overlay.segments["trade_id"]).issubset(set(overlay.markers["trade_id"]))
    assert overlay.markers["label"].str.contains("#").all()


def test_date_window_start_returns_expected_bounds():
    data = _fixture_ohlcv(n_bars=300)

    assert _date_window_start(data, "Tümü") is None
    assert _date_window_start(data, "3 Ay") < data["date"].iloc[-1]
    assert _date_window_start(data, "Yıl başı").month == 1


def test_parse_bist_catalog_html_extracts_symbols_and_names():
    raw_html = """
    <td class="sym svelte-x"><a href="/quote/ist/THYAO/">THYAO</a></td>
    <td class="slw svelte-x">Türk Hava Yolları Anonim Ortaklığı</td>
    <td class="sym svelte-x"><a href="/quote/ist/EREGL/">EREGL</a></td>
    <td class="slw svelte-x">Ereğli Demir ve Çelik Fabrikaları T.A.Ş.</td>
    """

    parsed = _parse_bist_catalog_html(raw_html)

    assert parsed == {
        "THYAO": "Türk Hava Yolları Anonim Ortaklığı",
        "EREGL": "Ereğli Demir ve Çelik Fabrikaları T.A.Ş.",
    }


def test_strategy_leaderboard_contains_cost_and_volume_columns(monkeypatch):
    class FakeProvider:
        def __init__(self, timeout):
            self.timeout = timeout

        def fetch_bars(self, request):
            return SimpleNamespace(
                success=True,
                data=_fixture_ohlcv(n_bars=220, symbol=request.symbol),
                warnings=[],
            )

    monkeypatch.setattr("quant_engine.app.ui_streamlit.app.YFinanceProvider", FakeProvider)
    if hasattr(build_strategy_leaderboard, "clear"):
        build_strategy_leaderboard.clear()

    df, warnings = build_strategy_leaderboard(
        ("AAA", "BBB"),
        "2022-01-01",
        "1d",
        ("SMA Kesişimi", "Al ve Tut"),
        100_000.0,
        0.001,
        5,
        0.95,
    )

    assert warnings == []
    assert len(df) == 4
    assert {"Sembol", "Strateji", "Net Getiri %", "İşlem Hacmi"}.issubset(df.columns)
    assert {"Komisyon", "Kayma", "Al Tut Fark %", "Skor"}.issubset(df.columns)
    assert (df["Final Sermaye"] > 0).all()
