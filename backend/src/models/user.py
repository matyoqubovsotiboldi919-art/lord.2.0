import uuid
from sqlalchemy import String, DateTime, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)

    public_id: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    address: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)

    balance_usdt: Mapped[float] = mapped_column(Numeric(20, 8), nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(16), nullable=False, server_default="ACTIVE")  # ACTIVE|FROZEN|LOCKED
    role: Mapped[str] = mapped_column(String(16), nullable=False, server_default="USER")     # USER|ADMIN

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_login_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)