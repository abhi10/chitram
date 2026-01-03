"""Unit tests for ThumbnailService."""

import io
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from PIL import Image as PILImage

from app.services.thumbnail_service import (
    THUMBNAIL_MAX_SIZE,
    THUMBNAIL_PREFIX,
    THUMBNAIL_QUALITY,
    ThumbnailService,
)


class TestThumbnailConfiguration:
    """Test thumbnail configuration constants."""

    def test_thumbnail_max_size_is_300(self):
        """Thumbnail max dimension should be 300px."""
        assert THUMBNAIL_MAX_SIZE == 300

    def test_thumbnail_quality_is_85(self):
        """Thumbnail quality should be 85%."""
        assert THUMBNAIL_QUALITY == 85

    def test_thumbnail_prefix(self):
        """Thumbnail prefix should be 'thumbs/'."""
        assert THUMBNAIL_PREFIX == "thumbs/"


class TestGetThumbnailKey:
    """Test thumbnail key generation."""

    def test_get_thumbnail_key_format(self):
        """Thumbnail key should have correct format."""
        image_id = "abc123"
        key = ThumbnailService.get_thumbnail_key(image_id)
        assert key == f"{THUMBNAIL_PREFIX}{image_id}_300.jpg"

    def test_get_thumbnail_key_different_ids(self):
        """Different image IDs should produce different keys."""
        key1 = ThumbnailService.get_thumbnail_key("image1")
        key2 = ThumbnailService.get_thumbnail_key("image2")
        assert key1 != key2


class TestGenerateThumbnailSync:
    """Test synchronous thumbnail generation."""

    @pytest.fixture
    def sample_jpeg_bytes(self) -> bytes:
        """Create a sample JPEG image."""
        img = PILImage.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    @pytest.fixture
    def sample_png_bytes(self) -> bytes:
        """Create a sample PNG image with alpha channel."""
        img = PILImage.new("RGBA", (800, 600), color=(0, 0, 255, 128))
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.read()

    @pytest.fixture
    def large_image_bytes(self) -> bytes:
        """Create a large image (1000x1000)."""
        img = PILImage.new("RGB", (1000, 1000), color="green")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    def test_generates_smaller_thumbnail(self, sample_jpeg_bytes: bytes):
        """Thumbnail should be smaller than max size."""
        result = ThumbnailService._generate_thumbnail_sync(sample_jpeg_bytes)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            assert img.size[0] <= THUMBNAIL_MAX_SIZE
            assert img.size[1] <= THUMBNAIL_MAX_SIZE

    def test_maintains_aspect_ratio(self, sample_jpeg_bytes: bytes):
        """Thumbnail should maintain original aspect ratio."""
        # Original is 800x600 (4:3 ratio)
        result = ThumbnailService._generate_thumbnail_sync(sample_jpeg_bytes)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            # Width should be 300, height should be 225 (4:3 ratio)
            assert img.size == (300, 225)

    def test_converts_png_to_jpeg(self, sample_png_bytes: bytes):
        """PNG should be converted to JPEG."""
        result = ThumbnailService._generate_thumbnail_sync(sample_png_bytes)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            assert img.format == "JPEG"
            # RGBA should be converted to RGB
            assert img.mode == "RGB"

    def test_large_image_resized(self, large_image_bytes: bytes):
        """Large image should be resized to fit max dimension."""
        result = ThumbnailService._generate_thumbnail_sync(large_image_bytes)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            assert img.size[0] <= THUMBNAIL_MAX_SIZE
            assert img.size[1] <= THUMBNAIL_MAX_SIZE

    def test_invalid_data_returns_none(self):
        """Invalid image data should return None."""
        result = ThumbnailService._generate_thumbnail_sync(b"not an image")
        assert result is None

    def test_empty_data_returns_none(self):
        """Empty data should return None."""
        result = ThumbnailService._generate_thumbnail_sync(b"")
        assert result is None

    def test_custom_max_size(self, sample_jpeg_bytes: bytes):
        """Custom max size should be respected."""
        result = ThumbnailService._generate_thumbnail_sync(sample_jpeg_bytes, max_size=150)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            assert img.size[0] <= 150
            assert img.size[1] <= 150


class TestGenerateThumbnailBytesAsync:
    """Test async thumbnail generation."""

    @pytest.fixture
    def sample_jpeg_bytes(self) -> bytes:
        """Create a sample JPEG image."""
        img = PILImage.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    @pytest.mark.asyncio
    async def test_generates_thumbnail_async(self, sample_jpeg_bytes: bytes):
        """Async method should generate thumbnail."""
        result = await ThumbnailService.generate_thumbnail_bytes(sample_jpeg_bytes)

        assert result is not None
        with PILImage.open(io.BytesIO(result)) as img:
            assert img.size[0] <= THUMBNAIL_MAX_SIZE
            assert img.size[1] <= THUMBNAIL_MAX_SIZE

    @pytest.mark.asyncio
    async def test_invalid_data_returns_none_async(self):
        """Invalid data should return None in async method."""
        result = await ThumbnailService.generate_thumbnail_bytes(b"not an image")
        assert result is None

    @pytest.mark.asyncio
    async def test_uses_thread_pool(self, sample_jpeg_bytes: bytes):
        """Async method should use thread pool for CPU-bound work."""
        with patch("asyncio.to_thread") as mock_to_thread:
            mock_to_thread.return_value = b"fake thumbnail"

            await ThumbnailService.generate_thumbnail_bytes(sample_jpeg_bytes)

            mock_to_thread.assert_called_once()


