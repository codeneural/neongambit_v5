import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class LichessGame(Base):
    __tablename__ = "lichess_games"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    lichess_game_id: Mapped[str] = mapped_column(String, index=True)
    eco_code: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    opening_name: Mapped[str | None] = mapped_column(String, nullable=True)
    winner: Mapped[str | None] = mapped_column(String, nullable=True)
    # 'white' | 'black' | 'draw'
    user_color: Mapped[str | None] = mapped_column(String, nullable=True)
    user_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    opponent_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pgn: Mapped[str | None] = mapped_column(String, nullable=True)
    played_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "lichess_game_id", name="uq_user_lichess_game"),
    )
