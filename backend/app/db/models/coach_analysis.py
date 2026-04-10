import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class CoachAnalysis(Base):
    """
    Stores Gemini-generated narratives for Glitch Report sections.
    Keyed by user + eco_code to avoid re-calling Gemini on re-renders.
    """

    __tablename__ = "coach_analysis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    eco_code: Mapped[str] = mapped_column(String, index=True)
    locale: Mapped[str] = mapped_column(String, default="en")
    neon_diagnosis: Mapped[str] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
