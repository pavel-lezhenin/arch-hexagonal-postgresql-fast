"""create outbox_events table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create outbox_events table for Transactional Outbox Pattern."""
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", sa.String(length=100), nullable=False),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempts", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Index for efficient querying of unpublished events
    op.create_index(
        "idx_outbox_unpublished",
        "outbox_events",
        ["published_at", "created_at"],
        postgresql_where=sa.text("published_at IS NULL"),
    )

    # Index for monitoring failed events
    op.create_index(
        "idx_outbox_failed",
        "outbox_events",
        ["attempts", "created_at"],
        postgresql_where=sa.text("attempts > 0 AND published_at IS NULL"),
    )


def downgrade() -> None:
    """Drop outbox_events table."""
    op.drop_index("idx_outbox_failed", table_name="outbox_events")
    op.drop_index("idx_outbox_unpublished", table_name="outbox_events")
    op.drop_table("outbox_events")
