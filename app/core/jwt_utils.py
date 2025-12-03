"""
JWT utilities for v2 authentication system
"""
import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional
import secrets
import hashlib
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def create_access_token(user_id: int, email: str) -> str:
    """
    Create a JWT access token with 3-hour expiry
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        Encoded JWT token string
    """
    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in environment variables")
    
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "exp": expire,  # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
        "type": "access"  # Token type
    }
    
    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return token


def verify_token(token: str) -> Dict:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded token payload as dictionary
        
    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    if not settings.JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in environment variables")
    
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {str(e)}")
        raise


def create_refresh_token() -> str:
    """
    Generate a secure random refresh token
    
    Returns:
        Random token string (URL-safe, 32 bytes = 43 characters)
    """
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """
    Hash a refresh token using SHA-256 for storage
    
    Args:
        token: Plain refresh token
        
    Returns:
        SHA-256 hash of the token (hex digest)
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_refresh_token_hash(token: str, hashed: str) -> bool:
    """
    Verify a refresh token against its hash
    
    Args:
        token: Plain refresh token
        hashed: Stored hash of the token
        
    Returns:
        True if token matches hash, False otherwise
    """
    token_hash = hash_refresh_token(token)
    return secrets.compare_digest(token_hash, hashed)

