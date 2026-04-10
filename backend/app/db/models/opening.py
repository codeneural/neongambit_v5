import uuid
from datetime import datetime

from sqlalchemy import JSON, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Opening(Base):
    __tablename__ = "openings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    eco_code: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    color: Mapped[str] = mapped_column(String)          # 'white' | 'black'
    starting_moves: Mapped[list] = mapped_column(JSON, default=list)
    # e.g. ['e4', 'c5', 'Nf3', 'd6'] — SAN notation
    theory_depth: Mapped[int] = mapped_column(default=10)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
