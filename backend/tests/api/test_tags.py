"""API tests for tag endpoints."""

import pytest
from httpx import AsyncClient


class TestGetImageTags:
    """Test GET /api/v1/images/{id}/tags endpoint."""

    @pytest.mark.asyncio
    async def test_get_tags_for_image_without_tags(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Get tags for image without tags returns empty list."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Get tags (should be empty)
        response = await client.get(f"/api/v1/images/{image_id}/tags")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_get_tags_for_image_with_tags(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Get tags for image with tags returns tag list."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Add tags
        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "nature", "category": "landscape"},
            headers=auth_headers,
        )

        # Get tags
        response = await client.get(f"/api/v1/images/{image_id}/tags")

        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 2
        assert tags[0]["name"] in ["sunset", "nature"]
        assert tags[0]["source"] == "user"
        assert tags[0]["confidence"] is None

    @pytest.mark.asyncio
    async def test_get_tags_for_nonexistent_image(self, client: AsyncClient):
        """Get tags for non-existent image returns empty list."""
        response = await client.get("/api/v1/images/nonexistent-id/tags")
        assert response.status_code == 200
        assert response.json() == []


class TestAddTagToImage:
    """Test POST /api/v1/images/{id}/tags endpoint."""

    @pytest.mark.asyncio
    async def test_add_tag_success(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Add tag to image returns tag details."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Add tag
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        tag_data = response.json()
        assert tag_data["name"] == "sunset"
        assert tag_data["source"] == "user"
        assert tag_data["confidence"] is None
        assert tag_data["category"] is None

    @pytest.mark.asyncio
    async def test_add_tag_with_category(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Add tag with category."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Add tag with category
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "mountain", "category": "landscape"},
            headers=auth_headers,
        )

        assert response.status_code == 201
        tag_data = response.json()
        assert tag_data["name"] == "mountain"
        assert tag_data["category"] == "landscape"

    @pytest.mark.asyncio
    async def test_add_tag_normalizes_name(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Tag name is normalized (lowercase, trimmed)."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Add tag with uppercase and whitespace
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "  SUNSET  "},
            headers=auth_headers,
        )

        assert response.status_code == 201
        assert response.json()["name"] == "sunset"

    @pytest.mark.asyncio
    async def test_add_duplicate_tag_fails(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Adding duplicate tag returns 400."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Add tag first time
        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # Add same tag again
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert response.json()["detail"]["code"] == "INVALID_REQUEST"

    @pytest.mark.asyncio
    async def test_add_tag_requires_authentication(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Add tag without auth returns 401."""
        # Upload an image with auth
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Try to add tag without auth
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_add_tag_requires_ownership(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_user_auth_headers: dict,
        sample_image_bytes: bytes,
    ):
        """Add tag to other user's image returns 403."""
        # User 1 uploads an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # User 2 tries to add tag
        response = await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=other_user_auth_headers,
        )

        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "FORBIDDEN"

    @pytest.mark.asyncio
    async def test_add_tag_to_nonexistent_image(self, client: AsyncClient, auth_headers: dict):
        """Add tag to non-existent image returns 404."""
        response = await client.post(
            "/api/v1/images/nonexistent-id/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "IMAGE_NOT_FOUND"


class TestRemoveTagFromImage:
    """Test DELETE /api/v1/images/{id}/tags/{tag} endpoint."""

    @pytest.mark.asyncio
    async def test_remove_tag_success(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Remove tag from image returns 204."""
        # Upload an image and add tag
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # Remove tag
        response = await client.delete(
            f"/api/v1/images/{image_id}/tags/sunset",
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Verify tag removed
        tags_response = await client.get(f"/api/v1/images/{image_id}/tags")
        assert tags_response.json() == []

    @pytest.mark.asyncio
    async def test_remove_tag_case_insensitive(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Remove tag is case-insensitive."""
        # Upload an image and add tag
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # Remove with different case
        response = await client.delete(
            f"/api/v1/images/{image_id}/tags/SUNSET",
            headers=auth_headers,
        )

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_remove_nonexistent_tag(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Remove non-existent tag returns 404."""
        # Upload an image
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        # Try to remove tag that doesn't exist
        response = await client.delete(
            f"/api/v1/images/{image_id}/tags/nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "TAG_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_remove_tag_requires_authentication(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Remove tag without auth returns 401."""
        # Upload an image and add tag
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # Try to remove without auth
        response = await client.delete(f"/api/v1/images/{image_id}/tags/sunset")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_remove_tag_requires_ownership(
        self,
        client: AsyncClient,
        auth_headers: dict,
        other_user_auth_headers: dict,
        sample_image_bytes: bytes,
    ):
        """Remove tag from other user's image returns 403."""
        # User 1 uploads image and adds tag
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # User 2 tries to remove tag
        response = await client.delete(
            f"/api/v1/images/{image_id}/tags/sunset",
            headers=other_user_auth_headers,
        )

        assert response.status_code == 403


class TestListTags:
    """Test GET /api/v1/tags endpoint."""

    @pytest.mark.asyncio
    async def test_list_tags_empty(self, client: AsyncClient):
        """List tags when no tags exist returns empty list."""
        response = await client.get("/api/v1/tags")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_tags_returns_all_tags(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """List tags returns all tags in system."""
        # Upload images and add tags
        for tag_name in ["sunset", "nature", "mountain"]:
            upload_response = await client.post(
                "/api/v1/images/upload",
                files={"file": (f"{tag_name}.jpg", sample_image_bytes, "image/jpeg")},
                headers=auth_headers,
            )
            image_id = upload_response.json()["id"]

            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": tag_name},
                headers=auth_headers,
            )

        # List all tags
        response = await client.get("/api/v1/tags")

        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 3
        tag_names = [tag["name"] for tag in tags]
        assert "sunset" in tag_names
        assert "nature" in tag_names
        assert "mountain" in tag_names

    @pytest.mark.asyncio
    async def test_list_tags_respects_limit(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """List tags respects limit parameter."""
        # Create 5 tags
        for i in range(5):
            upload_response = await client.post(
                "/api/v1/images/upload",
                files={"file": (f"test{i}.jpg", sample_image_bytes, "image/jpeg")},
                headers=auth_headers,
            )
            image_id = upload_response.json()["id"]

            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": f"tag{i}"},
                headers=auth_headers,
            )

        # Request only 3
        response = await client.get("/api/v1/tags?limit=3")

        assert response.status_code == 200
        assert len(response.json()) == 3


class TestPopularTags:
    """Test GET /api/v1/tags/popular endpoint."""

    @pytest.mark.asyncio
    async def test_popular_tags_empty(self, client: AsyncClient):
        """Popular tags when no tags exist returns empty list."""
        response = await client.get("/api/v1/tags/popular")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_popular_tags_ordered_by_count(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Popular tags returns tags ordered by usage count."""
        # Upload 3 images
        image_ids = []
        for i in range(3):
            upload_response = await client.post(
                "/api/v1/images/upload",
                files={"file": (f"test{i}.jpg", sample_image_bytes, "image/jpeg")},
                headers=auth_headers,
            )
            image_ids.append(upload_response.json()["id"])

        # Add "sunset" to all 3 images
        for image_id in image_ids:
            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": "sunset"},
                headers=auth_headers,
            )

        # Add "nature" to 2 images
        for image_id in image_ids[:2]:
            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": "nature"},
                headers=auth_headers,
            )

        # Add "mountain" to 1 image
        await client.post(
            f"/api/v1/images/{image_ids[0]}/tags",
            json={"tag": "mountain"},
            headers=auth_headers,
        )

        # Get popular tags
        response = await client.get("/api/v1/tags/popular")

        assert response.status_code == 200
        tags = response.json()
        assert len(tags) == 3
        # Should be ordered: sunset (3), nature (2), mountain (1)
        assert tags[0]["name"] == "sunset"
        assert tags[0]["count"] == 3
        assert tags[1]["name"] == "nature"
        assert tags[1]["count"] == 2
        assert tags[2]["name"] == "mountain"
        assert tags[2]["count"] == 1

    @pytest.mark.asyncio
    async def test_popular_tags_respects_limit(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Popular tags respects limit parameter."""
        # Upload image and add 5 tags
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        for i in range(5):
            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": f"tag{i}"},
                headers=auth_headers,
            )

        # Request only 3
        response = await client.get("/api/v1/tags/popular?limit=3")

        assert response.status_code == 200
        assert len(response.json()) == 3


class TestSearchTags:
    """Test GET /api/v1/tags/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_tags_empty_query(self, client: AsyncClient):
        """Search with empty query returns empty list."""
        response = await client.get("/api/v1/tags/search?q=")

        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_search_tags_prefix_match(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Search tags matches by prefix."""
        # Create tags: sunset, sun, mountain
        tags = ["sunset", "sun", "mountain"]
        for tag_name in tags:
            upload_response = await client.post(
                "/api/v1/images/upload",
                files={"file": (f"{tag_name}.jpg", sample_image_bytes, "image/jpeg")},
                headers=auth_headers,
            )
            image_id = upload_response.json()["id"]

            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": tag_name},
                headers=auth_headers,
            )

        # Search for "sun" prefix
        response = await client.get("/api/v1/tags/search?q=sun")

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        result_names = [tag["name"] for tag in results]
        assert "sun" in result_names
        assert "sunset" in result_names
        assert "mountain" not in result_names

    @pytest.mark.asyncio
    async def test_search_tags_case_insensitive(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Search is case-insensitive."""
        # Create tag "sunset"
        upload_response = await client.post(
            "/api/v1/images/upload",
            files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
            headers=auth_headers,
        )
        image_id = upload_response.json()["id"]

        await client.post(
            f"/api/v1/images/{image_id}/tags",
            json={"tag": "sunset"},
            headers=auth_headers,
        )

        # Search with uppercase
        response = await client.get("/api/v1/tags/search?q=SUN")

        assert response.status_code == 200
        results = response.json()
        assert len(results) == 1
        assert results[0]["name"] == "sunset"

    @pytest.mark.asyncio
    async def test_search_tags_respects_limit(
        self, client: AsyncClient, auth_headers: dict, sample_image_bytes: bytes
    ):
        """Search respects limit parameter."""
        # Create 5 tags starting with "tag"
        for i in range(5):
            upload_response = await client.post(
                "/api/v1/images/upload",
                files={"file": (f"test{i}.jpg", sample_image_bytes, "image/jpeg")},
                headers=auth_headers,
            )
            image_id = upload_response.json()["id"]

            await client.post(
                f"/api/v1/images/{image_id}/tags",
                json={"tag": f"tag{i}"},
                headers=auth_headers,
            )

        # Search with limit=3
        response = await client.get("/api/v1/tags/search?q=tag&limit=3")

        assert response.status_code == 200
        assert len(response.json()) == 3

    @pytest.mark.asyncio
    async def test_search_tags_no_results(self, client: AsyncClient):
        """Search with no matches returns empty list."""
        response = await client.get("/api/v1/tags/search?q=nonexistent")

        assert response.status_code == 200
        assert response.json() == []
