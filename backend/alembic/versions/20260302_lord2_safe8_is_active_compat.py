"""legacy users.is_active nullable + default true (compat)

Revision ID: 20260302_lord2_safe8
Revises: 20260302_lord2_safe7
Create Date: 2026-03-02
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260302_lord2_safe8"
down_revision = "20260302_lord2_safe7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          -- If users.is_active exists: make it safe for inserts that don't provide it
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name='users' AND column_name='is_active'
          ) THEN
            -- backfill existing NULLs
            UPDATE users SET is_active = TRUE WHERE is_active IS NULL;

            -- set default TRUE
            BEGIN
              ALTER TABLE users ALTER COLUMN is_active SET DEFAULT TRUE;
            EXCEPTION WHEN undefined_column THEN
              NULL;
            END;

            -- drop NOT NULL (so inserts without is_active won't crash)
            BEGIN
              ALTER TABLE users ALTER COLUMN is_active DROP NOT NULL;
            EXCEPTION WHEN undefined_column THEN
              NULL;
            END;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # keep compat changes (no downgrade)
    pass