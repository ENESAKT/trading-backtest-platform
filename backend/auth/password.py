"""
Argon2 şifre hash / doğrulama.
"""

import re

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_ph = PasswordHasher(
    time_cost=2,
    memory_cost=65536,
    parallelism=2,
    hash_len=32,
    salt_len=16,
)

COMMON_PASSWORDS = {
    "password", "12345678", "qwerty123", "password1", "admin123",
    "piyasapilot", "enes1234",
}


def validate_password_strength(password: str) -> list[str]:
    """Server-side password policy."""
    errors: list[str] = []
    if len(password) < 8:
        errors.append("Şifre en az 8 karakter olmalı.")
    if not re.search(r"[A-Z]", password):
        errors.append("Şifre en az 1 büyük harf içermeli.")
    if not re.search(r"\d", password):
        errors.append("Şifre en az 1 rakam içermeli.")
    if password.lower() in COMMON_PASSWORDS:
        errors.append("Bu şifre çok yaygın.")
    return errors


def hash_password(plain: str) -> str:
    """Argon2id ile şifre hash'le."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Hash doğrula.
    Yanlış şifre → False.
    Hash formatı hatalı → False.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(hashed: str) -> bool:
    """Argon2 parametreleri değiştiyse yeniden hash gerekli mi?"""
    return _ph.check_needs_rehash(hashed)
