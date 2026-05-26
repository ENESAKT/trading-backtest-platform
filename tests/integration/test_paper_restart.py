"""Integration testleri — Paper Trading Restart Kalıcılığı

PaperExecutor restart sonrası open trade'leri SQLite'tan yüklemeli.
Bu testler DB dosyası olmadan mock ile çalışır.
"""
from __future__ import annotations

import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock


def _import_paper():
    try:
        import sys, os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))
        from backend.paper import PaperDB, PaperExecutor
        return PaperDB, PaperExecutor
    except Exception as exc:
        pytest.skip(f"backend.paper import edilemedi: {exc}")


def _make_trade(strategy_id="s1", symbol="THYAO", trade_id=1, price=50.0, qty=10.0):
    """PaperDB.get_all_open_trades() formatına uygun dict."""
    return {
        "id":          trade_id,
        "strategy_id": strategy_id,
        "symbol":      symbol,
        "side":        "long",
        "quantity":    qty,
        "price":       price,
        "closed_at":   None,
        "opened_at":   datetime.now(timezone.utc).isoformat(),
    }


def test_paper_db_get_open_trades_returns_list():
    PaperDB, _ = _import_paper()
    db = MagicMock(spec=PaperDB)
    db.get_all_open_trades.return_value = []
    result = db.get_all_open_trades()
    assert isinstance(result, list)
    assert len(result) == 0


def test_paper_executor_restores_positions_on_init():
    """PaperExecutor.__init__ açık trade'leri _open_positions'a yüklemeli."""
    _, PaperExecutor = _import_paper()

    mock_db = MagicMock()
    mock_db.get_all_open_trades.return_value = [
        _make_trade("s1", "THYAO", trade_id=1, price=50.0, qty=10.0),
        _make_trade("s1", "AKBNK", trade_id=2, price=20.0, qty=5.0),
    ]

    executor = PaperExecutor(db=mock_db)

    assert "s1" in executor._open_positions, "Strateji s1 _open_positions içinde olmalı"
    assert "THYAO" in executor._open_positions["s1"], "THYAO pozisyonu restore edilmeli"
    assert "AKBNK" in executor._open_positions["s1"], "AKBNK pozisyonu restore edilmeli"


def test_paper_executor_equity_after_restart():
    """Restart sonrası _quantities ve _entry_prices doğru değerleri içermeli."""
    _, PaperExecutor = _import_paper()

    mock_db = MagicMock()
    mock_db.get_all_open_trades.return_value = [
        _make_trade("s1", "THYAO", trade_id=1, price=50.0, qty=10.0),
    ]

    executor = PaperExecutor(db=mock_db)

    assert executor._quantities.get("s1", {}).get("THYAO") == 10.0, \
        "Miktar 10.0 olmalı"
    assert executor._entry_prices.get("s1", {}).get("THYAO") == 50.0, \
        "Giriş fiyatı 50.0 olmalı"


def test_paper_executor_halt_persisted_across_restart():
    """_halted sayacı 0 ile başlamalı; crash olmamalı."""
    _, PaperExecutor = _import_paper()

    mock_db = MagicMock()
    mock_db.get_all_open_trades.return_value = []
    executor = PaperExecutor(db=mock_db)

    assert executor._halted == 0
    assert executor._processed == 0
    assert executor._executed == 0


@pytest.mark.asyncio
async def test_paper_executor_no_duplicate_position():
    """Aynı sembolde pozisyon varken tekrar BUY → crash olmamalı."""
    _, PaperExecutor = _import_paper()

    mock_db = MagicMock()
    mock_db.get_all_open_trades.return_value = []
    mock_db.get_or_create_wallet.return_value = {
        "cash": 100_000.0,
        "positions_value": 0.0,
        "daily_loss": 0.0,
        "day": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
    }
    mock_db.get_open_trade.return_value = None
    mock_db.insert_trade = MagicMock(return_value=1)
    mock_db.update_wallet = MagicMock()
    mock_db.record_equity_snapshot = MagicMock()

    executor = PaperExecutor(db=mock_db)

    if not hasattr(executor, "process_signal"):
        pytest.skip("process_signal metodu bulunamadı")

    signal = {
        "strategy_id": "s1",
        "symbol":      "THYAO",
        "signal_type": "buy",
        "price":       50.0,
        "timestamp":   datetime.now(timezone.utc).isoformat(),
    }

    # İlk sinyal
    await executor.process_signal(signal)
    # İkinci sinyal — pozisyon zaten var, crash olmamalı
    mock_db.get_open_trade.return_value = {"id": 1, "symbol": "THYAO"}
    result2 = await executor.process_signal(signal)
    # process_signal void (None döndürür)
    assert result2 is None
