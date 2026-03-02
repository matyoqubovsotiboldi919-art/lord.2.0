"""add ip and user_agent columns to system_logs

Revision ID: 20260302_lord2_safe3
Revises: 20260302_lord2_safe
Create Date: 2026-03-02
"""
from alembic import op

revision = "20260302_lord2_safe3"
down_revision = "20260302_lord2_safe"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    DO $$
    BEGIN
      IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='system_logs') THEN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_logs' AND column_name='ip') THEN
          ALTER TABLE system_logs ADD COLUMN ip VARCHAR(64);
        END IF;

        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='system_logs' AND column_name='user_agent') THEN
          ALTER TABLE system_logs ADD COLUMN user_agent VARCHAR(255);
        END IF;
      END IF;
    END $$;
    """)


def downgrade():
    pass