class TestThumbnailServiceInit:
    """Test ThumbnailService initialization."""

    def test_init_stores_storage(self):
        """Service should store storage reference."""
        mock_storage = MagicMock()
        mock_session_factory = MagicMock()

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        assert service.storage == mock_storage

    def test_init_stores_session_factory(self):
        """Service should store session factory reference."""
        mock_storage = MagicMock()
        mock_session_factory = MagicMock()

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        assert service.session_factory == mock_session_factory


class TestGenerateAndStoreThumbnail:
    """Test full thumbnail generation and storage workflow."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage service."""
        storage = MagicMock()
        storage.get = AsyncMock()
        storage.save = AsyncMock()
        return storage

    @pytest.fixture
    def sample_jpeg_bytes(self) -> bytes:
        """Create a sample JPEG image."""
        img = PILImage.new("RGB", (800, 600), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    @pytest.mark.asyncio
    async def test_returns_false_for_missing_image(self, mock_storage):
        """Should return False if image not found in database."""
        # Create mock session that returns no image
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.generate_and_store_thumbnail("nonexistent-id")
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_if_thumbnail_exists(self, mock_storage):
        """Should return True if thumbnail already exists."""
        # Create mock image with existing thumbnail
        mock_image = MagicMock()
        mock_image.thumbnail_key = "thumbs/existing_300.jpg"

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_image
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.generate_and_store_thumbnail("image-id")
        assert result is True
        mock_storage.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_false_if_original_not_found(self, mock_storage):
        """Should return False if original file not found in storage."""
        # Create mock image without thumbnail
        mock_image = MagicMock()
        mock_image.id = "image-id"
        mock_image.thumbnail_key = None
        mock_image.storage_key = "images/image.jpg"

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_image
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        mock_storage.get = AsyncMock(side_effect=FileNotFoundError())

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.generate_and_store_thumbnail("image-id")
        assert result is False


class TestDeleteThumbnail:
    """Test thumbnail deletion."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage service."""
        storage = MagicMock()
        storage.delete = AsyncMock()
        return storage

    @pytest.mark.asyncio
    async def test_delete_success(self, mock_storage):
        """Should return True on successful deletion."""
        mock_storage.delete = AsyncMock(return_value=True)
        mock_session_factory = MagicMock()

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.delete_thumbnail("thumbs/image_300.jpg")
        assert result is True
        mock_storage.delete.assert_called_once_with("thumbs/image_300.jpg")

    @pytest.mark.asyncio
    async def test_delete_failure(self, mock_storage):
        """Should return False on deletion failure."""
        mock_storage.delete = AsyncMock(side_effect=Exception("Storage error"))
        mock_session_factory = MagicMock()

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.delete_thumbnail("thumbs/image_300.jpg")
        assert result is False


class TestGetThumbnail:
    """Test thumbnail retrieval."""

    @pytest.fixture
    def mock_storage(self):
        """Create mock storage service."""
        storage = MagicMock()
        storage.get = AsyncMock()
        return storage

    @pytest.fixture
    def thumbnail_bytes(self) -> bytes:
        """Create sample thumbnail bytes."""
        img = PILImage.new("RGB", (300, 225), color="red")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG")
        buffer.seek(0)
        return buffer.read()

    @pytest.mark.asyncio
    async def test_returns_none_for_missing_image(self, mock_storage):
        """Should return None if image not found."""
        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.get_thumbnail("nonexistent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_if_thumbnail_not_ready(self, mock_storage):
        """Should return None if thumbnail_key is None."""
        mock_image = MagicMock()
        mock_image.thumbnail_key = None

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_image
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.get_thumbnail("image-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_thumbnail_data(self, mock_storage, thumbnail_bytes):
        """Should return thumbnail data and content type."""
        mock_image = MagicMock()
        mock_image.thumbnail_key = "thumbs/image_300.jpg"

        mock_session = MagicMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_image
        mock_session.execute = AsyncMock(return_value=mock_result)

        mock_session_factory = MagicMock(return_value=mock_session)

        mock_storage.get = AsyncMock(return_value=thumbnail_bytes)

        service = ThumbnailService(
            storage=mock_storage,
            session_factory=mock_session_factory,
        )

        result = await service.get_thumbnail("image-id")
        assert result is not None
        data, content_type = result
        assert data == thumbnail_bytes
        assert content_type == "image/jpeg"
