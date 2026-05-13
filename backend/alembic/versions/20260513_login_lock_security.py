"""add login lock security columns

Revision ID: 20260513_login_lock_security
Revises: 20260508_initial_schema
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa


revision = "20260513_login_lock_security"
down_revision = "20260508_initial_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "users",
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("users", "locked_until")
    op.drop_column("users", "failed_login_count")