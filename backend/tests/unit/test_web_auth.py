"""Unit tests for web authentication (cookie-based auth).

Tests the get_current_user_from_cookie dependency which uses the pluggable
auth provider pattern for token verification.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.web import AUTH_COOKIE_NAME, get_current_user_from_cookie
from app.models.user import User
from app.services.auth.base import AuthError, AuthErrorCode, UserInfo


class TestGetCurrentUserFromCookie:
    """Tests for get_current_user_from_cookie dependency."""

    @pytest.mark.asyncio
    async def test_returns_none_when_no_cookie(self):
        """Should return None when no auth cookie is present."""
        request = MagicMock()
        request.cookies.get.return_value = None
        db = AsyncMock()

        result = await get_current_user_from_cookie(request, db)

        assert result is None
        request.cookies.get.assert_called_once_with(AUTH_COOKIE_NAME)

    @pytest.mark.asyncio
    async def test_returns_none_when_token_invalid(self):
        """Should return None when token verification fails."""
        request = MagicMock()
        request.cookies.get.return_value = "invalid.token.here"
        db = AsyncMock()

        with (
            patch("app.api.web.get_settings") as mock_get_settings,
            patch("app.api.web.create_auth_provider") as mock_create_provider,
        ):
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            mock_provider = AsyncMock()
            mock_provider.verify_token.return_value = AuthError(
                code=AuthErrorCode.INVALID_TOKEN,
                message="Invalid token",
            )
            mock_create_provider.return_value = mock_provider

            result = await get_current_user_from_cookie(request, db)

        assert result is None
        mock_provider.verify_token.assert_called_once_with("invalid.token.here")

    @pytest.mark.asyncio
    async def test_returns_none_when_user_not_found(self):
        """Should return None when user_id from token doesn't exist in DB."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.token"
        db = AsyncMock()

        # Mock the database query to return None (user not found)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        with (
            patch("app.api.web.get_settings") as mock_get_settings,
            patch("app.api.web.create_auth_provider") as mock_create_provider,
        ):
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            mock_provider = AsyncMock()
            mock_provider.verify_token.return_value = UserInfo(
                local_user_id="user-123",
                email="test@example.com",
                is_active=True,
                provider="local",
            )
            mock_create_provider.return_value = mock_provider

            result = await get_current_user_from_cookie(request, db)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_user_inactive(self):
        """Should return None when user is inactive."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.token"
        db = AsyncMock()

        # Create an inactive user
        inactive_user = MagicMock(spec=User)
        inactive_user.is_active = False

        # Mock the database query to return the inactive user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = inactive_user
        db.execute.return_value = mock_result

        with (
            patch("app.api.web.get_settings") as mock_get_settings,
            patch("app.api.web.create_auth_provider") as mock_create_provider,
        ):
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            mock_provider = AsyncMock()
            mock_provider.verify_token.return_value = UserInfo(
                local_user_id="user-123",
                email="test@example.com",
                is_active=True,  # Provider says active, but DB user is inactive
                provider="local",
            )
            mock_create_provider.return_value = mock_provider

            result = await get_current_user_from_cookie(request, db)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_when_valid_token_and_active_user(self):
        """Should return user when token is valid and user is active."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.jwt.token"
        db = AsyncMock()

        # Create an active user
        active_user = MagicMock(spec=User)
        active_user.is_active = True
        active_user.id = "user-123"
        active_user.email = "test@example.com"

        # Mock the database query to return the active user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_user
        db.execute.return_value = mock_result

        with (
            patch("app.api.web.get_settings") as mock_get_settings,
            patch("app.api.web.create_auth_provider") as mock_create_provider,
        ):
            mock_settings = MagicMock()
            mock_get_settings.return_value = mock_settings

            mock_provider = AsyncMock()
            mock_provider.verify_token.return_value = UserInfo(
                local_user_id="user-123",
                email="test@example.com",
                is_active=True,
                provider="local",
            )
            mock_create_provider.return_value = mock_provider

            result = await get_current_user_from_cookie(request, db)

        assert result is active_user
        assert result.id == "user-123"

    @pytest.mark.asyncio
    async def test_uses_correct_cookie_name(self):
        """Should use AUTH_COOKIE_NAME constant for cookie lookup."""
        assert AUTH_COOKIE_NAME == "chitram_auth"

        request = MagicMock()
        request.cookies.get.return_value = None
        db = AsyncMock()

        await get_current_user_from_cookie(request, db)

        request.cookies.get.assert_called_with("chitram_auth")

    @pytest.mark.asyncio
    async def test_works_with_supabase_provider(self):
        """Should work with Supabase provider tokens."""
        request = MagicMock()
        request.cookies.get.return_value = "supabase.jwt.token"
        db = AsyncMock()

        # Create an active user with supabase_id
        active_user = MagicMock(spec=User)
        active_user.is_active = True
        active_user.id = "local-user-123"
        active_user.email = "test@example.com"
        active_user.supabase_id = "supabase-user-456"

        # Mock the database query to return the active user
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = active_user
        db.execute.return_value = mock_result

        with (
            patch("app.api.web.get_settings") as mock_get_settings,
            patch("app.api.web.create_auth_provider") as mock_create_provider,
        ):
            mock_settings = MagicMock()
            mock_settings.auth_provider = "supabase"
            mock_get_settings.return_value = mock_settings

            mock_provider = AsyncMock()
            mock_provider.verify_token.return_value = UserInfo(
                local_user_id="local-user-123",
                email="test@example.com",
                is_active=True,
                provider="supabase",
                external_id="supabase-user-456",
            )
            mock_create_provider.return_value = mock_provider

            result = await get_current_user_from_cookie(request, db)

        assert result is active_user
        assert result.id == "local-user-123"
        mock_create_provider.assert_called_once_with(db=db, settings=mock_settings)
