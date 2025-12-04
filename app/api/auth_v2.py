"""
V2 Authentication API endpoints using local PostgreSQL and JWT tokens
"""
from fastapi import APIRouter, Depends, Header, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.exceptions import AuthenticationException, ValidationException, handle_exception
from app.core.error_utils import handle_api_errors
from app.core.jwt_utils import create_access_token, verify_token, verify_refresh_token_hash, hash_refresh_token
from app.services.user_service import (
    create_user,
    authenticate_user,
    get_user_by_id,
    create_refresh_token_record,
    get_refresh_token_by_hash,
    increment_refresh_token_usage,
    revoke_all_user_refresh_tokens,
    cleanup_expired_refresh_tokens
)
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Request/Response models
class SignUpRequestV2(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class SignInRequestV2(BaseModel):
    email: EmailStr
    password: str

class AuthResponseV2(BaseModel):
    access_token: str
    refresh_token: str
    user: dict
    expires_in: int  # Seconds until access token expires

class SignUpResponseV2(BaseModel):
    success: bool
    message: str
    user_id: Optional[int] = None
    email: Optional[str] = None

class RefreshRequestV2(BaseModel):
    refresh_token: Optional[str] = None  # Can be in body or header

class UserResponseV2(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None
    created_at: str


async def get_current_user_v2(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get current authenticated user from JWT token (v2)
    
    Args:
        credentials: HTTP Bearer token credentials
        db: Database session
        
    Returns:
        User dictionary with id, email, full_name
        
    Raises:
        AuthenticationException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        
        # Verify JWT token
        payload = verify_token(token)
        
        # Extract user info from token
        user_id = int(payload.get("sub"))
        email = payload.get("email")
        
        # Optionally verify user still exists in database
        user = get_user_by_id(user_id, db)
        if not user:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message=f"User {user_id} not found in database"
            )
        
        return {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name
        }
    except AuthenticationException:
        raise
    except Exception as e:
        logger.error(f"Error verifying v2 JWT token: {str(e)}")
        raise AuthenticationException(
            user_message="Your session has expired. Please sign in again.",
            technical_message=f"JWT verification error: {str(e)}"
        )


@router.post("/auth/v2/signup", response_model=SignUpResponseV2)
@handle_api_errors(context="creating user account (v2)")
async def signup_v2(
    request: SignUpRequestV2,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Sign up a new user (v2 - local PostgreSQL only)
    
    NOTE: This endpoint ONLY uses local PostgreSQL database.
    No Supabase validation or checks are performed.
    
    Returns a simple success response - does NOT return tokens.
    User must sign in separately after account creation.
    """
    try:
        # Validate password (basic validation)
        if len(request.password) < 8:
            raise ValidationException(
                user_message="Password must be at least 8 characters long.",
                technical_message="Password validation failed: too short"
            )
        
        # Create user in local PostgreSQL database only
        # No Supabase check is performed
        try:
            user = create_user(
                email=request.email,
                password=request.password,
                full_name=request.full_name,
                db=db
            )
        except ValueError as e:
            # User already exists in local database
            raise ValidationException(
                user_message="An account with this email already exists. Please sign in instead.",
                technical_message=f"User creation failed in local database: {str(e)}"
            )
        
        # Log user creation
        try:
            await audit_logger.log(
                action=AuditLogAction.USER_CREATED,
                user_id=str(user.id),
                user_email=user.email,
                status="success",
                details={"self_registration": True, "auth_version": "v2"},
                request=http_request,
                db=db
            )
        except Exception as log_error:
            logger.warning(f"Failed to log user creation: {str(log_error)}")
        
        # Return simple success response - NO tokens
        return {
            "success": True,
            "message": "Account created successfully. Please sign in to continue.",
            "user_id": user.id,
            "email": user.email
        }
    except ValidationException:
        raise
    except Exception as e:
        raise handle_exception(e, context="creating user account (v2)")


@router.post("/auth/v2/signin", response_model=AuthResponseV2)
@handle_api_errors(context="signing in (v2)")
async def signin_v2(
    request: SignInRequestV2,
    http_request: Request,
    db: Session = Depends(get_db)
):
    """
    Sign in an existing user (v2 - local PostgreSQL only)
    
    NOTE: This endpoint ONLY uses local PostgreSQL database.
    No Supabase validation or checks are performed.
    """
    try:
        # Authenticate user against local PostgreSQL database only
        # No Supabase check is performed
        user = authenticate_user(request.email, request.password, db)
        
        if not user:
            # Log failed login attempt
            try:
                await audit_logger.log_login(
                    user_id="",
                    user_email=request.email,
                    status="error",
                    error_message="Invalid credentials",
                    request=http_request,
                    db=db
                )
            except:
                pass
            
            raise AuthenticationException(
                user_message="The email or password you entered is incorrect.",
                technical_message="Authentication failed: invalid credentials"
            )
        
        # Generate access token (3 hours)
        access_token = create_access_token(user_id=user.id, email=user.email)
        
        # Generate refresh token (15 hours, max 4 uses)
        refresh_token_record, plain_refresh_token = create_refresh_token_record(user.id, db)
        
        # Log successful login
        try:
            await audit_logger.log_login(
                user_id=str(user.id),
                user_email=user.email,
                status="success",
                request=http_request,
                db=db
            )
        except Exception as log_error:
            logger.warning(f"Failed to log login: {str(log_error)}")
        
        # Calculate expires_in (3 hours in seconds)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600
        
        return {
            "access_token": access_token,
            "refresh_token": plain_refresh_token,
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            },
            "expires_in": expires_in
        }
    except AuthenticationException:
        raise
    except Exception as e:
        # Log failed login attempt
        try:
            await audit_logger.log_login(
                user_id="",
                user_email=request.email,
                status="error",
                error_message=str(e),
                request=http_request,
                db=db
            )
        except:
            pass
        
        raise handle_exception(e, context="signing in (v2)")


@router.post("/auth/v2/refresh", response_model=AuthResponseV2)
@handle_api_errors(context="refreshing authentication token (v2)")
async def refresh_token_v2(
    refresh_token: Optional[str] = Header(None, alias="refresh-token"),
    refresh_token_body: Optional[RefreshRequestV2] = None,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token (v2)"""
    try:
        # Get refresh token from header or body
        token = refresh_token
        if not token and refresh_token_body:
            token = refresh_token_body.refresh_token
        
        if not token:
            raise AuthenticationException(
                user_message="Refresh token is required.",
                technical_message="No refresh token provided"
            )
        
        # Hash the provided token to look it up
        token_hash = hash_refresh_token(token)
        
        # Get refresh token record
        refresh_token_record = get_refresh_token_by_hash(token_hash, db)
        
        if not refresh_token_record:
            raise AuthenticationException(
                user_message="Invalid refresh token. Please sign in again.",
                technical_message="Refresh token not found"
            )
        
        # Check if expired
        from datetime import datetime, timezone
        if refresh_token_record.expires_at < datetime.now(timezone.utc):
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="Refresh token has expired"
            )
        
        # Check if usage limit reached
        if refresh_token_record.usage_count >= refresh_token_record.max_usage:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="Refresh token usage limit exceeded"
            )
        
        # Increment usage count
        success = increment_refresh_token_usage(refresh_token_record.id, db)
        if not success:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="Failed to increment refresh token usage"
            )
        
        # Get user
        user = get_user_by_id(refresh_token_record.user_id, db)
        if not user:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="User not found"
            )
        
        # Generate new access token (3 hours)
        access_token = create_access_token(user_id=user.id, email=user.email)
        
        # If usage limit is reached after increment, we could optionally rotate the refresh token
        # For now, we'll just return the same refresh token until it's exhausted
        # The client should request a new refresh token when this one is exhausted
        
        # Calculate expires_in (3 hours in seconds)
        expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS * 3600
        
        return {
            "access_token": access_token,
            "refresh_token": token,  # Return same refresh token (client should use it until exhausted)
            "user": {
                "id": user.id,
                "email": user.email,
                "full_name": user.full_name
            },
            "expires_in": expires_in
        }
    except AuthenticationException:
        raise
    except Exception as e:
        raise handle_exception(e, context="refreshing authentication token (v2)")


