"""Fix legacy int PK: users.id -> UUID + migrate transactions FK columns

Revision ID: 20260302_lord2_safe4
Revises: 20260302_lord2_safe3
Create Date: 2026-03-02
"""
from alembic import op

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
      has_tx boolean;
      con record;
    BEGIN
      -- pgcrypto for gen_random_uuid()
      BEGIN
        CREATE EXTENSION IF NOT EXISTS pgcrypto;
      EXCEPTION WHEN insufficient_privilege THEN
        NULL;
      END;

      SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema='public' AND table_name='users'
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

      SELECT data_type
      INTO id_type
      FROM information_schema.columns
      WHERE table_schema='public' AND table_name='users' AND column_name='id';

      -- already UUID -> nothing to do
      IF id_type = 'uuid' THEN
        RETURN;
      END IF;

      -- only handle legacy integer IDs
      IF id_type NOT IN ('integer','bigint','smallint') THEN
        RAISE NOTICE 'users.id type is %, skip', id_type;
        RETURN;
      END IF;

      -- check transactions table
      SELECT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema='public' AND table_name='transactions'
      ) INTO has_tx;

      -- 1) drop FK constraints in transactions that reference users (if tx exists)
      IF has_tx THEN
        FOR con IN
          SELECT c.conname
          FROM pg_constraint c
          WHERE c.contype='f'
            AND c.conrelid='transactions'::regclass
            AND c.confrelid='users'::regclass
        LOOP
          EXECUTE format('ALTER TABLE transactions DROP CONSTRAINT %I', con.conname);
        END LOOP;
      END IF;

      -- 2) prepare uuid column on users
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='users' AND column_name='id_uuid'
      ) THEN
        ALTER TABLE users ADD COLUMN id_uuid UUID;
      END IF;

      UPDATE users
      SET id_uuid = COALESCE(id_uuid, gen_random_uuid())
      WHERE id_uuid IS NULL;

      -- drop PK now (no FK dependency)
      FOR con IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid='users'::regclass AND contype='p'
      LOOP
        EXECUTE format('ALTER TABLE users DROP CONSTRAINT %I', con.conname);
      END LOOP;

      -- rename old int id -> legacy_id (keep for mapping)
      IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema='public' AND table_name='users' AND column_name='legacy_id'
      ) THEN
        ALTER TABLE users RENAME COLUMN id TO legacy_id;
      END IF;

      -- swap uuid into id
      ALTER TABLE users RENAME COLUMN id_uuid TO id;
      ALTER TABLE users ALTER COLUMN id SET NOT NULL;

      -- recreate PK
      ALTER TABLE users ADD CONSTRAINT users_pkey PRIMARY KEY (id);

      -- 3) migrate transactions columns (if tx exists)
      IF has_tx THEN

        -- CASE A: legacy schema has sender_id/receiver_id (int)
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_id')
           AND EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_id')
        THEN
          IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_user_id') THEN
            ALTER TABLE transactions ADD COLUMN sender_user_id UUID;
          END IF;
          IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_user_id') THEN
            ALTER TABLE transactions ADD COLUMN receiver_user_id UUID;
          END IF;

          UPDATE transactions t
          SET sender_user_id = u.id
          FROM users u
          WHERE t.sender_user_id IS NULL AND u.legacy_id = t.sender_id;

          UPDATE transactions t
          SET receiver_user_id = u.id
          FROM users u
          WHERE t.receiver_user_id IS NULL AND u.legacy_id = t.receiver_id;

        END IF;

        -- CASE B: columns already named sender_user_id/receiver_user_id but are integer
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_user_id'
                   AND data_type IN ('integer','bigint','smallint'))
        THEN
          ALTER TABLE transactions ADD COLUMN IF NOT EXISTS sender_user_id_uuid UUID;
          UPDATE transactions t
          SET sender_user_id_uuid = u.id
          FROM users u
          WHERE t.sender_user_id_uuid IS NULL AND u.legacy_id = t.sender_user_id::int;

          ALTER TABLE transactions RENAME COLUMN sender_user_id TO sender_user_legacy_id;
          ALTER TABLE transactions RENAME COLUMN sender_user_id_uuid TO sender_user_id;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_user_id'
                   AND data_type IN ('integer','bigint','smallint'))
        THEN
          ALTER TABLE transactions ADD COLUMN IF NOT EXISTS receiver_user_id_uuid UUID;
          UPDATE transactions t
          SET receiver_user_id_uuid = u.id
          FROM users u
          WHERE t.receiver_user_id_uuid IS NULL AND u.legacy_id = t.receiver_user_id::int;

          ALTER TABLE transactions RENAME COLUMN receiver_user_id TO receiver_user_legacy_id;
          ALTER TABLE transactions RENAME COLUMN receiver_user_id_uuid TO receiver_user_id;
        END IF;

        -- 4) recreate FKs if columns exist
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_user_id') THEN
          BEGIN
            ALTER TABLE transactions
              ADD CONSTRAINT transactions_sender_user_id_fkey
              FOREIGN KEY (sender_user_id) REFERENCES users(id);
          EXCEPTION WHEN duplicate_object THEN NULL;
          END;
        END IF;

        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_user_id') THEN
          BEGIN
            ALTER TABLE transactions
              ADD CONSTRAINT transactions_receiver_user_id_fkey
              FOREIGN KEY (receiver_user_id) REFERENCES users(id);
          EXCEPTION WHEN duplicate_object THEN NULL;
          END;
        END IF;

      END IF;

    END $$;
    """)


def downgrade():
    pass