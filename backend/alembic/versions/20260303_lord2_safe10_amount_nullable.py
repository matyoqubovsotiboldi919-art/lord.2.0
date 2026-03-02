"""legacy transactions.amount nullable + backfill from amount_usdt

Revision ID: 20260303_lord2_safe10
Revises: 9f76d23e8bb0
Create Date: 2026-03-03
"""
from alembic import op

revision = "20260303_lord2_safe10"
down_revision = "9f76d23e8bb0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='transactions' AND column_name='amount'
      ) THEN
        UPDATE transactions
        SET amount = amount_usdt
        WHERE amount IS NULL;

        BEGIN
          ALTER TABLE transactions ALTER COLUMN amount DROP NOT NULL;
        EXCEPTION WHEN others THEN
          NULL;
        END;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    pass