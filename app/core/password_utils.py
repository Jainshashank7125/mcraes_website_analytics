"""
Password hashing and verification utilities for v2 authentication
"""
import bcrypt
import logging

logger = logging.getLogger(__name__)

# Bcrypt rounds (cost factor)
BCRYPT_ROUNDS = 12


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt directly (bypassing passlib for compatibility)
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    try:
        # Encode password to bytes
        password_bytes = password.encode('utf-8')
        
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
        password_hash = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return password_hash.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise ValueError(f"Failed to hash password: {str(e)}")


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify a password against its hash using bcrypt directly
    
    Args:
        password: Plain text password
        hashed: Hashed password from database
        
    Returns:
        True if password matches hash, False otherwise
    """
    try:
        # Encode to bytes
        password_bytes = password.encode('utf-8')
        hashed_bytes = hashed.encode('utf-8')
        
        # Verify password
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False

