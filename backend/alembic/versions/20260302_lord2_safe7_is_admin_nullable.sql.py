"""legacy users.is_admin nullable + default false (compat)

Revision ID: 20260302_lord2_safe7
Revises: 20260302_lord2_safe6
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe7"
down_revision = "20260302_lord2_safe6"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
      v_nullable text;
    BEGIN
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='is_admin'
      ) THEN

        -- fill nulls
        UPDATE users SET is_admin = FALSE WHERE is_admin IS NULL;

        -- set default false (safe)
        BEGIN
          ALTER TABLE users ALTER COLUMN is_admin SET DEFAULT FALSE;
        EXCEPTION WHEN undefined_column THEN
          NULL;
        END;

        -- drop NOT NULL if needed
        SELECT c.is_nullable INTO v_nullable
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='is_admin';

        IF v_nullable = 'NO' THEN
          ALTER TABLE users ALTER COLUMN is_admin DROP NOT NULL;
        END IF;

      END IF;
    END $$;
    """)


def downgrade():
    pass