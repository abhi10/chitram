"""add width and height columns

Revision ID: a11aa549249d
Revises: d2dc1766a59c
Create Date: 2025-12-31 13:28:48.461812

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a11aa549249d"
down_revision: str | Sequence[str] | None = "d2dc1766a59c"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add width and height columns for image dimensions.

    Columns are nullable to support existing images without dimensions.
    New uploads will have these populated via Pillow.
    """
    op.add_column("images", sa.Column("width", sa.Integer, nullable=True))
    op.add_column("images", sa.Column("height", sa.Integer, nullable=True))


def downgrade() -> None:
    """Remove width and height columns."""
    op.drop_column("images", "height")
    op.drop_column("images", "width")
