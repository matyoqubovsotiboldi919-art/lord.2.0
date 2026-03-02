"""transactions legacy columns nullable (compat)

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
        WHERE table_schema='public' AND table_name='transactions' AND column_name='sender_id'
      ) THEN
        BEGIN
          ALTER TABLE transactions ALTER COLUMN sender_id DROP NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END;
      END IF;

      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='transactions' AND column_name='receiver_id'
      ) THEN
        BEGIN
          ALTER TABLE transactions ALTER COLUMN receiver_id DROP NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END;
      END IF;

      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='transactions' AND column_name='sender'
      ) THEN
        BEGIN
          ALTER TABLE transactions ALTER COLUMN sender DROP NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END;
      END IF;

      IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='transactions' AND column_name='receiver'
      ) THEN
        BEGIN
          ALTER TABLE transactions ALTER COLUMN receiver DROP NOT NULL;
        EXCEPTION WHEN others THEN NULL;
        END;
      END IF;
    END $$;
    """)


def downgrade() -> None:
    pass