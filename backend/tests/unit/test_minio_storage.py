"""Unit tests for MinIO storage backend.

These tests use mocking to test the MinioStorageBackend class without
requiring an actual MinIO server. For integration tests with a real
MinIO server, see tests/integration/test_minio_integration.py.

Note: Bucket initialization tests have been moved to test_performance_fixes.py
since the async factory method (MinioStorageBackend.create()) is now the
preferred initialization pattern.
"""

from unittest.mock import MagicMock, patch

import pytest
from minio.error import S3Error

from app.services.storage_service import MinioStorageBackend


class TestMinioStorageBackendInit:
    """Tests for MinioStorageBackend basic initialization.

    Note: Bucket initialization tests (async factory method, timeout behavior)
    are in test_performance_fixes.py::TestMinioAsyncTimeout.
    """

    @patch("app.services.storage_service.Minio")
    def test_init_creates_client_with_correct_params(self, mock_minio_class):
        """Backend creates MinIO client with correct parameters."""
        mock_client = MagicMock()
        mock_minio_class.return_value = mock_client

        backend = MinioStorageBackend(
            endpoint="localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            bucket="test-bucket",
            secure=True,
        )

        mock_minio_class.assert_called_once_with(
            "localhost:9000",
            access_key="testkey",
            secret_key="testsecret",
            secure=True,
        )
        assert backend.bucket == "test-bucket"
        assert backend.client is mock_client


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
