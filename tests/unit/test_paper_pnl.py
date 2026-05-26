"""Unit testler: Paper trading PnL muhasebesi (PaperExecutor).

Bölüm 18.14 — risk bazlı test kapsamı: paper PnL accounting.

Test senaryoları:
  - Alım → satım PnL hesabı (kar ve zarar durumları)
  - Komisyon doğru kesilmeli
  - Günlük zarar limiti: realized PnL bazlı donma
  - Mark-to-market günlük zarar limitinde donma
  - Açık pozisyon yokken SELL → None (işlem yapılmamalı)
  - Mevcut açık pozisyona ikinci BUY → None (duplicate koruması)
  - Restore: SQLite'dan açık pozisyonlar memory'ye yüklenmeli
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch
from typing import Any

from backend.paper.executor import PaperExecutor, COMMISSION_RATE, POSITION_SIZE_PCT, DAILY_LOSS_LIMIT_PCT


# ─── Yardımcılar ─────────────────────────────────────────────────────────────

def _make_db(
    initial_capital: float = 10_000.0,
    open_trades: list | None = None,
) -> MagicMock:
    """Sahte PaperDB döndürür."""
    db = MagicMock()
    wallet = {
        "strategy_id":     "s1",
        "cash":            initial_capital,
        "initial_capital": initial_capital,
        "daily_loss":      0.0,
        "daily_reset_date": "2026-01-01",
        "is_halted":       0,
    }
    db.get_or_create_wallet.return_value = wallet.copy()
    db.get_all_open_trades.return_value = open_trades or []
    db.record_trade.return_value = 42  # trade_id
    db.close_trade.return_value = None
    db.update_wallet.return_value = None
    db.halt_strategy.return_value = None
    db.record_equity.return_value = None
    return db


def _executor_with_wallet(cash=10_000.0) -> tuple[PaperExecutor, MagicMock]:
    db = _make_db(initial_capital=cash)
    ex = PaperExecutor(db)
    return ex, db


# ─── BUY → SELL PnL ──────────────────────────────────────────────────────────

class TestBuySellPnL:
    SID = "strategy_test"
    SYM = "THYAO"

    def _wallet(self, ex: PaperExecutor, initial=10_000.0):
        return {
            "strategy_id":     self.SID,
            "cash":            initial,
            "initial_capital": initial,
            "daily_loss":      0.0,
            "daily_reset_date": "2026-01-01",
            "is_halted":       0,
        }

    def test_buy_reduces_cash(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        result = ex._handle_buy(self.SID, self.SYM, price=100.0, reason="test", wallet=wallet)

        assert result is not None
        allocation = 10_000 * POSITION_SIZE_PCT
        commission = allocation * COMMISSION_RATE
        expected_cash = 10_000 - allocation - commission
        assert wallet["cash"] == pytest.approx(expected_cash, rel=1e-6)

    def test_buy_records_position(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="test", wallet=wallet)

        assert self.SYM in ex._open_positions.get(self.SID, {})
        assert ex._entry_prices[self.SID][self.SYM] == pytest.approx(100.0)

    def test_sell_profit_increases_cash(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="buy", wallet=wallet)
        cash_after_buy = wallet["cash"]

        result = ex._handle_sell(self.SID, self.SYM, price=120.0, reason="sell", wallet=wallet)

        assert result is not None
        assert result["tur"] == "satim"
        assert wallet["cash"] > cash_after_buy
        assert result["pnl"] > 0

    def test_sell_loss_decreases_cash(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="buy", wallet=wallet)

        result = ex._handle_sell(self.SID, self.SYM, price=80.0, reason="sell", wallet=wallet)

        assert result["pnl"] < 0

    def test_commission_deducted_on_both_legs(self):
        """Hem alım hem satımda komisyon kesilmeli."""
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)

        entry_price = 100.0
        exit_price  = 100.0  # Fiyat değişmedi, yine de komisyon var

        ex._handle_buy(self.SID, self.SYM, price=entry_price, reason="b", wallet=wallet)
        result = ex._handle_sell(self.SID, self.SYM, price=exit_price, reason="s", wallet=wallet)

        # Break-even satışta bile komisyon yüzünden PnL negatif
        assert result["pnl"] < 0

    def test_position_cleared_after_sell(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="b", wallet=wallet)
        ex._handle_sell(self.SID, self.SYM, price=110.0, reason="s", wallet=wallet)

        assert self.SYM not in ex._open_positions.get(self.SID, {})

    def test_sell_without_open_position_returns_none(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        result = ex._handle_sell(self.SID, self.SYM, price=100.0, reason="s", wallet=wallet)
        assert result is None

    def test_duplicate_buy_returns_none(self):
        ex, db = _executor_with_wallet(10_000)
        wallet = self._wallet(ex)
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="b", wallet=wallet)
        result = ex._handle_buy(self.SID, self.SYM, price=105.0, reason="b2", wallet=wallet)
        assert result is None


class TestDailyLossLimit:
    SID = "s_risk"
    SYM = "AAAA"

    def _wallet(self, initial=10_000.0):
        return {
            "strategy_id":     self.SID,
            "cash":            initial,
            "initial_capital": initial,
            "daily_loss":      0.0,
            "daily_reset_date": "2026-01-01",
            "is_halted":       0,
        }

    def test_halt_triggered_when_daily_loss_exceeds_limit(self):
        """Günlük zarar DAILY_LOSS_LIMIT_PCT'i aşınca donma tetiklenmeli.

        Senaryo: wallet daily_loss limiti eşiğinin hemen altında başlar;
        küçük bir satış zararı eşiği aşar ve halt tetiklenir.
        POSITION_SIZE_PCT=0.10 ile tek pozisyon initial'ın %10'unu kaybetmek
        için fiyatın sıfıra gitmesi gerekir — o yüzden önceki daily_loss ile
        eşiğe yaklaştırıp, son satışla aşıyoruz.
        """
        initial = 10_000.0
        ex, db  = _executor_with_wallet(initial)
        wallet  = self._wallet(initial)

        # Daha önceki zararlar günlük limiti eşiğe getirmiş olsun
        # Limit = initial * DAILY_LOSS_LIMIT_PCT = 1000 TL
        # 5 TL altında başlat → az bir zarar yetecek
        wallet["daily_loss"] = -(initial * DAILY_LOSS_LIMIT_PCT - 5.0)

        # Alım
        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="b", wallet=wallet)

        # Küçük zararla satış (5 TL'den fazla kaybet → limite düş)
        ex._handle_sell(self.SID, self.SYM, price=99.0, reason="s", wallet=wallet)

        db.halt_strategy.assert_called_once_with(self.SID)

    def test_no_halt_on_small_loss(self):
        """Küçük zarar donmayı tetiklemenmeli."""
        ex, db = _executor_with_wallet(10_000)
        wallet  = self._wallet(10_000.0)

        ex._handle_buy(self.SID, self.SYM, price=100.0, reason="b", wallet=wallet)
        small_loss_price = 99.0
        ex._handle_sell(self.SID, self.SYM, price=small_loss_price, reason="s", wallet=wallet)

        db.halt_strategy.assert_not_called()


class TestMarkToMarket:
    def test_update_prices_mark_to_market_loss_triggers_halt(self):
        """update_prices, mark-to-market ile daily loss limitini geçince donma üretmeli."""
        initial = 10_000.0
        db = _make_db(initial_capital=initial)
        ex = PaperExecutor(db)
        sid = "s_mtm"
        sym = "XXXX"

        # Manuel olarak açık pozisyon yerleştir
        ex._open_positions[sid] = {sym: 99}
        ex._entry_prices[sid]   = {sym: 100.0}
        ex._quantities[sid]     = {sym: 100.0}  # 100 lot

        wallet = {
            "strategy_id":     sid,
            "cash":            initial * 0.9,
            "initial_capital": initial,
            "daily_loss":      0.0,
            "daily_reset_date": "2026-01-01",
            "is_halted":       0,
        }
        db.get_or_create_wallet.return_value = wallet

        # Fiyat %15 düşsün → 100 lot * 15 TL = -1500 unrealized = -%15 daily loss
        crash_price = 100.0 * (1 - DAILY_LOSS_LIMIT_PCT - 0.05)
        ex.update_prices({sym: crash_price})

        db.halt_strategy.assert_called()


class TestRestore:
    def test_open_trades_loaded_from_db_on_init(self):
        """Başlatmada SQLite'daki açık trade'ler memory'ye yüklenmeli."""
        open_trades = [
            {"id": 1, "strategy_id": "s1", "symbol": "AABB", "price": 50.0, "quantity": 10.0}
        ]
        db = _make_db(open_trades=open_trades)
        ex = PaperExecutor(db)

        assert "AABB" in ex._open_positions.get("s1", {})
        assert ex._entry_prices["s1"]["AABB"] == pytest.approx(50.0)
        assert ex._quantities["s1"]["AABB"] == pytest.approx(10.0)
