import uuid
from sqlalchemy import String, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class Block(Base):
    __tablename__ = "blocks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    block_index: Mapped[int] = mapped_column(nullable=False, unique=True)
    prev_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    block_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    tx_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    sender_address: Mapped[str] = mapped_column(String(128), nullable=False)
    receiver_address: Mapped[str] = mapped_column(String(128), nullable=False)

    amount_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False)

    method: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)