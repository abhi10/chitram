"""add user lockout fields for brute force protection

Phase Security: Add failed_login_attempts counter and locked_until timestamp
for brute force protection. Accounts lock for 15 minutes after 5 failed attempts.

Revision ID: sec01_user_lockout
Revises: okr4l08scgm2
Create Date: 2026-02-02 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "sec01_user_lockout"
down_revision: str | Sequence[str] | None = "okr4l08scgm2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add brute force protection fields to users table."""
    # Add failed_login_attempts counter
    op.add_column(
        "users",
        sa.Column(
            "failed_login_attempts",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )

    # Add locked_until timestamp for account lockout
    op.add_column(
        "users",
        sa.Column(
            "locked_until",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove brute force protection fields from users table."""
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_attempts")
