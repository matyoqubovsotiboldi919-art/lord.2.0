"""initial schema

Revision ID: 20260508_initial_schema
Revises:
Create Date: 2026-05-08
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260508_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(320), nullable=False, unique=True),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("public_id", sa.String(32), nullable=False, unique=True),
        sa.Column("address", sa.String(128), nullable=False, unique=True),
        sa.Column("balance_usdt", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("status", sa.String(16), nullable=False, server_default="ACTIVE"),
        sa.Column("role", sa.String(16), nullable=False, server_default="USER"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tx_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("sender_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("receiver_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("sender_address", sa.String(128), nullable=False),
        sa.Column("receiver_address", sa.String(128), nullable=False),
        sa.Column("amount_usdt", sa.Numeric(20, 8), nullable=False),
        sa.Column("method", sa.String(16), nullable=False, server_default="WEB_UI"),
        sa.Column("status", sa.String(16), nullable=False, server_default="CONFIRMED"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
    )

    op.create_table(
        "blocks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("block_index", sa.Integer(), nullable=False, unique=True),
        sa.Column("prev_hash", sa.String(128), nullable=False),
        sa.Column("block_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("tx_hash", sa.String(128), nullable=False, unique=True),
        sa.Column("sender_address", sa.String(128), nullable=False),
        sa.Column("receiver_address", sa.String(128), nullable=False),
        sa.Column("amount_usdt", sa.Numeric(20, 8), nullable=False),
        sa.Column("method", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("session_id", sa.String(128), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "system_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("level", sa.String(8), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("ip", sa.String(64), nullable=True),
        sa.Column("user_agent", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("system_logs")
    op.drop_table("sessions")
    op.drop_table("blocks")
    op.drop_table("transactions")
    op.drop_table("users")