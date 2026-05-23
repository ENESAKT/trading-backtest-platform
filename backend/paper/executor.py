"""Paper trading executor — sinyal → sanal emir (Sprint 4.2–4.4)."""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any

from backend.paper.db import PaperDB

logger = logging.getLogger(__name__)

COMMISSION_RATE = 0.001   # %0.1
POSITION_SIZE_PCT = 0.10  # her işlemde cüzdanın %10'u
DAILY_LOSS_LIMIT_PCT = 0.10  # günlük max %10 zarar → dondur


class PaperExecutor:
    """Strateji-bazlı izole sanal cüzdan yöneticisi."""

    def __init__(self, db: PaperDB) -> None:
        self.db = db
        self._open_positions: dict[str, dict[str, int]] = {}
        self._entry_prices: dict[str, dict[str, float]] = {}
        self._quantities: dict[str, dict[str, float]] = {}
        self._current_prices: dict[str, float] = {}
        self._processed = 0
        self._executed = 0
        self._halted = 0
        # Restart sonrası açık pozisyonları SQLite'dan geri yükle
        self._restore_open_positions()

    def _restore_open_positions(self) -> None:
        """Restart sonrası in-memory pozisyon state'ini SQLite'dan restore et.

        paper_trades tablosunda closed_at IS NULL olan her kayıt,
        hâlâ açık bir pozisyonu temsil eder. Bu pozisyonlar
        _open_positions, _entry_prices ve _quantities sözlüklerine yüklenir.
        """
        try:
            open_trades = self.db.get_all_open_trades()
            for trade in open_trades:
                sid    = trade["strategy_id"]
                symbol = trade["symbol"]
                tid    = trade["id"]
                price  = trade["price"]
                qty    = trade["quantity"]

                if sid not in self._open_positions:
                    self._open_positions[sid] = {}
                    self._entry_prices[sid]   = {}
                    self._quantities[sid]     = {}

                self._open_positions[sid][symbol] = tid
                self._entry_prices[sid][symbol]   = price
                self._quantities[sid][symbol]     = qty

            if open_trades:
                logger.info(
                    "[executor] Restart: %d açık pozisyon SQLite'dan restore edildi.",
                    len(open_trades),
                )
        except Exception as exc:
            logger.error("[executor] Pozisyon restore hatası: %s", exc)

    def _utc_now(self) -> str:
        return dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat()

    def _today(self) -> str:
        return dt.date.today().isoformat()

    def _reset_daily_if_needed(self, wallet: dict[str, Any]) -> dict[str, Any]:
        today = self._today()
        if wallet["daily_reset_date"] != today:
            wallet["daily_loss"] = 0.0
            wallet["daily_reset_date"] = today
            self.db.update_wallet(
                wallet["strategy_id"], wallet["cash"], 0.0, today
            )
        return wallet

    def _equity_snapshot(self, strategy_id: str, wallet: dict[str, Any]) -> None:
        positions_val = sum(
            self._current_prices.get(sym, self._entry_prices.get(strategy_id, {}).get(sym, 0))
            * self._quantities.get(strategy_id, {}).get(sym, 0)
            for sym in (self._open_positions.get(strategy_id) or {})
        )
        total = wallet["cash"] + positions_val
        self.db.record_equity_snapshot(
            strategy_id, self._utc_now(), total, wallet["cash"], positions_val
        )

    async def process_signal(self, signal: dict[str, Any]) -> None:
        if signal.get("type") != "signal":
            return
        self._processed += 1

        strategy_id: str = signal.get("strategy_id", "")
        symbol: str = signal.get("symbol", "").upper()
        sig_type: str = signal.get("signal_type", "").upper()
        price: float = float(signal.get("price", 0))

        if not strategy_id or not symbol or price <= 0 or sig_type not in ("BUY", "SELL"):
            return

        # Sinyali bildirimlere ilet (STRONG sinyallerde)
        if sig_type in ("STRONG_BUY", "STRONG_SELL") or signal.get("strength", 0) >= 7:
            try:
                from backend.notifier.telegram import bildir_yeni_sinyal
                asyncio.create_task(bildir_yeni_sinyal(signal))
            except Exception as exc:  # noqa: BLE001
                logger.warning("telegram sinyal bildirimi gönderilemedi: %s", exc)

        loop = asyncio.get_running_loop()
        bildirim = await loop.run_in_executor(
            None, self._handle, strategy_id, symbol, sig_type, price,
            signal.get("reason", "")
        )

        if bildirim:
            await self._gonder_bildirim(bildirim)

    async def _gonder_bildirim(self, bildirim: dict[str, Any]) -> None:
        try:
            tur = bildirim.get("tur")
            if tur == "alim":
                from backend.notifier.telegram import bildir_alim
                await bildir_alim(
                    bildirim["strategy_id"], bildirim["symbol"],
                    bildirim["price"], bildirim["quantity"],
                    bildirim["tutar"], bildirim["reason"],
                )
            elif tur == "satim":
                from backend.notifier.telegram import bildir_satim
                await bildir_satim(
                    bildirim["strategy_id"], bildirim["symbol"],
                    bildirim["price"], bildirim["quantity"],
                    bildirim["pnl"], bildirim["reason"],
                )
            elif tur == "donduruldu":
                from backend.notifier.telegram import bildir_cuzdan_donduruldu
                await bildir_cuzdan_donduruldu(
                    bildirim["strategy_id"],
                    bildirim["daily_loss"],
                    bildirim["initial_capital"],
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("telegram bildirim hatası: %s", exc)

    def _handle(
        self, strategy_id: str, symbol: str, sig_type: str,
        price: float, reason: str,
    ) -> dict[str, Any] | None:
        wallet = self.db.get_or_create_wallet(strategy_id)
        wallet = self._reset_daily_if_needed(wallet)

        if wallet["is_halted"]:
            self._halted += 1
            return None

        if sig_type == "BUY":
            return self._handle_buy(strategy_id, symbol, price, reason, wallet)
        return self._handle_sell(strategy_id, symbol, price, reason, wallet)

    def _handle_buy(
        self, strategy_id: str, symbol: str, price: float,
        reason: str, wallet: dict[str, Any],
    ) -> dict[str, Any] | None:
        open_pos = self._open_positions.get(strategy_id, {})
        if symbol in open_pos:
            return None

        allocation = wallet["cash"] * POSITION_SIZE_PCT
        if allocation < price:
            return None

        quantity = allocation / price
        commission = allocation * COMMISSION_RATE
        total_cost = allocation + commission

        if wallet["cash"] < total_cost:
            return None

        now = self._utc_now()
        trade_id = self.db.record_trade(
            strategy_id=strategy_id, symbol=symbol, side="BUY",
            price=price, quantity=quantity, commission=commission,
            opened_at=now, reason=reason,
        )

        wallet["cash"] -= total_cost
        self.db.update_wallet(
            strategy_id, wallet["cash"],
            wallet["daily_loss"], wallet["daily_reset_date"]
        )

        if strategy_id not in self._open_positions:
            self._open_positions[strategy_id] = {}
            self._entry_prices[strategy_id] = {}
            self._quantities[strategy_id] = {}

        self._open_positions[strategy_id][symbol] = trade_id
        self._entry_prices[strategy_id][symbol] = price
        self._quantities[strategy_id][symbol] = quantity

        self._equity_snapshot(strategy_id, wallet)
        self._executed += 1
        logger.info("paper BUY %s %s @ %.4f qty=%.4f", strategy_id, symbol, price, quantity)

        return {
            "tur": "alim",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "tutar": allocation,
            "reason": reason,
        }

    def _handle_sell(
        self, strategy_id: str, symbol: str, price: float,
        reason: str, wallet: dict[str, Any],
    ) -> dict[str, Any] | None:
        open_pos = self._open_positions.get(strategy_id, {})
        if symbol not in open_pos:
            return None

        trade_id = open_pos[symbol]
        entry_price = self._entry_prices[strategy_id][symbol]
        quantity = self._quantities[strategy_id][symbol]

        gross = price * quantity
        commission = gross * COMMISSION_RATE
        net_proceeds = gross - commission
        pnl = net_proceeds - (entry_price * quantity)

        now = self._utc_now()
        self.db.close_trade(trade_id, price, pnl, now)

        wallet["cash"] += net_proceeds
        new_daily_loss = wallet["daily_loss"] + (pnl if pnl < 0 else 0)
        self.db.update_wallet(
            strategy_id, wallet["cash"],
            new_daily_loss, wallet["daily_reset_date"]
        )

        donduruldu = False
        initial = wallet["initial_capital"]
        if abs(new_daily_loss) / initial >= DAILY_LOSS_LIMIT_PCT:
            self.db.halt_strategy(strategy_id)
            logger.warning("paper executor: %s donduruldu (günlük zarar limiti)", strategy_id)
            donduruldu = True

        del self._open_positions[strategy_id][symbol]
        del self._entry_prices[strategy_id][symbol]
        del self._quantities[strategy_id][symbol]

        wallet["daily_loss"] = new_daily_loss
        self._equity_snapshot(strategy_id, wallet)
        self._executed += 1
        logger.info("paper SELL %s %s @ %.4f pnl=%.2f", strategy_id, symbol, price, pnl)

        if donduruldu:
            return {
                "tur": "donduruldu",
                "strategy_id": strategy_id,
                "daily_loss": new_daily_loss,
                "initial_capital": initial,
            }

        return {
            "tur": "satim",
            "strategy_id": strategy_id,
            "symbol": symbol,
            "price": price,
            "quantity": quantity,
            "pnl": pnl,
            "reason": reason,
        }

    def update_prices(self, price_map: dict[str, float]) -> None:
        """Anlık fiyatlarla in-memory unrealized PnL takibini güncelle.

        Her fiyat güncellemesinde açık pozisyonları mark-to-market değerler,
        equity snapshot yazar ve günlük zarar limitini unrealized PnL dahil izler.
        """
        clean_prices: dict[str, float] = {}
        for symbol, price in price_map.items():
            try:
                value = float(price)
            except (TypeError, ValueError):
                continue
            if symbol and value > 0:
                clean_prices[symbol.upper()] = value
        if not clean_prices:
            return

        self._current_prices = {**self._current_prices, **clean_prices}

        for strategy_id, positions in list(self._open_positions.items()):
            if not positions:
                continue
            wallet = self._reset_daily_if_needed(self.db.get_or_create_wallet(strategy_id))
            if wallet["is_halted"]:
                self._equity_snapshot(strategy_id, wallet)
                continue

            unrealized_pnl = 0.0
            for symbol in positions:
                qty = self._quantities.get(strategy_id, {}).get(symbol, 0.0)
                entry = self._entry_prices.get(strategy_id, {}).get(symbol, 0.0)
                current = self._current_prices.get(symbol, entry)
                unrealized_pnl += (current - entry) * qty

            mark_to_market_loss = min(0.0, unrealized_pnl)
            daily_loss = min(float(wallet["daily_loss"]), mark_to_market_loss)
            if daily_loss != wallet["daily_loss"]:
                self.db.update_wallet(
                    strategy_id,
                    float(wallet["cash"]),
                    daily_loss,
                    str(wallet["daily_reset_date"]),
                )
                wallet["daily_loss"] = daily_loss

            initial = float(wallet["initial_capital"])
            if initial > 0 and abs(daily_loss) / initial >= DAILY_LOSS_LIMIT_PCT:
                self.db.halt_strategy(strategy_id)
                wallet["is_halted"] = 1
                logger.warning(
                    "paper executor: %s mark-to-market günlük zarar limitinde donduruldu",
                    strategy_id,
                )

            self._equity_snapshot(strategy_id, wallet)

    def stats(self) -> dict[str, Any]:
        return {
            "processed": self._processed,
            "executed": self._executed,
            "halted_skips": self._halted,
            "open_positions": {
                sid: list(pos.keys())
                for sid, pos in self._open_positions.items()
                if pos
            },
        }
