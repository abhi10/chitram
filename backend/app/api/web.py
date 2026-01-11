"""Web UI routes using Jinja2 templates.

This module handles server-rendered HTML pages using HTMX + Jinja2.
All data access goes through ImageService for loose coupling.
"""

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_cache
from app.api.images import get_storage
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.services.auth import AuthError, create_auth_provider
from app.services.cache_service import CacheService
from app.services.image_service import ImageService
from app.services.storage_service import StorageService
from app.services.tag_service import TagService

router = APIRouter(tags=["web"])

# Cookie name for JWT token
AUTH_COOKIE_NAME = "chitram_auth"


def get_supabase_config() -> dict:
    """Get Supabase config for frontend OAuth (safe to expose)."""
    settings = get_settings()
    if settings.auth_provider == "supabase":
        return {
            "supabase_url": settings.supabase_url or "",
            "supabase_anon_key": settings.supabase_anon_key or "",
        }
    return {"supabase_url": "", "supabase_anon_key": ""}


# =============================================================================
# Dependencies
# =============================================================================


def get_image_service(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage),
    cache: CacheService | None = Depends(get_cache),
) -> ImageService:
    """Dependency to get image service."""
    return ImageService(db=db, storage=storage, cache=cache)


async def get_current_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current user from auth cookie.

    Extracts JWT from cookie and uses the pluggable auth provider for verification.
    Works with both local JWTs and Supabase tokens depending on AUTH_PROVIDER config.
    Returns None if not authenticated (allows anonymous access).
    """
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None

    # Use pluggable auth provider (handles both local and Supabase tokens)
    settings = get_settings()
    provider = create_auth_provider(db=db, settings=settings)
    result = await provider.verify_token(token)

    if isinstance(result, AuthError):
        return None

    # Get User model from local database
    from sqlalchemy import select

    stmt = select(User).where(User.id == result.local_user_id)
    db_result = await db.execute(stmt)
    user = db_result.scalar_one_or_none()

    if not user or not user.is_active:
        return None

    return user


def get_templates(request: Request):
    """Get templates from app state (configured in main.py)."""
    return request.app.state.templates


# =============================================================================
# Public Pages
# =============================================================================


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    service: ImageService = Depends(get_image_service),
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Home page - User's gallery (requires auth per FR-4.1 unlisted model).

    Per FR-4.1: System shall NOT provide a public listing of all images.
    Images are unlisted - accessible only by direct URL or from owner's gallery.
    """
    if not user:
        # Redirect anonymous users to login
        return RedirectResponse(url="/login", status_code=302)

    # Show only the authenticated user's images
    images = await service.list_by_user(user.id)
    templates = get_templates(request)

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={"images": images, "user": user, "image_count": len(images)},
    )


@router.get("/image/{image_id}", response_class=HTMLResponse)
async def image_detail(
    request: Request,
    image_id: str,
    service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Image detail page - Full image with metadata and tags."""
    image = await service.get_by_id(image_id)
    templates = get_templates(request)

    if not image:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"user": user, "message": "Image not found"},
            status_code=404,
        )

    is_owner = user and image.user_id and image.user_id == user.id

    # Fetch tags for this image
    tag_service = TagService(db=db)
    tags = await tag_service.get_image_tags(image_id)

    return templates.TemplateResponse(
        request=request,
        name="image.html",
        context={"image": image, "user": user, "is_owner": is_owner, "tags": tags},
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(
    request: Request,
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Upload page - Form to upload a new image. Requires authentication."""
    if not user:
        return RedirectResponse(url="/login?next=/upload", status_code=302)
    templates = get_templates(request)
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"user": user},
    )


# =============================================================================
# Authentication Pages
# =============================================================================


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Login page - Redirect if already authenticated."""
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = get_templates(request)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": None, **get_supabase_config()},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Registration page - Redirect if already authenticated."""
    if user:
        return RedirectResponse(url="/", status_code=302)

    templates = get_templates(request)
    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": None, **get_supabase_config()},
    )


@router.post("/logout")
async def logout():
    """Logout - Clear auth cookie and redirect to home."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


@router.get("/auth/callback", response_class=HTMLResponse)
async def auth_callback(
    request: Request,
):
    """OAuth callback page - Extracts tokens from URL hash and sets cookie.

    Supabase OAuth redirects here with tokens in the URL fragment (#access_token=...).
    Since URL fragments aren't sent to the server, we use JavaScript to extract
    the token, set the auth cookie, and redirect to home.
    """
    templates = get_templates(request)
    return templates.TemplateResponse(
        request=request,
        name="auth_callback.html",
        context={"user": None, **get_supabase_config()},
    )


# =============================================================================
# User Dashboard
# =============================================================================


@router.get("/my-images", response_class=HTMLResponse)
async def my_images(
    request: Request,
    service: ImageService = Depends(get_image_service),
    user: User | None = Depends(get_current_user_from_cookie),
):
    """My Images page - User's uploaded images (requires auth)."""
    if not user:
        return RedirectResponse(url="/login", status_code=302)

    images = await service.list_by_user(user.id)
    templates = get_templates(request)

    return templates.TemplateResponse(
        request=request,
        name="my_images.html",
        context={"images": images, "user": user, "image_count": len(images)},
    )


# =============================================================================
# HTMX Partials
# =============================================================================


@router.get("/partials/gallery", response_class=HTMLResponse)
async def gallery_partial(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    service: ImageService = Depends(get_image_service),
    user: User | None = Depends(get_current_user_from_cookie),
):
    """Gallery partial - Load more images for HTMX infinite scroll.

    Per FR-4.1: Only shows the authenticated user's images.
    Returns empty if not authenticated.
    """
    if not user:
        # Return empty partial for unauthenticated users
        templates = get_templates(request)
        return templates.TemplateResponse(
            request=request,
            name="partials/gallery_items.html",
            context={"images": [], "offset": 0},
        )

    images = await service.list_by_user(user.id, limit=limit, offset=offset)
    templates = get_templates(request)

    return templates.TemplateResponse(
        request=request,
        name="partials/gallery_items.html",
        context={"images": images, "offset": offset + limit},
    )
