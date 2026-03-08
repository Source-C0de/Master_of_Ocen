"""
app/db/redis_client.py
Async Redis client — token blacklist & session state.
"""
from __future__ import annotations

import redis.asyncio as aioredis
from redis.asyncio import Redis

from app.core.config import get_settings

settings = get_settings()

_redis_pool: Redis | None = None


async def get_redis() -> Redis:
    """Return (and lazily initialise) the shared Redis connection pool."""
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_pool


async def close_redis() -> None:
    global _redis_pool
    if _redis_pool:
        await _redis_pool.aclose()
        _redis_pool = None


# ── Blacklist helpers ─────────────────────────────────────────────────────────

_BLACKLIST_PREFIX = "bl:jti:"


async def blacklist_token(jti: str, ttl_seconds: int) -> None:
    """Add a JTI to the blacklist with the remaining token TTL."""
    r = await get_redis()
    await r.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")


async def is_token_blacklisted(jti: str) -> bool:
    """Return True if the JTI appears in the blacklist."""
    r = await get_redis()
    return bool(await r.exists(f"{_BLACKLIST_PREFIX}{jti}"))


# ── Refresh-token family revocation ──────────────────────────────────────────

_FAMILY_PREFIX = "rt:family:"


async def revoke_token_family(family_id: str) -> None:
    """Mark an entire refresh-token family as compromised."""
    r = await get_redis()
    ttl = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    await r.setex(f"{_FAMILY_PREFIX}{family_id}", ttl, "revoked")


async def is_family_revoked(family_id: str) -> bool:
    r = await get_redis()
    return bool(await r.exists(f"{_FAMILY_PREFIX}{family_id}"))
