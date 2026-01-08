"""Unit tests for auth provider implementations."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.auth.base import AuthError, AuthErrorCode, TokenPair, UserInfo
from app.services.auth.factory import create_auth_provider
from app.services.auth.local import LocalAuthProvider


class TestLocalAuthProvider:
    """Tests for LocalAuthProvider."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.jwt_secret_key = "test-secret-key-for-testing"
        settings.jwt_algorithm = "HS256"
        settings.jwt_expire_minutes = 60
        settings.auth_provider = "local"
        return settings

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    @pytest.fixture
    def provider(self, mock_db, mock_settings):
        """Create LocalAuthProvider instance."""
        return LocalAuthProvider(db=mock_db, settings=mock_settings)

    def test_provider_name(self, provider):
        """Test provider name is 'local'."""
        assert provider.provider_name == "local"

    def test_hash_password_returns_different_hash(self, provider):
        """Test password hashing returns different hash each time (due to salt)."""
        password = "testpassword123"
        hash1 = provider._hash_password(password)
        hash2 = provider._hash_password(password)

        assert hash1 != hash2  # Different salts
        assert hash1.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self, provider):
        """Test password verification with correct password."""
        password = "testpassword123"
        hashed = provider._hash_password(password)

        assert provider._verify_password(password, hashed) is True

    def test_verify_password_incorrect(self, provider):
        """Test password verification with incorrect password."""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = provider._hash_password(password)

        assert provider._verify_password(wrong_password, hashed) is False

    def test_verify_password_invalid_hash(self, provider):
        """Test password verification with invalid hash returns False."""
        assert provider._verify_password("password", "invalid-hash") is False

    def test_create_access_token(self, provider):
        """Test JWT token creation."""
        user_id = "test-user-id"
        token = provider._create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_decode_token_valid(self, provider):
        """Test decoding a valid token."""
        user_id = "test-user-id"
        token = provider._create_access_token(user_id)
        payload = provider._decode_token(token)

        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["provider"] == "local"

    def test_decode_token_invalid(self, provider):
        """Test decoding an invalid token returns None."""
        payload = provider._decode_token("invalid-token")
        assert payload is None

    def test_decode_token_wrong_secret(self, provider, mock_db):
        """Test decoding token with wrong secret returns None."""
        user_id = "test-user-id"
        token = provider._create_access_token(user_id)

        # Create provider with different secret
        other_settings = MagicMock()
        other_settings.jwt_secret_key = "different-secret"
        other_settings.jwt_algorithm = "HS256"
        other_provider = LocalAuthProvider(db=mock_db, settings=other_settings)

        payload = other_provider._decode_token(token)
        assert payload is None

    @pytest.mark.asyncio
    async def test_refresh_token_not_supported(self, provider):
        """Test refresh token returns error for local provider."""
        result = await provider.refresh_token("some-refresh-token")

        assert isinstance(result, AuthError)
        assert result.code == AuthErrorCode.PROVIDER_ERROR
        assert "not supported" in result.message.lower()

    @pytest.mark.asyncio
    async def test_request_password_reset_returns_true(self, provider):
        """Test password reset always returns True (security: no email enumeration)."""
        result = await provider.request_password_reset("test@example.com")
        assert result is True

        result = await provider.request_password_reset("nonexistent@example.com")
        assert result is True


class TestAuthProviderFactory:
    """Tests for auth provider factory."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        return AsyncMock()

    def test_create_local_provider(self, mock_db):
        """Test factory creates LocalAuthProvider for 'local' setting."""
        settings = MagicMock()
        settings.auth_provider = "local"
        settings.jwt_secret_key = "test-secret"
        settings.jwt_algorithm = "HS256"
        settings.jwt_expire_minutes = 60

        provider = create_auth_provider(db=mock_db, settings=settings)

        assert isinstance(provider, LocalAuthProvider)
        assert provider.provider_name == "local"

    def test_create_provider_invalid_type(self, mock_db):
        """Test factory raises error for unknown provider type."""
        settings = MagicMock()
        settings.auth_provider = "unknown-provider"

        with pytest.raises(ValueError, match="Unknown auth provider"):
            create_auth_provider(db=mock_db, settings=settings)

    def test_create_supabase_provider_missing_config(self, mock_db):
        """Test factory raises error when Supabase config is missing."""
        settings = MagicMock()
        settings.auth_provider = "supabase"
        settings.supabase_url = None
        settings.supabase_anon_key = None

        with pytest.raises(ValueError, match="SUPABASE_URL is required"):
            create_auth_provider(db=mock_db, settings=settings)


class TestAuthError:
    """Tests for AuthError dataclass."""

    def test_to_dict(self):
        """Test AuthError converts to dictionary correctly."""
        error = AuthError(
            code=AuthErrorCode.INVALID_CREDENTIALS,
            message="Invalid email or password",
        )
        result = error.to_dict()

        assert result == {
            "code": "INVALID_CREDENTIALS",
            "message": "Invalid email or password",
        }

    def test_immutable(self):
        """Test AuthError is immutable (frozen dataclass)."""
        error = AuthError(
            code=AuthErrorCode.EMAIL_EXISTS,
            message="Email already registered",
        )

        with pytest.raises(AttributeError):
            error.code = AuthErrorCode.INVALID_TOKEN


class TestUserInfo:
    """Tests for UserInfo dataclass."""

    def test_create_local_user_info(self):
        """Test creating UserInfo for local user."""
        info = UserInfo(
            local_user_id="user-123",
            email="test@example.com",
            is_active=True,
            provider="local",
        )

        assert info.local_user_id == "user-123"
        assert info.email == "test@example.com"
        assert info.is_active is True
        assert info.provider == "local"
        assert info.external_id is None

    def test_create_supabase_user_info(self):
        """Test creating UserInfo for Supabase user."""
        info = UserInfo(
            local_user_id="user-123",
            email="test@example.com",
            is_active=True,
            provider="supabase",
            external_id="supabase-uuid-456",
        )

        assert info.local_user_id == "user-123"
        assert info.provider == "supabase"
        assert info.external_id == "supabase-uuid-456"


class TestTokenPair:
    """Tests for TokenPair dataclass."""

    def test_access_token_only(self):
        """Test TokenPair with access token only."""
        pair = TokenPair(access_token="access-token-123")

        assert pair.access_token == "access-token-123"
        assert pair.refresh_token is None
        assert pair.expires_in is None

    def test_full_token_pair(self):
        """Test TokenPair with all fields."""
        pair = TokenPair(
            access_token="access-token-123",
            refresh_token="refresh-token-456",
            expires_in=3600,
        )

        assert pair.access_token == "access-token-123"
        assert pair.refresh_token == "refresh-token-456"
        assert pair.expires_in == 3600
