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
        self._processed = 0
        self._executed = 0
        self._halted = 0

    def _utc_now(self) -> str:
        return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()

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
        positions = self.db.get_positions(strategy_id)
        positions_val = sum(
            p["entry_price"] * p["quantity"] for p in positions
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
        # Açık pozisyon varsa tekrar al yapma
        if self.db.get_position(strategy_id, symbol) is not None:
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
        self.db.record_trade(
            strategy_id=strategy_id, symbol=symbol, side="BUY",
            price=price, quantity=quantity, commission=commission,
            opened_at=now, reason=reason,
        )

        wallet["cash"] -= total_cost
        self.db.update_wallet(
            strategy_id, wallet["cash"],
            wallet["daily_loss"], wallet["daily_reset_date"]
        )

        # Pozisyonu DB'ye kaydet
        self.db.upsert_position(
            strategy_id=strategy_id,
            symbol=symbol,
            quantity=quantity,
            entry_price=price,
            opened_at=now,
            updated_at=now,
        )

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
        pos = self.db.get_position(strategy_id, symbol)
        if pos is None:
            return None

        # Açık trade kaydını bul (close için)
        open_trade = self.db.get_open_trade(strategy_id, symbol)

        entry_price = pos["entry_price"]
        quantity = pos["quantity"]

        gross = price * quantity
        commission = gross * COMMISSION_RATE
        net_proceeds = gross - commission
        pnl = net_proceeds - (entry_price * quantity)

        now = self._utc_now()
        if open_trade:
            self.db.close_trade(open_trade["id"], price, pnl, now)

        wallet["cash"] += net_proceeds
        new_daily_loss = wallet["daily_loss"] + (pnl if pnl < 0 else 0)
        self.db.update_wallet(
            strategy_id, wallet["cash"],
            new_daily_loss, wallet["daily_reset_date"]
        )

        # Pozisyonu DB'den sil
        self.db.delete_position(strategy_id, symbol)

        donduruldu = False
        initial = wallet["initial_capital"]
        if abs(new_daily_loss) / initial >= DAILY_LOSS_LIMIT_PCT:
            self.db.halt_strategy(strategy_id)
            logger.warning("paper executor: %s donduruldu (günlük zarar limiti)", strategy_id)
            donduruldu = True

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
        """Mark-to-market: tüm açık pozisyonlar için unrealized PnL hesapla ve portfolio'ya yaz."""
        all_positions = self.db.all_positions()
        # strategy_id başına grupla
        by_strategy: dict[str, list[dict[str, Any]]] = {}
        for pos in all_positions:
            sid = pos["strategy_id"]
            by_strategy.setdefault(sid, []).append(pos)

        for sid, positions in by_strategy.items():
            unrealized = 0.0
            for pos in positions:
                sym = pos["symbol"]
                current_price = price_map.get(sym)
                if current_price is None:
                    # Fiyat yoksa entry price ile hesapla (PnL = 0)
                    current_price = pos["entry_price"]
                unrealized += (current_price - pos["entry_price"]) * pos["quantity"]
            self.db.update_unrealized_pnl(sid, unrealized)

    def get_open_positions(self, strategy_id: str) -> list[dict[str, Any]]:
        """Strateji için açık pozisyonları DB'den döndür."""
        return self.db.get_positions(strategy_id)

    def stats(self) -> dict[str, Any]:
        all_positions = self.db.all_positions()
        by_strategy: dict[str, list[str]] = {}
        for pos in all_positions:
            sid = pos["strategy_id"]
            by_strategy.setdefault(sid, []).append(pos["symbol"])
        return {
            "processed": self._processed,
            "executed": self._executed,
            "halted_skips": self._halted,
            "open_positions": by_strategy,
        }
