"""transactions.id integer -> uuid (legacy compat)

Revision ID: 20260303_lord2_safe9
Revises: 20260302_lord2_safe8
Create Date: 2026-03-03
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260303_lord2_safe9"
down_revision = "20260302_lord2_safe8"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
DO $$
DECLARE
  id_type text;
  pk_name text;
BEGIN
  -- Ensure pgcrypto for gen_random_uuid()
  BEGIN
    CREATE EXTENSION IF NOT EXISTS pgcrypto;
  EXCEPTION WHEN OTHERS THEN
    -- If extension cannot be created (permissions), we will still try; default may fail later
    NULL;
  END;

  -- Detect current data type of transactions.id
  SELECT data_type INTO id_type
  FROM information_schema.columns
  WHERE table_schema='public' AND table_name='transactions' AND column_name='id';

  -- If table/column missing -> nothing
  IF id_type IS NULL THEN
    RETURN;
  END IF;

  -- If already uuid -> ensure default
  IF id_type = 'uuid' THEN
    BEGIN
      ALTER TABLE public.transactions
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    EXCEPTION WHEN OTHERS THEN
      NULL;
    END;
    RETURN;
  END IF;

  -- If legacy integer -> migrate to uuid safely
  IF id_type IN ('integer', 'bigint', 'smallint') THEN

    -- 1) Add new uuid column if not exists
    IF NOT EXISTS (
      SELECT 1 FROM information_schema.columns
      WHERE table_schema='public' AND table_name='transactions' AND column_name='id_uuid'
    ) THEN
      ALTER TABLE public.transactions ADD COLUMN id_uuid uuid;
    END IF;

    -- 2) Backfill uuid for all rows
    UPDATE public.transactions
    SET id_uuid = gen_random_uuid()
    WHERE id_uuid IS NULL;

    -- 3) Drop PK constraint (if any) to allow swap
    SELECT tc.constraint_name INTO pk_name
    FROM information_schema.table_constraints tc
    WHERE tc.table_schema='public'
      AND tc.table_name='transactions'
      AND tc.constraint_type='PRIMARY KEY'
    LIMIT 1;

    IF pk_name IS NOT NULL THEN
      EXECUTE format('ALTER TABLE public.transactions DROP CONSTRAINT %I', pk_name);
    END IF;

    -- 4) Drop old id column (integer)
    ALTER TABLE public.transactions DROP COLUMN id;

    -- 5) Rename id_uuid -> id
    ALTER TABLE public.transactions RENAME COLUMN id_uuid TO id;

    -- 6) Set NOT NULL + DEFAULT + new PK
    BEGIN
      ALTER TABLE public.transactions
        ALTER COLUMN id SET NOT NULL,
        ALTER COLUMN id SET DEFAULT gen_random_uuid();
    EXCEPTION WHEN OTHERS THEN
      -- if default fails due to missing extension, still keep NOT NULL
      ALTER TABLE public.transactions
        ALTER COLUMN id SET NOT NULL;
    END;

    ALTER TABLE public.transactions
      ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);

  END IF;
END $$;
"""
    )


def downgrade():
    # We do not downgrade this legacy fix safely (would require generating sequences and losing UUID mapping).
    pass