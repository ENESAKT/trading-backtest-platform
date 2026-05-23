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
import smtplib
from email.mime.text import MIMEText
from typing import Any

from backend.config import getenv, mask_sensitive

logger = logging.getLogger(__name__)


def _smtp_port() -> int:
    try:
        return int(getenv("SMTP_PORT", "587"))
    except ValueError:
        return 587


def email_configured() -> bool:
    return bool(getenv("SMTP_USER") and getenv("SMTP_PASS") and getenv("NOTIFY_EMAIL_TO"))


def email_status() -> dict[str, Any]:
    return {
        "smtp_yapilandirildi": email_configured(),
        "smtp_host": getenv("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": _smtp_port(),
        "alici_yapilandirildi": bool(getenv("NOTIFY_EMAIL_TO")),
    }


def send_email(subject: str, body: str, html: bool = False) -> bool:
    """SMTP üzerinden email gönder."""
    smtp_host = getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port = _smtp_port()
    smtp_user = getenv("SMTP_USER")
    smtp_pass = getenv("SMTP_PASS")
    notify_email_to = getenv("NOTIFY_EMAIL_TO")
    if not smtp_user or not smtp_pass or not notify_email_to:
        logger.warning("email: SMTP bilgileri ayarlanmamış")
        return False

    try:
        msg = MIMEText(body, "html" if html else "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = smtp_user
        msg["To"] = notify_email_to

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info("email: gönderildi — %s", subject)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("email: gönderim hatası — %s", mask_sensitive(str(exc)))
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

    container_style = (
        "font-family:Arial,sans-serif;background:#0d1117;color:#c9d1d9;"
        "padding:20px;border-radius:8px"
    )
    return f"""
    <div style="{container_style}">
        <h2 style="color:#58a6ff">📊 PiyasaPilot Günlük Rapor</h2>
        {wallet_table}
        <p style="margin-top:12px">
            📈 Paper Trading Simülasyon Oranı (gerçek getiri değildir):
            <strong>{win_rate:.1f}%</strong> ({winners}/{trade_count})
        </p>
        <p style="margin-top:14px;color:#8b949e;font-size:12px;line-height:1.5">
            Bu e-posta yatırım tavsiyesi değildir. Eğitim, araştırma ve paper trading
            amaçlı otomatik rapordur; gerçek emir veya gerçek getiri garantisi içermez.
        </p>
    </div>
    """
