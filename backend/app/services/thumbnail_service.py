"""Thumbnail service - generates thumbnails in background tasks."""

import asyncio
import io
import logging
from typing import TYPE_CHECKING

from PIL import Image as PILImage
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.models.image import Image
from app.services.storage_service import StorageService

if TYPE_CHECKING:
    from app.services.cache_service import CacheService

logger = logging.getLogger(__name__)

# Thumbnail configuration
THUMBNAIL_MAX_SIZE = 300  # 300px max dimension
THUMBNAIL_QUALITY = 85  # JPEG quality
THUMBNAIL_PREFIX = "thumbs/"


class ThumbnailService:
    """Service for thumbnail generation."""

    def __init__(
        self,
        storage: StorageService,
        session_factory: async_sessionmaker[AsyncSession],
        cache: "CacheService | None" = None,
    ):
        """
        Initialize thumbnail service.

        Args:
            storage: Storage service for saving thumbnails
            session_factory: Async session factory for database operations
            cache: Optional cache service for invalidation after thumbnail generation
        """
        self.storage = storage
        self.session_factory = session_factory
        self.cache = cache

    @staticmethod
    def _generate_thumbnail_sync(
        data: bytes,
        max_size: int = THUMBNAIL_MAX_SIZE,
        quality: int = THUMBNAIL_QUALITY,
    ) -> bytes | None:
        """
        Synchronous helper to generate thumbnail.

        This is CPU-bound work that should be run in a thread pool.

        Args:
            data: Original image bytes
            max_size: Maximum dimension (width or height)
            quality: JPEG quality (1-100)

        Returns:
            Thumbnail bytes or None if generation fails
        """
        try:
            with PILImage.open(io.BytesIO(data)) as img:
                # Convert to RGB if necessary (for PNG with transparency)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                # Calculate new size maintaining aspect ratio
                img.thumbnail((max_size, max_size), PILImage.Resampling.LANCZOS)

                # Save to buffer as JPEG
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=quality, optimize=True)
                return buffer.getvalue()
        except Exception as e:
            logger.warning(f"Thumbnail generation failed: {e}")
            return None

    @staticmethod
    async def generate_thumbnail_bytes(
        data: bytes,
        max_size: int = THUMBNAIL_MAX_SIZE,
        quality: int = THUMBNAIL_QUALITY,
    ) -> bytes | None:
        """
        Generate thumbnail bytes without blocking event loop.

        Args:
            data: Original image bytes
            max_size: Maximum dimension (width or height)
            quality: JPEG quality (1-100)

        Returns:
            Thumbnail bytes or None if generation fails
        """
        return await asyncio.to_thread(
            ThumbnailService._generate_thumbnail_sync,
            data,
            max_size,
            quality,
        )

    @staticmethod
    def get_thumbnail_key(image_id: str) -> str:
        """Generate thumbnail storage key from image ID."""
        return f"{THUMBNAIL_PREFIX}{image_id}_300.jpg"

    async def generate_and_store_thumbnail(self, image_id: str) -> bool:
        """
        Generate and store thumbnail for an image.

        This method is designed to be called from a background task.
        It fetches the original image, generates a thumbnail, stores it,
        and updates the database record.

        Args:
            image_id: The image ID to generate thumbnail for

        Returns:
            True if successful, False otherwise
        """
        async with self.session_factory() as db:
            try:
                # Get image metadata
                result = await db.execute(select(Image).where(Image.id == image_id))
                image = result.scalar_one_or_none()

                if not image:
                    logger.warning(f"Thumbnail generation: Image {image_id} not found")
                    return False

                # Skip if thumbnail already exists
                if image.thumbnail_key:
                    logger.debug(f"Thumbnail already exists for image {image_id}")
                    return True

                # Fetch original image from storage
                try:
                    original_data = await self.storage.get(image.storage_key)
                except FileNotFoundError:
                    logger.warning(
                        f"Thumbnail generation: Original file not found for image {image_id}"
                    )
                    return False

                # Generate thumbnail
                thumbnail_data = await self.generate_thumbnail_bytes(original_data)
                if not thumbnail_data:
                    logger.warning(f"Thumbnail generation failed for image {image_id}")
                    return False

                # Store thumbnail
                thumbnail_key = self.get_thumbnail_key(image_id)
                await self.storage.save(thumbnail_key, thumbnail_data, "image/jpeg")

                # Update database record
                await db.execute(
                    update(Image).where(Image.id == image_id).values(thumbnail_key=thumbnail_key)
                )
                await db.commit()

                # Invalidate cache so next fetch gets updated thumbnail_key
                if self.cache:
                    await self.cache.invalidate_image(image_id)

                logger.info(f"Thumbnail generated for image {image_id}: {thumbnail_key}")
                return True

            except Exception as e:
                logger.exception(f"Thumbnail generation error for image {image_id}: {e}")
                return False

    async def get_thumbnail(self, image_id: str) -> tuple[bytes, str] | None:
        """
        Get thumbnail for an image.

        Args:
            image_id: The image ID

        Returns:
            Tuple of (thumbnail_bytes, content_type) or None if not available
        """
        async with self.session_factory() as db:
            result = await db.execute(select(Image).where(Image.id == image_id))
            image = result.scalar_one_or_none()

            if not image:
                return None

            if not image.thumbnail_key:
                return None

            try:
                data = await self.storage.get(image.thumbnail_key)
                return data, "image/jpeg"
            except FileNotFoundError:
                return None

    async def delete_thumbnail(self, thumbnail_key: str) -> bool:
        """
        Delete a thumbnail from storage.

        Args:
            thumbnail_key: The thumbnail storage key

        Returns:
            True if successful, False otherwise
        """
        try:
            await self.storage.delete(thumbnail_key)
            return True
        except Exception as e:
            logger.warning(f"Failed to delete thumbnail {thumbnail_key}: {e}")
            return False
