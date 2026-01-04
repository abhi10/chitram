"""API tests for image endpoints."""

from httpx import AsyncClient


class TestUploadImage:
    """Tests for POST /api/v1/images/upload."""

    async def test_upload_valid_jpeg(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Uploading a valid JPEG returns 201 with metadata including dimensions."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
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

    async def test_upload_valid_png(self, client: AsyncClient, sample_png_bytes: bytes):
        """Uploading a valid PNG returns 201 with metadata including dimensions."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.png", sample_png_bytes, "image/png")},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["content_type"] == "image/png"
        # Phase 1.5: Image dimensions
        assert data["width"] == 100  # Test fixture creates 100x100 image
        assert data["height"] == 100

    async def test_upload_invalid_file_type(self, client: AsyncClient, invalid_file_bytes: bytes):
        """Uploading a non-image returns 400 with error."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.txt", invalid_file_bytes, "text/plain")},
        )

        assert response.status_code == 400
        data = response.json()
        # FastAPI HTTPException uses "detail" key
        assert data["detail"]["code"] == "INVALID_FILE_FORMAT"

    async def test_upload_no_file(self, client: AsyncClient):
        """Uploading without a file returns 422."""
        response = await client.post("/api/v1/images/upload")

        assert response.status_code == 422


class TestGetImageMetadata:
    """Tests for GET /api/v1/images/{image_id}."""

    async def test_get_existing_image(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Getting metadata for existing image returns 200 with dimensions."""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]

        # Get metadata
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

    async def test_download_existing_image(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Downloading existing image returns file content."""
        # Upload first
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]

        # Download
        response = await client.get(f"/api/v1/images/{image_id}/file")

        assert response.status_code == 200
        assert response.headers["content-type"] == "image/jpeg"
        assert len(response.content) == len(sample_jpeg_bytes)

    async def test_download_includes_filename_in_header(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Content-Disposition header should include original filename with extension."""
        # Upload with a specific filename
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("my_photo.jpg", sample_jpeg_bytes, "image/jpeg")},
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

    async def test_delete_existing_image(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Deleting existing image with delete token returns 204."""
        # Upload first (anonymous gets delete_token)
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]
        delete_token = upload_response.json()["delete_token"]

        # Delete with token
        response = await client.delete(
            f"/api/v1/images/{image_id}", params={"delete_token": delete_token}
        )

        assert response.status_code == 204

        # Verify deleted
        get_response = await client.get(f"/api/v1/images/{image_id}")
        assert get_response.status_code == 404

    async def test_delete_nonexistent_image(self, client: AsyncClient):
        """Deleting nonexistent image returns 404."""
        response = await client.delete(
            "/api/v1/images/nonexistent-id", params={"delete_token": "any_token"}
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
