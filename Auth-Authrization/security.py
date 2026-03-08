"""
app/core/security.py
Cryptographic primitives — hashing, JWT creation/verification, constant-time comparison.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError
from jose import JWTError, jwt

from app.core.config import get_settings

settings = get_settings()

# ── Argon2id hasher (singleton) ───────────────────────────────────────────────

_ph = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
    hash_len=32,
    salt_len=16,
)


def hash_password(plain: str) -> str:
    """Return an Argon2id hash of *plain*."""
    return _ph.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """
    Constant-time Argon2id verification.

    Always runs the full verification even on mismatch to prevent
    timing-based user enumeration. Returns False on any error.
    """
    try:
        return _ph.verify(hashed, plain)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def password_needs_rehash(hashed: str) -> bool:
    """True when stored hash was produced with older Argon2 parameters."""
    return _ph.check_needs_rehash(hashed)


# ── JWT ───────────────────────────────────────────────────────────────────────

_SECRET = settings.JWT_SECRET_KEY
_ALG = settings.JWT_ALGORITHM


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


def create_access_token(
    subject: str,
    role: str,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a short-lived access JWT.

    Claims:
        sub  — user UUID (string)
        role — RBAC role
        type — literal "access"
        iat  — issued-at
        exp  — expiry
        jti  — unique token ID (for future per-token blacklisting)
    """
    now = _utcnow()
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, _SECRET, algorithm=_ALG)


def create_refresh_token(
    subject: str,
    family_id: str | None = None,
) -> tuple[str, str]:
    """
    Create a long-lived refresh JWT.

    Returns (raw_token, family_id).
    family_id chains related refresh tokens for rotation-breach detection.
    """
    now = _utcnow()
    fid = family_id or str(uuid.uuid4())
    payload: dict[str, Any] = {
        "sub": subject,
        "type": "refresh",
        "family": fid,
        "iat": now,
        "exp": now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _SECRET, algorithm=_ALG), fid


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT. Raises JWTError on any failure.
    Callers must catch JWTError.
    """
    return jwt.decode(token, _SECRET, algorithms=[_ALG])


# ── Token hashing (for DB storage) ───────────────────────────────────────────

def hash_token(raw_token: str) -> str:
    """SHA-256 hex digest of a raw token — safe to store in DB."""
    return hashlib.sha256(raw_token.encode()).hexdigest()


# ── Constant-time string comparison ──────────────────────────────────────────

def safe_str_cmp(a: str, b: str) -> bool:
    """
    HMAC-based constant-time string comparison.
    Prevents timing oracle attacks on token/secret comparison.
    """
    return hmac.compare_digest(
        a.encode("utf-8"),
        b.encode("utf-8"),
    )
