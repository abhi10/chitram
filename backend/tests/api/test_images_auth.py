"""API tests for image endpoints with authentication."""

import pytest
from httpx import AsyncClient


class TestUploadWithAuth:
    """Test image upload with authentication."""

    @pytest.mark.asyncio
    async def test_anonymous_upload_rejected(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Anonymous upload should return 401 Unauthorized."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 401
        assert response.json()["detail"]["code"] == "UNAUTHORIZED"

    @pytest.mark.asyncio
    async def test_authenticated_upload_succeeds(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Authenticated upload should succeed."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["delete_token"] is None  # Authenticated users don't get delete tokens


class TestDeleteWithAuth:
    """Test image deletion with authentication."""

    @pytest.mark.asyncio
    async def test_owner_can_delete_own_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Authenticated user can delete their own image."""
        # Upload with auth
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Delete own image
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_non_owner_cannot_delete_others_image(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Authenticated user cannot delete another user's image."""
        # Register user 1 and upload
        register1 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user1@example.com", "password": "password123"},
        )
        token1 = register1.json()["access_token"]

        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token1}"},
        )
        image_id = upload_response.json()["id"]

        # Register user 2
        register2 = await client.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com", "password": "password123"},
        )
        token2 = register2.json()["access_token"]

        # User 2 tries to delete user 1's image
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            headers={"Authorization": f"Bearer {token2}"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_unauthenticated_delete_rejected(
        self, client: AsyncClient, sample_jpeg_bytes: bytes, auth_headers: dict
    ):
        """Unauthenticated user cannot delete images."""
        # Upload with auth
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Try to delete without auth
        response = await client.delete(f"/api/v1/images/{image_id}")

        # Should get 403 (no delete token and not authenticated)
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_delete_nonexistent_image(self, client: AsyncClient, auth_headers: dict):
        """Deleting nonexistent image returns 404."""
        response = await client.delete(
            "/api/v1/images/nonexistent-id",
            headers=auth_headers,
        )

        assert response.status_code == 404
