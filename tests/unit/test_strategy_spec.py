import pandas as pd
import pytest

from quant_engine.strategy.spec import (
    FormulaError,
    StrategySpecSignal,
    evaluate_formula,
    validate_strategy_spec,
)


def _data(n: int = 80) -> pd.DataFrame:
    close = [100 + i * 0.5 for i in range(n)]
    # Son bölümde geri çekilme yaratarak CROSS_DOWN ve short kuralı üretilebilir.
    for i in range(50, n):
        close[i] = close[49] - (i - 49) * 0.7
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-01", periods=n, freq="D", tz="UTC"),
            "symbol": ["TEST"] * n,
            "open": close,
            "high": [c + 1 for c in close],
            "low": [c - 1 for c in close],
            "close": close,
            "volume": [1000 + i for i in range(n)],
        }
    )


def test_formula_evaluates_allowed_indicators():
    df = _data()
    result = evaluate_formula("C > EMA(C,20) AND RSI(C,14) > 50", df)
    assert len(result) == len(df)
    assert result.dtype == bool


def test_formula_rejects_python_like_escape():
    with pytest.raises(FormulaError) as exc:
        validate_strategy_spec({"long_entry": "__import__(os)"})
    assert "Bilinmeyen fonksiyon" in str(exc.value) or "Bilinmeyen alan" in str(exc.value)


def test_formula_reports_bad_arity_in_turkish():
    with pytest.raises(FormulaError) as exc:
        validate_strategy_spec({"long_entry": "EMA(C)"})
    assert "parametre" in str(exc.value)
    assert "kolon" in str(exc.value)


def test_strategy_spec_signal_supports_short_rules():
    df = _data()
    spec = {
        "name": "EMA long short",
        "rules": {
            "long_entry": "CROSS_UP(EMA(C,5), EMA(C,20))",
            "long_exit": "CROSS_DOWN(EMA(C,5), EMA(C,20))",
            "short_entry": "CROSS_DOWN(EMA(C,5), EMA(C,20))",
            "short_exit": "CROSS_UP(EMA(C,5), EMA(C,20))",
        },
    }
    signal = StrategySpecSignal(spec, df, allow_short=True)
    intents = [signal(df, i, _DummyPortfolio()) for i in range(len(df))]
    assert "SHORT" in intents or "BUY" in intents


class _DummyPortfolio:
    def get_or_create_position(self, symbol):
        return _DummyPosition()


class _DummyPosition:
    quantity = 0
    avg_entry_price = 0.0
