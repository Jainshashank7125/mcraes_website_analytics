from fastapi import APIRouter, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from sqlalchemy.orm import Session
from app.core.database import get_supabase_client
from app.core.exceptions import AuthenticationException, ValidationException, handle_exception
from app.core.error_utils import handle_api_errors
from app.services.audit_logger import audit_logger
from app.db.models import AuditLogAction
from app.db.database import get_db
from supabase import Client
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Request/Response models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    user: dict
    expires_in: Optional[int] = None

class UserResponse(BaseModel):
    id: str
    email: str
    user_metadata: Optional[dict] = None

def get_auth_client() -> Client:
    """Get Supabase client for authentication"""
    return get_supabase_client()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    client: Client = Depends(get_auth_client)
) -> dict:
    """Dependency to get current authenticated user"""
    try:
        token = credentials.credentials
        # Verify token and get user
        user_response = client.auth.get_user(token)
        if not user_response.user:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="Invalid authentication token: user not found"
            )
        return {
            "id": user_response.user.id,
            "email": user_response.user.email,
            "user_metadata": user_response.user.user_metadata or {}
        }
    except AuthenticationException:
        raise
    except Exception as e:
        raise AuthenticationException(
            user_message="Your session has expired. Please sign in again.",
            technical_message=f"Authentication error: {str(e)}"
        )

@router.post("/auth/signup", response_model=AuthResponse)
@handle_api_errors(context="creating user account")
async def signup(
    request: SignUpRequest,
    http_request: Request,
    client: Client = Depends(get_auth_client),
    db: Session = Depends(get_db)
):
    """Sign up a new user"""
    try:
        sign_up_data = {
            "email": request.email,
            "password": request.password,
        }
        
        if request.full_name:
            sign_up_data["data"] = {"full_name": request.full_name}
        
        response = client.auth.sign_up(sign_up_data)
        
        if not response.user:
            raise ValidationException(
                user_message="Unable to create your account. Please try again.",
                technical_message="User creation failed: no user returned"
            )
        
        # Log user creation
        # For signup endpoint, user is creating themselves (self-registration)
        try:
            await audit_logger.log(
                action=AuditLogAction.USER_CREATED,
                user_id=response.user.id,
                user_email=response.user.email,
                status="success",
                details={"self_registration": True},
                request=http_request,
                db=db
            )
        except Exception as log_error:
            logger.warning(f"Failed to log user creation: {str(log_error)}")
        
        # Get session if available
        session = response.session
        if session:
            return {
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {}
                },
                "expires_in": session.expires_in
            }
        else:
            # Email confirmation required
            return {
                "access_token": "",
                "refresh_token": "",
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "user_metadata": response.user.user_metadata or {}
                },
                "expires_in": None
            }
    except ValidationException:
        raise
    except Exception as e:
        error_msg = str(e).lower()
        if "already registered" in error_msg or "email exists" in error_msg or "already exists" in error_msg:
            raise ValidationException(
                user_message="An account with this email already exists. Please sign in instead.",
                technical_message=f"Signup error: {str(e)}"
            )
        raise handle_exception(e, context="creating user account")

@router.post("/auth/signin", response_model=AuthResponse)
@handle_api_errors(context="signing in")
async def signin(
    request: SignInRequest,
    http_request: Request,
    client: Client = Depends(get_auth_client),
    db: Session = Depends(get_db)
):
    """Sign in an existing user"""
    try:
        response = client.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })
        
        if not response.user or not response.session:
            # Log failed login attempt
            await audit_logger.log_login(
                user_id="",
                user_email=request.email,
                status="error",
                error_message="Invalid credentials",
                request=http_request,
                db=db
            )
            raise AuthenticationException(
                user_message="The email or password you entered is incorrect.",
                technical_message="Sign in failed: invalid credentials"
            )
        
        # Log successful login
        await audit_logger.log_login(
            user_id=response.user.id,
            user_email=response.user.email,
            status="success",
            request=http_request,
            db=db
        )
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata or {}
            },
            "expires_in": response.session.expires_in
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
        
        error_msg = str(e).lower()
        error_type = type(e).__name__
        
        # Check for email confirmation error
        if "email not confirmed" in error_msg or "email_not_confirmed" in error_msg or "not confirmed" in error_msg:
            raise AuthenticationException(
                user_message="Please check your email and confirm your account before signing in. If you didn't receive a confirmation email, please check your spam folder or request a new one.",
                technical_message=f"Email not confirmed: {str(e)}",
                details={"error_type": error_type, "context": "signing in", "requires_confirmation": True}
            )
        
        # Check for invalid credentials
        if "invalid" in error_msg or "credentials" in error_msg or "password" in error_msg or "wrong" in error_msg:
            raise AuthenticationException(
                user_message="The email or password you entered is incorrect.",
                technical_message=f"Sign in error: {str(e)}",
                details={"error_type": error_type, "context": "signing in"}
            )
        
        raise handle_exception(e, context="signing in")

@router.post("/auth/signout")
@handle_api_errors(context="signing out")
async def signout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    http_request: Request = None,
    current_user: dict = Depends(get_current_user),
    client: Client = Depends(get_auth_client),
    db: Session = Depends(get_db)
):
    """Sign out the current user"""
    try:
        token = credentials.credentials
        client.auth.sign_out(token)
        
        # Log logout
        await audit_logger.log_logout(
            user_id=current_user["id"],
            user_email=current_user["email"],
            request=http_request,
            db=db
        )
        
        return {"message": "Successfully signed out"}
    except Exception as e:
        logger.warning(f"Signout error (non-critical): {str(e)}")
        # Even if signout fails, return success (token will expire anyway)
        return {"message": "Signed out"}

@router.get("/auth/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information"""
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        user_metadata=current_user.get("user_metadata")
    )

@router.post("/auth/refresh")
@handle_api_errors(context="refreshing authentication token")
async def refresh_token(
    refresh_token: str = Header(..., alias="refresh-token"),
    client: Client = Depends(get_auth_client)
):
    """Refresh access token using refresh token"""
    try:
        response = client.auth.refresh_session(refresh_token)
        
        if not response.user or not response.session:
            raise AuthenticationException(
                user_message="Your session has expired. Please sign in again.",
                technical_message="Invalid refresh token"
            )
        
        return {
            "access_token": response.session.access_token,
            "refresh_token": response.session.refresh_token,
            "user": {
                "id": response.user.id,
                "email": response.user.email,
                "user_metadata": response.user.user_metadata or {}
            },
            "expires_in": response.session.expires_in
        }
    except AuthenticationException:
        raise
    except Exception as e:
        raise AuthenticationException(
            user_message="Your session has expired. Please sign in again.",
            technical_message=f"Token refresh error: {str(e)}"
        )