@router.post("/auth/v2/signout")
@handle_api_errors(context="signing out (v2)")
async def signout_v2(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    http_request: Request = None,
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Sign out the current user (v2)"""
    try:
        # Revoke all refresh tokens for this user
        count = revoke_all_user_refresh_tokens(current_user["id"], db)
        
        # Log logout
        try:
            await audit_logger.log_logout(
                user_id=str(current_user["id"]),
                user_email=current_user["email"],
                request=http_request,
                db=db
            )
        except Exception as log_error:
            logger.warning(f"Failed to log logout: {str(log_error)}")
        
        return {
            "message": "Successfully signed out",
            "tokens_revoked": count
        }
    except Exception as e:
        logger.warning(f"Signout error (non-critical): {str(e)}")
        # Even if signout fails, return success (token will expire anyway)
        return {"message": "Signed out"}


@router.get("/auth/v2/me", response_model=UserResponseV2)
@handle_api_errors(context="getting current user info (v2)")
async def get_current_user_info_v2(
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """Get current authenticated user information (v2)"""
    try:
        # Get fresh user data from database
        user = get_user_by_id(current_user["id"], db)
        if not user:
            raise AuthenticationException(
                user_message="User not found.",
                technical_message=f"User {current_user['id']} not found in database"
            )
        
        return UserResponseV2(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            created_at=user.created_at.isoformat() if user.created_at else ""
        )
    except AuthenticationException:
        raise
    except Exception as e:
        raise handle_exception(e, context="getting current user info (v2)")


@router.post("/auth/v2/cleanup-expired-tokens")
@handle_api_errors(context="cleaning up expired refresh tokens (v2)")
async def cleanup_expired_tokens_v2(
    current_user: dict = Depends(get_current_user_v2),
    db: Session = Depends(get_db)
):
    """
    Cleanup expired refresh tokens (admin/maintenance endpoint)
    This can be called manually or by a scheduled task
    """
    try:
        count = cleanup_expired_refresh_tokens(db)
        return {
            "message": f"Cleaned up {count} expired refresh tokens",
            "tokens_deleted": count
        }
    except Exception as e:
        raise handle_exception(e, context="cleaning up expired refresh tokens (v2)")

