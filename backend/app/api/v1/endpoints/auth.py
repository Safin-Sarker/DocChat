"""Authentication endpoints."""

from fastapi import APIRouter, HTTPException, status, Depends
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

router = APIRouter()


@router.post("/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Register a new user."""
    # Check if email already exists
    if User.exists(email=request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    if User.exists(username=request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    try:
        user = User.create(
            email=request.email,
            username=request.username,
            password=request.password
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
async def login(request: LoginRequest):
    """Login with email and password."""
    user = User.authenticate(request.email, request.password)

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
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user information."""
    return UserInfo(
        user_id=current_user["user_id"],
        email=current_user["email"],
        username=current_user["username"]
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout endpoint.
    Note: JWT tokens are stateless, so logout is handled client-side
    by removing the token. This endpoint is for API completeness.
    """
    return MessageResponse(message="Successfully logged out")
