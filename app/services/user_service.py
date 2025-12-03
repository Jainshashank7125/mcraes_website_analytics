"""
User service for v2 authentication - handles user CRUD and refresh token management
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional
from datetime import datetime, timedelta, timezone
from app.db.models import User, RefreshToken
from app.core.password_utils import hash_password, verify_password
from app.core.jwt_utils import create_refresh_token, hash_refresh_token
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_user(email: str, password: str, full_name: Optional[str], db: Session) -> User:
    """
    Create a new user account in local PostgreSQL database (v2 auth)
    
    NOTE: This function ONLY uses local PostgreSQL. No Supabase validation is performed.
    
    Args:
        email: User email address
        password: Plain text password (will be hashed)
        full_name: Optional full name
        db: Database session
        
    Returns:
        Created User object
        
    Raises:
        ValueError: If user with email already exists in local database
    """
    # Check if user already exists in local PostgreSQL database only
    # No Supabase check is performed - this is v2 local auth
    existing_user = get_user_by_email(email, db)
    if existing_user:
        raise ValueError(f"User with email {email} already exists in local database")
    
    # Hash password
    password_hash = hash_password(password)
    
    # Create user
    user = User(
        email=email,
        password_hash=password_hash,
        full_name=full_name
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Created new user: {user.id} ({user.email})")
    return user


def get_user_by_email(email: str, db: Session) -> Optional[User]:
    """
    Get user by email address
    
    Args:
        email: User email address
        db: Database session
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(user_id: int, db: Session) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()


def authenticate_user(email: str, password: str, db: Session) -> Optional[User]:
    """
    Authenticate a user by email and password
    
    Args:
        email: User email address
        password: Plain text password
        db: Database session
        
    Returns:
        User object if authentication successful, None otherwise
    """
    user = get_user_by_email(email, db)
    if not user:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    return user


def create_refresh_token_record(user_id: int, db: Session) -> tuple[RefreshToken, str]:
    """
    Create a new refresh token for a user
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Tuple of (RefreshToken object, plain token string)
    """
    # Generate plain refresh token
    plain_token = create_refresh_token()
    
    # Hash token for storage
    token_hash = hash_refresh_token(plain_token)
    
    # Calculate expiration
    expires_at = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_REFRESH_TOKEN_EXPIRE_HOURS)
    
    # Create refresh token record
    refresh_token = RefreshToken(
        user_id=user_id,
        token=token_hash,
        usage_count=0,
        max_usage=settings.JWT_REFRESH_TOKEN_MAX_USAGE,
        expires_at=expires_at
    )
    
    db.add(refresh_token)
    db.commit()
    db.refresh(refresh_token)
    
    logger.info(f"Created refresh token for user {user_id} (expires at {expires_at})")
    return refresh_token, plain_token


def get_refresh_token_by_hash(token_hash: str, db: Session) -> Optional[RefreshToken]:
    """
    Get refresh token by its hash
    
    Args:
        token_hash: Hashed refresh token
        db: Database session
        
    Returns:
        RefreshToken object if found, None otherwise
    """
    return db.query(RefreshToken).filter(RefreshToken.token == token_hash).first()


def increment_refresh_token_usage(token_id: int, db: Session) -> bool:
    """
    Increment usage count for a refresh token
    
    Args:
        token_id: Refresh token ID
        db: Database session
        
    Returns:
        True if successful, False if token not found or usage limit exceeded
    """
    refresh_token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if not refresh_token:
        return False
    
    # Check if usage limit reached
    if refresh_token.usage_count >= refresh_token.max_usage:
        logger.warning(f"Refresh token {token_id} has reached usage limit")
        return False
    
    # Check if expired
    if refresh_token.expires_at < datetime.now(timezone.utc):
        logger.warning(f"Refresh token {token_id} has expired")
        return False
    
    # Increment usage count and update last_used_at
    refresh_token.usage_count += 1
    refresh_token.last_used_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(refresh_token)
    
    logger.info(f"Incremented usage count for refresh token {token_id} (now {refresh_token.usage_count}/{refresh_token.max_usage})")
    return True


def revoke_refresh_token(token_id: int, db: Session) -> bool:
    """
    Revoke a refresh token by deleting it
    
    Args:
        token_id: Refresh token ID
        db: Database session
        
    Returns:
        True if successful, False if token not found
    """
    refresh_token = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if not refresh_token:
        return False
    
    db.delete(refresh_token)
    db.commit()
    
    logger.info(f"Revoked refresh token {token_id}")
    return True


def revoke_all_user_refresh_tokens(user_id: int, db: Session) -> int:
    """
    Revoke all refresh tokens for a user
    
    Args:
        user_id: User ID
        db: Database session
        
    Returns:
        Number of tokens revoked
    """
    tokens = db.query(RefreshToken).filter(RefreshToken.user_id == user_id).all()
    count = len(tokens)
    
    for token in tokens:
        db.delete(token)
    
    db.commit()
    
    logger.info(f"Revoked {count} refresh tokens for user {user_id}")
    return count


def cleanup_expired_refresh_tokens(db: Session) -> int:
    """
    Delete all expired refresh tokens
    
    Args:
        db: Database session
        
    Returns:
        Number of tokens deleted
    """
    now = datetime.now(timezone.utc)
    expired_tokens = db.query(RefreshToken).filter(RefreshToken.expires_at < now).all()
    count = len(expired_tokens)
    
    for token in expired_tokens:
        db.delete(token)
    
    db.commit()
    
    if count > 0:
        logger.info(f"Cleaned up {count} expired refresh tokens")
    
    return count

