"""
Email gönderme — SMTP + Jinja2 HTML şablonları.
"""

from __future__ import annotations

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

try:
    from jinja2 import Environment, FileSystemLoader
    _TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "email"
    _jinja_env = Environment(
        loader=FileSystemLoader(str(_TEMPLATES_DIR)),
        autoescape=True,
    ) if _TEMPLATES_DIR.exists() else None
except ImportError:
    _jinja_env = None

SMTP_HOST   = os.environ.get("SMTP_HOST",  "smtp.gmail.com")
SMTP_PORT   = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER   = os.environ.get("SMTP_USER",  "")
SMTP_PASS   = os.environ.get("SMTP_PASS",  "")
FROM_EMAIL  = os.environ.get("SMTP_USER",  "noreply@piyasapilotu.com")
BASE_URL    = os.environ.get("PUBLIC_BASE_URL", "https://piyasapilotu.com")


def _render(template_name: str, context: dict) -> str:
    """Jinja2 şablonu render et. Şablon yoksa düz metin fallback."""
    if _jinja_env:
        try:
            return _jinja_env.get_template(template_name).render(**context)
        except Exception:
            pass
    # Düz metin fallback
    return "\n".join(f"{k}: {v}" for k, v in context.items())


def _send(to: str, subject: str, html: str) -> None:
    if not SMTP_USER or not SMTP_PASS:
        # Dev modda konsola yaz
        print(f"[EMAIL DEV] To: {to} | Subject: {subject}\n{html[:200]}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = FROM_EMAIL
    msg["To"]      = to
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to, msg.as_string())
    except Exception as exc:
        print(f"[EMAIL ERROR] {exc}")


def send_verification_email(to: str, token: str, display_name: str = "") -> None:
    link = f"{BASE_URL}/verify-email?token={token}"
    html = _render("verify_email.html", {
        "display_name": display_name or to,
        "verify_link": link,
        "base_url": BASE_URL,
    })
    _send(to, "PiyasaPilot — E-posta adresinizi doğrulayın", html)


def send_password_reset_email(to: str, token: str) -> None:
    link = f"{BASE_URL}/reset-password?token={token}"
    html = _render("reset_password.html", {
        "reset_link": link,
        "base_url": BASE_URL,
    })
    _send(to, "PiyasaPilot — Şifre sıfırlama bağlantısı", html)


def send_welcome_email(to: str, display_name: str = "") -> None:
    html = _render("welcome.html", {
        "display_name": display_name or to,
        "app_url": f"{BASE_URL}/app",
        "base_url": BASE_URL,
    })
    _send(to, "PiyasaPilot'a hoş geldiniz!", html)


def send_payment_success_email(to: str, plan: str = "pro", display_name: str = "") -> None:
    """Başarılı ödeme sonrası tebrik maili."""
    html = _render("payment_success.html", {
        "display_name": display_name or to,
        "plan": plan,
        "app_url": f"{BASE_URL}/app",
        "base_url": BASE_URL,
    })
    _send(to, f"PiyasaPilot — {plan.capitalize()} planınız aktif!", html)


def send_payment_failed_email(to: str) -> None:
    """Başarısız ödeme uyarı maili."""
    html = _render("payment_failed.html", {
        "settings_url": f"{BASE_URL}/settings/billing",
        "base_url": BASE_URL,
    })
    _send(to, "PiyasaPilot — Ödeme alınamadı", html)
