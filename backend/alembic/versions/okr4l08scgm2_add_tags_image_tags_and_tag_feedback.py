"""add tags image_tags and tag_feedback tables

Revision ID: okr4l08scgm2
Revises: c3e5f8a92b1d
Create Date: 2026-01-10 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "okr4l08scgm2"
down_revision: str | Sequence[str] | None = "c3e5f8a92b1d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - add tag-related tables."""
    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("category", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)
    op.create_index(op.f("ix_tags_category"), "tags", ["category"], unique=False)

    # Create image_tags junction table
    op.create_table(
        "image_tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("image_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("confidence", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("image_id", "tag_id", name="uq_image_tag"),
    )
    op.create_index(op.f("ix_image_tags_image_id"), "image_tags", ["image_id"], unique=False)
    op.create_index(op.f("ix_image_tags_tag_id"), "image_tags", ["tag_id"], unique=False)

    # Create tag_feedback table (for future AI improvement - Phase 6/7)
    op.create_table(
        "tag_feedback",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("image_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.Column("feedback_type", sa.String(length=10), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["image_id"], ["images.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema - remove tag-related tables."""
    op.drop_table("tag_feedback")
    op.drop_index(op.f("ix_image_tags_tag_id"), table_name="image_tags")
    op.drop_index(op.f("ix_image_tags_image_id"), table_name="image_tags")
    op.drop_table("image_tags")
    op.drop_index(op.f("ix_tags_category"), table_name="tags")
    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")
