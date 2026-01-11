"""Tag Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TagBase(BaseModel):
    """Base tag schema with common fields."""

    name: str = Field(..., min_length=2, max_length=50, description="Tag name")
    category: str | None = Field(None, max_length=20, description="Tag category (optional)")

    @field_validator("name")
    @classmethod
    def normalize_tag_name(cls, v: str) -> str:
        """Normalize tag name: lowercase and strip whitespace."""
        return v.lower().strip()

    @field_validator("name")
    @classmethod
    def validate_tag_name(cls, v: str) -> str:
        """Validate tag name contains only allowed characters."""
        # Allow alphanumeric, spaces, hyphens
        if not all(c.isalnum() or c in (" ", "-") for c in v):
            raise ValueError("Tag name can only contain letters, numbers, spaces, and hyphens")
        return v


class TagCreate(TagBase):
    """Schema for creating a tag."""

    pass


class TagResponse(TagBase):
    """Schema for tag response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime


class ImageTagBase(BaseModel):
    """Base image-tag association schema."""

    source: str = Field(..., description="Tag source: 'ai' or 'user'")
    confidence: int | None = Field(
        None, ge=0, le=100, description="Confidence score (0-100) for AI tags"
    )


class ImageTagResponse(BaseModel):
    """Schema for image-tag association with tag details."""

    model_config = ConfigDict(from_attributes=True)

    name: str = Field(..., description="Tag name")
    category: str | None = Field(None, description="Tag category")
    source: str = Field(..., description="Tag source: 'ai' or 'user'")
    confidence: int | None = Field(None, description="Confidence score for AI tags")


class AddTagRequest(BaseModel):
    """Request schema for adding a tag to an image."""

    tag: str = Field(..., min_length=2, max_length=50, description="Tag name to add")
    category: str | None = Field(None, max_length=20, description="Tag category (optional)")

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, v: str) -> str:
        """Normalize tag name: lowercase and strip whitespace."""
        return v.lower().strip()


class TagWithCount(BaseModel):
    """Schema for tag with usage count (for popular tags)."""

    model_config = ConfigDict(from_attributes=True)

    name: str
    category: str | None
    count: int = Field(..., description="Number of images with this tag")
