"""
Centralized exception handling with user-friendly error messages
"""
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import logging
import traceback

logger = logging.getLogger(__name__)


class BaseAPIException(HTTPException):
    """Base exception class for API errors"""
    
    def __init__(
        self,
        status_code: int,
        user_message: str,
        technical_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.user_message = user_message
        self.technical_message = technical_message
        self.error_code = error_code
        self.details = details or {}
        
        # Log technical details for debugging
        if technical_message:
            logger.error(
                f"API Error [{error_code or 'UNKNOWN'}]: {technical_message}\n"
                f"User Message: {user_message}\n"
                f"Details: {details}\n"
                f"Traceback: {traceback.format_exc()}"
            )
        
        super().__init__(
            status_code=status_code,
            detail={
                "message": user_message,
                "error_code": error_code,
                "details": details
            }
        )


class DatabaseException(BaseAPIException):
    """Database-related errors"""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message=user_message,
            technical_message=technical_message,
            error_code="DATABASE_ERROR",
            details=details
        )


class AuthenticationException(BaseAPIException):
    """Authentication-related errors"""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            user_message=user_message,
            technical_message=technical_message,
            error_code="AUTH_ERROR",
            details=details
        )


class ValidationException(BaseAPIException):
    """Validation errors"""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            user_message=user_message,
            technical_message=technical_message,
            error_code="VALIDATION_ERROR",
            details=details
        )


class NotFoundException(BaseAPIException):
    """Resource not found errors"""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            user_message=user_message,
            technical_message=technical_message,
            error_code="NOT_FOUND",
            details=details
        )


class ExternalServiceException(BaseAPIException):
    """External service API errors"""
    
    def __init__(self, service_name: str, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            user_message=user_message,
            technical_message=technical_message,
            error_code=f"{service_name.upper()}_ERROR",
            details=details
        )


class ConfigurationException(BaseAPIException):
    """Configuration errors"""
    
    def __init__(self, user_message: str, technical_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            user_message=user_message,
            technical_message=technical_message,
            error_code="CONFIG_ERROR",
            details=details
        )


# Error message mappings for common technical errors
ERROR_MAPPINGS = {
    # Database errors
    "connection": {
        "patterns": ["connection", "connect", "network", "timeout", "refused"],
        "user_message": "Unable to connect to the database. Please try again in a moment.",
        "error_code": "DATABASE_CONNECTION_ERROR"
    },
    "query": {
        "patterns": ["query", "sql", "syntax", "invalid"],
        "user_message": "There was an issue retrieving data. Please try again.",
        "error_code": "DATABASE_QUERY_ERROR"
    },
    "constraint": {
        "patterns": ["constraint", "unique", "duplicate", "violation"],
        "user_message": "This record already exists. Please check your input.",
        "error_code": "DATABASE_CONSTRAINT_ERROR"
    },
    "not_found": {
        "patterns": ["not found", "does not exist", "no such"],
        "user_message": "The requested item could not be found.",
        "error_code": "RESOURCE_NOT_FOUND"
    },
    
    # Authentication errors
    "auth_invalid": {
        "patterns": ["invalid", "unauthorized", "authentication", "token"],
        "user_message": "Your session has expired. Please sign in again.",
        "error_code": "AUTH_INVALID"
    },
    "auth_expired": {
        "patterns": ["expired", "expiration"],
        "user_message": "Your session has expired. Please sign in again.",
        "error_code": "AUTH_EXPIRED"
    },
    "auth_credentials": {
        "patterns": ["password", "credentials", "wrong", "incorrect"],
        "user_message": "The email or password you entered is incorrect.",
        "error_code": "AUTH_CREDENTIALS_ERROR"
    },
    "auth_email_exists": {
        "patterns": ["already registered", "email exists", "already exists"],
        "user_message": "An account with this email already exists.",
        "error_code": "AUTH_EMAIL_EXISTS"
    },
    
    # External service errors
    "ga4_error": {
        "patterns": ["ga4", "google analytics", "analytics"],
        "user_message": "Unable to fetch Google Analytics data. Please check your configuration.",
        "error_code": "GA4_ERROR"
    },
    "scrunch_error": {
        "patterns": ["scrunch", "api"],
        "user_message": "Unable to fetch data from Scrunch AI. Please try again later.",
        "error_code": "SCRUNCH_ERROR"
    },
    "agency_analytics_error": {
        "patterns": ["agency analytics", "agency"],
        "user_message": "Unable to fetch Agency Analytics data. Please check your configuration.",
        "error_code": "AGENCY_ANALYTICS_ERROR"
    },
    "supabase_error": {
        "patterns": ["supabase"],
        "user_message": "Unable to connect to the database service. Please try again.",
        "error_code": "SUPABASE_ERROR"
    },
    
    # Validation errors
    "validation": {
        "patterns": ["validation", "invalid", "required", "missing"],
        "user_message": "Please check your input and try again.",
        "error_code": "VALIDATION_ERROR"
    },
    "date_format": {
        "patterns": ["date", "format", "yyyy-mm-dd"],
        "user_message": "Please enter dates in the format YYYY-MM-DD (e.g., 2024-01-15).",
        "error_code": "DATE_FORMAT_ERROR"
    },
    
    # Generic errors
    "timeout": {
        "patterns": ["timeout", "timed out"],
        "user_message": "The request took too long to complete. Please try again.",
        "error_code": "TIMEOUT_ERROR"
    },
    "rate_limit": {
        "patterns": ["rate limit", "too many requests"],
        "user_message": "Too many requests. Please wait a moment and try again.",
        "error_code": "RATE_LIMIT_ERROR"
    },
    "permission": {
        "patterns": ["permission", "forbidden", "access denied"],
        "user_message": "You don't have permission to perform this action.",
        "error_code": "PERMISSION_ERROR"
    }
}


