"""
app/core/config.py
Central configuration — all secrets sourced from environment variables.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, AnyUrl
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── App ──────────────────────────────────────────────────
    APP_NAME: str = "Booking & Queue Auth Service"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ─────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/booking_db"

    # ── Redis ────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"
    TOKEN_BLACKLIST_TTL: int = 60 * 15        # match access token lifetime (seconds)

    # ── JWT ──────────────────────────────────────────────────
    JWT_SECRET_KEY: str = secrets.token_urlsafe(64)   # MUST be overridden in production
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Cookie ───────────────────────────────────────────────
    COOKIE_DOMAIN: str | None = None          # None = same host
    COOKIE_SECURE: bool = True                # False only for local HTTP dev
    COOKIE_SAMESITE: str = "strict"
    REFRESH_COOKIE_NAME: str = "refresh_token"

    # ── Rate Limiting ─────────────────────────────────────────
    LOGIN_RATE_LIMIT: str = "10/minute"       # slowapi format
    GLOBAL_RATE_LIMIT: str = "200/minute"

    # ── Argon2id params ──────────────────────────────────────
    ARGON2_TIME_COST: int = 3
    ARGON2_MEMORY_COST: int = 65536           # 64 MB
    ARGON2_PARALLELISM: int = 4

    # ── Account lockout ──────────────────────────────────────
    MAX_FAILED_LOGINS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15

    @field_validator("APP_ENV")
    @classmethod
    def validate_env(cls, v: str) -> str:
        allowed = {"development", "staging", "production"}
        if v not in allowed:
            raise ValueError(f"APP_ENV must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()
