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


class TestLandingPage:
    """Tests for landing page at / (anonymous users)."""

    @pytest.mark.asyncio
    async def test_landing_page_anonymous_user(self, client: AsyncClient):
        """Anonymous users see landing page at /."""
        response = await client.get("/")

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "చిత్రం" in response.text  # Logo in Telugu
        assert "What will you upload today?" in response.text
        assert "Get Started Free" in response.text
        assert "Platform Stats" in response.text

    @pytest.mark.asyncio
    async def test_landing_page_shows_live_stats(self, client: AsyncClient, test_deps):
        """Landing page shows live stats (images, users)."""
        # Create test data
        auth_service = AuthService(test_deps.session)
        await auth_service.create_user("statsuser@example.com", "password123")

        # Anonymous user views landing
        response = await client.get("/")

        assert response.status_code == 200
        # Stats should show in HTML
        assert "Images Hosted" in response.text
        assert "Active Users" in response.text

    @pytest.mark.asyncio
    async def test_landing_page_authenticated_user_redirects(self, client: AsyncClient, test_deps):
        """Authenticated users are redirected from / to /gallery."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("redirect@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get("/", cookies={AUTH_COOKIE_NAME: token}, follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/gallery"


class TestGalleryRoute:
    """Tests for /gallery route (authenticated users)."""

    @pytest.mark.asyncio
    async def test_gallery_requires_authentication(self, client: AsyncClient):
        """Anonymous users redirected to login."""
        response = await client.get("/gallery", follow_redirects=False)

        assert response.status_code == 302
        assert "/login" in response.headers["location"]

    @pytest.mark.asyncio
    async def test_gallery_shows_user_images(self, client: AsyncClient, test_deps):
        """Authenticated users see their gallery."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("gallery@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get("/gallery", cookies={AUTH_COOKIE_NAME: token})

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Chitram" in response.text  # Brand name in nav

    @pytest.mark.asyncio
    async def test_gallery_only_shows_own_images(
        self, client: AsyncClient, test_deps, sample_jpeg_bytes
    ):
        """Gallery shows only user's own images (FR-4.1)."""
        auth_service = AuthService(test_deps.session)

        # User 1 uploads image
        user1 = await auth_service.create_user("user1@example.com", "password123")
        img1 = Image(
            filename="user1.jpg",
            content_type="image/jpeg",
            file_size=len(sample_jpeg_bytes),
            storage_key="user1-key.jpg",
            upload_ip="127.0.0.1",
            user_id=user1.id,
        )
        test_deps.session.add(img1)

        # User 2 uploads image
        user2 = await auth_service.create_user("user2@example.com", "password123")
        img2 = Image(
            filename="user2.jpg",
            content_type="image/jpeg",
            file_size=len(sample_jpeg_bytes),
            storage_key="user2-key.jpg",
            upload_ip="127.0.0.1",
            user_id=user2.id,
        )
        test_deps.session.add(img2)
        await test_deps.session.commit()
        await test_deps.session.refresh(img1)
        await test_deps.session.refresh(img2)

        # User 1's gallery should only show img1
        token1 = auth_service.create_access_token(user1.id)
        response = await client.get("/gallery", cookies={AUTH_COOKIE_NAME: token1})

        assert response.status_code == 200
        assert (
            str(img1.id) in response.text
            or "user1.jpg" in response.text
            or "user1-key" in response.text
        )
        # Should NOT show user2's images
        assert str(img2.id) not in response.text


class TestPublicPages:
    """Tests for public pages accessible without authentication."""

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
    async def test_upload_page_redirects_when_not_authenticated(self, client: AsyncClient):
        """Upload page should redirect to login when not authenticated."""
        response = await client.get("/upload", follow_redirects=False)

        assert response.status_code == 302
        assert response.headers["location"] == "/login?next=/upload"

    @pytest.mark.asyncio
    async def test_upload_page_returns_200_when_authenticated(self, client: AsyncClient, test_deps):
        """Upload page should return 200 for authenticated users."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("uploader@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get(
            "/upload",
            cookies={AUTH_COOKIE_NAME: token},
        )

        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "upload" in response.text.lower()

    @pytest.mark.asyncio
    async def test_upload_page_has_form_when_authenticated(self, client: AsyncClient, test_deps):
        """Upload page should contain upload form for authenticated users."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("formtest@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get(
            "/upload",
            cookies={AUTH_COOKIE_NAME: token},
        )

        assert response.status_code == 200
        assert "form" in response.text.lower()
        assert "drop" in response.text.lower()  # Drag-and-drop area

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
    async def test_gallery_partial_returns_empty_for_anonymous(
        self, client: AsyncClient, test_deps, sample_jpeg_bytes
    ):
        """Gallery partial should return empty for anonymous users (FR-4.1)."""
        # Create some images (without user ownership for test setup)
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
        # Anonymous users get empty response
        assert "masonry-item" not in response.text
        assert response.text.strip() == "" or "img" not in response.text

    @pytest.mark.asyncio
    async def test_gallery_partial_shows_only_users_images(
        self, client: AsyncClient, test_deps, sample_jpeg_bytes
    ):
        """Gallery partial should only show authenticated user's images (FR-4.1)."""
        # Create a user
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("gallery@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        # Create images owned by this user
        for i in range(2):
            image = Image(
                filename=f"myimage{i}.jpg",
                content_type="image/jpeg",
                file_size=len(sample_jpeg_bytes),
                storage_key=f"my-key-{i}.jpg",
                upload_ip="127.0.0.1",
                user_id=user.id,
            )
            test_deps.session.add(image)

        # Create image owned by another user (should NOT appear)
        other_user = await auth_service.create_user("other@example.com", "password123")
        other_image = Image(
            filename="otherimage.jpg",
            content_type="image/jpeg",
            file_size=len(sample_jpeg_bytes),
            storage_key="other-key.jpg",
            upload_ip="127.0.0.1",
            user_id=other_user.id,
        )
        test_deps.session.add(other_image)
        await test_deps.session.commit()

        response = await client.get("/partials/gallery", cookies={AUTH_COOKIE_NAME: token})

        assert response.status_code == 200
        # Should show user's images
        assert "myimage" in response.text or "my-key" in response.text
        # Should NOT show other user's images
        assert "otherimage" not in response.text


class TestNavigation:
    """Tests for navigation elements."""

    @pytest.mark.asyncio
    async def test_nav_anonymous_shows_home_link(self, client: AsyncClient):
        """Anonymous users see 'Home' link in nav."""
        response = await client.get("/login")  # Use login page to test nav

        assert response.status_code == 200
        assert "Home" in response.text
        assert "Login" in response.text
        assert "Register" in response.text

    @pytest.mark.asyncio
    async def test_nav_authenticated_shows_gallery_link(self, client: AsyncClient, test_deps):
        """Authenticated users see 'My Gallery' link in nav."""
        auth_service = AuthService(test_deps.session)
        user = await auth_service.create_user("nav@example.com", "password123")
        token = auth_service.create_access_token(user.id)

        response = await client.get("/gallery", cookies={AUTH_COOKIE_NAME: token})

        assert response.status_code == 200
        assert "My Gallery" in response.text
        assert "Logout" in response.text
        # Login/Register should NOT be shown when authenticated
        assert response.text.count("Login") <= 1  # May appear in footer/elsewhere but not in nav


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
