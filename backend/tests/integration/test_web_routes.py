"""Integration tests for web UI routes.

These tests verify that:
1. Routes return correct status codes
2. Templates render without errors
3. Auth-protected routes redirect properly
4. HTMX partial endpoints return HTML fragments
"""

import pytest
from httpx import AsyncClient

from app.api.web import AUTH_COOKIE_NAME
from app.models.image import Image
from app.services.auth_service import AuthService


class TestPublicPages:
    """Tests for public pages accessible without authentication."""

    @pytest.mark.asyncio
    async def test_home_page_returns_200(self, client: AsyncClient):
        """Home page should return 200 and HTML content."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Chitram" in response.text  # Brand name in nav

    @pytest.mark.asyncio
    async def test_home_page_shows_gallery(self, client: AsyncClient):
        """Home page should show gallery section."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "masonry-grid" in response.text or "gallery" in response.text.lower()

    @pytest.mark.asyncio
    async def test_upload_page_returns_200(self, client: AsyncClient):
        """Upload page should be accessible to anyone."""
        response = await client.get("/upload")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "upload" in response.text.lower()

    @pytest.mark.asyncio
    async def test_upload_page_has_form(self, client: AsyncClient):
        """Upload page should contain upload form."""
        response = await client.get("/upload")

        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "drop" in response.text.lower()  # Drag-and-drop area

    @pytest.mark.asyncio
    async def test_login_page_returns_200(self, client: AsyncClient):
        """Login page should be accessible."""
        response = await client.get("/login")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "login" in response.text.lower() or "sign in" in response.text.lower()

    @pytest.mark.asyncio
    async def test_register_page_returns_200(self, client: AsyncClient):
        """Register page should be accessible."""
        response = await client.get("/register")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "register" in response.text.lower() or "sign up" in response.text.lower()


class TestImageDetailPage:
    """Tests for image detail page."""

    @pytest.mark.asyncio
    async def test_image_detail_returns_404_for_missing_image(self, client: AsyncClient):
        """Should return 404 for non-existent image."""
        response = await client.get("/image/non-existent-id")

        assert response.status_code == 404
        assert "text/html" in response.headers["content-type"]
        assert "not found" in response.text.lower()

    @pytest.mark.asyncio
    async def test_image_detail_returns_200_for_existing_image(
        self, client: AsyncClient, test_deps, sample_jpeg_bytes
    ):
        """Should return 200 for existing image."""
        # Create an image in DB
        image = Image(
            filename="test.jpg",
            content_type="image/jpeg",
            file_size=len(sample_jpeg_bytes),
            storage_key="test-key.jpg",
            upload_ip="127.0.0.1",
        )
        test_deps.session.add(image)
        await test_deps.session.commit()
        await test_deps.session.refresh(image)

        response = await client.get(f"/image/{image.id}")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "test.jpg" in response.text


class TestAuthProtectedPages:
    """Tests for pages requiring authentication."""

    @pytest.mark.asyncio
    async def test_my_images_redirects_when_not_authenticated(self, client: AsyncClient):
        """My images page should redirect to login when not authenticated."""
        response = await client.get("/my-images", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login"

    @pytest.mark.asyncio
    async def test_my_images_returns_200_when_authenticated(self, client: AsyncClient, test_deps):
        """My images page should return 200 for authenticated users."""
        # Create a user
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("test@example.com", "password123")

        # Create JWT token
        token = auth_service.create_access_token(user.id)

        # Request with auth cookie
        response = await client.get(
            "/my-images",
            cookies={AUTH_COOKIE_NAME: token},
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "test@example.com" in response.text

    @pytest.mark.asyncio
    async def test_login_redirects_when_already_authenticated(self, client: AsyncClient, test_deps):
        """Login page should redirect to home when already authenticated."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("test@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get(
            "/login",
            cookies={AUTH_COOKIE_NAME: token},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_register_redirects_when_already_authenticated(
        self, client: AsyncClient, test_deps
    ):
        """Register page should redirect to home when already authenticated."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("test@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get(
            "/register",
            cookies={AUTH_COOKIE_NAME: token},
            follow_redirects=False,
        )

        assert response.status_code == 302
        assert response.headers["location"] == "/"


class TestLogout:
    """Tests for logout functionality."""

    @pytest.mark.asyncio
    async def test_logout_redirects_to_home(self, client: AsyncClient):
        """Logout should redirect to home page."""
        response = await client.post("/logout", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/"

    @pytest.mark.asyncio
    async def test_logout_clears_auth_cookie(self, client: AsyncClient, test_deps):
        """Logout should clear the auth cookie."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("test@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.post(
            "/logout",
            cookies={AUTH_COOKIE_NAME: token},
            follow_redirects=False,
        )

        assert response.status_code == 302
        # Check that cookie deletion is set (Max-Age=0 or expires in past)
        set_cookie = response.headers.get("set-cookie", "")
        assert AUTH_COOKIE_NAME in set_cookie


class TestHTMXPartials:
    """Tests for HTMX partial endpoints."""

    @pytest.mark.asyncio
    async def test_gallery_partial_returns_html(self, client: AsyncClient):
        """Gallery partial should return HTML fragment."""
        response = await client.get("/partials/gallery")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_gallery_partial_accepts_pagination(self, client: AsyncClient):
        """Gallery partial should accept offset and limit params."""
        response = await client.get("/partials/gallery?offset=20&limit=10")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_gallery_partial_shows_images(
        self, client: AsyncClient, test_deps, sample_jpeg_bytes
    ):
        """Gallery partial should include images in response."""
        # Create some images
        for i in range(3):
            image = Image(
                filename=f"test{i}.jpg",
                content_type="image/jpeg",
                file_size=len(sample_jpeg_bytes),
                storage_key=f"test-key-{i}.jpg",
                upload_ip="127.0.0.1",
            )
            test_deps.session.add(image)
        await test_deps.session.commit()

        response = await client.get("/partials/gallery")

        assert response.status_code == 200
        # Should contain image elements or masonry items
        assert "masonry-item" in response.text or "img" in response.text


class TestNavigation:
    """Tests for navigation elements."""

    @pytest.mark.asyncio
    async def test_nav_shows_login_when_anonymous(self, client: AsyncClient):
        """Navigation should show login link for anonymous users."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "login" in response.text.lower() or "sign in" in response.text.lower()

    @pytest.mark.asyncio
    async def test_nav_shows_profile_when_authenticated(self, client: AsyncClient, test_deps):
        """Navigation should show profile/user info for authenticated users."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("nav@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get(
            "/",
            cookies={AUTH_COOKIE_NAME: token},
        )

        assert response.status_code == 200
        # Should show user email or profile link, not login link
        assert "nav@example.com" in response.text or "my-images" in response.text.lower()


class TestErrorPages:
    """Tests for error page handling."""

    @pytest.mark.asyncio
    async def test_404_page_for_unknown_routes(self, client: AsyncClient):
        """Unknown routes should return proper 404 page."""
        response = await client.get("/this-route-does-not-exist-xyz")

        # FastAPI returns 404 for undefined routes
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_image_404_has_back_link(self, client: AsyncClient):
        """Image 404 page should have link back to home."""
        response = await client.get("/image/non-existent")

        assert response.status_code == 404
        assert 'href="/"' in response.text or "home" in response.text.lower()
