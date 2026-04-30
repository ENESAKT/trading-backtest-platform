from __future__ import annotations

from backend.notifier.email import email_configured, email_status


def test_email_status_uses_safe_public_fields(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.example.test")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_USER", "sender@example.test")
    monkeypatch.setenv("SMTP_PASS", "secret-pass")
    monkeypatch.setenv("NOTIFY_EMAIL_TO", "enes@example.test")

    status = email_status()

    assert email_configured() is True
    assert status == {
        "smtp_yapilandirildi": True,
        "smtp_host": "smtp.example.test",
        "smtp_port": 2525,
        "alici_yapilandirildi": True,
    }
    assert "secret-pass" not in str(status)


def test_email_status_handles_invalid_port(monkeypatch):
    monkeypatch.setenv("SMTP_PORT", "not-an-int")
    monkeypatch.delenv("SMTP_USER", raising=False)
    monkeypatch.delenv("SMTP_PASS", raising=False)
    monkeypatch.delenv("NOTIFY_EMAIL_TO", raising=False)

    status = email_status()

    assert status["smtp_yapilandirildi"] is False
    assert status["smtp_port"] == 587
