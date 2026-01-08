"""User SQLAlchemy model."""

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.image import generate_uuid


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(UTC)


class User(Base):
    """User model for authentication.

    Supports both local auth (password_hash) and external providers (supabase_id).
    For Supabase users, password_hash may be None as auth is handled externally.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=generate_uuid,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # External provider ID (e.g., Supabase user UUID)
    supabase_id: Mapped[str | None] = mapped_column(
        String(36), unique=True, nullable=True, index=True
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
