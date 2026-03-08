-- ============================================================
-- Booking & Queue System — Auth Schema
-- PostgreSQL migration
-- ============================================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Enums ────────────────────────────────────────────────────

CREATE TYPE user_role AS ENUM ('CUSTOMER', 'STAFF', 'MANAGER', 'ADMIN');
CREATE TYPE user_status AS ENUM ('ACTIVE', 'INACTIVE', 'SUSPENDED', 'PENDING_VERIFICATION');

-- ── Branches ─────────────────────────────────────────────────
-- Referenced by staff/manager users for queue context

CREATE TABLE branches (
    id            UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(120) NOT NULL,
    address       TEXT,
    timezone      VARCHAR(60)  NOT NULL DEFAULT 'UTC',
    is_active     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- ── Users ─────────────────────────────────────────────────────

CREATE TABLE users (
    id                  UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Identity fields (both nullable individually; at least one must be set — enforced at app layer)
    email               VARCHAR(254) UNIQUE,
    phone               VARCHAR(20)  UNIQUE,          -- E.164 format e.g. +966501234567
    -- Auth
    password_hash       TEXT         NOT NULL,
    role                user_role    NOT NULL DEFAULT 'CUSTOMER',
    status              user_status  NOT NULL DEFAULT 'ACTIVE',
    -- Profile
    full_name           VARCHAR(120) NOT NULL,
    -- Booking / Queue context
    assigned_branch_id  UUID         REFERENCES branches(id) ON DELETE SET NULL,
    -- Security bookkeeping
    last_login_at       TIMESTAMPTZ,
    failed_login_count  SMALLINT     NOT NULL DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    -- Metadata
    created_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- At least one identifier must exist
    CONSTRAINT chk_identifier CHECK (email IS NOT NULL OR phone IS NOT NULL)
);

CREATE INDEX idx_users_email  ON users (email)  WHERE email  IS NOT NULL;
CREATE INDEX idx_users_phone  ON users (phone)  WHERE phone  IS NOT NULL;
CREATE INDEX idx_users_role   ON users (role);
CREATE INDEX idx_users_branch ON users (assigned_branch_id) WHERE assigned_branch_id IS NOT NULL;

-- ── Refresh Token Store ───────────────────────────────────────
-- Persistent record; Redis acts as the fast revocation layer.
-- This table is the source of truth for audit/revocation.

CREATE TABLE refresh_tokens (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      UUID        NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash   TEXT        NOT NULL UNIQUE,   -- SHA-256 of the raw token
    family_id    UUID        NOT NULL,           -- Rotation family — reuse = revoke whole family
    issued_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at   TIMESTAMPTZ NOT NULL,
    revoked_at   TIMESTAMPTZ,
    revoke_reason VARCHAR(80),                   -- 'logout' | 'rotation' | 'compromised'
    user_agent   TEXT,
    ip_address   INET
);

CREATE INDEX idx_rt_user_id    ON refresh_tokens (user_id);
CREATE INDEX idx_rt_family     ON refresh_tokens (family_id);
CREATE INDEX idx_rt_expires_at ON refresh_tokens (expires_at);

-- ── updated_at auto-trigger ───────────────────────────────────

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_branches_updated_at
    BEFORE UPDATE ON branches
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();

-- ── Seed: default admin ────────────────────────────────────────
-- Password hash is a placeholder — replace before deploying.
-- Generate with: python -c "from argon2 import PasswordHasher; print(PasswordHasher().hash('ChangeMe!1'))"

INSERT INTO branches (id, name, timezone)
VALUES ('00000000-0000-0000-0000-000000000001', 'HQ Branch', 'Asia/Riyadh');

INSERT INTO users (email, password_hash, role, full_name, assigned_branch_id)
VALUES (
    'admin@bookingapp.local',
    '$argon2id$v=19$m=65536,t=3,p=4$PLACEHOLDER_HASH',
    'ADMIN',
    'System Admin',
    '00000000-0000-0000-0000-000000000001'
);
