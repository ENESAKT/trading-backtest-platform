"""
Auth Repository — MySQL CRUD işlemleri.
Tüm DB sorguları buradan yapılır, router'da SQL yok.
"""

from __future__ import annotations

import secrets
import string
from datetime import datetime, timezone

import aiomysql

from .jwt_utils import hash_token, refresh_token_expires_at
from .password import hash_password


async def get_user_by_email(pool: aiomysql.Pool, email: str) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM users WHERE email = %s AND is_active = TRUE LIMIT 1",
                (email,),
            )
            return await cur.fetchone()


async def get_user_by_id(pool: aiomysql.Pool, user_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM users WHERE id = %s AND is_active = TRUE LIMIT 1",
                (user_id,),
            )
            return await cur.fetchone()


async def create_user(
    pool: aiomysql.Pool,
    email: str,
    password: str | None,
    display_name: str,
    email_verified: bool = False,
    role: str = "free",
) -> int:
    """Kullanıcı oluştur, yeni user_id döndür."""
    ph = hash_password(password) if password else None
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO users
                   (email, email_verified, password_hash, display_name, role)
                   VALUES (%s, %s, %s, %s, %s)""",
                (email, email_verified, ph, display_name, role),
            )
            await conn.commit()
            # Aynı bağlantıda LAST_INSERT_ID al
            await cur.execute("SELECT LAST_INSERT_ID()")
            row = await cur.fetchone()
            user_id = row[0]

    # Varsayılan settings satırı oluştur
    await _create_user_settings(pool, user_id)
    await _assign_referral_code(pool, user_id)
    await _start_pro_trial(pool, user_id)
    return user_id


async def _assign_referral_code(pool: aiomysql.Pool, user_id: int) -> None:
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(5):
        code = "".join(secrets.choice(alphabet) for _ in range(6))
        try:
            async with pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("UPDATE users SET referral_code=%s WHERE id=%s", (code, user_id))
                    await conn.commit()
            return
        except Exception:
            continue


async def _start_pro_trial(pool: aiomysql.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("SELECT id FROM subscription_plans WHERE slug='pro' LIMIT 1")
            row = await cur.fetchone()
            if not row:
                return
            plan_id = row[0]
            await cur.execute(
                """INSERT INTO user_subscriptions
                   (user_id, plan_id, status, trial_ends_at, current_period_start, current_period_end)
                   VALUES (%s, %s, 'trialing', NOW() + INTERVAL 14 DAY, NOW(), NOW() + INTERVAL 14 DAY)""",
                (user_id, plan_id),
            )
            await cur.execute("UPDATE users SET role='pro' WHERE id=%s", (user_id,))
            await conn.commit()


async def _create_user_settings(pool: aiomysql.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "INSERT IGNORE INTO user_settings (user_id) VALUES (%s)",
                (user_id,),
            )
            await conn.commit()


async def mark_email_verified(pool: aiomysql.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET email_verified = TRUE WHERE id = %s",
                (user_id,),
            )
            await conn.commit()


async def update_last_login(pool: aiomysql.Pool, user_id: int) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET last_login_at = NOW() WHERE id = %s",
                (user_id,),
            )
            await conn.commit()


async def update_user_role(pool: aiomysql.Pool, user_id: int, role: str) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET role = %s WHERE id = %s",
                (role, user_id),
            )
            await conn.commit()


# ── Refresh Token ────────────────────────────────────────────────────────────

async def store_refresh_token(
    pool: aiomysql.Pool,
    user_id: int,
    token_hash: str,
    user_agent: str = "",
    ip_address: str = "",
    device_name: str | None = None,
) -> None:
    import uuid
    expires_at = refresh_token_expires_at()
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                """INSERT INTO refresh_tokens
                   (user_id, token_hash, jti, user_agent, ip_address, device_name, expires_at)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (user_id, token_hash, str(uuid.uuid4()), user_agent, ip_address, device_name, expires_at),
            )
            await conn.commit()


