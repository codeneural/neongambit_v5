import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class LichessRatingSnapshot(Base):
    __tablename__ = "lichess_rating_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    rating: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String, default="import")
    # 'import' | 'auto'
    snapshotted_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
