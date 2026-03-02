"""legacy users.hashed_password nullable + backfill from password_hash

Revision ID: 20260302_lord2_safe6
Revises: 20260302_lord2_safe5
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe6"
down_revision = "20260302_lord2_safe5"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
      v_nullable text;
    BEGIN
      -- If hashed_password exists, make it compatible with new app
      IF EXISTS (
        SELECT 1
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='hashed_password'
      ) THEN

        -- Backfill hashed_password from password_hash when possible
        IF EXISTS (
          SELECT 1
          FROM information_schema.columns c
          WHERE c.table_schema='public'
            AND c.table_name='users'
            AND c.column_name='password_hash'
        ) THEN
          UPDATE users
          SET hashed_password = password_hash
          WHERE hashed_password IS NULL AND password_hash IS NOT NULL;
        END IF;

        -- Drop NOT NULL if it is currently NOT NULL
        SELECT c.is_nullable INTO v_nullable
        FROM information_schema.columns c
        WHERE c.table_schema='public'
          AND c.table_name='users'
          AND c.column_name='hashed_password';

        IF v_nullable = 'NO' THEN
          ALTER TABLE users ALTER COLUMN hashed_password DROP NOT NULL;
        END IF;

      END IF;
    END $$;
    """)


def downgrade():
    pass