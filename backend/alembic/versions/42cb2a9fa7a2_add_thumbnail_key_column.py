"""add_thumbnail_key_column

Phase 2B: Add thumbnail_key column to store reference to generated thumbnail.

Revision ID: 42cb2a9fa7a2
Revises: 2f6a8fb30700
Create Date: 2026-01-03 02:30:00.373153

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "42cb2a9fa7a2"
down_revision: str | None = "2f6a8fb30700"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add thumbnail_key column to images table."""
    op.add_column("images", sa.Column("thumbnail_key", sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove thumbnail_key column from images table."""
    op.drop_column("images", "thumbnail_key")
