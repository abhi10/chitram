"""Image API endpoints."""

from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user, require_current_user
from app.api.dependencies import get_cache, get_rate_limiter, get_upload_semaphore
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.error import ErrorCodes, ErrorDetail, ErrorResponse
from app.schemas.image import ImageMetadata, ImageUploadResponse
from app.services.ai import AIProviderError, create_ai_provider
from app.services.cache_service import CacheService
from app.services.concurrency import UploadSemaphore
from app.services.image_service import ImageService
from app.services.rate_limiter import RateLimiter
from app.services.storage_service import StorageService
from app.services.tag_service import TagService
from app.services.thumbnail_service import ThumbnailService
from app.utils.validation import validate_image_file

router = APIRouter(prefix="/images", tags=["images"])
settings = get_settings()


def get_storage(request: Request) -> StorageService:
    """Dependency to get storage service from app state."""
    return request.app.state.storage


def get_thumbnail_service(request: Request) -> ThumbnailService:
    """Dependency to get thumbnail service from app state."""
    return request.app.state.thumbnail_service


def get_image_service(
    db: AsyncSession = Depends(get_db),
    storage: StorageService = Depends(get_storage),
    cache: CacheService | None = Depends(get_cache),
) -> ImageService:
    """Dependency to get image service."""
    return ImageService(db=db, storage=storage, cache=cache)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    # Check for forwarded headers (reverse proxy)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


async def check_rate_limit(
    request: Request,
    rate_limiter: RateLimiter | None = Depends(get_rate_limiter),
) -> None:
    """
    Dependency to check rate limit before processing request.

    Raises HTTPException 429 if rate limit is exceeded.
    """
    if not rate_limiter:
        return  # Rate limiting disabled

    client_ip = get_client_ip(request)
    result = await rate_limiter.check(client_ip)

    if not result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=ErrorDetail(
                code=ErrorCodes.RATE_LIMIT_EXCEEDED,
                message=f"Rate limit exceeded. Try again in {result.retry_after} seconds.",
                details={
                    "limit": result.limit,
                    "retry_after": result.retry_after,
                },
            ).model_dump(),
            headers={"Retry-After": str(result.retry_after)},
        )


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=ImageUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
        503: {"model": ErrorResponse, "description": "Server busy"},
    },
    dependencies=[Depends(check_rate_limit)],
)
async def upload_image(
    request: Request,
    background_tasks: BackgroundTasks,
    file: Annotated[UploadFile, File(description="Image file to upload")],
    service: ImageService = Depends(get_image_service),
    thumbnail_service: ThumbnailService = Depends(get_thumbnail_service),
    semaphore: UploadSemaphore | None = Depends(get_upload_semaphore),
    current_user: User = Depends(require_current_user),
) -> ImageUploadResponse:
    """
    Upload a new image. Requires authentication.

    Accepts JPEG and PNG files up to 5MB.
    Returns 401 if not authenticated.
    Returns 503 if server is too busy (concurrency limit reached).

    - All uploads are linked to the authenticated user.
    - Thumbnail generation is queued as a background task (Phase 2B).
    """
    # Acquire semaphore BEFORE reading file (memory optimization per ADR-0010)
    if semaphore:
        acquired = await semaphore.acquire_with_timeout()
        if not acquired:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=ErrorDetail(
                    code=ErrorCodes.SERVICE_UNAVAILABLE,
                    message="Server busy, try again later.",
                    details={"reason": "upload_concurrency_limit_exceeded"},
                ).model_dump(),
            )

    try:
        # Read file content (now protected by semaphore)
        content = await file.read()

        # Validate file
        validation_error = validate_image_file(
            content=content,
            content_type=file.content_type,
            filename=file.filename or "unnamed",
            max_size=settings.max_file_size_bytes,
            allowed_types=settings.allowed_content_types_list,
        )
        if validation_error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=validation_error.model_dump(),
            )

        # Get client IP
        client_ip = get_client_ip(request)

        # Upload image with optional user association
        user_id = current_user.id if current_user else None
        image, delete_token = await service.upload(
            data=content,
            filename=file.filename or "unnamed",
            content_type=file.content_type or "application/octet-stream",
            upload_ip=client_ip,
            user_id=user_id,
        )

        # Queue thumbnail generation as background task (Phase 2B)
        background_tasks.add_task(
            thumbnail_service.generate_and_store_thumbnail,
            image.id,
        )

        # Build response (delete_token only for anonymous uploads)
        # thumbnail_ready=False since background task hasn't run yet
        return ImageUploadResponse(
            id=image.id,
            filename=image.filename,
            content_type=image.content_type,
            file_size=image.file_size,
            url=f"/api/v1/images/{image.id}/file",
            created_at=image.created_at,
            width=image.width,
            height=image.height,
            delete_token=delete_token,
            thumbnail_ready=False,
            thumbnail_url=None,
        )
    finally:
        # Always release semaphore
        if semaphore:
            semaphore.release()


