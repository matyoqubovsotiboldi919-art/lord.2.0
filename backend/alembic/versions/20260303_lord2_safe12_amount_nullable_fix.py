"""legacy transactions.amount nullable + backfill from amount_usdt (compat)

Revision ID: 20260303_lord2_safe12
Revises: 20260303_lord2_safe11
Create Date: 2026-03-03
"""

from alembic import op
import sqlalchemy as sa

revision = "20260303_lord2_safe12"
down_revision = "20260303_lord2_safe11"
branch_labels = None
depends_on = None


def upgrade():
    # 1) amount ustunini NULL bo'lishiga ruxsat beramiz (legacy compat)
    op.alter_column("transactions", "amount", existing_type=sa.Numeric(20, 8), nullable=True)

    # 2) Eski rowlarda amount NULL bo'lsa amount_usdt dan to'ldiramiz
    op.execute("UPDATE transactions SET amount = amount_usdt WHERE amount IS NULL AND amount_usdt IS NOT NULL")


def downgrade():
    # Downgrade: NULL qolmasin deb 0 qo'yib, qayta NOT NULL qilamiz
    op.execute("UPDATE transactions SET amount = 0 WHERE amount IS NULL")
    op.alter_column("transactions", "amount", existing_type=sa.Numeric(20, 8), nullable=False)