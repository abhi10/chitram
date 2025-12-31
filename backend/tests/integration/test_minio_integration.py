"""Integration tests for MinIO storage backend.

These tests require a running MinIO server. They are skipped if MinIO
is not available. Run with:

    docker-compose up -d minio
    pytest tests/integration/ -v

Or in DevContainer where MinIO is already running.
"""

import os
import uuid

import pytest
from minio import Minio
from minio.error import S3Error

from app.services.storage_service import MinioStorageBackend


def minio_available() -> bool:
    """Check if MinIO is available."""
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    try:
        client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False,
        )
        # Try to list buckets to verify connection
        client.list_buckets()
        return True
    except Exception:
        return False


# Skip all tests in this module if MinIO is not available
pytestmark = pytest.mark.skipif(
    not minio_available(),
    reason="MinIO server not available",
)


@pytest.fixture
def test_bucket_name() -> str:
    """Generate unique bucket name for test isolation."""
    return f"test-bucket-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def minio_backend(test_bucket_name) -> MinioStorageBackend:
    """Create MinIO backend with test bucket."""
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

    backend = MinioStorageBackend(
        endpoint=endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket=test_bucket_name,
        secure=False,
    )

    yield backend

    # Cleanup: remove all objects and delete bucket
    try:
        objects = backend.client.list_objects(test_bucket_name)
        for obj in objects:
            backend.client.remove_object(test_bucket_name, obj.object_name)
        backend.client.remove_bucket(test_bucket_name)
    except Exception:
        pass


class TestMinioIntegration:
    """Integration tests for MinIO backend with real MinIO server."""

    @pytest.mark.asyncio
    async def test_save_and_get_roundtrip(self, minio_backend):
        """Test saving and retrieving a file."""
        test_data = b"Hello, MinIO integration test!"
        storage_key = f"test-{uuid.uuid4()}.txt"

        # Save
        result = await minio_backend.save(storage_key, test_data, "text/plain")
        assert result == f"s3://{minio_backend.bucket}/{storage_key}"

        # Get
        retrieved = await minio_backend.get(storage_key)
        assert retrieved == test_data

    @pytest.mark.asyncio
    async def test_save_and_get_binary_file(self, minio_backend, sample_jpeg_bytes):
        """Test saving and retrieving binary image file."""
        storage_key = f"image-{uuid.uuid4()}.jpg"

        # Save
        await minio_backend.save(storage_key, sample_jpeg_bytes, "image/jpeg")

        # Get
        retrieved = await minio_backend.get(storage_key)
        assert retrieved == sample_jpeg_bytes

    @pytest.mark.asyncio
    async def test_exists_for_existing_object(self, minio_backend):
        """Test exists returns True for existing object."""
        storage_key = f"test-{uuid.uuid4()}.txt"
        await minio_backend.save(storage_key, b"test", "text/plain")

        assert await minio_backend.exists(storage_key) is True

    @pytest.mark.asyncio
    async def test_exists_for_missing_object(self, minio_backend):
        """Test exists returns False for missing object."""
        assert await minio_backend.exists("nonexistent-key.txt") is False

    @pytest.mark.asyncio
    async def test_delete_existing_object(self, minio_backend):
        """Test deleting an existing object."""
        storage_key = f"test-{uuid.uuid4()}.txt"
        await minio_backend.save(storage_key, b"test", "text/plain")

        result = await minio_backend.delete(storage_key)
        assert result is True

        # Verify deleted
        assert await minio_backend.exists(storage_key) is False

    @pytest.mark.asyncio
    async def test_delete_missing_object(self, minio_backend):
        """Test deleting a missing object returns False."""
        result = await minio_backend.delete("nonexistent-key.txt")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_missing_object_raises_file_not_found(self, minio_backend):
        """Test getting a missing object raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            await minio_backend.get("nonexistent-key.txt")

    @pytest.mark.asyncio
    async def test_multiple_files_isolation(self, minio_backend):
        """Test multiple files don't interfere with each other."""
        key1 = f"file1-{uuid.uuid4()}.txt"
        key2 = f"file2-{uuid.uuid4()}.txt"
        data1 = b"Content of file 1"
        data2 = b"Content of file 2"

        await minio_backend.save(key1, data1, "text/plain")
        await minio_backend.save(key2, data2, "text/plain")

        assert await minio_backend.get(key1) == data1
        assert await minio_backend.get(key2) == data2

        # Delete one, verify other still exists
        await minio_backend.delete(key1)
        assert await minio_backend.exists(key1) is False
        assert await minio_backend.get(key2) == data2

    @pytest.mark.asyncio
    async def test_nested_keys(self, minio_backend):
        """Test storage keys with path-like structure."""
        key = f"images/2024/12/{uuid.uuid4()}.jpg"
        data = b"nested file data"

        await minio_backend.save(key, data, "image/jpeg")
        retrieved = await minio_backend.get(key)
        assert retrieved == data


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Create a valid JPEG test image."""
    import io
    from PIL import Image as PILImage

    img = PILImage.new("RGB", (100, 100), color="red")
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    buffer.seek(0)
    return buffer.read()
