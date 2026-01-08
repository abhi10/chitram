"""Auth provider module for pluggable authentication."""

from app.services.auth.base import AuthError, AuthErrorCode, AuthProvider, TokenPair, UserInfo
from app.services.auth.factory import create_auth_provider
from app.services.auth.local import LocalAuthProvider

__all__ = [
    "AuthError",
    "AuthErrorCode",
    "AuthProvider",
    "LocalAuthProvider",
    "TokenPair",
    "UserInfo",
    "create_auth_provider",
]
