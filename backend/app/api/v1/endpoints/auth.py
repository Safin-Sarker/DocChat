"""Authentication endpoints."""

from urllib.parse import urlencode
import json
import base64
import httpx
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import RedirectResponse
from starlette.requests import Request
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    UserInfo,
    MessageResponse
)
from app.models.user import User
from app.core.security import create_access_token
from app.core.auth import get_current_user
from app.core.config import settings
from app.core.limiter import limiter, _get_ip_address

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
@limiter.limit(settings.RATE_LIMIT_REGISTER, key_func=_get_ip_address)
async def register(request: Request, reg_request: RegisterRequest):
    """Register a new user."""
    # Check if email already exists
    if User.exists(email=reg_request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    if User.exists(username=reg_request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    try:
        user = User.create(
            email=reg_request.email,
            username=reg_request.username,
            password=reg_request.password
        )
        token = create_access_token(user["user_id"])

        return AuthResponse(
            access_token=token,
            user=UserInfo(**user)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN, key_func=_get_ip_address)
async def login(request: Request, login_request: LoginRequest):
    """Login with email and password."""
    user = User.authenticate(login_request.email, login_request.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(user["user_id"])

    return AuthResponse(
        access_token=token,
        user=UserInfo(**user)
    )


@router.get("/me", response_model=UserInfo)
@limiter.limit(settings.RATE_LIMIT_AUTH_ME)
async def get_me(request: Request, current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserInfo(
        user_id=current_user["user_id"],
        email=current_user["email"],
        username=current_user["username"]
    )


@router.post("/logout", response_model=MessageResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH_LOGOUT)
async def logout(request: Request, current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint.
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint is for API completeness.
    """
    return MessageResponse(message="Successfully logged out")


def _encode_user_payload(user: dict) -> str:
    payload = {
        "user_id": user["user_id"],
        "email": user["email"],
        "username": user["username"],
    }
    raw = json.dumps(payload).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def _build_frontend_redirect(token: str, user: dict) -> str:
    user_payload = _encode_user_payload(user)
    return f"{settings.OAUTH_FRONTEND_URL.rstrip('/')}/login#oauth=success&token={token}&user={user_payload}"


@router.get("/oauth/{provider}/start")
@limiter.limit(settings.RATE_LIMIT_OAUTH, key_func=_get_ip_address)
async def oauth_start(
    request: Request,
    provider: str,
    next_path: str = Query("/app"),
):
    """Start OAuth login flow by redirecting to provider auth page."""
    provider = provider.lower()
    backend_base = settings.OAUTH_BACKEND_URL.rstrip("/")
    callback_uri = f"{backend_base}/api/v1/auth/oauth/{provider}/callback"

    if provider == "google":
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(status_code=500, detail="Google OAuth is not configured")
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": callback_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "online",
            "prompt": "select_account",
            "state": next_path,
        }
        url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
        return RedirectResponse(url=url)

    raise HTTPException(status_code=400, detail="Unsupported OAuth provider")


@router.get("/oauth/{provider}/callback")
@limiter.limit(settings.RATE_LIMIT_OAUTH, key_func=_get_ip_address)
async def oauth_callback(
    request: Request,
    provider: str,
    code: str = Query(...),
    state: str = Query("/app"),
):
    """Handle OAuth callback and issue app JWT."""
    provider = provider.lower()
    backend_base = settings.OAUTH_BACKEND_URL.rstrip("/")
    callback_uri = f"{backend_base}/api/v1/auth/oauth/{provider}/callback"

    try:
        if provider == "google":
            async with httpx.AsyncClient(timeout=20) as client:
                token_res = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "code": code,
                        "client_id": settings.GOOGLE_CLIENT_ID,
                        "client_secret": settings.GOOGLE_CLIENT_SECRET,
                        "redirect_uri": callback_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                token_res.raise_for_status()
                token_json = token_res.json()
                access_token = token_json.get("access_token")
                if not access_token:
                    raise HTTPException(status_code=400, detail="Google OAuth token missing")

                profile_res = await client.get(
                    "https://openidconnect.googleapis.com/v1/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
                profile_res.raise_for_status()
                profile = profile_res.json()

                provider_user_id = profile.get("sub")
                email = profile.get("email")
                display_name = profile.get("name") or profile.get("given_name") or "google_user"

        else:
            raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

        if not provider_user_id:
            raise HTTPException(status_code=400, detail="OAuth provider user ID missing")

        user = User.find_or_create_from_oauth(
            provider=provider,
            provider_user_id=str(provider_user_id),
            email=email,
            display_name=display_name,
        )
        token = create_access_token(user["user_id"])
        redirect_url = _build_frontend_redirect(token, user)
        if state and state.startswith("/"):
            redirect_url += f"&next={state}"
        return RedirectResponse(url=redirect_url)
    except HTTPException:
        raise
    except Exception as exc:
        error_msg = str(exc).replace(" ", "_")
        return RedirectResponse(
            url=f"{settings.OAUTH_FRONTEND_URL.rstrip('/')}/login#oauth=error&message={error_msg}"
        )
