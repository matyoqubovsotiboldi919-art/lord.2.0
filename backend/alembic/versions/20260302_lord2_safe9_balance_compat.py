"""legacy users.balance nullable + default 0 (compat)

Revision ID: 20260302_lord2_safe9
Revises: 20260302_lord2_safe8
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe9"
down_revision = "20260302_lord2_safe8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_schema='public' AND table_name='users' AND column_name='balance'
          ) THEN
            -- fill existing nulls
            UPDATE users SET balance = 0 WHERE balance IS NULL;

            -- default 0
            BEGIN
              ALTER TABLE users ALTER COLUMN balance SET DEFAULT 0;
            EXCEPTION WHEN undefined_column THEN
              NULL;
            END;

            -- allow nulls so inserts don't crash (app doesn't write this column)
            BEGIN
              ALTER TABLE users ALTER COLUMN balance DROP NOT NULL;
            EXCEPTION WHEN undefined_column THEN
              NULL;
            END;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    pass