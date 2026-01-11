"""Unit tests for TagService."""

import pytest
from sqlalchemy import select

from app.models.image import Image
from app.models.tag import Tag
from app.services.tag_service import TagService


class TestGetOrCreateTag:
    """Test get_or_create_tag method."""

    @pytest.mark.asyncio
    async def test_creates_new_tag(self, test_db):
        """Should create a new tag if it doesn't exist."""
        service = TagService(test_db)

        tag = await service.get_or_create_tag("sunset", category="scene")

        assert tag.id is not None
        assert tag.name == "sunset"
        assert tag.category == "scene"
        assert tag.created_at is not None

    @pytest.mark.asyncio
    async def test_returns_existing_tag(self, test_db):
        """Should return existing tag instead of creating duplicate."""
        service = TagService(test_db)

        # Create first tag
        tag1 = await service.get_or_create_tag("mountain", category="object")
        tag1_id = tag1.id

        # Try to create same tag again
        tag2 = await service.get_or_create_tag("mountain", category="scene")  # Different category

        assert tag2.id == tag1_id  # Same ID
        assert tag2.name == "mountain"
        assert tag2.category == "object"  # Original category preserved

    @pytest.mark.asyncio
    async def test_normalizes_tag_name(self, test_db):
        """Should normalize tag name (lowercase, trim)."""
        service = TagService(test_db)

        # Create with uppercase and whitespace
        tag = await service.get_or_create_tag("  SUNSET  ", category="scene")

        assert tag.name == "sunset"

        # Try to create with different case - should return same tag
        tag2 = await service.get_or_create_tag("SuNsEt")

        assert tag2.id == tag.id

    @pytest.mark.asyncio
    async def test_handles_category_none(self, test_db):
        """Should allow NULL category."""
        service = TagService(test_db)

        tag = await service.get_or_create_tag("blue")

        assert tag.name == "blue"
        assert tag.category is None


