"""Image service - business logic layer."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.schemas.image import ImageCreate
from app.services.storage_service import StorageService


class ImageService:
    """Service for image operations."""

    def __init__(self, db: AsyncSession, storage: StorageService):
        self.db = db
        self.storage = storage

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

        # Save to storage
        await self.storage.save(storage_key, data, content_type)

        # Create database record
        image = Image(
            filename=safe_filename,
            storage_key=storage_key,
            content_type=content_type,
            file_size=len(data),
            upload_ip=upload_ip,
        )

        self.db.add(image)
        await self.db.commit()
        await self.db.refresh(image)

        return image

    async def get_by_id(self, image_id: str) -> Image | None:
        """Get image metadata by ID."""
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        return result.scalar_one_or_none()

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
        image = await self.get_by_id(image_id)
        if not image:
            return False

        # Delete from storage (graceful - continue even if storage delete fails)
        try:
            await self.storage.delete(image.storage_key)
        except Exception:
            pass  # Log this in production

        # Delete from database
        await self.db.delete(image)
        await self.db.commit()

        return True
