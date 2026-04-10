import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class GlitchReport(Base):
    __tablename__ = "glitch_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    games_analyzed: Mapped[int] = mapped_column(Integer, default=0)
    rating_at_generation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(default="lichess")
    # 'lichess' | 'sessions'
    critical_openings: Mapped[list] = mapped_column(JSON, default=list)
    # Each item: {eco_code, opening_name, games, wins, losses, win_rate,
    #   avg_collapse_move, collapse_type, neon_diagnosis, is_critical,
    #   linked_opening_id, training_unlocked}
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    overall_pattern: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
