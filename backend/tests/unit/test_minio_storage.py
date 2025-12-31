"""Unit tests for MinIO storage backend.

These tests use mocking to test the MinioStorageBackend class without
requiring an actual MinIO server. For integration tests with a real
MinIO server, see tests/integration/test_minio_integration.py.
"""

import io
from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error

from app.services.storage_service import MinioStorageBackend


class TestMinioStorageBackendInit:
    """Tests for MinioStorageBackend initialization."""

    @patch("app.services.storage_service.Minio")
    def test_init_creates_bucket_if_not_exists(self, mock_minio_class):
        """Backend creates bucket if it doesn't exist."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        mock_minio_class.return_value = mock_client

        backend = MinioStorageBackend(
            endpoint="localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            bucket="test-bucket",
            secure=False,
        )

        mock_client.bucket_exists.assert_called_once_with("test-bucket")
        mock_client.make_bucket.assert_called_once_with("test-bucket")

    @patch("app.services.storage_service.Minio")
    def test_init_skips_bucket_creation_if_exists(self, mock_minio_class):
        """Backend skips bucket creation if it already exists."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = True
        mock_minio_class.return_value = mock_client

        backend = MinioStorageBackend(
            endpoint="localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            bucket="test-bucket",
            secure=False,
        )

        mock_client.bucket_exists.assert_called_once_with("test-bucket")
        mock_client.make_bucket.assert_not_called()

    @patch("app.services.storage_service.Minio")
    def test_init_handles_bucket_already_owned_error(self, mock_minio_class):
        """Backend handles BucketAlreadyOwnedByYou error gracefully."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        error = S3Error(
            code="BucketAlreadyOwnedByYou",
            message="Bucket already exists",
            resource="test-bucket",
            request_id="test-request",
            host_id="test-host",
            response=MagicMock(),
        )
        mock_client.make_bucket.side_effect = error
        mock_minio_class.return_value = mock_client

        # Should not raise
        backend = MinioStorageBackend(
            endpoint="localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            bucket="test-bucket",
            secure=False,
        )

    @patch("app.services.storage_service.Minio")
    def test_init_raises_other_s3_errors(self, mock_minio_class):
        """Backend raises non-BucketAlreadyOwnedByYou S3 errors."""
        mock_client = MagicMock()
        mock_client.bucket_exists.return_value = False
        error = S3Error(
            code="AccessDenied",
            message="Access denied",
            resource="test-bucket",
            request_id="test-request",
            host_id="test-host",
            response=MagicMock(),
        )
        mock_client.make_bucket.side_effect = error
        mock_minio_class.return_value = mock_client

        with pytest.raises(S3Error) as exc_info:
            MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
            )
        assert exc_info.value.code == "AccessDenied"


class TestMinioStorageBackendSave:
    """Tests for MinioStorageBackend.save()."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock MinIO backend for testing."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            backend = MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
            )
            yield backend, mock_client

    @pytest.mark.asyncio
    async def test_save_uploads_object(self, mock_backend):
        """Save method uploads object to MinIO."""
        backend, mock_client = mock_backend
        test_data = b"test image data"

        result = await backend.save("test-key.jpg", test_data, "image/jpeg")

        assert result == "s3://test-bucket/test-key.jpg"
        mock_client.put_object.assert_called_once()
        call_args = mock_client.put_object.call_args
        assert call_args.kwargs["bucket_name"] == "test-bucket"
        assert call_args.kwargs["object_name"] == "test-key.jpg"
        assert call_args.kwargs["length"] == len(test_data)
        assert call_args.kwargs["content_type"] == "image/jpeg"


class TestMinioStorageBackendGet:
    """Tests for MinioStorageBackend.get()."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock MinIO backend for testing."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            backend = MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
            )
            yield backend, mock_client

    @pytest.mark.asyncio
    async def test_get_retrieves_object(self, mock_backend):
        """Get method retrieves object from MinIO."""
        backend, mock_client = mock_backend
        test_data = b"test image data"

        mock_response = MagicMock()
        mock_response.read.return_value = test_data
        mock_client.get_object.return_value = mock_response

        result = await backend.get("test-key.jpg")

        assert result == test_data
        mock_client.get_object.assert_called_once_with("test-bucket", "test-key.jpg")
        mock_response.close.assert_called_once()
        mock_response.release_conn.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_raises_file_not_found_for_missing_object(self, mock_backend):
        """Get method raises FileNotFoundError for missing objects."""
        backend, mock_client = mock_backend
        error = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test-key.jpg",
            request_id="test-request",
            host_id="test-host",
            response=MagicMock(),
        )
        mock_client.get_object.side_effect = error

        with pytest.raises(FileNotFoundError) as exc_info:
            await backend.get("test-key.jpg")
        assert "test-key.jpg" in str(exc_info.value)


class TestMinioStorageBackendDelete:
    """Tests for MinioStorageBackend.delete()."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock MinIO backend for testing."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            backend = MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
            )
            yield backend, mock_client

    @pytest.mark.asyncio
    async def test_delete_removes_object(self, mock_backend):
        """Delete method removes object from MinIO."""
        backend, mock_client = mock_backend
        mock_client.stat_object.return_value = MagicMock()

        result = await backend.delete("test-key.jpg")

        assert result is True
        mock_client.stat_object.assert_called_once_with("test-bucket", "test-key.jpg")
        mock_client.remove_object.assert_called_once_with("test-bucket", "test-key.jpg")

    @pytest.mark.asyncio
    async def test_delete_returns_false_for_missing_object(self, mock_backend):
        """Delete method returns False for missing objects."""
        backend, mock_client = mock_backend
        error = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test-key.jpg",
            request_id="test-request",
            host_id="test-host",
            response=MagicMock(),
        )
        mock_client.stat_object.side_effect = error

        result = await backend.delete("test-key.jpg")

        assert result is False
        mock_client.remove_object.assert_not_called()


class TestMinioStorageBackendExists:
    """Tests for MinioStorageBackend.exists()."""

    @pytest.fixture
    def mock_backend(self):
        """Create a mock MinIO backend for testing."""
        with patch("app.services.storage_service.Minio") as mock_minio_class:
            mock_client = MagicMock()
            mock_client.bucket_exists.return_value = True
            mock_minio_class.return_value = mock_client

            backend = MinioStorageBackend(
                endpoint="localhost:9000",
                access_key="testkey",
                secret_key="testsecret",
                bucket="test-bucket",
                secure=False,
            )
            yield backend, mock_client

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_existing_object(self, mock_backend):
        """Exists method returns True for existing objects."""
        backend, mock_client = mock_backend
        mock_client.stat_object.return_value = MagicMock()

        result = await backend.exists("test-key.jpg")

        assert result is True
        mock_client.stat_object.assert_called_once_with("test-bucket", "test-key.jpg")

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_object(self, mock_backend):
        """Exists method returns False for missing objects."""
        backend, mock_client = mock_backend
        error = S3Error(
            code="NoSuchKey",
            message="Object not found",
            resource="test-key.jpg",
            request_id="test-request",
            host_id="test-host",
            response=MagicMock(),
        )
        mock_client.stat_object.side_effect = error

        result = await backend.exists("test-key.jpg")

        assert result is False
