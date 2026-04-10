import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class OpeningCache(Base):
    """
    Caches Lichess Explorer moves for a given FEN + ELO bucket.
    TTL: 30 days (enforced by application logic, not DB).
    """

    __tablename__ = "opening_cache"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fen_hash: Mapped[str] = mapped_column(String, index=True)
    elo_bucket: Mapped[int] = mapped_column(Integer)  # e.g. 1200
    moves: Mapped[list] = mapped_column(JSON, default=list)
    # Each: {uci, san, frequency, win_rate}
    cached_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)
