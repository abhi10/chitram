"""Image service - business logic layer."""

import asyncio
import io
import logging
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from PIL import Image as PILImage
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.services.auth_service import AuthService
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
        return await asyncio.to_thread(ImageService._extract_dimensions_sync, data)

    async def upload(
        self,
        data: bytes,
        filename: str,
        content_type: str,
        upload_ip: str,
        user_id: str | None = None,
    ) -> tuple[Image, str | None]:
        """
        Upload a new image.

        Args:
            data: Image file content
            filename: Original filename
            content_type: MIME type
            upload_ip: Client IP address
            user_id: Authenticated user ID (None for anonymous)

        Returns:
            Tuple of (Created Image model, delete_token or None)
            delete_token is only returned for anonymous uploads
        """
        # Sanitize and generate keys
        safe_filename = self.sanitize_filename(filename)
        storage_key = self.generate_storage_key(safe_filename)

        # Extract image dimensions (non-blocking, runs in thread pool)
        dimensions = await self.get_image_dimensions(data)
        width, height = dimensions if dimensions else (None, None)

        # Generate delete token for anonymous uploads
        delete_token: str | None = None
        delete_token_hash: str | None = None
        if user_id is None:
            delete_token = AuthService.generate_delete_token()
            delete_token_hash = AuthService.hash_delete_token(delete_token)

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
            user_id=user_id,
            delete_token_hash=delete_token_hash,
        )

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        # Cache the newly uploaded image metadata
        if self.cache:
            await self.cache.set_image_metadata(image.id, self._image_to_dict(image))

        return image, delete_token

    async def list_recent(self, limit: int = 20, offset: int = 0) -> list[Image]:
        """
        List recent images ordered by creation date (newest first).

        Args:
            limit: Maximum number of images to return
            offset: Number of images to skip

        Returns:
            List of Image models
        """
        result = await self.db.execute(
            select(Image).order_by(desc(Image.created_at)).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def list_by_user(self, user_id: str) -> list[Image]:
        """
        List all images uploaded by a specific user.

        Args:
            user_id: User ID to filter by

        Returns:
            List of Image models ordered by creation date (newest first)
        """
        result = await self.db.execute(
            select(Image).where(Image.user_id == user_id).order_by(desc(Image.created_at))
        )
        return list(result.scalars().all())

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
                # Reconstruct Image model from cached dict with proper type conversion
                return self._dict_to_image(cached), "HIT"

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
            "user_id": image.user_id,
            "delete_token_hash": image.delete_token_hash,
            "thumbnail_key": image.thumbnail_key,
            "created_at": image.created_at.isoformat() if image.created_at else None,
        }

    @staticmethod
    def _dict_to_image(data: dict) -> Image:
        """
        Convert cached dict back to Image model.

        Handles type conversions (e.g., ISO string -> datetime) that are
        lost during JSON serialization in cache.
        """
        # Convert created_at from ISO string back to datetime
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            data["created_at"] = datetime.fromisoformat(created_at)

        return Image(**data)

    async def get_file(self, image_id: str) -> tuple[bytes, str, str] | None:
        """
        Get image file content.

        Returns:
            Tuple of (file_bytes, content_type, filename) or None if not found
        """
        image = await self.get_by_id(image_id)
        if not image:
            return None

        try:
            data = await self.storage.get(image.storage_key)
            return data, image.content_type, image.filename
        except FileNotFoundError:
            return None

    def can_delete(
        self,
        image: Image,
        user_id: str | None,
        delete_token: str | None,
    ) -> tuple[bool, str]:
        """
        Check if deletion is authorized.

        Args:
            image: The image to delete
            user_id: Authenticated user ID (None if anonymous)
            delete_token: Delete token for anonymous uploads

        Returns:
            Tuple of (authorized, reason)
        """
        # Authenticated user who owns the image
        if user_id and image.user_id == user_id:
            return True, "owner"

        # Anonymous image with valid delete token
        if (
            image.user_id is None
            and image.delete_token_hash
            and delete_token
            and AuthService.verify_delete_token(delete_token, image.delete_token_hash)
        ):
            return True, "token"

        # Forbidden cases
        if user_id and image.user_id and image.user_id != user_id:
            return False, "not_owner"

        if image.user_id is None and not delete_token:
            return False, "token_required"

        if image.user_id is None and delete_token:
            return False, "invalid_token"

        return False, "forbidden"

    async def delete(
        self,
        image_id: str,
        user_id: str | None = None,
        delete_token: str | None = None,
    ) -> tuple[bool, str]:
        """
        Delete an image with authorization check.

        Args:
            image_id: Image ID to delete
            user_id: Authenticated user ID (None if anonymous)
            delete_token: Delete token for anonymous uploads

        Returns:
            Tuple of (success, reason)
            - (True, "deleted") if deleted
            - (False, "not_found") if image doesn't exist
            - (False, "forbidden") if not authorized
        """
        # Skip cache when fetching for deletion to ensure we have fresh DB state
        image = await self.get_by_id(image_id, use_cache=False)
        if not image:
            return False, "not_found"

        # Check authorization
        authorized, reason = self.can_delete(image, user_id, delete_token)
        if not authorized:
            return False, reason

        # Delete from storage (graceful - continue even if storage delete fails)
        try:
            await self.storage.delete(image.storage_key)
        except Exception as e:
            # Log for orphan tracking but continue with DB deletion
            logger.warning(
                "Failed to delete storage file %s for image %s: %s. File may be orphaned.",
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

        return True, "deleted"
