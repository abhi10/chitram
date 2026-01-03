"""Image API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.api.dependencies import get_cache, get_rate_limiter, get_upload_semaphore
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.error import ErrorCodes, ErrorDetail, ErrorResponse
from app.schemas.image import ImageMetadata, ImageUploadResponse
from app.services.cache_service import CacheService
from app.services.concurrency import UploadSemaphore
from app.services.image_service import ImageService
from app.services.rate_limiter import RateLimiter
from app.services.storage_service import StorageService
from app.utils.validation import validate_image_file

router = APIRouter(prefix="/images", tags=["images"])
settings = get_settings()


def get_storage(request: Request) -> StorageService:
    """Dependency to get storage service from app state."""
    return request.app.state.storage


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
    file: Annotated[UploadFile, File(description="Image file to upload")],
    service: ImageService = Depends(get_image_service),
    semaphore: UploadSemaphore | None = Depends(get_upload_semaphore),
    current_user: User | None = Depends(get_current_user),
) -> ImageUploadResponse:
    """
    Upload a new image.

    Accepts JPEG and PNG files up to 5MB.
    Returns 503 if server is too busy (concurrency limit reached).

    - Anonymous uploads receive a delete_token for later deletion.
    - Authenticated uploads are linked to the user (no delete token needed).
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

        # Build response (delete_token only for anonymous uploads)
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

    Returns X-Cache header: HIT (from cache), MISS (from DB, cached), or DISABLED
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

    metadata = ImageMetadata.model_validate(image)
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

    data, content_type = result
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f"inline; filename={image_id}"},
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
