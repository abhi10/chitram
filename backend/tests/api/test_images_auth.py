"""API tests for image endpoints with authentication."""

import pytest
from httpx import AsyncClient


class TestUploadWithAuth:
    """Test image upload with authentication."""

    @pytest.mark.asyncio
    async def test_anonymous_upload_returns_delete_token(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Anonymous upload should return a delete token."""
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )

        assert response.status_code == 201
        data = response.json()
        assert "delete_token" in data
        assert data["delete_token"] is not None
        assert len(data["delete_token"]) >= 40  # 32-byte base64

    @pytest.mark.asyncio
    async def test_authenticated_upload_no_delete_token(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Authenticated upload should not return a delete token."""
        # Register and get token
        register_response = await client.post(
            "/api/v1/auth/register",
            json={"email": "uploader@example.com", "password": "password123"},
        )
        token = register_response.json()["access_token"]

        # Upload with auth
        response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["delete_token"] is None


class TestDeleteWithAuth:
    """Test image deletion with authentication."""

    @pytest.mark.asyncio
    async def test_anonymous_delete_with_valid_token(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Anonymous upload can be deleted with correct token."""
        # Upload anonymously
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]
        delete_token = upload_response.json()["delete_token"]

        # Delete with token
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            params={"delete_token": delete_token},
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_anonymous_delete_without_token_fails(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Anonymous upload deletion without token fails."""
        # Upload anonymously
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]

        # Try to delete without token
        response = await client.delete(f"/api/v1/images/{image_id}")

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "DELETE_TOKEN_REQUIRED"

    @pytest.mark.asyncio
    async def test_anonymous_delete_with_wrong_token_fails(
        self, client: AsyncClient, sample_jpeg_bytes: bytes
    ):
        """Anonymous upload deletion with wrong token fails."""
        # Upload anonymously
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
        )
        image_id = upload_response.json()["id"]

        # Try to delete with wrong token
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            params={"delete_token": "wrong_token_here"},
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "INVALID_DELETE_TOKEN"

    @pytest.mark.asyncio
    async def test_owner_can_delete_own_image(self, client: AsyncClient, sample_jpeg_bytes: bytes):
        """Authenticated user can delete their own image."""
        # Register and get token
        register_response = await client.post(
            "/api/v1/auth/register",
            json={"email": "owner@example.com", "password": "password123"},
        )
        token = register_response.json()["access_token"]

        # Upload with auth
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_jpeg_bytes, "image/jpeg")},
            headers={"Authorization": f"Bearer {token}"},
        )
        image_id = upload_response.json()["id"]

        # Delete own image
        response = await client.delete(
            f"/api/v1/images/{image_id}",
            headers={"Authorization": f"Bearer {token}"},
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
    async def test_delete_nonexistent_image(self, client: AsyncClient):
        """Deleting nonexistent image returns 404."""
        response = await client.delete(
            "/api/v1/images/nonexistent-id",
            params={"delete_token": "any_token"},
        )

        assert response.status_code == 404
