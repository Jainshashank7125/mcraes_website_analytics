"""
FastAPI exception handlers for user-friendly error responses
"""
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import BaseAPIException, handle_exception
import logging

logger = logging.getLogger(__name__)


async def base_api_exception_handler(request: Request, exc: BaseAPIException):
    """Handle custom API exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.user_message,
                "error_code": exc.error_code,
                "details": exc.details
            }
        }
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle FastAPI validation errors"""
    errors = exc.errors()
    error_messages = []
    
    for error in errors:
        field = ".".join(str(loc) for loc in error.get("loc", []))
        error_type = error.get("type", "")
        error_msg = error.get("msg", "")
        
        # User-friendly validation messages
        if error_type == "missing":
            error_messages.append(f"{field}: This field is required.")
        elif error_type == "value_error":
            error_messages.append(f"{field}: Invalid value provided.")
        elif error_type == "type_error":
            error_messages.append(f"{field}: Invalid data type.")
        else:
            error_messages.append(f"{field}: {error_msg}")
    
    user_message = "Please check your input: " + "; ".join(error_messages[:3])
    if len(error_messages) > 3:
        user_message += f" (and {len(error_messages) - 3} more)"
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": user_message,
                "error_code": "VALIDATION_ERROR",
                "details": {
                    "validation_errors": errors
                }
            }
        }
    )


async def http_exception_handler(request: Request, exc):
    """Handle HTTP exceptions"""
    # If it's already a BaseAPIException, use its handler
    if isinstance(exc, BaseAPIException):
        return await base_api_exception_handler(request, exc)
    
    # Convert to user-friendly message
    user_message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    
    # Try to make it more user-friendly
    detail_lower = user_message.lower()
    if "not found" in detail_lower:
        user_message = "The requested resource could not be found."
    elif "unauthorized" in detail_lower or "forbidden" in detail_lower:
        user_message = "You don't have permission to access this resource."
    elif "internal server error" in detail_lower:
        user_message = "Something went wrong. Please try again in a moment."
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": user_message,
                "error_code": f"HTTP_{exc.status_code}",
                "details": {}
            }
        }
    )


async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions"""
    # Convert to user-friendly exception
    api_exception = handle_exception(exc, context=f"{request.method} {request.url.path}")
    
    return JSONResponse(
        status_code=api_exception.status_code,
        content={
            "error": {
                "message": api_exception.user_message,
                "error_code": api_exception.error_code,
                "details": api_exception.details
            }
        }
    )

