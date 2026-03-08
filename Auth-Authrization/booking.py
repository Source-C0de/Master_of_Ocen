"""
app/api/v1/endpoints/booking.py

Example protected routes that demonstrate the RBAC middleware.
These are NOT full implementations — they exist solely to show
how require_roles / require_same_branch / etc. are applied.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends

from app.middleware.rbac import (
    get_current_user,
    require_admin,
    require_manager,
    require_roles,
    require_same_branch,
    require_staff,
)
from app.models.user import User, UserRole
from app.schemas.auth import UserPublic

router = APIRouter(prefix="/booking", tags=["Booking (RBAC demo)"])


# ── Any authenticated user ────────────────────────────────────────────────────

@router.get("/appointments/my")
async def get_my_appointments(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Any logged-in user can fetch their own appointments."""
    return {"user_id": str(current_user.id), "appointments": []}


# ── Customer only ─────────────────────────────────────────────────────────────

@router.post("/appointments/book")
async def book_appointment(
    current_user: User = Depends(require_roles(UserRole.CUSTOMER)),
) -> dict:
    """Only CUSTOMER role can book an appointment."""
    return {"status": "booked", "customer_id": str(current_user.id)}


# ── Staff or above ────────────────────────────────────────────────────────────

@router.get("/queue/status")
async def get_queue_status(
    current_user: User = Depends(require_staff),
) -> dict:
    """STAFF / MANAGER / ADMIN can view the queue."""
    return {
        "branch_id": str(current_user.assigned_branch_id),
        "queue": [],
    }


# ── Branch-scoped: Staff acting on their own branch ───────────────────────────

@router.put("/branches/{branch_id}/queue/next")
async def advance_queue(
    branch_id: uuid.UUID,
    current_user: User = Depends(require_same_branch()),
) -> dict:
    """
    STAFF/MANAGER can advance the queue for their assigned branch.
    ADMIN bypasses the branch restriction.
    """
    return {"branch_id": str(branch_id), "advanced_by": str(current_user.id)}


# ── Manager or above ──────────────────────────────────────────────────────────

@router.get("/branches/{branch_id}/reports")
async def get_branch_reports(
    branch_id: uuid.UUID,
    current_user: User = Depends(require_manager),
) -> dict:
    """Only MANAGER / ADMIN can access branch reports."""
    return {"branch_id": str(branch_id), "report": {}}


@router.post("/branches/{branch_id}/staff")
async def assign_staff(
    branch_id: uuid.UUID,
    current_user: User = Depends(require_manager),
) -> dict:
    """MANAGER / ADMIN can assign staff to a branch."""
    return {"branch_id": str(branch_id), "assigned_by": str(current_user.id)}


# ── Admin only ────────────────────────────────────────────────────────────────

@router.get("/admin/users")
async def list_all_users(
    current_user: User = Depends(require_admin),
) -> dict:
    """ADMIN can list all users across all branches."""
    return {"admin": str(current_user.id), "users": []}


@router.delete("/admin/users/{user_id}")
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_admin),
) -> dict:
    """ADMIN only — delete a user account."""
    return {"deleted": str(user_id), "by": str(current_user.id)}
