"""
Admin-only route protection built on top of v2 authentication
"""
from fastapi import Depends
from app.api.auth_v2 import get_current_user_v2
from app.core.exceptions import AuthorizationException


async def require_admin(current_user: dict = Depends(get_current_user_v2)) -> dict:
    """
    Dependency that requires the current authenticated user to have the 'admin' role.

    Args:
        current_user: Resolved by get_current_user_v2 (already verifies JWT + active status)

    Returns:
        The current user dict (with 'role' included)

    Raises:
        AuthorizationException: If the user is not an admin
    """
    if current_user.get("role") != "admin":
        raise AuthorizationException(
            user_message="Admin access required.",
            technical_message=f"User {current_user.get('id')} with role '{current_user.get('role')}' attempted an admin-only action"
        )
    return current_user
