"""
app/api/v1/endpoints/auth.py
Auth endpoints: /login  /refresh  /logout
"""
from __future__ import annotations

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.db.session import get_db
from app.middleware.rbac import get_current_user
from app.models.user import User
from app.schemas.auth import LoginRequest, MessageResponse, TokenResponse
from app.services.auth_service import AuthError, TokenError, login, logout, refresh

settings = get_settings()
router   = APIRouter(prefix="/auth", tags=["Authentication"])
limiter  = Limiter(key_func=get_remote_address)

_COOKIE_NAME = settings.REFRESH_COOKIE_NAME


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",   # Scope cookie to auth routes only
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=_COOKIE_NAME,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        domain=settings.COOKIE_DOMAIN,
        path="/api/v1/auth",
    )


# ── POST /auth/login ──────────────────────────────────────────────────────────

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate a user (email or phone + password)",
    responses={
        401: {"description": "Invalid credentials"},
        429: {"description": "Too many requests / account locked"},
    },
)
@limiter.limit(settings.LOGIN_RATE_LIMIT)
async def login_endpoint(
    payload: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Response:
    try:
        token_resp, raw_refresh, _ = await login(payload, db, request)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message)

    response = JSONResponse(
        content=token_resp.model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
    _set_refresh_cookie(response, raw_refresh)
    return response


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Rotate refresh token and obtain a new access token",
    responses={
        401: {"description": "Invalid or expired refresh token"},
    },
)
async def refresh_endpoint(
    request: Request,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> Response:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        token_resp, new_raw_refresh, _ = await refresh(refresh_token, db, request)
    except TokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=exc.message)

    response = JSONResponse(
        content=token_resp.model_dump(mode="json"),
        status_code=status.HTTP_200_OK,
    )
    _set_refresh_cookie(response, new_raw_refresh)
    return response


# ── POST /auth/logout ─────────────────────────────────────────────────────────

@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke session (refresh + access tokens)",
)
async def logout_endpoint(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    refresh_token: str | None = Cookie(default=None, alias=_COOKIE_NAME),
) -> Response:
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active session found",
        )

    # Extract JTI from the access token claims (already validated by get_current_user)
    from app.core.security import decode_token
    from jose import JWTError

    access_jti: str | None = None
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            claims = decode_token(auth_header[7:])
            access_jti = claims.get("jti")
        except JWTError:
            pass

    await logout(refresh_token, access_jti, db)

    resp = JSONResponse(
        content={"message": "Successfully logged out"},
        status_code=status.HTTP_200_OK,
    )
    _clear_refresh_cookie(resp)
    return resp


# ── GET /auth/me ──────────────────────────────────────────────────────────────
# Convenience endpoint — returns current user from access token

@router.get(
    "/me",
    summary="Return the currently authenticated user",
)
async def me_endpoint(
    current_user: User = Depends(get_current_user),
) -> dict:
    from app.schemas.auth import UserPublic
    return UserPublic.model_validate(current_user).model_dump(mode="json")
