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
      v_is_nullable text;
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='username'
      ) THEN
        SELECT c.is_nullable
          INTO v_is_nullable
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='username';

        IF v_is_nullable = 'NO' THEN
          ALTER TABLE users ALTER COLUMN username DROP NOT NULL;
        END IF;
      END IF;
    END $$;
    """)


def downgrade():
    pass