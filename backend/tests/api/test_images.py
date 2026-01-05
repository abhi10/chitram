"""API tests for image endpoints."""

from httpx import AsyncClient


class TestUploadImage:
    """Tests for POST /api/v1/images/upload."""

    async def test_upload_valid_jpeg(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Uploading a valid JPEG returns 201 with metadata including dimensions."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["filename"] == "test.jpg"
        assert data["content_type"] == "image/jpeg"
        assert data["file_size"] == len(sample_jpeg_bytes)
        assert "url" in data
        # Phase 1.5: Image dimensions
        assert data["width"] == 100  # Test fixture creates 100x100 image
        assert data["height"] == 100

    async def test_upload_valid_png(
        self, client: AsyncClient, sample_png_bytes: bytes, auth_headers: dict
    ):
        """Uploading a valid PNG returns 201 with metadata including dimensions."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.png", sample_png_bytes, "image/png")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content_type"] == "image/png"
        # Phase 1.5: Image dimensions
        assert data["width"] == 100  # Test fixture creates 100x100 image
        assert data["height"] == 100

    async def test_upload_invalid_file_type(
        self, client: AsyncClient, invalid_file_bytes: bytes, auth_headers: dict
    ):
        """Uploading a non-image returns 400 with error."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.txt", invalid_file_bytes, "text/plain")},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException uses "detail" key
        assert data["detail"]["code"] == "INVALID_FILE_FORMAT"

    async def test_upload_no_file(self, client: AsyncClient, auth_headers: dict):
        """Uploading without a file returns 422."""
        response = await client.post("/api/v1/images/upload", headers=auth_headers)

        assert response.status_code == 422

    async def test_upload_requires_authentication(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Uploading without authentication returns 401."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 401
        data = response.json()
        assert data["detail"]["code"] == "UNAUTHORIZED"


class TestGetImageMetadata:
    """Tests for GET /api/v1/images/{image_id}."""

    async def test_get_existing_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Getting metadata for existing image returns 200 with dimensions."""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Get metadata (no auth required for viewing)
        response = await client.get(f"/api/v1/images/{image_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == image_id
        assert data["filename"] == "test.jpg"
        # Phase 1.5: Image dimensions
        assert data["width"] == 100
        assert data["height"] == 100

    async def test_get_nonexistent_image(self, client: AsyncClient):
        """Getting metadata for nonexistent image returns 404."""
        response = await client.get("/api/v1/images/nonexistent-id")

        assert response.status_code == 404
        data = response.json()
        # FastAPI HTTPException uses "detail" key
        assert data["detail"]["code"] == "IMAGE_NOT_FOUND"


class TestDownloadImage:
    """Tests for GET /api/v1/images/{image_id}/file."""

    async def test_download_existing_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Downloading existing image returns file content."""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Download (no auth required for viewing)
        response = await client.get(f"/api/v1/images/{image_id}/file")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) == len(sample_jpeg_bytes)

    async def test_download_includes_filename_in_header(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Content-Disposition header should include original filename with extension."""
        # Upload with a specific filename
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("my_photo.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Download
        response = await client.get(f"/api/v1/images/{image_id}/file")

        assert response.status_code == 200
        # Verify Content-Disposition includes the original filename
        content_disposition = response.headers.get("content-disposition", "")
        assert "my_photo.jpg" in content_disposition
        assert "filename=" in content_disposition

    async def test_download_nonexistent_image(self, client: AsyncClient):
        """Downloading nonexistent image returns 404."""
        response = await client.get("/api/v1/images/nonexistent-id/file")

        assert response.status_code == 404


class TestDeleteImage:
    """Tests for DELETE /api/v1/images/{image_id}."""

    async def test_delete_own_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Authenticated user can delete their own image."""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Delete with auth (owner can delete)
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/images/{image_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_image(self, client: AsyncClient, auth_headers: dict):
        """Deleting nonexistent image returns 404."""
        response = await client.delete(
            "/api/v1/images/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404


class TestHealthCheck:
    """Tests for GET /health."""

    async def test_health_check(self, client: AsyncClient):
        """Health check returns status info."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
