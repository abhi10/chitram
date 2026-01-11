"""Tag API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import require_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.error import ErrorCodes, ErrorDetail, ErrorResponse
from app.schemas.tag import AddTagRequest, ImageTagResponse, TagResponse, TagWithCount
from app.services.tag_service import TagService

router = APIRouter(tags=["tags"])


def get_tag_service(db: AsyncSession = Depends(get_db)) -> TagService:
    """Dependency to get tag service."""
    return TagService(db=db)


@router.get(
    "/images/{image_id}/tags",
    response_model=list[ImageTagResponse],
    responses={
        404: {"model": ErrorResponse, "description": "Image not found"},
    },
)
async def get_image_tags(
    image_id: str,
    service: TagService = Depends(get_tag_service),
) -> list[ImageTagResponse]:
    """
    Get all tags for an image.

    Returns list of tags with their source (ai/user) and confidence scores.
    Public endpoint - no authentication required.
    """
    return await service.get_image_tags(image_id)


@router.post(
    "/images/{image_id}/tags",
    status_code=status.HTTP_201_CREATED,
    response_model=ImageTagResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        400: {"model": ErrorResponse, "description": "Tag already exists or invalid"},
    },
)
async def add_tag_to_image(
    image_id: str,
    request: AddTagRequest,
    service: TagService = Depends(get_tag_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
) -> ImageTagResponse:
    """
    Add a tag to an image.

    Requires authentication. User must own the image.
    Creates tag if it doesn't exist. Tag names are automatically normalized (lowercase, trimmed).
    """
    # Check if image exists and user owns it
    from sqlalchemy import select

    from app.models.image import Image

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

    # Check ownership
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="FORBIDDEN",
                message="You do not own this image",
            ).model_dump(),
        )

    # Add tag to image
    try:
        await service.add_tag_to_image(
            image_id=image_id,
            tag_name=request.tag,
            source="user",
            confidence=None,
            category=request.category,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorDetail(
                code="INVALID_REQUEST",
                message=str(e),
            ).model_dump(),
        ) from e

    # Return response matching ImageTagResponse schema
    tags = await service.get_image_tags(image_id)
    # Find the tag we just added
    for tag in tags:
        if tag.name == request.tag.lower().strip():
            return tag

    # Fallback (shouldn't happen)
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=ErrorDetail(
            code="INTERNAL_ERROR",
            message="Tag added but not found in response",
        ).model_dump(),
    )


@router.delete(
    "/images/{image_id}/tags/{tag_name}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
        404: {"model": ErrorResponse, "description": "Image or tag not found"},
    },
)
async def remove_tag_from_image(
    image_id: str,
    tag_name: str,
    service: TagService = Depends(get_tag_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
) -> None:
    """
    Remove a tag from an image.

    Requires authentication. User must own the image.
    Tag name is case-insensitive.
    """
    # Check if image exists and user owns it
    from sqlalchemy import select

    from app.models.image import Image

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

    # Check ownership
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="FORBIDDEN",
                message="You do not own this image",
            ).model_dump(),
        )

    # Remove tag
    success = await service.remove_tag_from_image(image_id, tag_name)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code="TAG_NOT_FOUND",
                message=f"Tag '{tag_name}' not found for this image",
            ).model_dump(),
        )


@router.get(
    "/tags",
    response_model=list[TagResponse],
)
async def list_tags(
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of tags")] = 20,
    service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """
    List all tags in the system.

    Returns tags ordered alphabetically by name.
    Public endpoint - no authentication required.
    """
    # Get all tags via search with empty query (returns all)
    from sqlalchemy import select

    from app.models.tag import Tag

    db = service.db
    result = await db.execute(select(Tag).order_by(Tag.name).limit(limit))
    tags = result.scalars().all()

    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            category=tag.category,
            created_at=tag.created_at,
        )
        for tag in tags
    ]


@router.get(
    "/tags/popular",
    response_model=list[TagWithCount],
)
async def get_popular_tags(
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of tags")] = 20,
    service: TagService = Depends(get_tag_service),
) -> list[TagWithCount]:
    """
    Get most popular tags by usage count.

    Returns tags ordered by number of images (descending).
    Public endpoint - no authentication required.
    """
    return await service.get_popular_tags(limit=limit)


@router.get(
    "/tags/search",
    response_model=list[TagResponse],
)
async def search_tags(
    q: Annotated[str, Query(max_length=50, description="Search query")] = "",
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum number of results")] = 10,
    service: TagService = Depends(get_tag_service),
) -> list[TagResponse]:
    """
    Search tags by name prefix (autocomplete).

    Case-insensitive prefix matching.
    Public endpoint - no authentication required.
    """
    if not q:
        return []

    tags = await service.search_tags(query=q, limit=limit)

    return [
        TagResponse(
            id=tag.id,
            name=tag.name,
            category=tag.category,
            created_at=tag.created_at,
        )
        for tag in tags
    ]
