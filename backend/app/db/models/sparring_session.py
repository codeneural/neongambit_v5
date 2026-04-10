import uuid
from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SparringSession(Base):
    __tablename__ = "sparring_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    opening_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("openings.id"), nullable=True
    )
    player_color: Mapped[str] = mapped_column(String)       # 'white' | 'black'
    opponent_elo: Mapped[int] = mapped_column(Integer, default=1200)
    current_fen: Mapped[str] = mapped_column(String)
    move_history: Mapped[list] = mapped_column(JSON, default=list)
    accuracy_score: Mapped[float] = mapped_column(Float, default=100.0)
    theory_integrity: Mapped[float] = mapped_column(Float, default=100.0)
    theory_exit_move: Mapped[int | None] = mapped_column(Integer, nullable=True)
    session_status: Mapped[str] = mapped_column(String, default="active")
    result: Mapped[str | None] = mapped_column(String, nullable=True)
    # 'win' | 'loss' | 'draw' | null
    excellent_moves: Mapped[int] = mapped_column(Integer, default=0)
    good_moves: Mapped[int] = mapped_column(Integer, default=0)
    inaccuracies: Mapped[int] = mapped_column(Integer, default=0)
    mistakes: Mapped[int] = mapped_column(Integer, default=0)
    blunders: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "session_status IN ('active','completed','abandoned')",
            name="ck_session_status",
        ),
        CheckConstraint(
            "accuracy_score >= 0 AND accuracy_score <= 100",
            name="ck_accuracy_range",
        ),
    )
