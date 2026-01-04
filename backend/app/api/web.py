"""Web UI routes using Jinja2 templates."""

from pathlib import Path

from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.image import Image
from app.models.user import User
from app.services.auth_service import AuthService

router = APIRouter(tags=["web"])

# Template configuration
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Cookie name for JWT token
AUTH_COOKIE_NAME = "chitram_auth"


async def get_current_user_from_cookie(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User | None:
    """
    Get current user from httpOnly cookie.

    Returns None if not authenticated (no cookie or invalid token).
    Does not raise exception for anonymous access.
    """
    token = request.cookies.get(AUTH_COOKIE_NAME)
    if not token:
        return None

    auth_service = AuthService(db)
    return await auth_service.get_current_user(token)


# =============================================================================
# Public Pages
# =============================================================================


@router.get("/", response_class=HTMLResponse)
async def home(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """
    Home page - Gallery of recent public images.

    Shows thumbnails in a masonry grid layout.
    """
    # Fetch recent images (limit 20 for initial load)
    result = await db.execute(select(Image).order_by(desc(Image.created_at)).limit(20))
    images = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="home.html",
        context={
            "images": images,
            "user": current_user,
        },
    )


@router.get("/image/{image_id}", response_class=HTMLResponse)
async def image_detail(
    request: Request,
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """
    Image detail page - Full image with metadata.

    Dark background with glassmorphism card.
    """
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()

    if not image:
        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"user": current_user, "message": "Image not found"},
            status_code=404,
        )

    # Check if current user is the owner
    is_owner = current_user and image.user_id and image.user_id == current_user.id

    return templates.TemplateResponse(
        request=request,
        name="image.html",
        context={
            "image": image,
            "user": current_user,
            "is_owner": is_owner,
        },
    )


@router.get("/upload", response_class=HTMLResponse)
async def upload_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Upload page - Form to upload a new image."""
    return templates.TemplateResponse(
        request=request,
        name="upload.html",
        context={"user": current_user},
    )


# =============================================================================
# Authentication Pages
# =============================================================================


@router.get("/login", response_class=HTMLResponse)
async def login_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Login page - Email and password form."""
    # Redirect if already logged in
    if current_user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"user": None},
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(
    request: Request,
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """Registration page - Create new account form."""
    # Redirect if already logged in
    if current_user:
        return RedirectResponse(url="/", status_code=302)

    return templates.TemplateResponse(
        request=request,
        name="register.html",
        context={"user": None},
    )


@router.post("/logout")
async def logout(response: Response):
    """
    Logout - Clear auth cookie and redirect to home.
    """
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response


# =============================================================================
# User Dashboard
# =============================================================================


@router.get("/my-images", response_class=HTMLResponse)
async def my_images(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User | None = Depends(get_current_user_from_cookie),
):
    """
    My Images page - User's uploaded images.

    Requires authentication.
    """
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)

    # Fetch user's images
    result = await db.execute(
        select(Image).where(Image.user_id == current_user.id).order_by(desc(Image.created_at))
    )
    images = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="my_images.html",
        context={
            "images": images,
            "user": current_user,
            "image_count": len(images),
        },
    )


# =============================================================================
# HTMX Partials
# =============================================================================


@router.get("/partials/gallery", response_class=HTMLResponse)
async def gallery_partial(
    request: Request,
    offset: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
):
    """
    Gallery partial - Load more images for infinite scroll/pagination.

    Used by HTMX for "Load More" functionality.
    """
    result = await db.execute(
        select(Image).order_by(desc(Image.created_at)).offset(offset).limit(limit)
    )
    images = result.scalars().all()

    return templates.TemplateResponse(
        request=request,
        name="partials/gallery_items.html",
        context={"images": images, "offset": offset + limit},
    )