class TestAddTagToImage:
    """Test add_tag_to_image method."""

    @pytest.mark.asyncio
    async def test_adds_tag_to_image(self, test_db):
        """Should successfully add tag to image."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add tag
        image_tag = await service.add_tag_to_image(
            image.id, "nature", source="user", category="scene"
        )

        assert image_tag.image_id == image.id
        assert image_tag.source == "user"
        assert image_tag.confidence is None

    @pytest.mark.asyncio
    async def test_creates_tag_if_not_exists(self, test_db):
        """Should create tag if it doesn't exist."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add tag (tag doesn't exist yet)
        await service.add_tag_to_image(image.id, "newdtag", category="object")

        # Verify tag was created
        result = await test_db.execute(select(Tag).where(Tag.name == "newdtag"))
        tag = result.scalar_one_or_none()

        assert tag is not None
        assert tag.name == "newdtag"

    @pytest.mark.asyncio
    async def test_ai_tag_with_confidence(self, test_db):
        """Should store confidence for AI tags."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add AI tag with confidence
        image_tag = await service.add_tag_to_image(image.id, "cat", source="ai", confidence=95)

        assert image_tag.source == "ai"
        assert image_tag.confidence == 95

    @pytest.mark.asyncio
    async def test_raises_error_if_image_not_found(self, test_db):
        """Should raise ValueError if image doesn't exist."""
        service = TagService(test_db)

        with pytest.raises(ValueError, match="Image .* not found"):
            await service.add_tag_to_image("nonexistent-id", "tag", source="user")

    @pytest.mark.asyncio
    async def test_raises_error_if_tag_already_exists(self, test_db):
        """Should raise ValueError if tag already added to image."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add tag first time
        await service.add_tag_to_image(image.id, "duplicate", source="user")

        # Try to add same tag again
        with pytest.raises(ValueError, match="already exists"):
            await service.add_tag_to_image(image.id, "duplicate", source="ai")


class TestRemoveTagFromImage:
    """Test remove_tag_from_image method."""

    @pytest.mark.asyncio
    async def test_removes_tag_from_image(self, test_db):
        """Should successfully remove tag from image."""
        service = TagService(test_db)

        # Create image and add tag
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        await service.add_tag_to_image(image.id, "removeme", source="user")

        # Remove tag
        result = await service.remove_tag_from_image(image.id, "removeme")

        assert result is True

        # Verify tag was removed
        image_tags = await service.get_image_tags(image.id)
        assert len(image_tags) == 0

    @pytest.mark.asyncio
    async def test_returns_false_if_tag_not_found(self, test_db):
        """Should return False if tag doesn't exist."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Try to remove non-existent tag
        result = await service.remove_tag_from_image(image.id, "nonexistent")

        assert result is False

    @pytest.mark.asyncio
    async def test_returns_false_if_association_not_exists(self, test_db):
        """Should return False if tag exists but not associated with image."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)

        # Create tag (not associated with image)
        tag = Tag(name="orphan", category="test")
        test_db.add(tag)

        await test_db.commit()

        # Try to remove tag that's not associated
        result = await service.remove_tag_from_image(image.id, "orphan")

        assert result is False

    @pytest.mark.asyncio
    async def test_normalizes_tag_name_when_removing(self, test_db):
        """Should normalize tag name (case-insensitive removal)."""
        service = TagService(test_db)

        # Create image and add tag
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        await service.add_tag_to_image(image.id, "sunset", source="user")

        # Remove with different case
        result = await service.remove_tag_from_image(image.id, "SUNSET")

        assert result is True


class TestGetImageTags:
    """Test get_image_tags method."""

    @pytest.mark.asyncio
    async def test_returns_all_tags_for_image(self, test_db):
        """Should return all tags associated with an image."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add multiple tags
        await service.add_tag_to_image(image.id, "nature", source="user")
        await service.add_tag_to_image(image.id, "sunset", source="ai", confidence=85)
        await service.add_tag_to_image(image.id, "mountain", source="user")

        # Get tags
        tags = await service.get_image_tags(image.id)

        assert len(tags) == 3
        tag_names = {tag.name for tag in tags}
        assert tag_names == {"nature", "sunset", "mountain"}

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_tags(self, test_db):
        """Should return empty list if image has no tags."""
        service = TagService(test_db)

        # Create image without tags
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Get tags
        tags = await service.get_image_tags(image.id)

        assert len(tags) == 0

    @pytest.mark.asyncio
    async def test_returns_tag_details_with_metadata(self, test_db):
        """Should return tag details including source and confidence."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add AI tag
        await service.add_tag_to_image(
            image.id, "cat", source="ai", confidence=92, category="object"
        )

        # Get tags
        tags = await service.get_image_tags(image.id)

        assert len(tags) == 1
        assert tags[0].name == "cat"
        assert tags[0].category == "object"
        assert tags[0].source == "ai"
        assert tags[0].confidence == 92


class TestGetPopularTags:
    """Test get_popular_tags method."""

    @pytest.mark.asyncio
    async def test_returns_tags_ordered_by_count(self, test_db):
        """Should return tags ordered by usage count (descending)."""
        service = TagService(test_db)

        # Create multiple images
        images = []
        for i in range(3):
            image = Image(
                filename=f"test{i}.jpg",
                storage_key=f"test-key-{i}",
                content_type="image/jpeg",
                file_size=1024,
                upload_ip="127.0.0.1",
            )
            test_db.add(image)
            images.append(image)

        await test_db.commit()
        for img in images:
            await test_db.refresh(img)

        # Add tags with different frequencies
        # "popular": 3 times
        # "common": 2 times
        # "rare": 1 time
        await service.add_tag_to_image(images[0].id, "popular", source="user")
        await service.add_tag_to_image(images[1].id, "popular", source="user")
        await service.add_tag_to_image(images[2].id, "popular", source="user")

        await service.add_tag_to_image(images[0].id, "common", source="user")
        await service.add_tag_to_image(images[1].id, "common", source="user")

        await service.add_tag_to_image(images[0].id, "rare", source="user")

        # Get popular tags
        popular = await service.get_popular_tags(limit=10)

        assert len(popular) == 3
        assert popular[0].name == "popular"
        assert popular[0].count == 3
        assert popular[1].name == "common"
        assert popular[1].count == 2
        assert popular[2].name == "rare"
        assert popular[2].count == 1

    @pytest.mark.asyncio
    async def test_respects_limit(self, test_db):
        """Should respect the limit parameter."""
        service = TagService(test_db)

        # Create image
        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Add 5 tags
        for i in range(5):
            await service.add_tag_to_image(image.id, f"tag{i}", source="user")

        # Get with limit=3
        popular = await service.get_popular_tags(limit=3)

        assert len(popular) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_if_no_tags(self, test_db):
        """Should return empty list if no tags exist."""
        service = TagService(test_db)

        popular = await service.get_popular_tags(limit=10)

        assert len(popular) == 0


class TestSearchTags:
    """Test search_tags method."""

    @pytest.mark.asyncio
    async def test_finds_tags_by_prefix(self, test_db):
        """Should find tags matching prefix."""
        service = TagService(test_db)

        # Create tags
        await service.get_or_create_tag("sunset")
        await service.get_or_create_tag("sunrise")
        await service.get_or_create_tag("mountain")

        # Search for "sun" prefix
        results = await service.search_tags("sun", limit=10)

        assert len(results) == 2
        tag_names = {tag.name for tag in results}
        assert tag_names == {"sunset", "sunrise"}

    @pytest.mark.asyncio
    async def test_search_is_case_insensitive(self, test_db):
        """Should be case-insensitive."""
        service = TagService(test_db)

        await service.get_or_create_tag("mountain")

        results = await service.search_tags("MOUN", limit=10)

        assert len(results) == 1
        assert results[0].name == "mountain"

    @pytest.mark.asyncio
    async def test_respects_limit(self, test_db):
        """Should respect limit parameter."""
        service = TagService(test_db)

        # Create 5 tags with same prefix
        for i in range(5):
            await service.get_or_create_tag(f"test{i}")

        results = await service.search_tags("test", limit=3)

        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_for_empty_query(self, test_db):
        """Should return empty list for empty query."""
        service = TagService(test_db)

        await service.get_or_create_tag("sometag")

        results = await service.search_tags("", limit=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_matches(self, test_db):
        """Should return empty list if no tags match."""
        service = TagService(test_db)

        await service.get_or_create_tag("sunset")

        results = await service.search_tags("mountain", limit=10)

        assert len(results) == 0


class TestGetTagByName:
    """Test get_tag_by_name method."""

    @pytest.mark.asyncio
    async def test_finds_existing_tag(self, test_db):
        """Should find tag by name."""
        service = TagService(test_db)

        await service.get_or_create_tag("sunset", category="scene")

        tag = await service.get_tag_by_name("sunset")

        assert tag is not None
        assert tag.name == "sunset"
        assert tag.category == "scene"

    @pytest.mark.asyncio
    async def test_returns_none_if_not_found(self, test_db):
        """Should return None if tag doesn't exist."""
        service = TagService(test_db)

        tag = await service.get_tag_by_name("nonexistent")

        assert tag is None

    @pytest.mark.asyncio
    async def test_is_case_insensitive(self, test_db):
        """Should be case-insensitive."""
        service = TagService(test_db)

        await service.get_or_create_tag("mountain")

        tag = await service.get_tag_by_name("MOUNTAIN")

        assert tag is not None
        assert tag.name == "mountain"


