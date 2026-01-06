"""
Utility functions for error handling in endpoints
"""
from functools import wraps
from typing import Callable, Any
from fastapi import HTTPException
from app.core.exceptions import handle_exception, BaseAPIException
import logging

logger = logging.getLogger(__name__)


def handle_api_errors(context: str = None):
    """
    Decorator to handle exceptions in API endpoints and convert them to user-friendly errors.
    
    Usage:
        @handle_api_errors(context="fetching brands")
        async def get_brands():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except BaseAPIException:
                # Re-raise custom exceptions as-is
                raise
            except HTTPException:
                # Re-raise FastAPI HTTPException as-is (handled by FastAPI exception handlers)
                raise
            except Exception as e:
                # Convert other exceptions to user-friendly errors
                raise handle_exception(e, context=context or func.__name__)
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except BaseAPIException:
                # Re-raise custom exceptions as-is
                raise
            except HTTPException:
                # Re-raise FastAPI HTTPException as-is (handled by FastAPI exception handlers)
                raise
            except Exception as e:
                # Convert other exceptions to user-friendly errors
                raise handle_exception(e, context=context or func.__name__)
        
        # Return appropriate wrapper based on whether function is async
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator

