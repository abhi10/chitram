"""Authentication API endpoints.

This module provides the auth API using the pluggable AuthProvider interface.
The actual provider (local, supabase, etc.) is determined by configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
)
from app.schemas.error import ErrorDetail
from app.services.auth import AuthError, AuthProvider, create_auth_provider

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_auth_provider(db: AsyncSession = Depends(get_db)) -> AuthProvider:
    """Dependency to get auth provider based on configuration."""
    settings = get_settings()
    return create_auth_provider(db=db, settings=settings)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    provider: AuthProvider = Depends(get_auth_provider),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """Get current user from JWT token. Returns None if not authenticated."""
    if token is None:
        return None

    result = await provider.verify_token(token)
    if isinstance(result, AuthError):
        return None

    # Get the actual User model from DB (for backward compatibility)
    from sqlalchemy import select

    stmt = select(User).where(User.id == result.local_user_id)
    db_result = await db.execute(stmt)
    return db_result.scalar_one_or_none()


async def require_current_user(
    user: User | None = Depends(get_current_user),
) -> User:
    """Require authenticated user. Raises 401 if not authenticated."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code="UNAUTHORIZED",
                message="Not authenticated",
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: UserRegister,
    provider: AuthProvider = Depends(get_auth_provider),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Register a new user account."""
    result = await provider.register(data.email, data.password)

    if isinstance(result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.to_dict(),
        )

    # Get token via login
    login_result = await provider.login(data.email, data.password)
    if isinstance(login_result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="REGISTRATION_ERROR",
                message="Registration succeeded but login failed",
            ).model_dump(),
        )

    user_info, token_pair = login_result

    # Get User model for response
    from sqlalchemy import select

    stmt = select(User).where(User.id == user_info.local_user_id)
    db_result = await db.execute(stmt)
    user = db_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="USER_NOT_FOUND",
                message="User created but not found in database",
            ).model_dump(),
        )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token_pair.access_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: UserLogin,
    provider: AuthProvider = Depends(get_auth_provider),
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    """Login with email and password."""
    result = await provider.login(data.email, data.password)

    if isinstance(result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.to_dict(),
        )

    user_info, token_pair = result

    # Get User model for response
    from sqlalchemy import select

    stmt = select(User).where(User.id == user_info.local_user_id)
    db_result = await db.execute(stmt)
    user = db_result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="USER_NOT_FOUND",
                message="Login succeeded but user not found in database",
            ).model_dump(),
        )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=token_pair.access_token,
    )


@router.post("/token", response_model=Token)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    provider: AuthProvider = Depends(get_auth_provider),
) -> Token:
    """OAuth2 compatible token endpoint for Swagger UI."""
    result = await provider.login(form_data.username, form_data.password)

    if isinstance(result, AuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=result.to_dict(),
            headers={"WWW-Authenticate": "Bearer"},
        )

    _, token_pair = result
    return Token(access_token=token_pair.access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_current_user),
) -> UserResponse:
    """Get current authenticated user profile."""
    return UserResponse.model_validate(user)


@router.post(
    "/password-reset",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_password_reset(
    data: PasswordResetRequest,
    provider: AuthProvider = Depends(get_auth_provider),
) -> PasswordResetResponse:
    """Request password reset email.

    Always returns success to prevent email enumeration.
    """
    await provider.request_password_reset(data.email)
    return PasswordResetResponse()
