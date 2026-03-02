import uuid
from sqlalchemy import String, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    tx_hash: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    sender_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    receiver_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)

    sender_address: Mapped[str] = mapped_column(String(128), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(128), nullable=False)

    amount_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)

    method: Mapped[str] = mapped_column(String(16), nullable=False, server_default="WEB_UI")  # WEB_UI|API|SYSTEM
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="CONFIRMED")  # PENDING|CONFIRMED|FAILED

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)