"""Unit tests for ImageService cache serialization/deserialization.

These tests verify that Image models survive the cache round-trip
with proper type preservation (especially datetime fields).
"""

from datetime import UTC, datetime
from unittest.mock import MagicMock

from app.models.image import Image
from app.services.image_service import ImageService


class TestImageCacheSerialization:
    """Tests for _image_to_dict and _dict_to_image methods."""

    def test_image_to_dict_serializes_datetime_as_iso_string(self):
        """created_at should be serialized as ISO format string."""
        now = datetime(2025, 1, 3, 12, 30, 45, tzinfo=UTC)
        image = MagicMock(spec=Image)
        image.id = "test-id"
        image.filename = "test.jpg"
        image.storage_key = "abc123.jpg"
        image.content_type = "image/jpeg"
        image.file_size = 1024
        image.upload_ip = "127.0.0.1"
        image.width = 100
        image.height = 100
        image.user_id = None
        image.delete_token_hash = None
        image.thumbnail_key = None
        image.created_at = now

        result = ImageService._image_to_dict(image)

        assert result["created_at"] == "2025-01-03T12:30:45+00:00"
        assert isinstance(result["created_at"], str)

    def test_image_to_dict_handles_none_created_at(self):
        """Should handle None created_at gracefully."""
        image = MagicMock(spec=Image)
        image.id = "test-id"
        image.filename = "test.jpg"
        image.storage_key = "abc123.jpg"
        image.content_type = "image/jpeg"
        image.file_size = 1024
        image.upload_ip = "127.0.0.1"
        image.width = None
        image.height = None
        image.user_id = None
        image.delete_token_hash = None
        image.thumbnail_key = None
        image.created_at = None

        result = ImageService._image_to_dict(image)

        assert result["created_at"] is None

    def test_dict_to_image_converts_iso_string_to_datetime(self):
        """ISO string should be converted back to datetime object."""
        data = {
            "id": "test-id",
            "filename": "test.jpg",
            "storage_key": "abc123.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "upload_ip": "127.0.0.1",
            "width": 100,
            "height": 100,
            "user_id": None,
            "delete_token_hash": None,
            "thumbnail_key": None,
            "created_at": "2025-01-03T12:30:45",
        }

        result = ImageService._dict_to_image(data)

        assert isinstance(result.created_at, datetime)
        assert result.created_at.year == 2025
        assert result.created_at.month == 1
        assert result.created_at.day == 3
        assert result.created_at.hour == 12
        assert result.created_at.minute == 30

    def test_dict_to_image_handles_none_created_at(self):
        """Should handle None created_at gracefully."""
        data = {
            "id": "test-id",
            "filename": "test.jpg",
            "storage_key": "abc123.jpg",
            "content_type": "image/jpeg",
            "file_size": 1024,
            "upload_ip": "127.0.0.1",
            "width": None,
            "height": None,
            "user_id": None,
            "delete_token_hash": None,
            "thumbnail_key": None,
            "created_at": None,
        }

        result = ImageService._dict_to_image(data)

        assert result.created_at is None

    def test_round_trip_preserves_datetime(self):
        """
        Image -> dict -> Image should preserve datetime type.

        This is the bug that caused the template error:
        strftime() was called on a string instead of datetime.
        """
        now = datetime(2025, 1, 3, 12, 30, 45, tzinfo=UTC)
        original = MagicMock(spec=Image)
        original.id = "test-id"
        original.filename = "test.jpg"
        original.storage_key = "abc123.jpg"
        original.content_type = "image/jpeg"
        original.file_size = 1024
        original.upload_ip = "127.0.0.1"
        original.width = 100
        original.height = 100
        original.user_id = "user-123"
        original.delete_token_hash = None
        original.thumbnail_key = "thumb.jpg"
        original.created_at = now

        # Simulate cache: serialize then deserialize
        cached_dict = ImageService._image_to_dict(original)
        restored = ImageService._dict_to_image(cached_dict)

        # The key assertion: created_at must be a datetime, not a string
        assert isinstance(restored.created_at, datetime)
        assert restored.created_at == now

        # Verify strftime works (this is what the template does)
        formatted = restored.created_at.strftime("%B %d, %Y")
        assert formatted == "January 03, 2025"
