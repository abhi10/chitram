"""Local authentication provider using bcrypt + JWT.

This provider implements the existing authentication logic from
auth_service.py, wrapped in the AuthProvider interface.
"""

from datetime import UTC, datetime, timedelta

import bcrypt as bcrypt_lib
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.models.user import User
from app.services.auth.base import (
    AuthError,
    AuthErrorCode,
    AuthProvider,
    TokenPair,
    UserInfo,
)

# bcrypt work factor 12 (takes ~200-400ms to hash)
BCRYPT_WORK_FACTOR = 12


class LocalAuthProvider(AuthProvider):
    """Local authentication using bcrypt password hashing and JWT tokens.

    This is the default provider that stores users in our PostgreSQL database.
    Passwords are hashed with bcrypt (work factor 12) and tokens are JWTs.
    """

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
    ):
        self._db = db
        self._settings = settings

    @property
    def provider_name(self) -> str:
        return "local"

    # --- Password Hashing (internal) ---

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt with work factor 12."""
        salt = bcrypt_lib.gensalt(rounds=BCRYPT_WORK_FACTOR)
        hashed = bcrypt_lib.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash using timing-safe comparison."""
        try:
            return bcrypt_lib.checkpw(
                plain_password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    # --- JWT Token Management (internal) ---

    def _create_access_token(self, user_id: str) -> str:
        """Create JWT access token with user_id as subject."""
        expire = datetime.now(UTC) + timedelta(minutes=self._settings.jwt_expire_minutes)
        payload = {
            "sub": user_id,
            "exp": expire,
            "iat": datetime.now(UTC),
            "provider": "local",
        }
        return jwt.encode(
            payload,
            self._settings.jwt_secret_key,
            algorithm=self._settings.jwt_algorithm,
        )

    def _decode_token(self, token: str) -> dict | None:
        """Decode and verify JWT token. Returns payload or None."""
        try:
            return jwt.decode(
                token,
                self._settings.jwt_secret_key,
                algorithms=[self._settings.jwt_algorithm],
            )
        except JWTError:
            return None

    # --- Database Operations (internal) ---

    async def _get_user_by_email(self, email: str) -> User | None:
        """Get user by email address."""
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID."""
        result = await self._db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    def _user_to_info(self, user: User) -> UserInfo:
        """Convert User model to UserInfo."""
        return UserInfo(
            local_user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            provider="local",
            external_id=None,
        )

    # --- AuthProvider Interface Implementation ---

    async def register(
        self,
        email: str,
        password: str,
    ) -> UserInfo | AuthError:
        """Register a new user with email and password."""
        # Check if email already exists
        existing = await self._get_user_by_email(email)
        if existing:
            return AuthError(
                code=AuthErrorCode.EMAIL_EXISTS,
                message="Email already registered",
            )

        # Create user with hashed password
        password_hash = self._hash_password(password)
        user = User(email=email, password_hash=password_hash)
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        return self._user_to_info(user)

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[UserInfo, TokenPair] | AuthError:
        """Authenticate user and return tokens."""
        user = await self._get_user_by_email(email)

        if user is None:
            # Run hash anyway to prevent timing attacks (user enumeration)
            self._hash_password(password)
            return AuthError(
                code=AuthErrorCode.INVALID_CREDENTIALS,
                message="Invalid email or password",
            )

        if not self._verify_password(password, user.password_hash):
            return AuthError(
                code=AuthErrorCode.INVALID_CREDENTIALS,
                message="Invalid email or password",
            )

        if not user.is_active:
            return AuthError(
                code=AuthErrorCode.USER_INACTIVE,
                message="User account is inactive",
            )

        access_token = self._create_access_token(user.id)
        token_pair = TokenPair(
            access_token=access_token,
            refresh_token=None,  # Local provider doesn't use refresh tokens
            expires_in=self._settings.jwt_expire_minutes * 60,
        )

        return (self._user_to_info(user), token_pair)

    async def verify_token(
        self,
        token: str,
    ) -> UserInfo | AuthError:
        """Verify access token and return user info."""
        payload = self._decode_token(token)
        if payload is None:
            return AuthError(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid or expired token",
            )

        user_id = payload.get("sub")
        if user_id is None:
            return AuthError(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Token missing user ID",
            )

        user = await self._get_user_by_id(user_id)
        if user is None:
            return AuthError(
                code=AuthErrorCode.USER_NOT_FOUND,
                message="User not found",
            )

        if not user.is_active:
            return AuthError(
                code=AuthErrorCode.USER_INACTIVE,
                message="User account is inactive",
            )

        return self._user_to_info(user)

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> TokenPair | AuthError:
        """Refresh tokens - not supported by local provider.

        Local provider uses long-lived JWTs (24h) without refresh tokens.
        Clients should re-authenticate when token expires.
        """
        return AuthError(
            code=AuthErrorCode.PROVIDER_ERROR,
            message="Token refresh not supported by local provider",
        )

    async def request_password_reset(
        self,
        email: str,
    ) -> bool:
        """Request password reset - not supported by local provider.

        Local provider doesn't have email sending capability.
        Returns True to not reveal if email exists.
        """
        # For security, always return True (don't reveal if email exists)
        # Log for debugging but don't send email
        return True
