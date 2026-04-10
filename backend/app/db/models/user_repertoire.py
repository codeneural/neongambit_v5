import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UserRepertoire(Base):
    __tablename__ = "user_repertoire"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    opening_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("openings.id", ondelete="CASCADE")
    )
    training_unlocked: Mapped[bool] = mapped_column(Boolean, default=False)
    # Free tier: top 2 critical openings = True. Pro: all = True.
    added_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user_id", "opening_id", name="uq_user_opening"),
    )
