""".env başlangıç validasyonu — kritik yapılandırma yokluğunu açıkça raporlar.

Kullanım:
    from backend.env_validator import validate_env
    validate_env()

Davranış:
  * Kritik olmayan eksikler uyarı loglanır.
  * ``STRICT_ENV_VALIDATION=1`` setliyse eksik *gerekli* alanlar RuntimeError fırlatır.
  * Token/secret değerleri asla loglanmaz.
"""

from __future__ import annotations

import logging
import os

_logger = logging.getLogger(__name__)


class EnvValidationError(RuntimeError):
    """Kritik .env değişkeni eksik."""


# Gerekli (strict modda eksikse RuntimeError)
REQUIRED_VARS: list[tuple[str, str]] = [
    # Şu an zorunlu gerekli değişken yok — tümü opsiyonel.
    # İleride dışa açılacaksa:
    # ("API_KEY", "API erişimi için zorunlu anahtar"),
]

# Opsiyonel (eksikse uyarı loglanır)
OPTIONAL_VARS: list[tuple[str, str]] = [
    ("TELEGRAM_BOT_TOKEN", "Telegram bildirimleri devre dışı"),
    ("TELEGRAM_CHAT_ID", "Telegram yetkili kullanıcı tanımlı değil"),
    ("SMTP_HOST", "E-posta bildirimleri devre dışı"),
    ("SMTP_USER", "E-posta gönderici hesap tanımlı değil"),
    ("BIST_HTTP_URL_TEMPLATE", "Lisanslı BIST feed bağlı değil — Yahoo fallback aktif"),
    ("VIOP_HTTP_URL_TEMPLATE", "Lisanslı VİOP feed bağlı değil"),
    ("ANTHROPIC_API_KEY", "LLM serbest sohbet devre dışı"),
]


def validate_env(*, strict: bool | None = None) -> dict[str, list[str]]:
    """Ortam değişkenlerini doğrula.

    Args:
        strict: None ise ``STRICT_ENV_VALIDATION`` env'den okunur.

    Returns:
        ``{"missing_required": [...], "missing_optional": [...]}``

    Raises:
        EnvValidationError: strict modda gerekli değişken eksikse.
    """
    from backend.config import load_environment
    load_environment()

    if strict is None:
        strict = os.environ.get("STRICT_ENV_VALIDATION", "") == "1"

    missing_required: list[str] = []
    missing_optional: list[str] = []

    for key, note in REQUIRED_VARS:
        if not os.environ.get(key):
            missing_required.append(key)
            _logger.error("[env] ZORUNLU değişken eksik: %s — %s", key, note)

    for key, note in OPTIONAL_VARS:
        if not os.environ.get(key):
            missing_optional.append(key)
            _logger.warning("[env] Opsiyonel değişken eksik: %s — %s", key, note)

    if strict and missing_required:
        raise EnvValidationError(
            f"Eksik zorunlu .env değişkenleri: {', '.join(missing_required)}. "
            f"Detay için .env.example dosyasına bakın."
        )

    if not missing_required and not missing_optional:
        _logger.info("[env] Tüm ortam değişkenleri doğrulandı ✅")

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
    }
