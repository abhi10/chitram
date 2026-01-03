"""Authentication API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.schemas.auth import AuthResponse, Token, UserLogin, UserRegister, UserResponse
from app.schemas.error import ErrorDetail
from app.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token", auto_error=False)


def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency to get auth service."""
    return AuthService(db)


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User | None:
    """Get current user from JWT token. Returns None if not authenticated."""
    if token is None:
        return None
    user_id = auth_service.verify_token(token)
    if user_id is None:
        return None
    user = await auth_service.get_user_by_id(user_id)
    if user is None or not user.is_active:
        return None
    return user


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
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register a new user account."""
    existing = await auth_service.get_user_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="EMAIL_EXISTS",
                message="Email already registered",
            ).model_dump(),
        )

    user = await auth_service.create_user(data.email, data.password)
    access_token = auth_service.create_access_token(user.id)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: UserLogin,
    auth_service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Login with email and password."""
    user = await auth_service.authenticate_user(data.email, data.password)
    if user is None:
        # Generic error to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password",
            ).model_dump(),
        )

    access_token = auth_service.create_access_token(user.id)

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
    )


@router.post("/token", response_model=Token)
async def login_for_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
) -> Token:
    """OAuth2 compatible token endpoint for Swagger UI."""
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorDetail(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password",
            ).model_dump(),
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth_service.create_access_token(user.id)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(require_current_user),
) -> UserResponse:
    """Get current authenticated user profile."""
    return UserResponse.model_validate(user)
