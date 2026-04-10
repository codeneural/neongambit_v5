import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    firebase_uid: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    guest_token: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    lichess_username: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )
    target_elo: Mapped[int] = mapped_column(Integer, default=1200)
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("target_elo BETWEEN 800 AND 3000", name="ck_user_elo_range"),
    )