class TestGetImagesByTag:
    """Test get_images_by_tag method."""

    @pytest.mark.asyncio
    async def test_finds_images_with_tag(self, test_db):
        """Should find all images with specified tag."""
        service = TagService(test_db)

        # Create 3 images
        images = []
        for i in range(3):
            image = Image(
                filename=f"test{i}.jpg",
                storage_key=f"test-key-{i}",
                content_type="image/jpeg",
                file_size=1024,
                upload_ip="127.0.0.1",
            )
            test_db.add(image)
            images.append(image)

        await test_db.commit()
        for img in images:
            await test_db.refresh(img)

        # Add "sunset" tag to 2 images
        await service.add_tag_to_image(images[0].id, "sunset", source="user")
        await service.add_tag_to_image(images[1].id, "sunset", source="user")

        # Add different tag to 3rd image
        await service.add_tag_to_image(images[2].id, "mountain", source="user")

        # Get images with "sunset" tag
        results = await service.get_images_by_tag("sunset", limit=10)

        assert len(results) == 2
        result_ids = {img.id for img in results}
        assert result_ids == {images[0].id, images[1].id}

    @pytest.mark.asyncio
    async def test_returns_empty_for_nonexistent_tag(self, test_db):
        """Should return empty list if tag doesn't exist."""
        service = TagService(test_db)

        results = await service.get_images_by_tag("nonexistent", limit=10)

        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_respects_limit_and_offset(self, test_db):
        """Should respect limit and offset parameters."""
        service = TagService(test_db)

        # Create 5 images with same tag
        images = []
        for i in range(5):
            image = Image(
                filename=f"test{i}.jpg",
                storage_key=f"test-key-{i}",
                content_type="image/jpeg",
                file_size=1024,
                upload_ip="127.0.0.1",
            )
            test_db.add(image)
            images.append(image)

        await test_db.commit()
        for img in images:
            await test_db.refresh(img)
            await service.add_tag_to_image(img.id, "common", source="user")

        # Get with limit=2, offset=2
        results = await service.get_images_by_tag("common", limit=2, offset=2)

        assert len(results) == 2


class TestEdgeCases:
    """Test edge cases and special scenarios."""

    @pytest.mark.asyncio
    async def test_tag_name_with_hyphens(self, test_db):
        """Should allow hyphens in tag names."""
        service = TagService(test_db)

        tag = await service.get_or_create_tag("mountain-landscape")

        assert tag.name == "mountain-landscape"

    @pytest.mark.asyncio
    async def test_tag_name_with_spaces(self, test_db):
        """Should allow spaces in tag names."""
        service = TagService(test_db)

        tag = await service.get_or_create_tag("blue sky")

        assert tag.name == "blue sky"

    @pytest.mark.asyncio
    async def test_confidence_zero(self, test_db):
        """Should allow confidence=0."""
        service = TagService(test_db)

        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        image_tag = await service.add_tag_to_image(image.id, "uncertain", source="ai", confidence=0)

        assert image_tag.confidence == 0

    @pytest.mark.asyncio
    async def test_confidence_hundred(self, test_db):
        """Should allow confidence=100."""
        service = TagService(test_db)

        image = Image(
            filename="test.jpg",
            storage_key="test-key",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        image_tag = await service.add_tag_to_image(image.id, "certain", source="ai", confidence=100)

        assert image_tag.confidence == 100
