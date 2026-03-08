"""
app/services/auth_service.py
Core authentication business logic — login, refresh, logout.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Tuple

from fastapi import Request
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    password_needs_rehash,
    verify_password,
)
from app.db.redis_client import (
    blacklist_token,
    is_family_revoked,
    is_token_blacklisted,
    revoke_token_family,
)
from app.models.user import RefreshToken, User, UserStatus
from app.schemas.auth import LoginRequest, TokenResponse, UserPublic

settings = get_settings()

# ── Generic auth error to prevent enumeration ─────────────────────────────────

_AUTH_ERROR = "Invalid credentials"


class AuthError(Exception):
    """Raised for any authentication failure (opaque to callers)."""
    def __init__(self, message: str = _AUTH_ERROR, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class TokenError(Exception):
    """Raised when a token cannot be decoded or has been revoked."""
    def __init__(self, message: str = "Invalid or expired token"):
        self.message = message
        super().__init__(message)


# ── Internal helpers ──────────────────────────────────────────────────────────

async def _fetch_user_by_identifier(db: AsyncSession, identifier: str) -> User | None:
    """Lookup by email (case-insensitive) or phone."""
    if "@" in identifier:
        stmt = (
            select(User)
            .where(User.email == identifier.lower())
            .options(selectinload(User.assigned_branch))
        )
    else:
        stmt = (
            select(User)
            .where(User.phone == identifier)
            .options(selectinload(User.assigned_branch))
        )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def _record_failed_login(db: AsyncSession, user: User) -> None:
    new_count = (user.failed_login_count or 0) + 1
    locked_until = None
    if new_count >= settings.MAX_FAILED_LOGINS:
        locked_until = datetime.now(tz=timezone.utc) + timedelta(
            minutes=settings.LOCKOUT_DURATION_MINUTES
        )
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(failed_login_count=new_count, locked_until=locked_until)
    )
    await db.commit()


async def _record_successful_login(db: AsyncSession, user: User) -> None:
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(
            failed_login_count=0,
            locked_until=None,
            last_login_at=datetime.now(tz=timezone.utc),
        )
    )
    await db.commit()


async def _store_refresh_token(
    db: AsyncSession,
    user_id: uuid.UUID,
    raw_token: str,
    family_id: str,
    request: Request,
) -> RefreshToken:
    expires_at = datetime.now(tz=timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    rt = RefreshToken(
        user_id=user_id,
        token_hash=hash_token(raw_token),
        family_id=uuid.UUID(family_id),
        expires_at=expires_at,
        user_agent=request.headers.get("user-agent", "")[:500],
        ip_address=request.client.host if request.client else None,
    )
    db.add(rt)
    await db.commit()
    await db.refresh(rt)
    return rt


async def _revoke_refresh_token(
    db: AsyncSession,
    token_hash: str,
    reason: str = "logout",
) -> None:
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
        .values(revoked_at=datetime.now(tz=timezone.utc), revoke_reason=reason)
    )
    await db.commit()


def _build_token_response(user: User, access_token: str) -> TokenResponse:
    return TokenResponse(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserPublic.model_validate(user),
    )


# ── Public service functions ──────────────────────────────────────────────────

async def login(
    payload: LoginRequest,
    db: AsyncSession,
    request: Request,
) -> Tuple[TokenResponse, str, str]:
    """
    Authenticate a user.

    Returns (token_response, raw_refresh_token, family_id).
    Raises AuthError on any failure (opaque message for anti-enumeration).
    """
    user = await _fetch_user_by_identifier(db, payload.identifier)

    # ── Anti-enumeration: always run password hashing even for unknown users
    dummy_hash = "$argon2id$v=19$m=65536,t=3,p=4$dummysaltdummysalt$dummyhashvalueplaceholder"
    candidate_hash = user.password_hash if user else dummy_hash

    password_ok = verify_password(payload.password, candidate_hash)

    if not user or not password_ok:
        if user:
            await _record_failed_login(db, user)
        raise AuthError()

    # ── Account state checks
    if user.is_locked:
        raise AuthError("Account temporarily locked. Try again later.", 429)

    if not user.is_active_account:
        raise AuthError()   # opaque — don't reveal suspension

    # ── Rehash if parameters have changed
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(payload.password)
        db.add(user)
        await db.commit()

    await _record_successful_login(db, user)

    # ── Issue tokens
    extra = {}
    if user.assigned_branch_id:
        extra["branch_id"] = str(user.assigned_branch_id)

    access_token = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        extra_claims=extra,
    )
    raw_refresh, family_id = create_refresh_token(subject=str(user.id))
    await _store_refresh_token(db, user.id, raw_refresh, family_id, request)

    return _build_token_response(user, access_token), raw_refresh, family_id


async def refresh(
    raw_refresh_token: str,
    db: AsyncSession,
    request: Request,
) -> Tuple[TokenResponse, str, str]:
    """
    Rotate a refresh token.

    If an already-revoked token is presented (token reuse attack),
    the entire family is immediately revoked.

    Returns (token_response, new_raw_refresh_token, new_family_id).
    Raises TokenError on any failure.
    """
    try:
        claims = decode_token(raw_refresh_token)
    except JWTError:
        raise TokenError()

    if claims.get("type") != "refresh":
        raise TokenError()

    family_id = claims.get("family")
    jti = claims.get("jti")

    # ── Check family revocation (Redis fast path)
    if family_id and await is_family_revoked(family_id):
        raise TokenError("Session has been revoked")

    token_hash = hash_token(raw_refresh_token)

    # ── Lookup stored token
    stmt = (
        select(RefreshToken)
        .where(RefreshToken.token_hash == token_hash)
    )
    result = await db.execute(stmt)
    stored_rt = result.scalar_one_or_none()

    if stored_rt is None:
        # Token not in DB at all — reuse of a never-issued token
        raise TokenError()

    if not stored_rt.is_valid:
        # Reuse of a revoked/expired token → revoke entire family
        if family_id:
            await revoke_token_family(family_id)
            await db.execute(
                update(RefreshToken)
                .where(RefreshToken.family_id == stored_rt.family_id)
                .values(
                    revoked_at=datetime.now(tz=timezone.utc),
                    revoke_reason="compromised",
                )
            )
            await db.commit()
        raise TokenError("Token reuse detected — all sessions revoked")

    # ── Load user
    stmt2 = (
        select(User)
        .where(User.id == stored_rt.user_id)
        .options(selectinload(User.assigned_branch))
    )
    result2 = await db.execute(stmt2)
    user = result2.scalar_one_or_none()

    if not user or not user.is_active_account:
        raise TokenError()

    # ── Rotate: revoke old, issue new
    await _revoke_refresh_token(db, token_hash, reason="rotation")

    extra = {}
    if user.assigned_branch_id:
        extra["branch_id"] = str(user.assigned_branch_id)

    new_access = create_access_token(
        subject=str(user.id),
        role=user.role.value,
        extra_claims=extra,
    )
    new_raw_refresh, new_family_id = create_refresh_token(
        subject=str(user.id),
        family_id=family_id,   # keep same family to chain rotation
    )
    await _store_refresh_token(db, user.id, new_raw_refresh, new_family_id, request)

    return _build_token_response(user, new_access), new_raw_refresh, new_family_id


async def logout(
    raw_refresh_token: str,
    access_jti: str | None,
    db: AsyncSession,
) -> None:
    """
    Revoke refresh token in DB + blacklist access JTI in Redis.
    """
    token_hash = hash_token(raw_refresh_token)
    await _revoke_refresh_token(db, token_hash, reason="logout")

    if access_jti:
        await blacklist_token(
            access_jti,
            ttl_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
