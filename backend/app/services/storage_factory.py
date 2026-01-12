"""Storage backend factory.

Centralized storage initialization logic used by both:
- Main application (app/main.py)
- Background tasks (app/tasks/ai_tagging.py)

This ensures consistent storage configuration across the application.
"""

from app.config import Settings
from app.services.storage_service import (
    LocalStorageBackend,
    MinioStorageBackend,
    StorageBackend,
)


async def create_storage_backend(settings: Settings) -> StorageBackend:
    """Create storage backend based on configuration.

    Single source of truth for storage initialization.
    Supports multiple backends: local filesystem, MinIO, S3, etc.

    Args:
        settings: Application settings with storage configuration

    Returns:
        Initialized storage backend ready for use

    Example:
        >>> settings = get_settings()
        >>> backend = await create_storage_backend(settings)
        >>> storage = StorageService(backend=backend)
    """
    if settings.storage_backend == "minio":
        return await MinioStorageBackend.create(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            bucket=settings.minio_bucket,
            secure=settings.minio_secure,
            startup_timeout=settings.minio_startup_timeout,
        )
    if settings.storage_backend == "local":
        return LocalStorageBackend(base_path=settings.local_storage_path)
    # Default to local storage if backend not recognized
    # This provides graceful degradation
    return LocalStorageBackend(base_path=settings.local_storage_path)
