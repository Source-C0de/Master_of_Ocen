"""
app/middleware/rbac.py

FastAPI dependencies for:
  - Extracting & validating the current user from a Bearer token
  - Role-based access control (RBAC) guard factory

Usage
-----
    from app.middleware.rbac import get_current_user, require_roles
    from app.models.user import UserRole

    # Protect a route — any authenticated user
    @router.get("/profile")
    async def profile(user = Depends(get_current_user)):
        ...

    # Protect a route — specific roles only
    @router.get("/admin/dashboard")
    async def dashboard(user = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))):
        ...
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from fastapi import Cookie, Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.security import decode_token
from app.db.redis_client import is_token_blacklisted
from app.db.session import get_db
from app.models.user import User, UserRole

_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)

_FORBIDDEN_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN,
    detail="Insufficient permissions",
)


# ── Token Claims dataclass ────────────────────────────────────────────────────

@dataclass(frozen=True)
class TokenClaims:
    sub:       str
    role:      str
    jti:       str
    branch_id: str | None = None


# ── Dependency: parse & validate Access Token ─────────────────────────────────

async def _extract_claims(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> TokenClaims:
    """
    Parse Bearer token from Authorization header.
    Validates signature, expiry, token type, and blacklist status.
    """
    if credentials is None:
        raise _CREDENTIALS_EXCEPTION

    try:
        claims = decode_token(credentials.credentials)
    except JWTError:
        raise _CREDENTIALS_EXCEPTION

    if claims.get("type") != "access":
        raise _CREDENTIALS_EXCEPTION

    jti = claims.get("jti")
    if jti and await is_token_blacklisted(jti):
        raise _CREDENTIALS_EXCEPTION

    return TokenClaims(
        sub=claims["sub"],
        role=claims["role"],
        jti=jti or "",
        branch_id=claims.get("branch_id"),
    )


async def get_current_user(
    claims: TokenClaims = Depends(_extract_claims),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve token claims → live User ORM object.
    Ensures the account still exists and is active.
    """
    stmt = (
        select(User)
        .where(User.id == claims.sub)
        .options(selectinload(User.assigned_branch))
    )
    result = await db.execute(stmt)
    user: User | None = result.scalar_one_or_none()

    if user is None or not user.is_active_account:
        raise _CREDENTIALS_EXCEPTION

    return user


# ── RBAC factory ──────────────────────────────────────────────────────────────

def require_roles(*roles: UserRole):
    """
    Dependency factory — return a FastAPI dependency that enforces
    the caller must hold one of the supplied roles.

    Example:
        @router.delete("/users/{user_id}")
        async def delete_user(
            user = Depends(require_roles(UserRole.ADMIN))
        ):
            ...

        @router.get("/queue/dashboard")
        async def queue_dashboard(
            user = Depends(require_roles(UserRole.MANAGER, UserRole.ADMIN))
        ):
            ...
    """
    allowed: frozenset[str] = frozenset(r.value for r in roles)

    async def _check(user: User = Depends(get_current_user)) -> User:
        if user.role.value not in allowed:
            raise _FORBIDDEN_EXCEPTION
        return user

    return _check


# ── Convenience pre-built guards ─────────────────────────────────────────────

require_admin    = require_roles(UserRole.ADMIN)
require_manager  = require_roles(UserRole.ADMIN, UserRole.MANAGER)
require_staff    = require_roles(UserRole.ADMIN, UserRole.MANAGER, UserRole.STAFF)
require_customer = require_roles(UserRole.CUSTOMER)


# ── Optional: branch-scoped guard ────────────────────────────────────────────

def require_same_branch():
    """
    Guard for Staff/Managers — ensures they can only act on resources
    belonging to their assigned branch.

    Usage:
        @router.get("/branches/{branch_id}/queue")
        async def get_queue(
            branch_id: uuid.UUID,
            user = Depends(require_staff),
            _    = Depends(require_same_branch()),
        ):
            ...
    """
    async def _check(
        request: Request,
        user: User = Depends(require_staff),
    ) -> User:
        # Admins bypass branch restriction
        if user.role.value == UserRole.ADMIN.value:
            return user

        branch_id = request.path_params.get("branch_id")
        if branch_id and str(user.assigned_branch_id) != str(branch_id):
            raise _FORBIDDEN_EXCEPTION
        return user

    return _check
