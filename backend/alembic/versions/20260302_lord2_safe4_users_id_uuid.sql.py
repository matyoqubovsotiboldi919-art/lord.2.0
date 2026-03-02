"""users.id -> UUID safety fix (convert int id to uuid if needed)

Revision ID: 20260302_lord2_safe4
Revises: 20260302_lord2_safe3
Create Date: 2026-03-02
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260302_lord2_safe4"
down_revision = "20260302_lord2_safe3"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    DECLARE
      id_type text;
      has_users boolean;
    BEGIN
      -- pgcrypto for gen_random_uuid()
      BEGIN
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
      EXCEPTION WHEN insufficient_privilege THEN
        -- ignore if cannot create extension (Render usually allows)
        NULL;
      END;

      SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = 'users'
      ) INTO has_users;

      IF NOT has_users THEN
        -- Fresh DB: create users with UUID PK
        CREATE TABLE users (
          id UUID PRIMARY KEY,
          email VARCHAR(255) UNIQUE NOT NULL,
          password_hash VARCHAR(255) NOT NULL,
          public_id VARCHAR(32) UNIQUE,
          address VARCHAR(128) UNIQUE,
          balance_usdt NUMERIC(20,8) NOT NULL DEFAULT 0,
          status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE',
          role VARCHAR(16) NOT NULL DEFAULT 'USER',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          last_login_at TIMESTAMPTZ NULL
        );
        RETURN;
      END IF;

      -- users exists: check current id datatype
      SELECT data_type
      INTO id_type
      FROM information_schema.columns
      WHERE table_schema='public' AND table_name='users' AND column_name='id';

      -- If already UUID, do nothing
      IF id_type = 'uuid' THEN
        RETURN;
      END IF;

      -- If integer/bigint: convert safely by creating new uuid column then swapping
      IF id_type IN ('integer', 'bigint', 'smallint') THEN

        -- add new uuid column if missing
        IF NOT EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema='public' AND table_name='users' AND column_name='id_uuid'
        ) THEN
          ALTER TABLE users ADD COLUMN id_uuid UUID;
        END IF;

        -- fill nulls
        UPDATE users
        SET id_uuid = COALESCE(id_uuid, gen_random_uuid())
        WHERE id_uuid IS NULL;

        -- drop old PK if exists (name unknown) and create PK on uuid later
        -- first drop constraints that are primary keys on users
        PERFORM 1;

        -- rename old id to legacy_id (if not already)
        IF EXISTS (
          SELECT 1 FROM information_schema.columns
          WHERE table_schema='public' AND table_name='users' AND column_name='legacy_id'
        ) THEN
          -- already renamed before, do nothing
          NULL;
        ELSE
          ALTER TABLE users RENAME COLUMN id TO legacy_id;
        END IF;

        -- rename id_uuid to id
        ALTER TABLE users RENAME COLUMN id_uuid TO id;

        -- set not null
        ALTER TABLE users ALTER COLUMN id SET NOT NULL;

        -- drop existing PK constraint (whatever name)
        EXECUTE (
          SELECT format('ALTER TABLE users DROP CONSTRAINT %I', conname)
          FROM pg_constraint
          WHERE conrelid = 'users'::regclass AND contype='p'
          LIMIT 1
        );

        -- create new PK
        ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id);

        -- ensure email unique (if not exists)
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='uq_users_email') THEN
          BEGIN
            CREATE UNIQUE INDEX uq_users_email ON users(email);
          EXCEPTION WHEN duplicate_table THEN
            NULL;
          END;
        END IF;

      END IF;
    END $$;
    """)


def downgrade():
    # Intentionally no downgrade (dangerous to revert ids)
    pass