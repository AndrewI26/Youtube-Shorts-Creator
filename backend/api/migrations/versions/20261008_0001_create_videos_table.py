"""create videos table

Revision ID: 0001
Revises: 
Create Date: 2026-10-08 14:56:29.867665

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "videos",
        sa.Column("id", sa.BigInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("subreddit", sa.String(length=255), nullable=False),
        sa.Column("post_title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_name", sa.String(length=225), nullable=False),
        sa.Column("video_choice", sa.String(length=500), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("videos")
