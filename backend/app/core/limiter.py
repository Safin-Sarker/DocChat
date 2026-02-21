"""Rate limiter configuration using slowapi."""

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request
from jose import jwt, JWTError
from app.core.config import settings


def _get_user_id_from_jwt(request: Request) -> str:
    """
    Extract user_id from the Authorization header's JWT token.

    Falls back to IP address if the token is missing or invalid.
    This is used as the rate limit key for authenticated endpoints.
    """
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=["HS256"]
            )
            user_id = payload.get("sub")
            if user_id:
                return f"user:{user_id}"
        except JWTError:
            pass
    return get_remote_address(request)


def _get_ip_address(request: Request) -> str:
    """Rate limit key based on client IP address."""
    return get_remote_address(request)


limiter = Limiter(
    key_func=_get_user_id_from_jwt,
    default_limits=[],
    enabled=settings.RATE_LIMIT_ENABLED,
)
