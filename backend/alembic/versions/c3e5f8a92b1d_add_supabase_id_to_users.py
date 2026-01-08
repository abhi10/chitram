"""add_supabase_id_to_users

Phase 3.5: Add supabase_id column and make password_hash nullable.
Enables Supabase auth integration while preserving local auth.

Revision ID: c3e5f8a92b1d
Revises: 42cb2a9fa7a2
Create Date: 2026-01-07 10:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3e5f8a92b1d"
down_revision: str | None = "42cb2a9fa7a2"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Add supabase_id column and make password_hash nullable."""
    # Add supabase_id column for external provider linking
    op.add_column(
        "users",
        sa.Column("supabase_id", sa.String(36), nullable=True),
    )
    # Add unique index for efficient lookup
    op.create_index(
        "ix_users_supabase_id",
        "users",
        ["supabase_id"],
        unique=True,
    )

    # Make password_hash nullable (Supabase users don't need local hash)
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=True,
    )


def downgrade() -> None:
    """Remove supabase_id column and make password_hash non-nullable."""
    # Revert password_hash to non-nullable
    # Note: This will fail if there are users with NULL password_hash
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=False,
    )

    # Remove supabase_id index and column
    op.drop_index("ix_users_supabase_id", table_name="users")
    op.drop_column("users", "supabase_id")
