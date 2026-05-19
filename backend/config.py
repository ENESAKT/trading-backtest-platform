"""Ortak uygulama yapılandırması.

Gizli değerler yalnızca süreç ortamına yüklenir; log, endpoint veya Telegram
cevaplarında açık değer döndürülmez.
"""

from __future__ import annotations

import os
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def load_environment() -> bool:
    """Repo kökündeki .env dosyasını ortam değişkenlerine yükle.

    Dönüş değeri sadece dosyanın var olup olmadığını belirtir. Değerler hiçbir
    şekilde döndürülmez veya loglanmaz.
    """
    env_path = ROOT / ".env"
    if not env_path.exists():
        return False

    try:
        from dotenv import load_dotenv

        load_dotenv(dotenv_path=env_path, override=False)
        return True
    except ImportError:
        pass

    # Hafif fallback: python-dotenv yoksa basit KEY=VALUE satırlarını yükle.
    # Var olan process env değerlerinin üzerine yazılmaz.
    for raw_line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ[key] = value
    return True


def getenv(name: str, default: str = "") -> str:
    """Ortam değişkeni oku; önce .env yüklemesini garanti eder."""
    load_environment()
    return os.getenv(name, default)


def telegram_configured() -> bool:
    """Telegram token ve yetkili chat ayarı var mı?"""
    return bool(getenv("TELEGRAM_BOT_TOKEN") and getenv("TELEGRAM_CHAT_ID"))


def telegram_authorized_chat_configured() -> bool:
    """Yetkili Telegram kullanıcı/chat ayarı var mı?"""
    return bool(getenv("TELEGRAM_CHAT_ID"))


def llm_configured() -> bool:
    """Serbest sohbet için LLM anahtarı var mı?"""
    return bool(getenv("ANTHROPIC_API_KEY"))


def mask_sensitive(text: str | None) -> str | None:
    """Log/API/Telegram cevabı için gizli değerleri maskele."""
    if text is None:
        return None
    masked = str(text)
    masked = re.sub(r"\d{8,}:[A-Za-z0-9_-]{20,}", "[TOKEN_GIZLI]", masked)
    masked = re.sub(
        r"(?i)(token|key|password|secret|api_key)\s*[:=]\s*\S+",
        r"\1=[GIZLI]",
        masked,
    )
    for secret_name in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "ANTHROPIC_API_KEY"):
        secret = getenv(secret_name)
        if secret:
            masked = masked.replace(secret, "[GIZLI]")
    return masked
