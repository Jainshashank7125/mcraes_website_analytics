"""
Admin-only user management endpoints (CRUD + password reset)
"""
from fastapi import APIRouter, Query, Depends, Request
from typing import Optional
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
import logging

from app.db.database import get_db
from app.core.admin_auth import require_admin
from app.core.error_utils import handle_api_errors
from app.core.exceptions import ValidationException, NotFoundException
from app.services import user_service
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction

logger = logging.getLogger(__name__)
router = APIRouter()


class UserAdminResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    role: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @classmethod
    def from_user(cls, user):
        return cls(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat() if user.created_at else None,
            updated_at=user.updated_at.isoformat() if user.updated_at else None
        )


class UserCreateRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: str = "user"


class UserUpdateRequest(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserRoleUpdateRequest(BaseModel):
    role: str


class UserStatusUpdateRequest(BaseModel):
    is_active: bool


class UserPasswordResetRequest(BaseModel):
    new_password: str


def _validate_password(password: str):
    if len(password) < 8:
        raise ValidationException(
            user_message="Password must be at least 8 characters long.",
            technical_message="Password validation failed: too short"
        )


@router.get("/data/users")
@handle_api_errors(context="fetching users")
async def get_users(
    page: Optional[int] = Query(1, description="Page number (1-indexed)"),
    page_size: Optional[int] = Query(25, description="Number of records per page"),
    search: Optional[str] = Query(None, description="Search by email or full name"),
    active: Optional[str] = Query("active", description="Filter by active status: 'active' (default), 'inactive', or 'all'"),
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List users with pagination, search, and active filter (admin only)"""
    result = user_service.list_users(page=page, page_size=page_size, search=search, active=active, db=db)
    result["items"] = [UserAdminResponse.from_user(u) for u in result["items"]]
    return result


@router.get("/data/users/{user_id}")
@handle_api_errors(context="fetching user")
async def get_user(
    user_id: int,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Get a single user by ID (admin only)"""
    user = user_service.get_user_by_id(user_id, db)
    if not user:
        raise NotFoundException(user_message="User not found.", technical_message=f"User {user_id} not found")
    return UserAdminResponse.from_user(user)


@router.post("/data/users")
@handle_api_errors(context="creating user")
async def create_user_admin(
    request: UserCreateRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)"""
    _validate_password(request.password)

    try:
        user = user_service.create_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name,
            db=db,
            role=request.role
        )
    except ValueError as e:
        raise ValidationException(user_message=str(e), technical_message=str(e))

    try:
        await audit_logger.log(
            action=AuditLogAction.USER_CREATED,
            user_id=str(user.id),
            user_email=user.email,
            status="success",
            details={"created_by": current_user.get("email"), "role": user.role, "self_registration": False},
            request=http_request,
            db=db
        )
    except Exception as log_error:
        logger.warning(f"Failed to log admin user creation: {str(log_error)}")

    return UserAdminResponse.from_user(user)


@router.patch("/data/users/{user_id}")
@handle_api_errors(context="updating user")
async def update_user_admin(
    user_id: int,
    request: UserUpdateRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user's full name and/or email (admin only)"""
    try:
        user = user_service.update_user(
            user_id=user_id,
            db=db,
            full_name=request.full_name,
            email=request.email
        )
    except ValueError as e:
        raise ValidationException(user_message=str(e), technical_message=str(e))

    if not user:
        raise NotFoundException(user_message="User not found.", technical_message=f"User {user_id} not found")

    try:
        await audit_logger.log(
            action=AuditLogAction.USER_UPDATED,
            user_id=str(user.id),
            user_email=user.email,
            status="success",
            details={"updated_by": current_user.get("email")},
            request=http_request,
            db=db
        )
    except Exception as log_error:
        logger.warning(f"Failed to log user update: {str(log_error)}")

    return UserAdminResponse.from_user(user)


@router.patch("/data/users/{user_id}/role")
@handle_api_errors(context="updating user role")
async def update_user_role(
    user_id: int,
    request: UserRoleUpdateRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Change a user's role (admin only). Cannot demote yourself if you're the last active admin."""
    target = user_service.get_user_by_id(user_id, db)
    if not target:
        raise NotFoundException(user_message="User not found.", technical_message=f"User {user_id} not found")

    if (
        request.role != "admin"
        and target.role == "admin"
        and target.id == current_user.get("id")
        and user_service.count_active_admins(db) <= 1
    ):
        raise ValidationException(
            user_message="You cannot remove your own admin role because you are the last active admin.",
            technical_message=f"Blocked self-demotion of last admin (user {user_id})"
        )

    try:
        user = user_service.set_user_role(user_id, request.role, db)
    except ValueError as e:
        raise ValidationException(user_message=str(e), technical_message=str(e))

    try:
        await audit_logger.log(
            action=AuditLogAction.USER_ROLE_CHANGED,
            user_id=str(user.id),
            user_email=user.email,
            status="success",
            details={"changed_by": current_user.get("email"), "new_role": user.role},
            request=http_request,
            db=db
        )
    except Exception as log_error:
        logger.warning(f"Failed to log user role change: {str(log_error)}")

    return UserAdminResponse.from_user(user)


@router.patch("/data/users/{user_id}/status")
@handle_api_errors(context="updating user status")
async def update_user_status(
    user_id: int,
    request: UserStatusUpdateRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate or deactivate a user (admin only, soft delete toggle)."""
    target = user_service.get_user_by_id(user_id, db)
    if not target:
        raise NotFoundException(user_message="User not found.", technical_message=f"User {user_id} not found")

    if not request.is_active:
        if target.id == current_user.get("id"):
            raise ValidationException(
                user_message="You cannot deactivate your own account.",
                technical_message=f"Blocked self-deactivation (user {user_id})"
            )
        if target.role == "admin" and user_service.count_active_admins(db) <= 1:
            raise ValidationException(
                user_message="You cannot deactivate the last remaining active admin.",
                technical_message=f"Blocked deactivation of last admin (user {user_id})"
            )

    user = user_service.set_user_active(user_id, request.is_active, db)

    try:
        await audit_logger.log(
            action=AuditLogAction.USER_REACTIVATED if request.is_active else AuditLogAction.USER_DEACTIVATED,
            user_id=str(user.id),
            user_email=user.email,
            status="success",
            details={"changed_by": current_user.get("email")},
            request=http_request,
            db=db
        )
    except Exception as log_error:
        logger.warning(f"Failed to log user status change: {str(log_error)}")

    return UserAdminResponse.from_user(user)


@router.post("/data/users/{user_id}/reset-password")
@handle_api_errors(context="resetting user password")
async def reset_user_password(
    user_id: int,
    request: UserPasswordResetRequest,
    http_request: Request,
    current_user: dict = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Admin-initiated password reset for a user. Revokes their active sessions."""
    _validate_password(request.new_password)

    user = user_service.admin_reset_password(user_id, request.new_password, db)
    if not user:
        raise NotFoundException(user_message="User not found.", technical_message=f"User {user_id} not found")

    try:
        await audit_logger.log(
            action=AuditLogAction.USER_PASSWORD_RESET_BY_ADMIN,
            user_id=str(user.id),
            user_email=user.email,
            status="success",
            details={"reset_by": current_user.get("email")},
            request=http_request,
            db=db
        )
    except Exception as log_error:
        logger.warning(f"Failed to log admin password reset: {str(log_error)}")

    return {"message": "Password reset successfully. The user has been signed out of all sessions."}
