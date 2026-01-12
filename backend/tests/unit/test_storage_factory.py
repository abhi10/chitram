"""Unit tests for storage factory.

Tests the storage factory creates correct backends based on configuration.
"""

import pytest

from app.config import Settings
from app.services.storage_factory import create_storage_backend
from app.services.storage_service import LocalStorageBackend, MinioStorageBackend


class TestStorageFactory:
    """Tests for create_storage_backend factory function."""

    @pytest.mark.asyncio
    async def test_creates_local_backend_when_configured(self, tmp_path):
        """Factory creates LocalStorageBackend when storage_backend='local'."""
        settings = Settings(
            storage_backend="local",
            local_storage_path=str(tmp_path),
        )

        backend = await create_storage_backend(settings)

        assert isinstance(backend, LocalStorageBackend)
        assert str(backend.base_path) == str(tmp_path)

    @pytest.mark.asyncio
    async def test_creates_local_backend_by_default(self, tmp_path):
        """Factory defaults to LocalStorageBackend for unknown backends."""
        settings = Settings(
            storage_backend="unknown-backend",
            local_storage_path=str(tmp_path),
        )

        backend = await create_storage_backend(settings)

        assert isinstance(backend, LocalStorageBackend)

    @pytest.mark.skip(reason="Requires MinIO running - move to integration tests")
    @pytest.mark.asyncio
    async def test_creates_minio_backend_when_configured(self):
        """Factory creates MinioStorageBackend when storage_backend='minio'."""
        settings = Settings(
            storage_backend="minio",
            minio_endpoint="localhost:9000",
            minio_access_key="test-access",
            minio_secret_key="test-secret",
            minio_bucket="test-bucket",
            minio_secure=False,
        )

        backend = await create_storage_backend(settings)

        assert isinstance(backend, MinioStorageBackend)
        assert backend.bucket == "test-bucket"

    @pytest.mark.asyncio
    async def test_consistent_backends_for_same_settings(self, tmp_path):
        """Factory creates same backend type for identical settings."""
        settings = Settings(
            storage_backend="local",
            local_storage_path=str(tmp_path),
        )

        backend1 = await create_storage_backend(settings)
        backend2 = await create_storage_backend(settings)

        # Should be same type (but different instances)
        assert type(backend1) is type(backend2)
        assert backend1 is not backend2  # Different instances

    @pytest.mark.skip(reason="Requires MinIO running - move to integration tests")
    @pytest.mark.asyncio
    async def test_minio_backend_respects_secure_flag(self):
        """Factory passes secure flag to MinIO backend correctly."""
        settings_secure = Settings(
            storage_backend="minio",
            minio_endpoint="s3.amazonaws.com",
            minio_access_key="test",
            minio_secret_key="test",
            minio_bucket="bucket",
            minio_secure=True,
        )

        backend = await create_storage_backend(settings_secure)

        assert isinstance(backend, MinioStorageBackend)
        # MinioStorageBackend stores secure flag
        assert backend._secure is True
