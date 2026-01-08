"""API tests for authentication endpoints."""

import pytest
from httpx import AsyncClient


class TestRegister:
    """Test user registration endpoint."""

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient):
        """Successful registration returns user and token."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "secure_password_123"},
        )

        assert response.status_code == 201
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["email"] == "test@example.com"
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient):
        """Duplicate email returns 400."""
        # First registration
        await client.post(
            "/api/v1/auth/register",
            json={"email": "dupe@example.com", "password": "password123"},
        )

        # Second registration with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "dupe@example.com", "password": "different_password"},
        )

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "EMAIL_EXISTS"

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, client: AsyncClient):
        """Invalid email format returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "password123"},
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_short_password(self, client: AsyncClient):
        """Password too short returns 422."""
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short"},
        )

        assert response.status_code == 422


class TestLogin:
    """Test user login endpoint."""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient):
        """Successful login returns user and token."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "password123"},
        )

        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "access_token" in data
        assert data["user"]["email"] == "login@example.com"

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client: AsyncClient):
        """Wrong password returns 401."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrong@example.com", "password": "correct_password"},
        )

        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrong@example.com", "password": "wrong_password"},
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Nonexistent user returns same error as wrong password (no enumeration)."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "any_password"},
        )

        assert response.status_code == 401
        # Same error code as wrong password (prevents user enumeration)
        assert response.json()["detail"]["code"] == "INVALID_CREDENTIALS"


class TestGetMe:
    """Test get current user endpoint."""

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client: AsyncClient):
        """Authenticated user can get their profile."""
        # Register and get token
        register_response = await client.post(
            "/api/v1/auth/register",
            json={"email": "me@example.com", "password": "password123"},
        )
        token = register_response.json()["access_token"]

        # Get profile
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"
        assert "password_hash" not in data  # Password should not be exposed

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Unauthenticated request returns 401."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Invalid token returns 401."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401


class TestTokenEndpoint:
    """Test OAuth2 token endpoint (for Swagger UI)."""

    @pytest.mark.asyncio
    async def test_token_endpoint_success(self, client: AsyncClient):
        """Token endpoint returns access token."""
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "oauth@example.com", "password": "password123"},
        )

        # Get token using OAuth2 form
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": "oauth@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_token_endpoint_invalid_credentials(self, client: AsyncClient):
        """Invalid credentials returns 401."""
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": "bad@example.com", "password": "wrong"},
        )

        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset endpoint."""

    @pytest.mark.asyncio
    async def test_password_reset_returns_202(self, client: AsyncClient):
        """Password reset request always returns 202 (prevents email enumeration)."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 202
        data = response.json()
        assert "message" in data
        assert "password reset" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_password_reset_nonexistent_email(self, client: AsyncClient):
        """Nonexistent email still returns 202 (security: no enumeration)."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "nonexistent@example.com"},
        )

        # Should return same response as existing email
        assert response.status_code == 202

    @pytest.mark.asyncio
    async def test_password_reset_invalid_email(self, client: AsyncClient):
        """Invalid email format returns 422."""
        response = await client.post(
            "/api/v1/auth/password-reset",
            json={"email": "not-an-email"},
        )

        assert response.status_code == 422
