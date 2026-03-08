"""
app/main.py
FastAPI application factory.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.booking import router as booking_router
from app.core.config import get_settings
from app.db.redis_client import close_redis, get_redis

settings = get_settings()

# ── Rate limiter (shared instance) ───────────────────────────────────────────

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.GLOBAL_RATE_LIMIT],
)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up Redis connection
    await get_redis()
    yield
    await close_redis()


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        openapi_url="/openapi.json" if not settings.is_production else None,
        lifespan=lifespan,
    )

    # ── Rate limiting ─────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    # ── Trusted hosts (production hardening) ──────────────────
    if settings.is_production and settings.COOKIE_DOMAIN:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=[settings.COOKIE_DOMAIN, f"*.{settings.COOKIE_DOMAIN}"],
        )

    # ── CORS ──────────────────────────────────────────────────
    # Tighten allowed_origins in production
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if not settings.is_production else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Security headers middleware ───────────────────────────
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        return response

    # ── Routers ───────────────────────────────────────────────
    app.include_router(auth_router,    prefix=settings.API_V1_PREFIX)
    app.include_router(booking_router, prefix=settings.API_V1_PREFIX)

    # ── Health check ──────────────────────────────────────────
    @app.get("/health", tags=["System"], include_in_schema=False)
    async def health() -> dict:
        return {"status": "ok", "service": settings.APP_NAME}

    return app


app = create_app()
