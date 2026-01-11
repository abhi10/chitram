"""Tag and ImageTag SQLAlchemy models."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.image import generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.image import Image


class Tag(Base):
    """Tag model for image categorization.

    Normalized tag storage - each unique tag stored once.
    """

    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    image_tags: Mapped[list["ImageTag"]] = relationship(
        "ImageTag",
        back_populates="tag",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Tag(id={self.id}, name={self.name})>"


class ImageTag(Base):
    """Junction table linking images to tags.

    Tracks source (AI vs user) and confidence for AI-generated tags.
    """

    __tablename__ = "image_tags"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    image_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("images.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source: Mapped[str] = mapped_column(String(10), nullable=False)  # 'ai' or 'user'
    confidence: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # 0-100 for AI, NULL for user
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    image: Mapped["Image"] = relationship(  # type: ignore[name-defined]
        "Image", back_populates="image_tags"
    )
    tag: Mapped["Tag"] = relationship("Tag", back_populates="image_tags")

    # Constraints
    __table_args__ = (UniqueConstraint("image_id", "tag_id", name="uq_image_tag"),)

    def __repr__(self) -> str:
        return f"<ImageTag(image_id={self.image_id}, tag_id={self.tag_id}, source={self.source})>"
