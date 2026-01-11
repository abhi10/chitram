"""Tag service - business logic layer for tag operations."""

import logging
from typing import TYPE_CHECKING

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.image import Image
from app.models.tag import ImageTag, Tag

if TYPE_CHECKING:
    from app.schemas.tag import ImageTagResponse, TagWithCount

logger = logging.getLogger(__name__)


class TagService:
    """Service for tag operations."""

    def __init__(self, db: AsyncSession):
        """Initialize tag service.

        Args:
            db: SQLAlchemy async session
        """
        self.db = db

    async def get_or_create_tag(self, name: str, category: str | None = None) -> Tag:
        """Get existing tag or create new one (idempotent).

        Uses PostgreSQL INSERT ... ON CONFLICT to handle race conditions.

        Args:
            name: Tag name (will be normalized: lowercase, trimmed)
            category: Optional tag category

        Returns:
            Tag instance (either existing or newly created)
        """
        # Normalize name
        normalized_name = name.lower().strip()

        # PostgreSQL-specific upsert
        stmt = insert(Tag).values(name=normalized_name, category=category)
        stmt = stmt.on_conflict_do_nothing(index_elements=["name"])

        await self.db.execute(stmt)
        await self.db.commit()

        # Fetch the tag (either just created or existing)
        result = await self.db.execute(select(Tag).where(Tag.name == normalized_name))
        return result.scalar_one()

    async def add_tag_to_image(
        self,
        image_id: str,
        tag_name: str,
        source: str = "user",
        confidence: int | None = None,
        category: str | None = None,
    ) -> ImageTag:
        """Add a tag to an image.

        Creates tag if it doesn't exist. Handles duplicate gracefully.

        Args:
            image_id: Image UUID
            tag_name: Tag name
            source: 'ai' or 'user' (default: 'user')
            confidence: Confidence score 0-100 for AI tags, None for user tags
            category: Optional tag category

        Returns:
            ImageTag instance

        Raises:
            ValueError: If image doesn't exist or tag already exists for image
        """
        # Verify image exists
        result = await self.db.execute(select(Image).where(Image.id == image_id))
        image = result.scalar_one_or_none()
        if not image:
            raise ValueError(f"Image {image_id} not found")

        # Get or create tag
        tag = await self.get_or_create_tag(tag_name, category)

        # Check if tag already exists for this image
        result = await self.db.execute(
            select(ImageTag).where(ImageTag.image_id == image_id, ImageTag.tag_id == tag.id)
        )
        existing = result.scalar_one_or_none()

        if existing:
            raise ValueError(f"Tag '{tag_name}' already exists for image {image_id}")

        # Create image-tag association
        image_tag = ImageTag(
            image_id=image_id,
            tag_id=tag.id,
            source=source,
            confidence=confidence,
        )

        self.db.add(image_tag)
        await self.db.commit()
        await self.db.refresh(image_tag)

        return image_tag

    async def remove_tag_from_image(self, image_id: str, tag_name: str) -> bool:
        """Remove a tag from an image.

        Args:
            image_id: Image UUID
            tag_name: Tag name (case-insensitive)

        Returns:
            True if tag was removed, False if tag wasn't associated with image
        """
        # Normalize tag name
        normalized_name = tag_name.lower().strip()

        # Find the tag
        result = await self.db.execute(select(Tag).where(Tag.name == normalized_name))
        tag = result.scalar_one_or_none()

        if not tag:
            return False  # Tag doesn't exist at all

        # Find and delete the image-tag association
        result = await self.db.execute(
            select(ImageTag).where(ImageTag.image_id == image_id, ImageTag.tag_id == tag.id)
        )
        image_tag = result.scalar_one_or_none()

        if not image_tag:
            return False  # Association doesn't exist

        await self.db.delete(image_tag)
        await self.db.commit()

        return True

    async def get_image_tags(self, image_id: str) -> list["ImageTagResponse"]:
        """Get all tags for an image.

        Args:
            image_id: Image UUID

        Returns:
            List of ImageTagResponse objects with tag details and metadata
        """
        # Query with join to get tag details
        stmt = (
            select(ImageTag, Tag)
            .join(Tag, ImageTag.tag_id == Tag.id)
            .where(ImageTag.image_id == image_id)
            .order_by(Tag.name)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Build response objects
        from app.schemas.tag import ImageTagResponse

        return [
            ImageTagResponse(
                name=tag.name,
                category=tag.category,
                source=image_tag.source,
                confidence=image_tag.confidence,
            )
            for image_tag, tag in rows
        ]

    async def get_popular_tags(self, limit: int = 20) -> list["TagWithCount"]:
        """Get most popular tags by usage count.

        Args:
            limit: Maximum number of tags to return (default: 20)

        Returns:
            List of TagWithCount objects ordered by usage count (descending)
        """
        # Query with count aggregation
        stmt = (
            select(
                Tag.name,
                Tag.category,
                func.count(ImageTag.id).label("count"),
            )
            .join(ImageTag, Tag.id == ImageTag.tag_id)
            .group_by(Tag.id, Tag.name, Tag.category)
            .order_by(func.count(ImageTag.id).desc())
            .limit(limit)
        )

        result = await self.db.execute(stmt)
        rows = result.all()

        # Build response objects
        from app.schemas.tag import TagWithCount

        return [
            TagWithCount(name=name, category=category, count=count)
            for name, category, count in rows
        ]

    async def search_tags(self, query: str, limit: int = 10) -> list[Tag]:
        """Search tags by name prefix for autocomplete.

        Args:
            query: Search query (case-insensitive prefix match)
            limit: Maximum number of results (default: 10)

        Returns:
            List of Tag objects matching the query
        """
        # Normalize query
        normalized_query = query.lower().strip()

        if not normalized_query:
            return []

        # Prefix search with LIKE
        stmt = (
            select(Tag).where(Tag.name.like(f"{normalized_query}%")).order_by(Tag.name).limit(limit)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_tag_by_name(self, name: str) -> Tag | None:
        """Get a tag by name.

        Args:
            name: Tag name (case-insensitive)

        Returns:
            Tag instance or None if not found
        """
        normalized_name = name.lower().strip()

        result = await self.db.execute(select(Tag).where(Tag.name == normalized_name))
        return result.scalar_one_or_none()

    async def get_images_by_tag(
        self, tag_name: str, limit: int = 20, offset: int = 0
    ) -> list[Image]:
        """Get images that have a specific tag.

        Args:
            tag_name: Tag name to search for
            limit: Maximum number of images to return
            offset: Number of images to skip (for pagination)

        Returns:
            List of Image objects with the specified tag
        """
        # Normalize tag name
        normalized_name = tag_name.lower().strip()

        # Find the tag
        tag = await self.get_tag_by_name(normalized_name)
        if not tag:
            return []

        # Query images with this tag
        stmt = (
            select(Image)
            .join(ImageTag, Image.id == ImageTag.image_id)
            .where(ImageTag.tag_id == tag.id)
            .order_by(Image.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
