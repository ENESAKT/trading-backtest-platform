"""Telegram bot bildirim modülü (Sprint 7.4).

Kullanım:
    export TELEGRAM_BOT_TOKEN="123456:ABC-DEF..."
    export TELEGRAM_CHAT_ID="987654321"
"""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"


async def send_telegram(text: str, parse_mode: str = "Markdown") -> bool:
    """Telegram mesajı gönder (httpx ile)."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("telegram: BOT_TOKEN veya CHAT_ID ayarlanmamış")
        return False

    try:
        import httpx

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(
                f"{API_URL}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": text,
                    "parse_mode": parse_mode,
                },
            )
            if resp.status_code == 200:
                logger.info("telegram: mesaj gönderildi")
                return True
            logger.warning("telegram: hata %d — %s", resp.status_code, resp.text)
            return False
    except Exception as exc:  # noqa: BLE001
        logger.warning("telegram: gönderim hatası — %s", exc)
        return False


def format_signal(signal: dict[str, Any]) -> str:
    """Sinyal dict'ini Telegram Markdown formatına çevir."""
    symbol = signal.get("symbol", "?")
    sig_type = signal.get("signal_type", "?")
    price = signal.get("price", 0)
    strategy = signal.get("strategy_id", "?")
    strength = signal.get("strength", 5)
    reason = signal.get("reason", "")

    emoji = "🟢" if "BUY" in sig_type else "🔴" if "SELL" in sig_type else "⚪"
    stars = "⭐" * min(strength // 2, 5)

    return (
        f"{emoji} *{sig_type}* — {symbol}\n"
        f"💰 Fiyat: `{price:.4f}`\n"
        f"📊 Strateji: `{strategy}`\n"
        f"💪 Güç: {strength}/10 {stars}\n"
        f"📝 {reason}"
    )


def format_daily_report(wallets: list[dict], trades: list[dict]) -> str:
    """Günlük paper trading özeti."""
    lines = ["📊 *Günlük Paper Trading Raporu*\n"]

    for w in wallets:
        pnl = w["cash"] - w["initial_capital"]
        emoji = "🟢" if pnl >= 0 else "🔴"
        status = "🔒 DONDURULDU" if w["is_halted"] else "✅ Aktif"
        lines.append(
            f"*{w['strategy_id']}*: {status}\n"
            f"  {emoji} Nakit: `{w['cash']:,.2f}₺` | PnL: `{pnl:+,.2f}₺`"
        )

    if trades:
        completed = [t for t in trades if t.get("closed_at")]
        winners = [t for t in completed if (t.get("pnl") or 0) > 0]
        if completed:
            win_rate = len(winners) / len(completed) * 100
            lines.append(f"\n📈 Win Rate: `{win_rate:.1f}%` ({len(winners)}/{len(completed)})")

    return "\n".join(lines)