@router.get(
    "/{image_id}",
    responses={
        200: {"model": ImageMetadata},
        404: {"model": ErrorResponse, "description": "Image not found"},
    },
)
async def get_image_metadata(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> Response:
    """
    Get image metadata by ID.

    Returns X-Cache header: HIT (from cache), MISS (from DB, cached), or DISABLED.
    Includes thumbnail_ready and thumbnail_url if thumbnail is available.
    """
    image, cache_status = await service.get_by_id_with_cache_status(image_id)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )

    # Build metadata with thumbnail info
    thumbnail_ready = image.thumbnail_key is not None
    thumbnail_url = f"/api/v1/images/{image_id}/thumbnail" if thumbnail_ready else None

    metadata = ImageMetadata(
        id=image.id,
        filename=image.filename,
        content_type=image.content_type,
        file_size=image.file_size,
        created_at=image.created_at,
        width=image.width,
        height=image.height,
        thumbnail_ready=thumbnail_ready,
        thumbnail_url=thumbnail_url,
    )
    return Response(
        content=metadata.model_dump_json(),
        media_type="application/json",
        headers={"X-Cache": cache_status},
    )


@router.get(
    "/{image_id}/file",
    responses={
        200: {"content": {"image/jpeg": {}, "image/png": {}}},
        404: {"model": ErrorResponse, "description": "Image not found"},
    },
)
async def download_image(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> Response:
    """Download image file."""
    result = await service.get_file(image_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )

    data, content_type, filename = result
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.get(
    "/{image_id}/thumbnail",
    responses={
        200: {"content": {"image/jpeg": {}}},
        404: {"model": ErrorResponse, "description": "Image or thumbnail not found"},
    },
)
async def get_thumbnail(
    image_id: str,
    service: ImageService = Depends(get_image_service),
    thumbnail_service: ThumbnailService = Depends(get_thumbnail_service),
) -> Response:
    """
    Get thumbnail for an image.

    Returns the 300px thumbnail if available.
    Returns 404 with THUMBNAIL_NOT_READY if thumbnail hasn't been generated yet.
    Returns 404 with IMAGE_NOT_FOUND if image doesn't exist.
    """
    # First check if image exists using the injected service
    image = await service.get_by_id(image_id)

    if image is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )

    # Check if thumbnail is ready
    if not image.thumbnail_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.THUMBNAIL_NOT_READY,
                message="Thumbnail is not yet available. Try again later.",
            ).model_dump(),
        )

    # Get thumbnail from storage
    result = await thumbnail_service.get_thumbnail(image_id)

    if result is None:
        # Thumbnail key exists but file not found in storage - treat as not ready
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.THUMBNAIL_NOT_READY,
                message="Thumbnail is not yet available. Try again later.",
            ).model_dump(),
        )

    data, content_type = result
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"inline; filename={image_id}_thumbnail.jpg"},
    )


