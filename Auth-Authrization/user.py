"""
app/models/user.py
SQLAlchemy ORM models — User, Branch, RefreshToken.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean, Column, DateTime, Enum, ForeignKey,
    Index, Integer, SmallInteger, String, Text, func,
)
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import relationship

from app.db.session import Base


# ── Enumerations ──────────────────────────────────────────────────────────────

class UserRole(str, enum.Enum):
    CUSTOMER = "CUSTOMER"
    STAFF    = "STAFF"
    MANAGER  = "MANAGER"
    ADMIN    = "ADMIN"


class UserStatus(str, enum.Enum):
    ACTIVE               = "ACTIVE"
    INACTIVE             = "INACTIVE"
    SUSPENDED            = "SUSPENDED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


# ── Branch ────────────────────────────────────────────────────────────────────

class Branch(Base):
    __tablename__ = "branches"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name       = Column(String(120), nullable=False)
    address    = Column(Text)
    timezone   = Column(String(60), nullable=False, default="UTC")
    is_active  = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    users = relationship("User", back_populates="assigned_branch")


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id                 = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email              = Column(String(254), unique=True, nullable=True, index=True)
    phone              = Column(String(20),  unique=True, nullable=True, index=True)
    password_hash      = Column(Text, nullable=False)
    role               = Column(
        Enum(UserRole, name="user_role"),
        nullable=False,
        default=UserRole.CUSTOMER,
        index=True,
    )
    status             = Column(
        Enum(UserStatus, name="user_status"),
        nullable=False,
        default=UserStatus.ACTIVE,
    )
    full_name          = Column(String(120), nullable=False)
    assigned_branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Security bookkeeping
    last_login_at      = Column(DateTime(timezone=True), nullable=True)
    failed_login_count = Column(SmallInteger, nullable=False, default=0)
    locked_until       = Column(DateTime(timezone=True), nullable=True)

    created_at         = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at         = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    assigned_branch    = relationship("Branch", back_populates="users")
    refresh_tokens     = relationship("RefreshToken", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_users_email_lower", func.lower(email), unique=True),
    )

    @property
    def is_locked(self) -> bool:
        from datetime import timezone
        if self.locked_until is None:
            return False
        return self.locked_until > datetime.now(tz=timezone.utc)

    @property
    def is_active_account(self) -> bool:
        return self.status == UserStatus.ACTIVE


# ── RefreshToken ──────────────────────────────────────────────────────────────

class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash    = Column(Text, nullable=False, unique=True)   # SHA-256 hex
    family_id     = Column(UUID(as_uuid=True), nullable=False, index=True)
    issued_at     = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at    = Column(DateTime(timezone=True), nullable=False)
    revoked_at    = Column(DateTime(timezone=True), nullable=True)
    revoke_reason = Column(String(80), nullable=True)
    user_agent    = Column(Text, nullable=True)
    ip_address    = Column(INET, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")

    @property
    def is_valid(self) -> bool:
        from datetime import timezone
        return (
            self.revoked_at is None
            and self.expires_at > datetime.now(tz=timezone.utc)
        )
