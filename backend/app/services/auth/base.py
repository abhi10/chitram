"""Base authentication provider interface and types.

This module defines the AuthProvider abstract base class that all
authentication providers must implement. Follows the Strategy pattern
used by StorageBackend in this codebase.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class AuthErrorCode(str, Enum):
    """Machine-readable error codes for auth operations."""

    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    EMAIL_EXISTS = "EMAIL_EXISTS"
    USER_NOT_FOUND = "USER_NOT_FOUND"
    USER_INACTIVE = "USER_INACTIVE"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    PROVIDER_ERROR = "PROVIDER_ERROR"
    WEAK_PASSWORD = "WEAK_PASSWORD"
    INVALID_EMAIL = "INVALID_EMAIL"


@dataclass(frozen=True)
class AuthError:
    """Domain error for authentication failures.

    Immutable dataclass to ensure error details can't be accidentally modified.
    """

    code: AuthErrorCode
    message: str

    def to_dict(self) -> dict:
        """Convert to dictionary for HTTP responses."""
        return {"code": self.code.value, "message": self.message}


@dataclass(frozen=True)
class UserInfo:
    """User information returned by auth providers.

    Provider-agnostic user representation. The local_user_id is the
    ID in our local database (used for FKs to images table).
    """

    local_user_id: str  # Our DB user.id - used for image FKs
    email: str
    is_active: bool
    provider: str  # "local" or "supabase"
    external_id: str | None = None  # Supabase user ID, if applicable


@dataclass(frozen=True)
class TokenPair:
    """Access and refresh tokens."""

    access_token: str
    refresh_token: str | None = None
    expires_in: int | None = None  # Seconds until access_token expires


class AuthProvider(ABC):
    """Abstract base class for authentication providers.

    All auth providers must implement these methods. The interface is
    designed to be minimal - only 5 core operations needed.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider identifier (e.g., 'local', 'supabase')."""
        ...

    @abstractmethod
    async def register(
        self,
        email: str,
        password: str,
    ) -> UserInfo | AuthError:
        """Register a new user.

        Returns UserInfo on success, AuthError on failure.
        Provider is responsible for:
        - Validating email format
        - Checking password strength
        - Creating user in their system
        - Syncing to local DB if external provider
        """
        ...

    @abstractmethod
    async def login(
        self,
        email: str,
        password: str,
    ) -> tuple[UserInfo, TokenPair] | AuthError:
        """Authenticate user and return tokens.

        Returns (UserInfo, TokenPair) on success, AuthError on failure.
        Provider handles:
        - Credential verification
        - Token generation
        - Local DB sync for external providers
        """
        ...

    @abstractmethod
    async def verify_token(
        self,
        token: str,
    ) -> UserInfo | AuthError:
        """Verify access token and return user info.

        Returns UserInfo if token is valid, AuthError otherwise.
        Used by get_current_user dependency.
        """
        ...

    @abstractmethod
    async def refresh_token(
        self,
        refresh_token: str,
    ) -> TokenPair | AuthError:
        """Refresh access token using refresh token.

        Returns new TokenPair on success, AuthError on failure.
        LocalAuthProvider may return AuthError with NOT_SUPPORTED
        if refresh tokens aren't implemented.
        """
        ...

    @abstractmethod
    async def request_password_reset(
        self,
        email: str,
    ) -> bool:
        """Request password reset email.

        Returns True if request was processed (doesn't reveal if email exists).
        For security, always returns True even if email not found.
        """
        ...