@router.delete(
    "/{image_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        404: {"model": ErrorResponse, "description": "Image not found"},
        403: {"model": ErrorResponse, "description": "Not authorized to delete"},
    },
)
async def delete_image(
    image_id: str,
    delete_token: Annotated[
        str | None, Query(description="Delete token for anonymous uploads")
    ] = None,
    service: ImageService = Depends(get_image_service),
    current_user: User | None = Depends(get_current_user),
) -> None:
    """
    Delete an image.

    - Authenticated users can delete their own images.
    - Anonymous uploads require the delete_token returned during upload.
    """
    user_id = current_user.id if current_user else None
    success, reason = await service.delete(image_id, user_id=user_id, delete_token=delete_token)

    if not success:
        if reason == "not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorDetail(
                    code=ErrorCodes.IMAGE_NOT_FOUND,
                    message=f"Image with ID '{image_id}' not found",
                ).model_dump(),
            )
        if reason == "not_owner":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorDetail(
                    code="FORBIDDEN",
                    message="You do not own this image",
                ).model_dump(),
            )
        if reason == "token_required":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorDetail(
                    code="DELETE_TOKEN_REQUIRED",
                    message="Delete token is required for anonymous uploads",
                ).model_dump(),
            )
        if reason == "invalid_token":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorDetail(
                    code="INVALID_DELETE_TOKEN",
                    message="Invalid delete token",
                ).model_dump(),
            )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="FORBIDDEN",
                message="Not authorized to delete this image",
            ).model_dump(),
        )


@router.post(
    "/{image_id}/ai-tag",
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "AI tags generated successfully"},
        404: {"model": ErrorResponse, "description": "Image not found"},
        403: {"model": ErrorResponse, "description": "Not authorized"},
        500: {"model": ErrorResponse, "description": "AI provider error"},
    },
)
async def generate_ai_tags(
    image_id: str,
    service: ImageService = Depends(get_image_service),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_current_user),
) -> dict:
    """
    TEMPORARY ENDPOINT (Phase 5): Manually trigger AI tagging for an image.

    This endpoint will be removed in Phase 6 when auto-tagging is integrated
    into the upload flow as a background task.

    Usage:
    1. Upload an image via web UI
    2. Call POST /api/v1/images/{id}/ai-tag
    3. Refresh page to see AI tags

    Requires:
    - Authentication (user must be logged in)
    - User must own the image
    - OPENAI_API_KEY configured in environment

    Returns:
    - List of AI-generated tags with confidence scores
    - Tags are automatically saved to database (source='ai')
    """
    # 1. Get image metadata and verify ownership
    image = await service.get_by_id(image_id)

    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )

    # 2. Verify user owns this image
    if image.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorDetail(
                code="FORBIDDEN",
                message="You do not own this image",
            ).model_dump(),
        )

    # 3. Fetch image bytes from storage
    result = await service.get_file(image_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message="Image file not found in storage",
            ).model_dump(),
        )

    image_bytes, _, _ = result

    # 4. Call AI provider
    try:
        ai_provider = create_ai_provider(settings)
        tags = await ai_provider.analyze_image(image_bytes)
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorDetail(
                code="AI_PROVIDER_ERROR",
                message=f"AI provider failed: {str(e)}",
            ).model_dump(),
        ) from e

    # 5. Save tags to database
    tag_service = TagService(db=db)
    saved_tags = []

    for tag in tags:
        try:
            await tag_service.add_tag_to_image(
                image_id=image_id,
                tag_name=tag.name,
                source="ai",
                confidence=tag.confidence,
                category=tag.category,
            )
            saved_tags.append(
                {
                    "name": tag.name,
                    "confidence": tag.confidence,
                    "category": tag.category,
                }
            )
        except Exception as e:
            # Log error but continue with other tags
            print(f"Failed to save tag {tag.name}: {e}")

    # 6. Return results
    return {
        "message": f"Added {len(saved_tags)} AI tags to image",
        "image_id": image_id,
        "tags": saved_tags,
        "provider": settings.ai_provider,
        "model": settings.openai_vision_model if settings.ai_provider == "openai" else None,
    }
