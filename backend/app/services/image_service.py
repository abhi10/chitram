"""Image service - business logic layer."""

import asyncio
import io
import logging
import uuid
from typing import TYPE_CHECKING

from PIL import Image as PILImage
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from app.services.cache_service import CacheService


class ImageService:
    """Service for image operations."""

    def __init__(
        self,
        db: AsyncSession,
        storage: StorageService,
        cache: "CacheService | None" = None,
    ):
        self.db = db
        self.storage = storage
        self.cache = cache

    @staticmethod
    def generate_storage_key(filename: str) -> str:
        """Generate unique storage key preserving file extension."""
        extension = filename.rsplit(".", 1)[-1] if "." in filename else "bin"
        return f"{uuid.uuid4()}.{extension.lower()}"

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent path traversal."""
        # Remove path separators and null bytes
        sanitized = filename.replace("/", "_").replace("\\", "_").replace("\x00", "")
        # Limit length
        if len(sanitized) > 255:
            name, ext = sanitized.rsplit(".", 1) if "." in sanitized else (sanitized, "")
            sanitized = f"{name[:250]}.{ext}" if ext else name[:255]
        return sanitized or "unnamed"

    @staticmethod
    def _extract_dimensions_sync(data: bytes) -> tuple[int, int] | None:
        """
        Synchronous helper to extract image dimensions using Pillow.

        This is CPU-bound work that should be run in a thread pool.
        """
        try:
            with PILImage.open(io.BytesIO(data)) as img:
                return img.size  # Returns (width, height)
        except Exception:
            return None

    @staticmethod
    async def get_image_dimensions(data: bytes) -> tuple[int, int] | None:
        """
        Extract image dimensions using Pillow without blocking event loop.

        Uses asyncio.to_thread() to run CPU-bound Pillow operations
        in a thread pool, preventing event loop blocking.

        Args:
            data: Raw image bytes

        Returns:
            Tuple of (width, height) or None if extraction fails
        """
        return await asyncio.to_thread(
            ImageService._extract_dimensions_sync, data
        )

    async def upload(
        self,
        data: bytes,
        filename: str,
        content_type: str,
        upload_ip: str,
    ) -> Image:
        """
        Upload a new image.

        Args:
            data: Image file content
            filename: Original filename
            content_type: MIME type
            upload_ip: Client IP address

        Returns:
            Created Image model
        """
        # Sanitize and generate keys
        safe_filename = self.sanitize_filename(filename)
        storage_key = self.generate_storage_key(safe_filename)

        # Extract image dimensions (non-blocking, runs in thread pool)
        dimensions = await self.get_image_dimensions(data)
        width, height = dimensions if dimensions else (None, None)

        # Save to storage
        await self.storage.save(storage_key, data, content_type)

        # Create database record
        image = Image(
            filename=safe_filename,
            storage_key=storage_key,
            content_type=content_type,
            file_size=len(data),
            upload_ip=upload_ip,
            width=width,
            height=height,
        )

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        # Cache the newly uploaded image metadata
        if self.cache:
            await self.cache.set_image_metadata(image.id, self._image_to_dict(image))

        return image

    async def get_by_id(self, image_id: str, use_cache: bool = True) -> Image | None:
        """
        Get image metadata by ID with optional caching.

        Args:
            image_id: The image UUID
            use_cache: Whether to use cache (default True)

        Returns:
            Image model or None if not found
        """
        result, _ = await self.get_by_id_with_cache_status(image_id, use_cache)
        return result

    async def get_by_id_with_cache_status(
        self, image_id: str, use_cache: bool = True
    ) -> tuple[Image | None, str]:
        """
        Get image metadata by ID with cache hit/miss status.

        Args:
            image_id: The image UUID
            use_cache: Whether to use cache (default True)

        Returns:
            Tuple of (Image model or None, cache_status)
            cache_status is one of: "HIT", "MISS", "DISABLED"
        """
        # Try cache first
        if use_cache and self.cache:
            cached = await self.cache.get_image_metadata(image_id)
            if cached:
                # Reconstruct Image model from cached dict
                return Image(**cached), "HIT"

            # Cache miss - fetch from DB
            result = await self.db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()

            # Populate cache on DB hit
            if image:
                await self.cache.set_image_metadata(image_id, self._image_to_dict(image))

            return image, "MISS"

        # Cache disabled or not configured
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        return image, "DISABLED"

    @staticmethod
    def _image_to_dict(image: Image) -> dict:
        """Convert Image model to dict for caching."""
        return {
            "id": image.id,
            "filename": image.filename,
            "storage_key": image.storage_key,
            "content_type": image.content_type,
            "file_size": image.file_size,
            "upload_ip": image.upload_ip,
            "width": image.width,
            "height": image.height,
            "created_at": image.created_at.isoformat() if image.created_at else None,
        }

    async def get_file(self, image_id: str) -> tuple[bytes, str] | None:
        """
        Get image file content.

        Returns:
            Tuple of (file_bytes, content_type) or None if not found
        """
        image = await self.get_by_id(image_id)
        if not image:
            return None

        try:
            data = await self.storage.get(image.storage_key)
            return data, image.content_type
        except FileNotFoundError:
            return None

    async def delete(self, image_id: str) -> bool:
        """
        Delete an image.

        Returns:
            True if deleted, False if not found
        """
        # Skip cache when fetching for deletion to ensure we have fresh DB state
        image = await self.get_by_id(image_id, use_cache=False)
        if not image:
            return False

        # Delete from storage (graceful - continue even if storage delete fails)
        try:
            await self.storage.delete(image.storage_key)
        except Exception as e:
            # Log for orphan tracking but continue with DB deletion
            logger.warning(
                "Failed to delete storage file %s for image %s: %s. "
                "File may be orphaned.",
                image.storage_key,
                image_id,
                str(e),
            )

        # Invalidate cache
        if self.cache:
            await self.cache.invalidate_image(image_id)

        # Delete from database
        await self.db.delete(image)
        await self.db.commit()

        return True
