"""API tests for thumbnail endpoint."""

import pytest
from httpx import AsyncClient


class TestUploadWithThumbnail:
    """Test upload endpoint includes thumbnail fields."""

    @pytest.mark.asyncio
    async def test_upload_response_includes_thumbnail_ready_false(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Upload response should include thumbnail_ready=False."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "thumbnail_ready" in data
        assert data["thumbnail_ready"] is False

    @pytest.mark.asyncio
    async def test_upload_response_includes_thumbnail_url_none(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Upload response should include thumbnail_url=None initially."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "thumbnail_url" in data
        assert data["thumbnail_url"] is None


class TestGetMetadataWithThumbnail:
    """Test get metadata endpoint includes thumbnail fields."""

    @pytest.mark.asyncio
    async def test_metadata_includes_thumbnail_ready(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Metadata response should include thumbnail_ready field."""
        # Upload an image first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Get metadata
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert "thumbnail_ready" in data
        # Initially False since background task may not have run yet
        assert isinstance(data["thumbnail_ready"], bool)

    @pytest.mark.asyncio
    async def test_metadata_includes_thumbnail_url(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Metadata response should include thumbnail_url field."""
        # Upload an image first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Get metadata
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert "thumbnail_url" in data


class TestThumbnailEndpoint:
    """Test GET /api/v1/images/{id}/thumbnail endpoint."""

    @pytest.mark.asyncio
    async def test_thumbnail_not_found_for_nonexistent_image(self, client: AsyncClient):
        """Should return 404 with IMAGE_NOT_FOUND for nonexistent image."""
        response = await client.get("/api/v1/images/nonexistent-id/thumbnail")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "IMAGE_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_thumbnail_endpoint_for_new_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """After upload, thumbnail should be accessible (background task runs in test)."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # In test mode, background tasks run immediately, so thumbnail should be ready
        response = await client.get(f"/api/v1/images/{image_id}/thumbnail")

        # Background task runs in TestClient, so thumbnail should be generated
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_thumbnail_not_ready_requires_image_without_thumbnail(
        self, client: AsyncClient, test_db
    ):
        """THUMBNAIL_NOT_READY should be returned for images without thumbnail_key."""
        from app.models.image import Image

        # Create an image directly in DB without thumbnail
        image = Image(
            filename="test.jpg",
            storage_key="test-key-no-thumb",
            content_type="image/jpeg",
            file_size=1000,
            upload_ip="127.0.0.1",
            thumbnail_key=None,  # No thumbnail
        )
        test_db.add(image)
        await test_db.commit()
        await test_db.refresh(image)

        # Try to get thumbnail
        response = await client.get(f"/api/v1/images/{image.id}/thumbnail")

        assert response.status_code == 404
        data = response.json()
        assert data["detail"]["code"] == "THUMBNAIL_NOT_READY"
        assert "not yet available" in data["detail"]["message"].lower()


class TestThumbnailEndpointWithReadyThumbnail:
    """Test thumbnail endpoint when thumbnail is available."""

    @pytest.mark.asyncio
    async def test_thumbnail_returns_jpeg(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """When thumbnail is ready, should return JPEG image."""
        # This test requires manually triggering thumbnail generation
        # since background tasks don't run synchronously in tests

        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Manually trigger thumbnail generation
        from app.main import app

        thumbnail_service = app.state.thumbnail_service
        success = await thumbnail_service.generate_and_store_thumbnail(image_id)
        assert success is True

        # Now get the thumbnail
        response = await client.get(f"/api/v1/images/{image_id}/thumbnail")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"

    @pytest.mark.asyncio
    async def test_thumbnail_is_smaller_than_original(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Thumbnail should be smaller than original image."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Manually trigger thumbnail generation
        from app.main import app

        thumbnail_service = app.state.thumbnail_service
        await thumbnail_service.generate_and_store_thumbnail(image_id)

        # Get thumbnail
        response = await client.get(f"/api/v1/images/{image_id}/thumbnail")

        assert response.status_code == 200
        # Thumbnail should be smaller than original
        assert len(response.content) < len(sample_jpeg_bytes)

    @pytest.mark.asyncio
    async def test_thumbnail_has_content_disposition(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Thumbnail response should have Content-Disposition header."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Manually trigger thumbnail generation
        from app.main import app

        thumbnail_service = app.state.thumbnail_service
        await thumbnail_service.generate_and_store_thumbnail(image_id)

        # Get thumbnail
        response = await client.get(f"/api/v1/images/{image_id}/thumbnail")

        assert response.status_code == 200
        assert "content-disposition" in response.headers
        assert "thumbnail" in response.headers["content-disposition"]


class TestMetadataAfterThumbnailGenerated:
    """Test metadata endpoint after thumbnail is generated."""

    @pytest.mark.asyncio
    async def test_metadata_shows_thumbnail_ready_true(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Metadata should show thumbnail_ready=True after generation."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Manually trigger thumbnail generation
        from app.main import app

        thumbnail_service = app.state.thumbnail_service
        await thumbnail_service.generate_and_store_thumbnail(image_id)

        # Get metadata
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["thumbnail_ready"] is True

    @pytest.mark.asyncio
    async def test_metadata_shows_thumbnail_url(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Metadata should include thumbnail_url after generation."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Manually trigger thumbnail generation
        from app.main import app

        thumbnail_service = app.state.thumbnail_service
        await thumbnail_service.generate_and_store_thumbnail(image_id)

        # Get metadata
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["thumbnail_url"] == f"/api/v1/images/{image_id}/thumbnail"
