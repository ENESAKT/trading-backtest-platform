"""Redis helpers for auth state, rate limits and token blocking."""

from __future__ import annotations


class AuthRedisStore:
    def __init__(self, redis_client):
        self.r = redis_client

    async def set_oauth_state(self, state: str, data: str, ttl: int = 600) -> None:
        await self.r.set(f"oauth:{state}", data, ex=ttl)

    async def get_oauth_state(self, state: str) -> str | None:
        key = f"oauth:{state}"
        val = await self.r.get(key)
        await self.r.delete(key)
        return val

    async def block_token(self, jti: str, ttl: int) -> None:
        if jti:
            await self.r.set(f"blocked_jti:{jti}", "1", ex=ttl)

    async def is_token_blocked(self, jti: str) -> bool:
        if not jti:
            return False
        return bool(await self.r.exists(f"blocked_jti:{jti}"))

    async def incr_login_fail(self, email: str) -> int:
        key = f"login_fail:{email.lower()}"
        count = await self.r.incr(key)
        await self.r.expire(key, 1800)
        return int(count)

    async def clear_login_fail(self, email: str) -> None:
        await self.r.delete(f"login_fail:{email.lower()}")
