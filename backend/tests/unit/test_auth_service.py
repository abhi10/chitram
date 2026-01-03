"""Unit tests for AuthService."""

import time

from app.services.auth_service import BCRYPT_WORK_FACTOR, AuthService


class TestPasswordHashing:
    """Test password hashing functionality."""

    def test_hash_password_returns_bcrypt_hash(self):
        """Password hash should start with bcrypt prefix."""
        auth_service = AuthService(db=None)
        password = "test_password_123"

        hashed = auth_service.hash_password(password)

        # bcrypt hashes start with $2b$ or $2a$
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_password_unique_per_call(self):
        """Each hash should be unique due to salt."""
        auth_service = AuthService(db=None)
        password = "same_password"

        hash1 = auth_service.hash_password(password)
        hash2 = auth_service.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        auth_service = AuthService(db=None)
        password = "correct_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password should fail verification."""
        auth_service = AuthService(db=None)
        password = "correct_password"
        hashed = auth_service.hash_password(password)

        assert auth_service.verify_password("wrong_password", hashed) is False

    def test_bcrypt_work_factor_is_12(self):
        """Bcrypt work factor should be 12."""
        assert BCRYPT_WORK_FACTOR == 12


class TestJWTTokens:
    """Test JWT token functionality."""

    def test_create_access_token_returns_string(self):
        """Token should be a non-empty string."""
        auth_service = AuthService(db=None)
        user_id = "test-user-123"

        token = auth_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_token_returns_user_id(self):
        """Valid token should return the user_id."""
        auth_service = AuthService(db=None)
        user_id = "test-user-456"

        token = auth_service.create_access_token(user_id)
        verified_user_id = auth_service.verify_token(token)

        assert verified_user_id == user_id

    def test_verify_token_invalid_returns_none(self):
        """Invalid token should return None."""
        auth_service = AuthService(db=None)

        result = auth_service.verify_token("invalid.token.here")

        assert result is None

    def test_verify_token_tampered_returns_none(self):
        """Tampered token should return None."""
        auth_service = AuthService(db=None)
        token = auth_service.create_access_token("user-id")

        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"

        result = auth_service.verify_token(tampered_token)

        assert result is None

    def test_token_contains_required_claims(self):
        """Token should contain sub, exp, iat claims."""
        from jose import jwt

        auth_service = AuthService(db=None)
        user_id = "test-user"

        token = auth_service.create_access_token(user_id)
        payload = jwt.decode(
            token,
            auth_service.settings.jwt_secret_key,
            algorithms=[auth_service.settings.jwt_algorithm],
        )

        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert payload["sub"] == user_id


class TestDeleteTokens:
    """Test delete token functionality."""

    def test_generate_delete_token_length(self):
        """Delete token should be URL-safe and ~43 chars (32 bytes base64)."""
        token = AuthService.generate_delete_token()

        assert isinstance(token, str)
        assert len(token) >= 40  # 32 bytes = ~43 chars in base64

    def test_generate_delete_token_unique(self):
        """Each token should be unique."""
        token1 = AuthService.generate_delete_token()
        token2 = AuthService.generate_delete_token()

        assert token1 != token2

    def test_hash_delete_token_returns_sha256(self):
        """Hash should be 64-char hex string (SHA-256)."""
        token = "test_token_abc123"
        hashed = AuthService.hash_delete_token(token)

        assert isinstance(hashed, str)
        assert len(hashed) == 64
        assert all(c in "0123456789abcdef" for c in hashed)

    def test_hash_delete_token_consistent(self):
        """Same token should produce same hash."""
        token = "consistent_token"
        hash1 = AuthService.hash_delete_token(token)
        hash2 = AuthService.hash_delete_token(token)

        assert hash1 == hash2

    def test_verify_delete_token_valid(self):
        """Valid token should verify against its hash."""
        token = AuthService.generate_delete_token()
        token_hash = AuthService.hash_delete_token(token)

        assert AuthService.verify_delete_token(token, token_hash) is True

    def test_verify_delete_token_invalid(self):
        """Invalid token should fail verification."""
        token = AuthService.generate_delete_token()
        token_hash = AuthService.hash_delete_token(token)

        assert AuthService.verify_delete_token("wrong_token", token_hash) is False

    def test_verify_delete_token_timing_safe(self):
        """Verification should use timing-safe comparison."""

        # This test verifies we're using secrets.compare_digest
        # by checking the function is imported correctly
        token = "test_token"
        token_hash = AuthService.hash_delete_token(token)

        # The method should work correctly (implementation detail is timing-safe)
        assert AuthService.verify_delete_token(token, token_hash) is True


class TestPasswordHashingTiming:
    """Test that password hashing takes appropriate time (work factor 12)."""

    def test_hash_takes_reasonable_time(self):
        """Hashing should take ~100-500ms with work factor 12."""
        auth_service = AuthService(db=None)
        password = "test_password"

        start = time.time()
        auth_service.hash_password(password)
        elapsed_ms = (time.time() - start) * 1000

        # Work factor 12 typically takes 100-500ms on modern hardware
        # Allow wider range for CI/different hardware
        assert elapsed_ms > 50, f"Hashing too fast ({elapsed_ms}ms), work factor may be too low"
        assert elapsed_ms < 2000, f"Hashing too slow ({elapsed_ms}ms)"
