"""Unit tests for web authentication (cookie-based auth)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.web import AUTH_COOKIE_NAME, get_current_user_from_cookie
from app.models.user import User


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

        with patch("app.api.web.AuthService") as mock_auth_service:
            mock_auth = mock_auth_service.return_value
            mock_auth.verify_token.return_value = None

            result = await get_current_user_from_cookie(request, db)

        assert result is None
        mock_auth.verify_token.assert_called_once_with("invalid.token.here")

    @pytest.mark.asyncio
    async def test_returns_none_when_user_not_found(self):
        """Should return None when user_id from token doesn't exist in DB."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.token"
        db = AsyncMock()

        with patch("app.api.web.AuthService") as mock_auth_service:
            mock_auth = mock_auth_service.return_value
            mock_auth.verify_token.return_value = "user-123"
            mock_auth.get_user_by_id = AsyncMock(return_value=None)

            result = await get_current_user_from_cookie(request, db)

        assert result is None
        mock_auth.get_user_by_id.assert_called_once_with("user-123")

    @pytest.mark.asyncio
    async def test_returns_none_when_user_inactive(self):
        """Should return None when user is inactive."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.token"
        db = AsyncMock()

        inactive_user = MagicMock(spec=User)
        inactive_user.is_active = False

        with patch("app.api.web.AuthService") as mock_auth_service:
            mock_auth = mock_auth_service.return_value
            mock_auth.verify_token.return_value = "user-123"
            mock_auth.get_user_by_id = AsyncMock(return_value=inactive_user)

            result = await get_current_user_from_cookie(request, db)

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_user_when_valid_token_and_active_user(self):
        """Should return user when token is valid and user is active."""
        request = MagicMock()
        request.cookies.get.return_value = "valid.jwt.token"
        db = AsyncMock()

        active_user = MagicMock(spec=User)
        active_user.is_active = True
        active_user.id = "user-123"
        active_user.email = "test@example.com"

        with patch("app.api.web.AuthService") as mock_auth_service:
            mock_auth = mock_auth_service.return_value
            mock_auth.verify_token.return_value = "user-123"
            mock_auth.get_user_by_id = AsyncMock(return_value=active_user)

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
