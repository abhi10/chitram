"""Unit tests for Tag and ImageTag models."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.image import Image
from app.models.tag import ImageTag, Tag


@pytest.mark.asyncio
async def test_create_tag(test_db):
    """Test creating a tag."""
    tag = Tag(
        name="sunset",
        category="scene",
    )
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)

    assert tag.id is not None
    assert tag.name == "sunset"
    assert tag.category == "scene"
    assert tag.created_at is not None


@pytest.mark.asyncio
async def test_tag_name_must_be_unique(test_db):
    """Test that tag names must be unique."""
    # Create first tag
    tag1 = Tag(name="mountain", category="object")
    test_db.add(tag1)
    await test_db.commit()

    # Try to create second tag with same name
    tag2 = Tag(name="mountain", category="scene")
    test_db.add(tag2)

    with pytest.raises(IntegrityError):
        await test_db.commit()


@pytest.mark.asyncio
async def test_tag_category_is_optional(test_db):
    """Test that tag category is optional."""
    tag = Tag(name="blue")
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)

    assert tag.id is not None
    assert tag.name == "blue"
    assert tag.category is None


@pytest.mark.asyncio
async def test_create_image_tag_relationship(test_db):
    """Test creating an image-tag relationship."""
    # Create image
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    test_db.add(image)

    # Create tag
    tag = Tag(name="nature", category="scene")
    test_db.add(tag)

    await test_db.commit()
    await test_db.refresh(image)
    await test_db.refresh(tag)

    # Create image-tag relationship
    image_tag = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="user",
        confidence=None,
    )
    test_db.add(image_tag)
    await test_db.commit()
    await test_db.refresh(image_tag)

    assert image_tag.id is not None
    assert image_tag.image_id == image.id
    assert image_tag.tag_id == tag.id
    assert image_tag.source == "user"
    assert image_tag.confidence is None
    assert image_tag.created_at is not None


@pytest.mark.asyncio
async def test_ai_tag_with_confidence(test_db):
    """Test creating an AI-generated tag with confidence score."""
    # Create image and tag
    image = Image(
        filename="cat.jpg",
        storage_key="cat-key",
        content_type="image/jpeg",
        file_size=2048,
        upload_ip="127.0.0.1",
    )
    tag = Tag(name="cat", category="object")
    test_db.add_all([image, tag])
    await test_db.commit()

    # Create AI tag with confidence
    image_tag = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="ai",
        confidence=95,
    )
    test_db.add(image_tag)
    await test_db.commit()
    await test_db.refresh(image_tag)

    assert image_tag.source == "ai"
    assert image_tag.confidence == 95


@pytest.mark.asyncio
async def test_image_tag_unique_constraint(test_db):
    """Test that the same tag cannot be added twice to the same image."""
    # Create image and tag
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    tag = Tag(name="duplicate", category="test")
    test_db.add_all([image, tag])
    await test_db.commit()

    # Add tag to image first time
    image_tag1 = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="user",
    )
    test_db.add(image_tag1)
    await test_db.commit()

    # Try to add same tag to same image again
    image_tag2 = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="ai",
        confidence=80,
    )
    test_db.add(image_tag2)

    with pytest.raises(IntegrityError):
        await test_db.commit()


@pytest.mark.asyncio
async def test_tag_cascade_delete(test_db):
    """Test that deleting a tag removes associated image_tags."""
    # Create image and tag
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    tag = Tag(name="temporary", category="test")
    test_db.add_all([image, tag])
    await test_db.commit()

    # Create image-tag relationship
    image_tag = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="user",
    )
    test_db.add(image_tag)
    await test_db.commit()

    # Verify image_tag exists
    result = await test_db.execute(select(ImageTag).where(ImageTag.image_id == image.id))
    assert result.scalar_one_or_none() is not None

    # Delete tag
    await test_db.delete(tag)
    await test_db.commit()

    # Verify image_tag was cascade deleted
    result = await test_db.execute(select(ImageTag).where(ImageTag.image_id == image.id))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_image_cascade_delete(test_db):
    """Test that deleting an image removes associated image_tags."""
    # Create image and tag
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    tag = Tag(name="persistent", category="test")
    test_db.add_all([image, tag])
    await test_db.commit()

    # Create image-tag relationship
    image_tag = ImageTag(
        image_id=image.id,
        tag_id=tag.id,
        source="user",
    )
    test_db.add(image_tag)
    await test_db.commit()

    # Delete image
    await test_db.delete(image)
    await test_db.commit()

    # Verify image_tag was cascade deleted
    result = await test_db.execute(select(ImageTag).where(ImageTag.tag_id == tag.id))
    assert result.scalar_one_or_none() is None

    # Verify tag still exists
    result = await test_db.execute(select(Tag).where(Tag.id == tag.id))
    assert result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_tag_relationship_loading(test_db):
    """Test that tag relationships work correctly."""
    # Create image and tags
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    tag1 = Tag(name="tag1", category="scene")
    tag2 = Tag(name="tag2", category="object")
    test_db.add_all([image, tag1, tag2])
    await test_db.commit()

    # Create relationships
    image_tag1 = ImageTag(image_id=image.id, tag_id=tag1.id, source="ai", confidence=90)
    image_tag2 = ImageTag(image_id=image.id, tag_id=tag2.id, source="user")
    test_db.add_all([image_tag1, image_tag2])
    await test_db.commit()

    # Query to verify relationships exist
    result = await test_db.execute(select(ImageTag).where(ImageTag.image_id == image.id))
    image_tags = result.scalars().all()

    # Verify we have 2 image_tags associated with this image
    assert len(image_tags) == 2
    assert image_tags[0].image_id == image.id
    assert image_tags[1].image_id == image.id


@pytest.mark.asyncio
async def test_tag_name_normalization(test_db):
    """Test edge cases for tag names."""
    # Tag names should handle special characters, spaces, etc.
    tag = Tag(name="mountain-landscape", category="scene")
    test_db.add(tag)
    await test_db.commit()
    await test_db.refresh(tag)

    assert tag.name == "mountain-landscape"


@pytest.mark.asyncio
async def test_confidence_range(test_db):
    """Test that confidence can be null or 0-100."""
    image = Image(
        filename="test.jpg",
        storage_key="test-key",
        content_type="image/jpeg",
        file_size=1024,
        upload_ip="127.0.0.1",
    )
    tag = Tag(name="test", category="test")
    test_db.add_all([image, tag])
    await test_db.commit()

    # Test edge cases for confidence
    test_cases = [
        (None, "user"),  # User tags have no confidence
        (0, "ai"),  # AI with 0% confidence
        (100, "ai"),  # AI with 100% confidence
        (50, "ai"),  # AI with 50% confidence
    ]

    for i, (confidence, source) in enumerate(test_cases):
        # Create new image for each test to avoid unique constraint
        img = Image(
            filename=f"test{i}.jpg",
            storage_key=f"test-key-{i}",
            content_type="image/jpeg",
            file_size=1024,
            upload_ip="127.0.0.1",
        )
        test_db.add(img)
        await test_db.commit()
        await test_db.refresh(img)

        image_tag = ImageTag(
            image_id=img.id,
            tag_id=tag.id,
            source=source,
            confidence=confidence,
        )
        test_db.add(image_tag)
        await test_db.commit()
        await test_db.refresh(image_tag)

        assert image_tag.confidence == confidence
        assert image_tag.source == source
