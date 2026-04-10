# Skill: database-neon

SQLAlchemy async models + Alembic migrations for Neon PostgreSQL.

## Session Setup (Section 3)

```python
# app/db/session.py
engine = create_async_engine(
    settings.DATABASE_URL,   # postgresql+asyncpg://...
    pool_pre_ping=True, pool_size=5, max_overflow=10,
)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## Core Models (Section 4)

### User
```python
class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    firebase_uid: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    guest_token: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    lichess_username: Mapped[str | None] = mapped_column(String, index=True)
    target_elo: Mapped[int] = mapped_column(Integer, default=1200)
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    __table_args__ = (CheckConstraint("target_elo BETWEEN 800 AND 3000"),)
```

### SparringSession
```python
class SparringSession(Base):
    __tablename__ = "sparring_sessions"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opening_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("openings.id"))
    player_color: Mapped[str] = mapped_column(String)
    current_fen: Mapped[str] = mapped_column(String)
    move_history: Mapped[list] = mapped_column(JSON, default=list)
    accuracy_score: Mapped[float] = mapped_column(Float, default=100.0)
    theory_integrity: Mapped[float] = mapped_column(Float, default=100.0)
    theory_exit_move: Mapped[int | None] = mapped_column(Integer)
    session_status: Mapped[str] = mapped_column(String, default="active")
    __table_args__ = (
        CheckConstraint("session_status IN ('active','completed','abandoned')"),
        CheckConstraint("accuracy_score >= 0 AND accuracy_score <= 100"),
    )
```

### GlitchReport
```python
class GlitchReport(Base):
    __tablename__ = "glitch_reports"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    critical_openings: Mapped[list] = mapped_column(JSON, default=list)
    # Each item: {eco_code, opening_name, games, wins, losses, win_rate, avg_collapse_move,
    #   collapse_type ('opening_error'|'tactical_blunder'|'positional_drift'|'time_pressure'),
    #   neon_diagnosis, is_critical, linked_opening_id, training_unlocked}
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    overall_pattern: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
```

### UserMoveMastery (SRS cards)
```python
class UserMoveMastery(Base):
    __tablename__ = "user_move_mastery"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    opening_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("openings.id", ondelete="CASCADE"))
    move_sequence_hash: Mapped[str] = mapped_column(String)
    expected_move: Mapped[str] = mapped_column(String)
    fen_before: Mapped[str] = mapped_column(String)
    easiness_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
```

## MVP Models (do NOT create Phase 2 tables)

**MVP only:** users, openings, user_repertoire, sparring_sessions, lichess_games,
glitch_reports, lichess_rating_snapshots, user_move_mastery, user_stats,
opening_cache, coach_analysis, subscriptions.

**Phase 2 deferred (never create unless explicitly asked):** conversion_failures,
endgame_drill_cards, achievements.

## Alembic (async config)

```python
# alembic/env.py
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
# Alembic uses sync driver (psycopg2) for migrations
target_metadata = Base.metadata
```

Commands:
```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

**NEVER run migrations in production without explicit user confirmation.**

## All models re-exported from `app/db/models/__init__.py` so Alembic detects them.
