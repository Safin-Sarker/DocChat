"""Authentication dependencies for FastAPI."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .security import verify_token
from .config import settings
from app.models.user import User

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Dependency to get the current authenticated user.

    Raises HTTPException 401 if token is invalid or user not found.
    """
    token = credentials.credentials
    user_id = verify_token(token)

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = User.get_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def is_owner(user: dict) -> bool:
    """Check if the user is the application owner (exempt from usage limits)."""
    owner_email = settings.OWNER_EMAIL.strip().lower()
    return bool(owner_email and user.get("email", "").lower() == owner_email)


async def get_current_admin(
    current_user: dict = Depends(get_current_user),
) -> dict:
    """
    Dependency to get the current admin user.

    Raises HTTPException 403 if user is not an admin.
    """
    if not current_user.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> dict | None:
    """
    Optional authentication - returns None if no token provided.
    Useful for endpoints that work with or without authentication.
    """
    if credentials is None:
        return None

    token = credentials.credentials
    user_id = verify_token(token)

    if not user_id:
        return None

    return User.get_by_id(user_id)
