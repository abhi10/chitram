"""Factory for creating auth providers based on configuration.

This module provides the create_auth_provider function that instantiates
the appropriate auth provider based on settings.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.services.auth.base import AuthProvider
from app.services.auth.local import LocalAuthProvider


def create_auth_provider(
    db: AsyncSession,
    settings: Settings,
) -> AuthProvider:
    """Create auth provider based on settings.

    Args:
        db: Database session for user operations
        settings: Application settings

    Returns:
        AuthProvider instance based on settings.auth_provider

    Raises:
        ValueError: If auth_provider setting is invalid
    """
    provider_type = getattr(settings, "auth_provider", "local")

    if provider_type == "local":
        return LocalAuthProvider(db=db, settings=settings)
    if provider_type == "supabase":
        # Import here to avoid circular imports and allow optional dependency
        from app.services.auth.supabase import SupabaseAuthProvider

        return SupabaseAuthProvider(db=db, settings=settings)
    raise ValueError(f"Unknown auth provider: {provider_type}")
