"""
app/schemas/auth.py
Pydantic v2 schemas for auth request / response payloads.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


# ── Helpers ───────────────────────────────────────────────────────────────────

_PHONE_RE = re.compile(r"^\+[1-9]\d{7,14}$")   # loose E.164


def _looks_like_email(value: str) -> bool:
    return "@" in value


def _looks_like_phone(value: str) -> bool:
    return _PHONE_RE.match(value) is not None


# ── Request schemas ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    """
    Accepts either email or phone as the identifier.
    Password must be 8–128 characters.
    """
    identifier: Annotated[str, Field(min_length=3, max_length=254, examples=["user@example.com", "+966501234567"])]
    password:   Annotated[str, Field(min_length=8, max_length=128)]

    @field_validator("identifier")
    @classmethod
    def validate_identifier(cls, v: str) -> str:
        v = v.strip()
        if _looks_like_email(v):
            # basic email sanity
            if not re.match(r"^[^@]+@[^@]+\.[^@]+$", v):
                raise ValueError("Invalid email format")
            return v.lower()
        if _looks_like_phone(v):
            return v
        raise ValueError("Identifier must be a valid email or E.164 phone number")


# ── Nested response objects ───────────────────────────────────────────────────

class BranchInfo(BaseModel):
    id:       uuid.UUID
    name:     str
    timezone: str

    model_config = {"from_attributes": True}


class UserPublic(BaseModel):
    """
    Safe user representation embedded in login response.
    Includes queue-system context fields.
    """
    id:                 uuid.UUID
    full_name:          str
    email:              str | None
    phone:              str | None
    role:               str
    status:             str
    assigned_branch_id: uuid.UUID | None = None
    assigned_branch:    BranchInfo | None = None
    last_login_at:      datetime | None = None

    model_config = {"from_attributes": True}


# ── Response schemas ──────────────────────────────────────────────────────────

class TokenResponse(BaseModel):
    """Returned by /auth/login and /auth/refresh."""
    access_token:  str
    token_type:    str = "bearer"
    expires_in:    int              # seconds
    user:          UserPublic


class MessageResponse(BaseModel):
    """Generic success/info message."""
    message: str


class ErrorResponse(BaseModel):
    """
    Anti-enumeration: all auth errors use the same surface message.
    Detail is only populated in non-production environments.
    """
    error:  str
    detail: str | None = None