async def get_refresh_token(
    pool: aiomysql.Pool, token_hash: str
) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM refresh_tokens
                   WHERE token_hash = %s
                     AND revoked_at IS NULL
                     AND expires_at > NOW()
                   LIMIT 1""",
                (token_hash,),
            )
            return await cur.fetchone()


async def revoke_refresh_token(pool: aiomysql.Pool, token_hash: str) -> None:
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE token_hash = %s",
                (token_hash,),
            )
            await conn.commit()


async def revoke_all_user_tokens(pool: aiomysql.Pool, user_id: int) -> None:
    """Tüm aktif oturumları kapat (şifre değişikliği / hesap silme)."""
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE refresh_tokens SET revoked_at = NOW() WHERE user_id = %s AND revoked_at IS NULL",
                (user_id,),
            )
            await conn.commit()


# ── Email Doğrulama ──────────────────────────────────────────────────────────

async def create_email_verification_token(
    pool: aiomysql.Pool, user_id: int
) -> str:
    """
    Rastgele token üret, hash'ini DB'ye kaydet, raw token döndür.
    Raw token email'de link olarak kullanılır.
    """
    raw = secrets.token_urlsafe(32)
    token_hash = hash_token(raw)
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            # Önceki tokenları geçersiz kıl
            await cur.execute(
                "UPDATE email_verification_tokens SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL",
                (user_id,),
            )
            await cur.execute(
                "INSERT INTO email_verification_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user_id, token_hash, expires_at),
            )
            await conn.commit()
    return raw


async def consume_email_verification_token(
    pool: aiomysql.Pool, raw_token: str
) -> int | None:
    """
    Token doğrula ve kullan (tek kullanımlık).
    Returns: user_id veya None
    """
    token_hash = hash_token(raw_token)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM email_verification_tokens
                   WHERE token_hash = %s
                     AND used_at IS NULL
                     AND expires_at > NOW()
                   LIMIT 1""",
                (token_hash,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            await cur.execute(
                "UPDATE email_verification_tokens SET used_at = NOW() WHERE id = %s",
                (row["id"],),
            )
            await conn.commit()
            return row["user_id"]


# ── Şifre Sıfırlama ──────────────────────────────────────────────────────────

async def create_password_reset_token(
    pool: aiomysql.Pool, user_id: int
) -> str:
    raw = secrets.token_urlsafe(32)
    token_hash = hash_token(raw)
    from datetime import timedelta
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE password_reset_tokens SET used_at = NOW() WHERE user_id = %s AND used_at IS NULL",
                (user_id,),
            )
            await cur.execute(
                "INSERT INTO password_reset_tokens (user_id, token_hash, expires_at) VALUES (%s, %s, %s)",
                (user_id, token_hash, expires_at),
            )
            await conn.commit()
    return raw


async def consume_password_reset_token(
    pool: aiomysql.Pool, raw_token: str
) -> int | None:
    token_hash = hash_token(raw_token)
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                """SELECT * FROM password_reset_tokens
                   WHERE token_hash = %s
                     AND used_at IS NULL
                     AND expires_at > NOW()
                   LIMIT 1""",
                (token_hash,),
            )
            row = await cur.fetchone()
            if not row:
                return None
            await cur.execute(
                "UPDATE password_reset_tokens SET used_at = NOW() WHERE id = %s",
                (row["id"],),
            )
            await conn.commit()
            return row["user_id"]


async def update_password(
    pool: aiomysql.Pool, user_id: int, new_password: str
) -> None:
    ph = hash_password(new_password)
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (ph, user_id),
            )
            await conn.commit()


# ── Kullanıcı Ayarları ───────────────────────────────────────────────────────

async def get_user_settings(pool: aiomysql.Pool, user_id: int) -> dict | None:
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            await cur.execute(
                "SELECT * FROM user_settings WHERE user_id = %s",
                (user_id,),
            )
            return await cur.fetchone()


async def update_user_settings(
    pool: aiomysql.Pool, user_id: int, updates: dict
) -> None:
    if not updates:
        return
    set_parts = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [user_id]
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute(
                f"UPDATE user_settings SET {set_parts} WHERE user_id = %s",
                values,
            )
            await conn.commit()


# ── OAuth ────────────────────────────────────────────────────────────────────

async def get_or_create_oauth_user(
    pool: aiomysql.Pool,
    provider: str,
    provider_user_id: str,
    email: str,
    display_name: str,
    avatar_url: str | None = None,
) -> tuple[int, bool]:
    """
    OAuth kullanıcısını bul veya oluştur.
    Returns: (user_id, is_new)
    """
    async with pool.acquire() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
            # Önce OAuth kaydı var mı?
            await cur.execute(
                "SELECT user_id FROM oauth_accounts WHERE provider=%s AND provider_user_id=%s LIMIT 1",
                (provider, provider_user_id),
            )
            row = await cur.fetchone()
            if row:
                return row["user_id"], False

            # Email ile mevcut kullanıcı var mı?
            await cur.execute(
                "SELECT id FROM users WHERE email = %s LIMIT 1",
                (email,),
            )
            user_row = await cur.fetchone()

            if user_row:
                user_id = user_row["id"]
                is_new = False
            else:
                # Yeni kullanıcı oluştur
                await cur.execute(
                    """INSERT INTO users (email, email_verified, display_name, avatar_url, role)
                       VALUES (%s, TRUE, %s, %s, 'free')""",
                    (email, display_name, avatar_url),
                )
                await conn.commit()
                await cur.execute("SELECT LAST_INSERT_ID()")
                user_id = (await cur.fetchone())["LAST_INSERT_ID()"]
                is_new = True
                await _create_user_settings(pool, user_id)

            # OAuth kaydı ekle
            await cur.execute(
                """INSERT INTO oauth_accounts (user_id, provider, provider_user_id)
                   VALUES (%s, %s, %s)""",
                (user_id, provider, provider_user_id),
            )
            await conn.commit()
            return user_id, is_new
