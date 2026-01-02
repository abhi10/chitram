"""Image Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ImageBase(BaseModel):
    """Base image schema with common fields."""

    filename: str = Field(..., min_length=1, max_length=255)
    content_type: str = Field(..., description="MIME type")


class ImageCreate(ImageBase):
    """Schema for image creation (internal use)."""

    storage_key: str
    file_size: int = Field(..., gt=0)
    upload_ip: str


class ImageMetadata(BaseModel):
    """Schema for image metadata response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    content_type: str
    file_size: int
    created_at: datetime
    # Phase 1.5: Image dimensions (optional for backward compatibility)
    width: int | None = None
    height: int | None = None


class ImageResponse(ImageMetadata):
    """Full image response with URL."""

    url: str = Field(..., description="URL to download the image")


class ImageUploadResponse(BaseModel):
    """Response after successful upload."""

    id: str
    filename: str
    content_type: str
    file_size: int
    url: str
    created_at: datetime
    # Phase 1.5: Image dimensions (optional for backward compatibility)
    width: int | None = None
    height: int | None = None
