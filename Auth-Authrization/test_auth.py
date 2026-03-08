"""
tests/test_auth.py
Auth endpoint tests — uses httpx AsyncClient with mocked DB/Redis.
"""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.security import hash_password, create_access_token, create_refresh_token, hash_token
from app.main import app
from app.models.user import User, UserRole, UserStatus, Branch


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _make_user(
    role: UserRole = UserRole.CUSTOMER,
    branch_id: uuid.UUID | None = None,
    **kwargs,
) -> MagicMock:
    u = MagicMock(spec=User)
    u.id = uuid.uuid4()
    u.email = "test@example.com"
    u.phone = None
    u.full_name = "Test User"
    u.password_hash = hash_password("SecurePass1!")
    u.role = role
    u.status = UserStatus.ACTIVE
    u.assigned_branch_id = branch_id
    u.assigned_branch = None
    u.last_login_at = None
    u.failed_login_count = 0
    u.locked_until = None
    u.is_locked = False
    u.is_active_account = True
    for k, v in kwargs.items():
        setattr(u, k, v)
    return u


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


# ── Login tests ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success_email(client: AsyncClient):
    user = _make_user()

    with (
        patch("app.services.auth_service._fetch_user_by_identifier", new_callable=AsyncMock, return_value=user),
        patch("app.services.auth_service._record_successful_login", new_callable=AsyncMock),
        patch("app.services.auth_service._store_refresh_token", new_callable=AsyncMock),
        patch("app.db.session.get_db", return_value=AsyncMock()),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "test@example.com", "password": "SecurePass1!"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "CUSTOMER"
    # Refresh token must be in HttpOnly cookie
    assert "refresh_token" in resp.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient):
    user = _make_user()

    with (
        patch("app.services.auth_service._fetch_user_by_identifier", new_callable=AsyncMock, return_value=user),
        patch("app.services.auth_service._record_failed_login", new_callable=AsyncMock),
        patch("app.db.session.get_db", return_value=AsyncMock()),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "test@example.com", "password": "WrongPassword!"},
        )

    assert resp.status_code == 401
    # Anti-enumeration: generic message only
    assert resp.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_unknown_user_generic_error(client: AsyncClient):
    """Unknown user must return the exact same error as wrong password."""
    with (
        patch("app.services.auth_service._fetch_user_by_identifier", new_callable=AsyncMock, return_value=None),
        patch("app.db.session.get_db", return_value=AsyncMock()),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "nobody@example.com", "password": "anything"},
        )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Invalid credentials"


@pytest.mark.asyncio
async def test_login_locked_account(client: AsyncClient):
    user = _make_user(
        is_locked=True,
        locked_until=datetime.now(tz=timezone.utc) + timedelta(minutes=10),
    )

    with (
        patch("app.services.auth_service._fetch_user_by_identifier", new_callable=AsyncMock, return_value=user),
        patch("app.db.session.get_db", return_value=AsyncMock()),
    ):
        resp = await client.post(
            "/api/v1/auth/login",
            json={"identifier": "test@example.com", "password": "SecurePass1!"},
        )

    assert resp.status_code in (401, 429)


# ── Refresh tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_no_cookie(client: AsyncClient):
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_invalid_token(client: AsyncClient):
    client.cookies.set("refresh_token", "invalid.jwt.token")
    resp = await client.post("/api/v1/auth/refresh")
    assert resp.status_code == 401


# ── Logout tests ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_logout_requires_auth(client: AsyncClient):
    resp = await client.post("/api/v1/auth/logout")
    assert resp.status_code == 401


# ── RBAC tests ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_route_rejects_customer(client: AsyncClient):
    customer = _make_user(role=UserRole.CUSTOMER)
    access_token = create_access_token(
        subject=str(customer.id),
        role=UserRole.CUSTOMER.value,
    )

    with (
        patch("app.middleware.rbac.is_token_blacklisted", new_callable=AsyncMock, return_value=False),
        patch("app.middleware.rbac.get_current_user", new_callable=AsyncMock, return_value=customer),
    ):
        resp = await client.get(
            "/api/v1/booking/admin/users",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_staff_can_see_queue(client: AsyncClient):
    staff = _make_user(role=UserRole.STAFF, branch_id=uuid.uuid4())
    access_token = create_access_token(
        subject=str(staff.id),
        role=UserRole.STAFF.value,
    )

    with (
        patch("app.middleware.rbac.is_token_blacklisted", new_callable=AsyncMock, return_value=False),
        patch("app.middleware.rbac.get_current_user", new_callable=AsyncMock, return_value=staff),
    ):
        resp = await client.get(
            "/api/v1/booking/queue/status",
            headers={"Authorization": f"Bearer {access_token}"},
        )

    assert resp.status_code == 200


# ── Security: constant-time comparison ───────────────────────────────────────

def test_password_hash_not_reversible():
    pw = "SuperSecret99!"
    h = hash_password(pw)
    assert pw not in h
    assert h.startswith("$argon2id$")


def test_verify_password_wrong():
    from app.core.security import verify_password
    h = hash_password("correct-password")
    assert verify_password("correct-password", h) is True
    assert verify_password("wrong-password", h) is False


def test_safe_str_cmp():
    from app.core.security import safe_str_cmp
    assert safe_str_cmp("abc", "abc") is True
    assert safe_str_cmp("abc", "xyz") is False


def test_token_hash_is_deterministic():
    raw = "some.jwt.token"
    assert hash_token(raw) == hash_token(raw)
    assert hash_token(raw) != raw