def get_user_friendly_message(error: Exception, context: Optional[str] = None) -> tuple[str, str]:
    """
    Convert technical error messages to user-friendly messages.
    
    Returns:
        tuple[str, str]: (user_message, error_code)
    """
    error_str = str(error).lower()
    error_type = type(error).__name__.lower()
    
    # Check for specific error patterns
    for error_key, error_info in ERROR_MAPPINGS.items():
        for pattern in error_info["patterns"]:
            if pattern in error_str or pattern in error_type:
                return error_info["user_message"], error_info["error_code"]
    
    # Context-specific messages
    if context:
        context_lower = context.lower()
        if "brand" in context_lower:
            if "not found" in error_str:
                return "The brand you're looking for doesn't exist.", "BRAND_NOT_FOUND"
            if "fetch" in error_str or "load" in error_str:
                return "Unable to load brand information. Please try again.", "BRAND_LOAD_ERROR"
        
        if "sync" in context_lower:
            if "connection" in error_str:
                return "Unable to sync data. Please check your internet connection and try again.", "SYNC_CONNECTION_ERROR"
            return "Unable to sync data. Please try again in a moment.", "SYNC_ERROR"
        
        if "analytics" in context_lower:
            return "Unable to load analytics data. Please try again.", "ANALYTICS_LOAD_ERROR"
    
    # Default fallback message
    return (
        "Something went wrong. Our team has been notified. Please try again in a moment.",
        "UNKNOWN_ERROR"
    )


def handle_exception(error: Exception, context: Optional[str] = None) -> BaseAPIException:
    """
    Handle exceptions and convert them to user-friendly API exceptions.
    
    Args:
        error: The exception that occurred
        context: Optional context about where the error occurred (e.g., "fetching brands", "syncing data")
    
    Returns:
        BaseAPIException: A user-friendly exception
    """
    user_message, error_code = get_user_friendly_message(error, context)
    technical_message = str(error)
    
    # Determine exception type based on error
    error_str = str(error).lower()
    error_type = type(error).__name__
    
    # Database errors
    if any(pattern in error_str for pattern in ["connection", "database", "postgres", "supabase", "query", "sql"]):
        return DatabaseException(
            user_message=user_message,
            technical_message=technical_message,
            details={"error_type": error_type, "context": context}
        )
    
    # Authentication errors
    if any(pattern in error_str for pattern in ["auth", "token", "unauthorized", "credential", "password"]):
        return AuthenticationException(
            user_message=user_message,
            technical_message=technical_message,
            details={"error_type": error_type, "context": context}
        )
    
    # Validation errors
    if any(pattern in error_str for pattern in ["validation", "invalid", "required", "missing", "format"]):
        return ValidationException(
            user_message=user_message,
            technical_message=technical_message,
            details={"error_type": error_type, "context": context}
        )
    
    # Not found errors
    if any(pattern in error_str for pattern in ["not found", "does not exist", "no such"]):
        return NotFoundException(
            user_message=user_message,
            technical_message=technical_message,
            details={"error_type": error_type, "context": context}
        )
    
    # External service errors
    if any(pattern in error_str for pattern in ["ga4", "google analytics", "scrunch", "agency analytics"]):
        service_name = "GA4" if "ga4" in error_str or "google analytics" in error_str else \
                      "Scrunch" if "scrunch" in error_str else \
                      "AgencyAnalytics" if "agency" in error_str else "ExternalService"
        return ExternalServiceException(
            service_name=service_name,
            user_message=user_message,
            technical_message=technical_message,
            details={"error_type": error_type, "context": context}
        )
    
    # Default to generic database error for unknown errors
    return DatabaseException(
        user_message=user_message,
        technical_message=technical_message,
        details={"error_type": error_type, "context": context}
    )

