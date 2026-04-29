"""Email bildirim modülü (Sprint 7.5).

Kullanım:
    export SMTP_HOST="smtp.gmail.com"
    export SMTP_PORT="587"
    export SMTP_USER="user@gmail.com"
    export SMTP_PASS="app-password"
    export NOTIFY_EMAIL_TO="user@gmail.com"
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.mime.text import MIMEText
from typing import Any

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_EMAIL_TO = os.getenv("NOTIFY_EMAIL_TO", "")


def send_email(subject: str, body: str, html: bool = False) -> bool:
    """SMTP üzerinden email gönder."""
    if not SMTP_USER or not SMTP_PASS or not NOTIFY_EMAIL_TO:
        logger.warning("email: SMTP bilgileri ayarlanmamış")
        return False

    try:
        msg = MIMEText(body, "html" if html else "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = NOTIFY_EMAIL_TO

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)

        logger.info("email: gönderildi — %s", subject)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("email: gönderim hatası — %s", exc)
        return False


def format_daily_email(wallets: list[dict[str, Any]], trades: list[dict[str, Any]]) -> str:
    """Günlük rapor HTML email formatı."""
    rows = []
    for w in wallets:
        pnl = w["cash"] - w["initial_capital"]
        color = "#3fb950" if pnl >= 0 else "#f85149"
        status = "🔒" if w["is_halted"] else "✅"
        rows.append(
            f"<tr>"
            f"<td>{status} {w['strategy_id']}</td>"
            f"<td>{w['cash']:,.2f}₺</td>"
            f'<td style="color:{color}">{pnl:+,.2f}₺</td>'
            f"</tr>"
        )

    wallet_table = (
        '<table style="border-collapse:collapse;width:100%">'
        '<tr style="background:#161b22;color:#c9d1d9">'
        "<th>Strateji</th><th>Nakit</th><th>K/Z</th></tr>"
        + "".join(rows)
        + "</table>"
    )

    completed = [t for t in trades if t.get("closed_at")]
    trade_count = len(completed)
    winners = sum(1 for t in completed if (t.get("pnl") or 0) > 0)
    win_rate = (winners / trade_count * 100) if trade_count > 0 else 0

    return f"""
    <div style="font-family:Arial,sans-serif;background:#0d1117;color:#c9d1d9;padding:20px;border-radius:8px">
        <h2 style="color:#58a6ff">📊 PiyasaPilot Günlük Rapor</h2>
        {wallet_table}
        <p style="margin-top:12px">
            📈 Win Rate: <strong>{win_rate:.1f}%</strong> ({winners}/{trade_count})
        </p>
    </div>
    """
