"""Shared FastAPI dependencies for API endpoints."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_current_user
from app.database import get_db
from app.models.image import Image
from app.models.user import User
from app.schemas.error import ErrorCodes, ErrorDetail
from app.services.cache_service import CacheService
from app.services.concurrency import UploadSemaphore
from app.services.rate_limiter import RateLimiter


def get_cache(request: Request) -> CacheService | None:
    """Dependency to get cache service from app state."""
    return getattr(request.app.state, "cache", None)


def get_rate_limiter(request: Request) -> RateLimiter | None:
    """Dependency to get rate limiter from app state."""
    return getattr(request.app.state, "rate_limiter", None)


def get_upload_semaphore(request: Request) -> UploadSemaphore | None:
    """Dependency to get upload semaphore from app state."""
    return getattr(request.app.state, "upload_semaphore", None)


async def verify_image_ownership(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
) -> Image:
    """
    Verify that an image exists and the current user owns it.

    Args:
        image_id: ID of the image to check
        db: Database session
        current_user: Authenticated user

    Returns:
        Image object if found and owned by user

    Raises:
        HTTPException: 404 if image not found, 403 if user doesn't own it
    """
    result = await db.execute(select(Image).where(Image.id == image_id))
    image = result.scalar_one_or_none()

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )

    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="FORBIDDEN",
                message="You do not own this image",
            ).model_dump(),
        )

    return image
