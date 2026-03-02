"""safe schema upgrade for LORD 2.0

Revision ID: 20260302_lord2_safe
Revises: 
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
      -- USERS
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='public_id') THEN
        ALTER TABLE users ADD COLUMN public_id VARCHAR(32);
      END IF;
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='address') THEN
        ALTER TABLE users ADD COLUMN address VARCHAR(128);
      END IF;
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='balance_usdt') THEN
        ALTER TABLE users ADD COLUMN balance_usdt NUMERIC(20,8) NOT NULL DEFAULT 0;
      END IF;
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='status') THEN
        ALTER TABLE users ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'ACTIVE';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='role') THEN
        ALTER TABLE users ADD COLUMN role VARCHAR(16) NOT NULL DEFAULT 'USER';
      END IF;
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='last_login_at') THEN
        ALTER TABLE users ADD COLUMN last_login_at TIMESTAMPTZ NULL;
      END IF;

      -- password_hash (agar hali yo‘q bo‘lsa ham qo‘shib qo‘yamiz)
      IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='users' AND column_name='password_hash') THEN
        ALTER TABLE users ADD COLUMN password_hash TEXT NULL;
      END IF;

      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='uq_users_public_id') THEN
        CREATE UNIQUE INDEX uq_users_public_id ON users(public_id);
      END IF;
      IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='uq_users_address') THEN
        CREATE UNIQUE INDEX uq_users_address ON users(address);
      END IF;

      -- TRANSACTIONS
      IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='transactions') THEN
        CREATE TABLE transactions (
          id UUID PRIMARY KEY,
          tx_hash VARCHAR(128) UNIQUE NOT NULL,
          sender_user_id UUID NOT NULL,
          receiver_user_id UUID NOT NULL,
          sender_address VARCHAR(128) NOT NULL,
          receiver_address VARCHAR(128) NOT NULL,
          amount_usdt NUMERIC(20,8) NOT NULL,
          method VARCHAR(16) NOT NULL DEFAULT 'WEB_UI',
          status VARCHAR(16) NOT NULL DEFAULT 'CONFIRMED',
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          note TEXT NULL
        );
      ELSE
        -- Jadval bor bo‘lsa: kerakli ustunlarni qo‘shib chiqamiz
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='tx_hash') THEN
          ALTER TABLE transactions ADD COLUMN tx_hash VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_user_id') THEN
          ALTER TABLE transactions ADD COLUMN sender_user_id UUID;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_user_id') THEN
          ALTER TABLE transactions ADD COLUMN receiver_user_id UUID;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_address') THEN
          ALTER TABLE transactions ADD COLUMN sender_address VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_address') THEN
          ALTER TABLE transactions ADD COLUMN receiver_address VARCHAR(128);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='amount_usdt') THEN
          ALTER TABLE transactions ADD COLUMN amount_usdt NUMERIC(20,8);
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='method') THEN
          ALTER TABLE transactions ADD COLUMN method VARCHAR(16) NOT NULL DEFAULT 'WEB_UI';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='status') THEN
          ALTER TABLE transactions ADD COLUMN status VARCHAR(16) NOT NULL DEFAULT 'CONFIRMED';
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='created_at') THEN
          ALTER TABLE transactions ADD COLUMN created_at TIMESTAMPTZ NOT NULL DEFAULT now();
        END IF;
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='note') THEN
          ALTER TABLE transactions ADD COLUMN note TEXT;
        END IF;

        -- constraints/indexes safe
        IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='uq_transactions_tx_hash') THEN
          CREATE UNIQUE INDEX uq_transactions_tx_hash ON transactions(tx_hash);
        END IF;
      END IF;

      -- indexes (faqat ustun bor bo‘lsa)
      IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='sender_user_id')
         AND NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ix_tx_sender_created') THEN
        CREATE INDEX ix_tx_sender_created ON transactions(sender_user_id, created_at DESC);
      END IF;

      IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='transactions' AND column_name='receiver_user_id')
         AND NOT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname='ix_tx_receiver_created') THEN
        CREATE INDEX ix_tx_receiver_created ON transactions(receiver_user_id, created_at DESC);
      END IF;

      -- BLOCKS
      IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='blocks') THEN
        CREATE TABLE blocks (
          id UUID PRIMARY KEY,
          block_index BIGINT UNIQUE NOT NULL,
          prev_hash VARCHAR(128) NOT NULL,
          block_hash VARCHAR(128) UNIQUE NOT NULL,
          tx_hash VARCHAR(128) UNIQUE NOT NULL,
          sender_address VARCHAR(128) NOT NULL,
          receiver_address VARCHAR(128) NOT NULL,
          amount_usdt NUMERIC(20,8) NOT NULL,
          method VARCHAR(16) NOT NULL,
          status VARCHAR(16) NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
      END IF;

      -- SESSIONS
      IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='sessions') THEN
        CREATE TABLE sessions (
          id UUID PRIMARY KEY,
          user_id UUID NOT NULL,
          session_id VARCHAR(128) UNIQUE NOT NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
          revoked_at TIMESTAMPTZ NULL
        );
        CREATE INDEX ix_sessions_user ON sessions(user_id);
      END IF;

      -- SYSTEM LOGS
      IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='system_logs') THEN
        CREATE TABLE system_logs (
          id UUID PRIMARY KEY,
          level VARCHAR(8) NOT NULL,
          event_type VARCHAR(32) NOT NULL,
          message TEXT NOT NULL,
          actor_user_id UUID NULL,
          created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        );
        CREATE INDEX ix_system_logs_created ON system_logs(created_at DESC);
      END IF;
    END $$;
    """)


def downgrade():
    pass