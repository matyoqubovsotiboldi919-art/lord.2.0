"""merge heads safe9

Revision ID: 9f76d23e8bb0
Revises: 20260302_lord2_safe9, 20260303_lord2_safe9
Create Date: 2026-03-03
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "9f76d23e8bb0"
down_revision = ("20260302_lord2_safe9", "20260303_lord2_safe9")
branch_labels = None
depends_on = None


def upgrade() -> None:
    # merge revision - no DB changes
    pass


def downgrade() -> None:
    # cannot reliably downgrade a merge without choosing a branch
    pass