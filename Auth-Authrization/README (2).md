# 🔐 Booking & Queue — Auth System

Production-ready Authentication & Authorization for a FastAPI + PostgreSQL appointment/queue platform.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser / App)                   │
│   Authorization: Bearer <access_token (15m JWT)>                │
│   Cookie: refresh_token=<refresh_token (7d JWT, HttpOnly)>      │
└────────────────┬────────────────────────────────────────────────┘
                 │  HTTPS
┌────────────────▼────────────────────────────────────────────────┐
│                         FastAPI App                             │
│                                                                  │
│  POST /api/v1/auth/login    ──► AuthService.login()            │
│  POST /api/v1/auth/refresh  ──► AuthService.refresh()          │
│  POST /api/v1/auth/logout   ──► AuthService.logout()           │
│  GET  /api/v1/auth/me       ──► get_current_user dep           │
│                                                                  │
│  Protected routes use Depends(require_roles(...))               │
└──────────┬──────────────────────┬───────────────────────────────┘
           │                      │
┌──────────▼──────┐    ┌──────────▼──────────────┐
│   PostgreSQL    │    │    Redis                │
│                 │    │                         │
│  users          │    │  bl:jti:<jti>  (15m)    │  ← blacklisted access JTIs
│  refresh_tokens │    │  rt:family:<id>         │  ← revoked token families
│  branches       │    │                         │
└─────────────────┘    └─────────────────────────┘
```

---

## Security Design Decisions

| Concern | Implementation |
|---|---|
| Password hashing | **Argon2id** — time=3, mem=64MB, para=4 |
| Anti-enumeration | Dummy hash is **always** run for unknown users — response time is identical |
| Timing attacks | `hmac.compare_digest` for all string comparisons |
| Token storage | Access token → `Authorization` header (memory only). Refresh → `HttpOnly; Secure; SameSite=Strict` cookie scoped to `/api/v1/auth` |
| Token rotation | Each refresh issues a new refresh token; old one is revoked. Reuse of a revoked token **revokes the entire family** |
| Revocation | Access tokens: Redis JTI blacklist (TTL = remaining token lifetime). Refresh tokens: DB `revoked_at` + Redis family revocation |
| Rate limiting | `slowapi` per-IP: 10 login attempts/min, 200 global req/min |
| Account lockout | 5 failed attempts → 15-minute lockout |
| Security headers | HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy |

---

## Database Schema

```
branches
  └── id (PK, UUID)
  └── name, address, timezone, is_active

users
  ├── id (PK, UUID)
  ├── email (unique, nullable)        ← E.164
  ├── phone (unique, nullable)        ← at least one required
  ├── password_hash (Argon2id)
  ├── role  ENUM(CUSTOMER|STAFF|MANAGER|ADMIN)
  ├── status ENUM(ACTIVE|INACTIVE|SUSPENDED|PENDING_VERIFICATION)
  ├── full_name
  ├── assigned_branch_id (FK → branches)   ← queue context
  ├── last_login_at, failed_login_count, locked_until
  └── created_at, updated_at

refresh_tokens
  ├── id (PK, UUID)
  ├── user_id (FK → users, CASCADE DELETE)
  ├── token_hash (SHA-256 of raw token)
  ├── family_id (UUID, chains rotation)
  ├── issued_at, expires_at, revoked_at, revoke_reason
  └── user_agent, ip_address
```

---

## Role Hierarchy

```
ADMIN   ──► Full access (bypasses branch restrictions)
  │
MANAGER ──► Branch reports, staff assignment, queue management
  │
STAFF   ──► Queue operations within assigned branch
  │
CUSTOMER──► Book/manage own appointments
```

---

## Quick Start

```bash
# 1. Copy env template
cp .env.example .env
# Edit .env — at minimum set JWT_SECRET_KEY

# 2. Start services
docker compose up --build

# 3. Schema is auto-applied via docker-entrypoint-initdb.d

# 4. Explore the API
open http://localhost:8000/docs
```

---

## API Reference

### POST `/api/v1/auth/login`
```json
// Request
{ "identifier": "user@example.com", "password": "SecurePass1!" }
// identifier accepts email OR E.164 phone e.g. "+966501234567"

// Response 200
{
  "access_token": "<JWT>",
  "token_type": "bearer",
  "expires_in": 900,
  "user": {
    "id": "...", "full_name": "...", "role": "STAFF",
    "assigned_branch_id": "...", "assigned_branch": { "name": "HQ", "timezone": "Asia/Riyadh" }
  }
}
// + Set-Cookie: refresh_token=<JWT>; HttpOnly; Secure; SameSite=Strict; Path=/api/v1/auth
```

### POST `/api/v1/auth/refresh`
```
Cookie: refresh_token=<old_refresh_JWT>
→ 200: new access_token + rotated refresh cookie
→ 401: token invalid/expired/reused
```

### POST `/api/v1/auth/logout`
```
Authorization: Bearer <access_token>
Cookie: refresh_token=<refresh_JWT>
→ 200: { "message": "Successfully logged out" }
   Clears cookie, blacklists access JTI, revokes refresh token in DB
```

---

## Using RBAC in Your Routes

```python
from app.middleware.rbac import require_roles, require_manager, require_staff
from app.models.user import UserRole

# Require specific role(s)
@router.get("/admin/dashboard")
async def admin_dashboard(user = Depends(require_roles(UserRole.ADMIN, UserRole.MANAGER))):
    ...

# Use pre-built guards
@router.get("/queue")
async def queue(user = Depends(require_staff)):       # STAFF | MANAGER | ADMIN
    ...

# Branch-scoped: staff can only act on their own branch
@router.put("/branches/{branch_id}/queue/next")
async def advance_queue(branch_id: uuid.UUID, user = Depends(require_same_branch())):
    ...
```

---

## JWT Claims Structure

**Access Token**
```json
{
  "sub": "<user_uuid>",
  "role": "STAFF",
  "type": "access",
  "branch_id": "<branch_uuid>",   // only for STAFF/MANAGER
  "iat": 1710000000,
  "exp": 1710000900,
  "jti": "<uuid>"
}
```

**Refresh Token**
```json
{
  "sub": "<user_uuid>",
  "type": "refresh",
  "family": "<family_uuid>",
  "iat": 1710000000,
  "exp": 1710604800,
  "jti": "<uuid>"
}
```

---

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```
