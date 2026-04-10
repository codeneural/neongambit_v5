import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UserMoveMastery(Base):
    __tablename__ = "user_move_mastery"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    opening_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("openings.id", ondelete="CASCADE"), index=True
    )
    move_sequence_hash: Mapped[str] = mapped_column(String, index=True)
    expected_move: Mapped[str] = mapped_column(String)  # SAN notation
    fen_before: Mapped[str] = mapped_column(String)
    move_number: Mapped[int] = mapped_column(Integer, default=1)
    easiness_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    next_review: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "move_sequence_hash", name="uq_user_move_hash"),
    )
