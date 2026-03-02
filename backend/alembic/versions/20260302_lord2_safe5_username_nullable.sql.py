"""users.username nullable fix (legacy db compatibility)

Revision ID: 20260302_lord2_safe5
Revises: 20260302_lord2_safe4
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe5"
down_revision = "20260302_lord2_safe4"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
      is_nullable text;
    BEGIN
      -- If users.username exists and is NOT NULL -> make it nullable
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='users' AND column_name='username'
      ) THEN
        SELECT is_nullable INTO is_nullable
        FROM information_schema.columns
        WHERE table_schema='public' AND table_name='users' AND column_name='username';

        IF is_nullable = 'NO' THEN
          ALTER TABLE users ALTER COLUMN username DROP NOT NULL;
        END IF;

        -- Optional: if there is a unique index/constraint on username, we keep it.
        -- Because username is no longer used by the app, leaving it is safe.
      END IF;
    END $$;
    """)


def downgrade():
    pass