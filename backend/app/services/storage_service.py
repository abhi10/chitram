"""Storage service with backend abstraction (Strategy Pattern)."""

import asyncio
import io
from abc import ABC, abstractmethod
from pathlib import Path

import aiofiles
import aiofiles.os
from minio import Minio
from minio.error import S3Error


class StorageBackend(ABC):
    """Abstract base class for storage backends."""

    @abstractmethod
    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """
        Save file to storage.

        Args:
            key: Unique storage key
            data: File content as bytes
            content_type: MIME type

        Returns:
            Storage URL/path
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> bytes:
        """
        Retrieve file from storage.

        Args:
            key: Storage key

        Returns:
            File content as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete file from storage.

        Args:
            key: Storage key

        Returns:
            True if deleted, False if not found
        """
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if file exists in storage."""
        pass


class LocalStorageBackend(StorageBackend):
    """Local filesystem storage backend (for development)."""

    def __init__(self, base_path: str = "./uploads"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        """Get full path for a storage key."""
        return self.base_path / key

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Save file to local filesystem."""
        file_path = self._get_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        async with aiofiles.open(file_path, "wb") as f:
            await f.write(data)

        return str(file_path)

    async def get(self, key: str) -> bytes:
        """Retrieve file from local filesystem."""
        file_path = self._get_path(key)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {key}")

        async with aiofiles.open(file_path, "rb") as f:
            return await f.read()

    async def delete(self, key: str) -> bool:
        """Delete file from local filesystem."""
        file_path = self._get_path(key)

        if not file_path.exists():
            return False

        await aiofiles.os.remove(file_path)
        return True

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        return self._get_path(key).exists()


class MinioStorageBackend(StorageBackend):
    """MinIO/S3-compatible storage backend (for production).

    Uses synchronous MinIO client wrapped in asyncio.to_thread for async compatibility.
    This approach is recommended for I/O-bound operations with sync libraries.
    """

    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        bucket: str,
        secure: bool = False,
    ):
        """
        Initialize MinIO backend.

        Args:
            endpoint: MinIO server endpoint (e.g., "localhost:9000")
            access_key: MinIO access key
            secret_key: MinIO secret key
            bucket: Bucket name for storing images
            secure: Use HTTPS if True
        """
        self.bucket = bucket
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )
        # Ensure bucket exists on initialization
        self._ensure_bucket()

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            # Log and continue - bucket might already exist or be created by another process
            if e.code != "BucketAlreadyOwnedByYou":
                raise

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Save file to MinIO."""

        def _save() -> str:
            self.client.put_object(
                bucket_name=self.bucket,
                object_name=key,
                data=io.BytesIO(data),
                length=len(data),
                content_type=content_type,
            )
            return f"s3://{self.bucket}/{key}"

        return await asyncio.to_thread(_save)

    async def get(self, key: str) -> bytes:
        """Retrieve file from MinIO."""

        def _get() -> bytes:
            try:
                response = self.client.get_object(self.bucket, key)
                try:
                    return response.read()
                finally:
                    response.close()
                    response.release_conn()
            except S3Error as e:
                if e.code == "NoSuchKey":
                    raise FileNotFoundError(f"File not found: {key}") from e
                raise

        return await asyncio.to_thread(_get)

    async def delete(self, key: str) -> bool:
        """Delete file from MinIO."""

        def _delete() -> bool:
            try:
                # Check if object exists first
                self.client.stat_object(self.bucket, key)
                self.client.remove_object(self.bucket, key)
                return True
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return False
                raise

        return await asyncio.to_thread(_delete)

    async def exists(self, key: str) -> bool:
        """Check if file exists in MinIO."""

        def _exists() -> bool:
            try:
                self.client.stat_object(self.bucket, key)
                return True
            except S3Error as e:
                if e.code == "NoSuchKey":
                    return False
                raise

        return await asyncio.to_thread(_exists)


class StorageService:
    """Storage service wrapper with graceful degradation."""

    def __init__(self, backend: StorageBackend):
        self.backend = backend

    async def save(self, key: str, data: bytes, content_type: str) -> str:
        """Save file to storage."""
        return await self.backend.save(key, data, content_type)

    async def get(self, key: str) -> bytes:
        """Retrieve file from storage."""
        return await self.backend.get(key)

    async def delete(self, key: str) -> bool:
        """Delete file from storage."""
        return await self.backend.delete(key)

    async def exists(self, key: str) -> bool:
        """Check if file exists."""
        return await self.backend.exists(key)
