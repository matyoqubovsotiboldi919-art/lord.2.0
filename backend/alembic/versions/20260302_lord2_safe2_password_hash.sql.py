"""add users.password_hash safely

Revision ID: 20260302_lord2_safe2
Revises: 20260302_lord2_safe
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe2"
down_revision = "20260302_lord2_safe"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='users' AND column_name='password_hash'
      ) THEN
        ALTER TABLE users ADD COLUMN password_hash TEXT;
      END IF;
    END $$;
    """)


def downgrade():
    pass