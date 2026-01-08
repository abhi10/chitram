"""Supabase authentication provider.

This provider integrates with Supabase Auth for user management while
syncing users to the local database for FK relationships with images.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import Client, create_client

from app.config import Settings
from app.models.user import User
from app.services.auth.base import (
    AuthError,
    AuthErrorCode,
    AuthProvider,
    TokenPair,
    UserInfo,
)

logger = logging.getLogger(__name__)


class SupabaseAuthProvider(AuthProvider):
    """Supabase authentication provider with local DB sync.

    Uses Supabase for auth operations (register, login, password reset)
    and syncs users to local DB on successful authentication.

    Sync-on-auth strategy:
    1. User authenticates with Supabase
    2. On success, find or create local user by supabase_id or email
    3. Return local user.id for FK relationships
    """

    def __init__(
        self,
        db: AsyncSession,
        settings: Settings,
    ):
        self._db = db
        self._settings = settings

        # Validate required settings
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL is required for Supabase auth provider")
        if not settings.supabase_anon_key:
            raise ValueError("SUPABASE_ANON_KEY is required for Supabase auth provider")

        # Initialize Supabase client (using defaults - no session persistence needed server-side)
        self._client: Client = create_client(
            settings.supabase_url,
            settings.supabase_anon_key,
        )

    @property
    def provider_name(self) -> str:
        return "supabase"

    # --- Local DB Sync Operations ---

    async def _find_or_create_local_user(
        self,
        supabase_id: str,
        email: str,
    ) -> User:
        """Find or create local user for Supabase user.

        Sync strategy:
        1. If supabase_id exists in local DB → return that user
        2. If email exists → link to Supabase (migration path)
        3. Otherwise → create new local user
        """
        # Try to find by supabase_id first (fastest path)
        result = await self._db.execute(select(User).where(User.supabase_id == supabase_id))
        user = result.scalar_one_or_none()
        if user:
            return user

        # Try to find by email (migration path: local user → Supabase)
        result = await self._db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user:
            # Link existing local user to Supabase
            user.supabase_id = supabase_id
            await self._db.commit()
            await self._db.refresh(user)
            logger.info(f"Linked existing user {user.id} to Supabase ID {supabase_id}")
            return user

        # Create new local user (no password_hash for Supabase users)
        user = User(
            email=email,
            password_hash=None,  # Supabase handles auth
            supabase_id=supabase_id,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        logger.info(f"Created new local user {user.id} for Supabase ID {supabase_id}")
        return user

    def _user_to_info(self, user: User) -> UserInfo:
        """Convert User model to UserInfo."""
        return UserInfo(
            local_user_id=user.id,
            email=user.email,
            is_active=user.is_active,
            provider="supabase",
            external_id=user.supabase_id,
        )

    # --- AuthProvider Interface Implementation ---

    async def register(
        self,
        email: str,
        password: str,
    ) -> UserInfo | AuthError:
        """Register a new user with Supabase."""
        try:
            response = self._client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )

            if response.user is None:
                return AuthError(
                    code=AuthErrorCode.PROVIDER_ERROR,
                    message="Registration failed - no user returned",
                )

            # Sync to local DB
            user = await self._find_or_create_local_user(
                supabase_id=response.user.id,
                email=email,
            )

            return self._user_to_info(user)

        except Exception as e:
            error_msg = str(e).lower()
            if "already registered" in error_msg or "already exists" in error_msg:
                return AuthError(
                    code=AuthErrorCode.EMAIL_EXISTS,
                    message="Email already registered",
                )
            logger.exception("Supabase registration error")
            return AuthError(
                code=AuthErrorCode.PROVIDER_ERROR,
                message=f"Registration failed: {e!s}",
            )

    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[UserInfo, TokenPair] | AuthError:
        """Authenticate user with Supabase."""
        try:
            response = self._client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            if response.user is None or response.session is None:
                return AuthError(
                    code=AuthErrorCode.INVALID_CREDENTIALS,
                    message="Invalid email or password",
                )

            # Sync to local DB
            user = await self._find_or_create_local_user(
                supabase_id=response.user.id,
                email=email,
            )

            if not user.is_active:
                return AuthError(
                    code=AuthErrorCode.USER_INACTIVE,
                    message="User account is inactive",
                )

            token_pair = TokenPair(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_in=response.session.expires_in,
            )

            return (self._user_to_info(user), token_pair)

        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "credentials" in error_msg:
                return AuthError(
                    code=AuthErrorCode.INVALID_CREDENTIALS,
                    message="Invalid email or password",
                )
            logger.exception("Supabase login error")
            return AuthError(
                code=AuthErrorCode.PROVIDER_ERROR,
                message=f"Login failed: {e!s}",
            )

    async def verify_token(
        self,
        token: str,
    ) -> UserInfo | AuthError:
        """Verify Supabase access token."""
        try:
            response = self._client.auth.get_user(token)

            if response.user is None:
                return AuthError(
                    code=AuthErrorCode.INVALID_TOKEN,
                    message="Invalid or expired token",
                )

            # Find local user by supabase_id
            result = await self._db.execute(
                select(User).where(User.supabase_id == response.user.id)
            )
            user = result.scalar_one_or_none()

            if user is None:
                # User exists in Supabase but not locally - create them
                user = await self._find_or_create_local_user(
                    supabase_id=response.user.id,
                    email=response.user.email or "",
                )

            if not user.is_active:
                return AuthError(
                    code=AuthErrorCode.USER_INACTIVE,
                    message="User account is inactive",
                )

            return self._user_to_info(user)

        except Exception as e:
            error_msg = str(e).lower()
            if "invalid" in error_msg or "expired" in error_msg:
                return AuthError(
                    code=AuthErrorCode.INVALID_TOKEN,
                    message="Invalid or expired token",
                )
            logger.exception("Supabase token verification error")
            return AuthError(
                code=AuthErrorCode.PROVIDER_ERROR,
                message=f"Token verification failed: {e!s}",
            )

    async def refresh_token(
        self,
        refresh_token: str,
    ) -> TokenPair | AuthError:
        """Refresh Supabase access token."""
        try:
            response = self._client.auth.refresh_session(refresh_token)

            if response.session is None:
                return AuthError(
                    code=AuthErrorCode.INVALID_TOKEN,
                    message="Invalid refresh token",
                )

            return TokenPair(
                access_token=response.session.access_token,
                refresh_token=response.session.refresh_token,
                expires_in=response.session.expires_in,
            )

        except Exception as e:
            logger.exception("Supabase token refresh error")
            return AuthError(
                code=AuthErrorCode.PROVIDER_ERROR,
                message=f"Token refresh failed: {e!s}",
            )

    async def request_password_reset(
        self,
        email: str,
    ) -> bool:
        """Request password reset email from Supabase."""
        try:
            self._client.auth.reset_password_email(email)
            return True
        except Exception as e:
            # Log but don't expose errors (security: don't reveal if email exists)
            logger.warning(f"Password reset request failed: {e}")
            return True  # Always return True to prevent email enumeration
