"""Unit tests for Phase 2 performance fixes.

Tests cover:
1. Pillow async image dimension extraction (asyncio.to_thread)
2. MinIO async bucket check with timeout
3. Storage deletion failure logging
"""

import asyncio
import io
import logging
from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error
from PIL import Image as PILImage

from app.services.image_service import ImageService
from app.services.storage_service import MinioStorageBackend


class TestPillowAsyncDimensions:
    """Tests for async image dimension extraction using asyncio.to_thread."""

    @pytest.fixture
    def valid_jpeg_bytes(self) -> bytes:
        """Create valid JPEG image bytes."""
        img = PILImage.new("RGB", (640, 480), color="blue")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    @pytest.fixture
    def valid_png_bytes(self) -> bytes:
        """Create valid PNG image bytes."""
        img = PILImage.new("RGBA", (1920, 1080), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.read()

    @pytest.mark.asyncio
    async def test_get_image_dimensions_extracts_jpeg(self, valid_jpeg_bytes: bytes):
        """Dimensions extracted correctly from JPEG."""
        dimensions = await ImageService.get_image_dimensions(valid_jpeg_bytes)

        assert dimensions == (640, 480)

    @pytest.mark.asyncio
    async def test_get_image_dimensions_extracts_png(self, valid_png_bytes: bytes):
        """Dimensions extracted correctly from PNG."""
        dimensions = await ImageService.get_image_dimensions(valid_png_bytes)

        assert dimensions == (1920, 1080)

    @pytest.mark.asyncio
    async def test_get_image_dimensions_returns_none_for_invalid_data(self):
        """Returns None for invalid image data."""
        invalid_data = b"not an image"

        dimensions = await ImageService.get_image_dimensions(invalid_data)

        assert dimensions is None

    @pytest.mark.asyncio
    async def test_get_image_dimensions_returns_none_for_empty_data(self):
        """Returns None for empty data."""
        dimensions = await ImageService.get_image_dimensions(b"")

        assert dimensions is None

    @pytest.mark.asyncio
    async def test_get_image_dimensions_uses_thread_pool(self, valid_jpeg_bytes: bytes):
        """Verifies dimension extraction runs in thread pool."""
        with patch("app.services.image_service.asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = (640, 480)

            await ImageService.get_image_dimensions(valid_jpeg_bytes)

            mock_to_thread.assert_called_once()
            # First arg should be the sync helper function
            call_args = mock_to_thread.call_args
            assert call_args[0][0] == ImageService._extract_dimensions_sync

    def test_extract_dimensions_sync_helper(self, valid_jpeg_bytes: bytes):
        """Sync helper correctly extracts dimensions."""
        result = ImageService._extract_dimensions_sync(valid_jpeg_bytes)

        assert result == (640, 480)

    def test_extract_dimensions_sync_handles_error(self):
        """Sync helper returns None on error."""
        result = ImageService._extract_dimensions_sync(b"invalid")

        assert result is None


class TestMinioAsyncTimeout:
    """Tests for MinIO async bucket check with timeout."""

    @pytest.mark.asyncio
    async def test_create_initializes_bucket_async(self):
        """Async factory method initializes bucket."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = False
            mock_minio_class.return_value = mock_client

            backend = await MinioStorageBackend.create(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
                startup_timeout=5.0,
            )

            assert backend.bucket == "test-bucket"
            mock_client.bucket_exists.assert_called_once_with("test-bucket")
            mock_client.make_bucket.assert_called_once_with("test-bucket")

    @pytest.mark.asyncio
    async def test_create_skips_bucket_if_exists(self):
        """Async factory skips bucket creation if it exists."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            backend = await MinioStorageBackend.create(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="existing-bucket",
                secure=False,
            )

            mock_client.make_bucket.assert_not_called()
            assert backend.bucket == "existing-bucket"

    @pytest.mark.asyncio
    async def test_create_times_out_on_slow_minio(self):
        """Async factory raises TimeoutError when MinIO is slow."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()

            # Simulate slow MinIO response
            def slow_bucket_check(bucket_name):
                import time

                time.sleep(0.5)  # Slow response
                return False

            mock_client.bucket_exists.side_effect = slow_bucket_check
            mock_minio_class.return_value = mock_client

            with pytest.raises(asyncio.TimeoutError):
                await MinioStorageBackend.create(
                    endpoint="localhost:9000",
                    access_key="testkey",
                    secret_key="testsecret",
                    bucket="test-bucket",
                    secure=False,
                    startup_timeout=0.1,  # Very short timeout
                )

    @pytest.mark.asyncio
    async def test_ensure_bucket_async_logs_timeout(self, caplog):
        """Timeout logs error with endpoint info."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client._base_url = "http://localhost:9000"

            def slow_check(bucket_name):
                import time

                time.sleep(0.5)
                return False

            mock_client.bucket_exists.side_effect = slow_check
            mock_minio_class.return_value = mock_client

            backend = MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
            )

            with caplog.at_level(logging.ERROR), pytest.raises(asyncio.TimeoutError):
                await backend._ensure_bucket_async(timeout=0.1)

            assert "MinIO bucket check timed out" in caplog.text

    @pytest.mark.asyncio
    async def test_create_handles_bucket_already_owned_error(self):
        """Async factory handles BucketAlreadyOwnedByYou gracefully."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = False
            error = S3Error(
                code="BucketAlreadyOwnedByYou",
                message="Bucket exists",
                resource="test-bucket",
                request_id="req-1",
                host_id="host-1",
                response=MagicMock(),
            )
            mock_client.make_bucket.side_effect = error
            mock_minio_class.return_value = mock_client

            # Should not raise
            backend = await MinioStorageBackend.create(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
            )

            assert backend is not None

    @pytest.mark.asyncio
    async def test_create_raises_other_s3_errors(self):
        """Async factory raises non-BucketAlreadyOwnedByYou errors."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = False
            error = S3Error(
                code="AccessDenied",
                message="Access denied",
                resource="test-bucket",
                request_id="req-1",
                host_id="host-1",
                response=MagicMock(),
            )
            mock_client.make_bucket.side_effect = error
            mock_minio_class.return_value = mock_client

            with pytest.raises(S3Error) as exc_info:
                await MinioStorageBackend.create(
                    endpoint="localhost:9000",
                    access_key="testkey",
                    secret_key="testsecret",
                    bucket="test-bucket",
                )

            assert exc_info.value.code == "AccessDenied"

    def test_init_does_not_call_bucket_check(self):
        """Direct __init__ does not check bucket (deferred to create)."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_minio_class.return_value = mock_client

            MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
            )

            # bucket_exists should NOT be called in __init__
            mock_client.bucket_exists.assert_not_called()


class TestStorageDeletionLogging:
    """Tests for storage deletion failure logging."""

    @pytest.fixture
    def mock_db(self):
        """Create mock database session."""
        mock = MagicMock()
        mock.execute = MagicMock()
        mock.delete = MagicMock()
        mock.commit = MagicMock()
        return mock

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage service."""
        return MagicMock()

    @pytest.fixture
    def mock_cache(self):
        """Create mock cache service."""
        return MagicMock()

    @pytest.mark.asyncio
    async def test_delete_logs_storage_failure(self, mock_db, mock_storage, mock_cache, caplog):
        """Delete operation logs warning when storage delete fails."""
        from unittest.mock import AsyncMock

        from app.models.image import Image

        # Setup mock image
        # Use user_id for owned image (no delete token needed)
        test_image = Image(
            id="test-uuid",
            filename="test.jpg",
            storage_key="abc123.jpg",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
            user_id="test-user",  # Owned image
        )

        # Mock get_by_id to return test image
        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_image
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        # Mock storage to raise an error on delete
        mock_storage.delete = AsyncMock(side_effect=Exception("Storage unavailable"))

        # Mock cache
        mock_cache.invalidate_image = AsyncMock()

        service = ImageService(db=mock_db, storage=mock_storage, cache=mock_cache)

        with caplog.at_level(logging.WARNING):
            # Pass user_id to authorize deletion
            success, reason = await service.delete("test-uuid", user_id="test-user")

        # Delete should still succeed (graceful degradation)
        assert success is True
        assert reason == "deleted"

        # Warning should be logged
        assert "Failed to delete storage file" in caplog.text
        assert "abc123.jpg" in caplog.text
        assert "orphaned" in caplog.text.lower()

    @pytest.mark.asyncio
    async def test_delete_continues_after_storage_failure(self, mock_db, mock_storage, mock_cache):
        """Delete completes DB operation even when storage fails."""
        from unittest.mock import AsyncMock

        from app.models.image import Image

        test_image = Image(
            id="test-uuid",
            filename="test.jpg",
            storage_key="abc123.jpg",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
            user_id="test-user",  # Owned image
        )

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_image
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_storage.delete = AsyncMock(side_effect=Exception("Network error"))
        mock_cache.invalidate_image = AsyncMock()

        service = ImageService(db=mock_db, storage=mock_storage, cache=mock_cache)

        success, reason = await service.delete("test-uuid", user_id="test-user")

        assert success is True
        assert reason == "deleted"
        # DB operations should still be called
        mock_db.delete.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_cache.invalidate_image.assert_called_once_with("test-uuid")

    @pytest.mark.asyncio
    async def test_delete_succeeds_without_logging_on_success(
        self, mock_db, mock_storage, mock_cache, caplog
    ):
        """No warning logged when storage delete succeeds."""
        from unittest.mock import AsyncMock

        from app.models.image import Image

        test_image = Image(
            id="test-uuid",
            filename="test.jpg",
            storage_key="abc123.jpg",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
            user_id="test-user",  # Owned image
        )

        mock_db.execute = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = test_image
        mock_db.execute.return_value = mock_result
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_storage.delete = AsyncMock(return_value=True)  # Success
        mock_cache.invalidate_image = AsyncMock()

        service = ImageService(db=mock_db, storage=mock_storage, cache=mock_cache)

        with caplog.at_level(logging.WARNING):
            success, reason = await service.delete("test-uuid", user_id="test-user")

        assert success is True
        assert reason == "deleted"
        assert "Failed to delete storage file" not in caplog.text
