"""Image API endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.schemas.error import ErrorCodes, ErrorDetail, ErrorResponse
from app.schemas.image import ImageMetadata, ImageUploadResponse
from app.services.cache_service import CacheService
from app.services.image_service import ImageService
from app.services.storage_service import StorageService
from app.utils.validation import validate_image_file

router = APIRouter(prefix="/images", tags=["images"])
settings = get_settings()


def get_storage(request: Request) -> StorageService:
    """Dependency to get storage service from app state."""
    return request.app.state.storage


def get_cache(request: Request) -> CacheService | None:
    """Dependency to get cache service from app state."""
    return getattr(request.app.state, "cache", None)


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


@router.post(
    "/upload",
    status_code=status.HTTP_201_CREATED,
    response_model=ImageUploadResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid file"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
)
async def upload_image(
    request: Request,
    file: Annotated[UploadFile, File(description="Image file to upload")],
    service: ImageService = Depends(get_image_service),
) -> ImageUploadResponse:
    """
    Upload a new image.

    Accepts JPEG and PNG files up to 5MB.
    """
    # Read file content
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

    # Upload image
    image = await service.upload(
        data=content,
        filename=file.filename or "unnamed",
        content_type=file.content_type or "application/octet-stream",
        upload_ip=client_ip,
    )

    # Build response
    return ImageUploadResponse(
        id=image.id,
        filename=image.filename,
        content_type=image.content_type,
        file_size=image.file_size,
        url=f"/api/v1/images/{image.id}/file",
        created_at=image.created_at,
        width=image.width,
        height=image.height,
    )


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
    responses={404: {"model": ErrorResponse, "description": "Image not found"}},
)
async def delete_image(
    image_id: str,
    service: ImageService = Depends(get_image_service),
) -> None:
    """Delete an image."""
    deleted = await service.delete(image_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorDetail(
                code=ErrorCodes.IMAGE_NOT_FOUND,
                message=f"Image with ID '{image_id}' not found",
            ).model_dump(),
        )
