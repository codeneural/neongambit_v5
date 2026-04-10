# DIRECTIVE D-001 — Backend Scaffold
**Status:** ISSUED
**Phase:** 0 — Foundation
**Branch:** `agent/backend-scaffold`
**Skills required:** `backend-fastapi`, `database-neon`
**Blocks:** D-003 (Auth), D-005 (Lichess Import), D-007 (Glitch Report), D-009 (Sparring), D-011 (Neural Drill), D-013 (Analytics), D-015 (Subscriptions)
**ADR flags:** None — this directive contains no auth logic, no Stripe, no production DB access.

---

## Objective

Create the complete `/backend/` directory structure for NeonGambit. This includes:
- FastAPI application factory with lifespan
- Pydantic settings (config.py)
- All MVP SQLAlchemy async models
- Alembic migration configuration
- Auth dependencies (skeleton only — no business logic yet)
- `/health` endpoint
- pytest conftest.py with async test fixtures
- TDD: `test_health.py` (written BEFORE implementation per TDD mandate)

**Do NOT implement any service logic.** Do NOT create `/frontend/`. Do NOT run `alembic upgrade head`.

---

## Branch Instructions

```bash
git checkout master
git pull origin master
git checkout -b agent/backend-scaffold
```

All commits to this branch. Conventional commit format required.

---

## Directory Structure to Create

Create exactly this structure under `/backend/`:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py
│   │   └── exceptions.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── session.py
│   │   └── models/
│   │       ├── __init__.py
│   │       ├── user.py
│   │       ├── sparring_session.py
│   │       ├── opening.py
│   │       ├── user_repertoire.py
│   │       ├── lichess_game.py
│   │       ├── glitch_report.py
│   │       ├── lichess_rating_snapshot.py
│   │       ├── user_move_mastery.py
│   │       ├── user_stats.py
│   │       ├── opening_cache.py
│   │       ├── coach_analysis.py
│   │       └── subscription.py
│   ├── schemas/
│   │   └── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── router.py
│   ├── services/
│   │   └── __init__.py
│   ├── workers/
│   │   └── __init__.py
│   └── utils/
│       ├── __init__.py
│       └── cache.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
├── alembic/
│   ├── env.py
│   └── script.py.mako
├── alembic.ini
├── requirements.txt
├── .env.example
└── pyproject.toml
```

---

## File Specifications

### `/backend/requirements.txt`

```
fastapi==0.111.0
uvicorn[standard]==0.29.0
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
psycopg2-binary==2.9.9
alembic==1.13.1
pydantic-settings==2.2.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
redis==5.0.4
firebase-admin==6.5.0
google-generativeai==0.5.4
stripe==9.9.0
python-chess==1.999
pytest==8.2.0
pytest-asyncio==0.23.6
pytest-cov==5.0.0
anyio==4.3.0
black==24.4.2
ruff==0.4.4
mypy==1.10.0
```

---

### `/backend/pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
select = ["E", "F", "I"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true
```

---

### `/backend/.env.example`

```
DATABASE_URL=postgresql+asyncpg://user:password@host/dbname
REDIS_URL=redis://localhost:6379
FIREBASE_PROJECT_ID=your-firebase-project-id
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-credentials.json
JWT_SECRET_KEY=change-this-to-a-secure-random-string
GOOGLE_GEMINI_API_KEY=your-gemini-api-key
STOCKFISH_PATH=/usr/local/bin/stockfish
STOCKFISH_MAX_DEPTH=15
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
CORS_ORIGINS=["http://localhost:3000","https://neongambit.com"]
RATE_LIMIT_DRILLS_FREE_PER_DAY=5
```

**CRITICAL: Never create a `.env` file. Only `.env.example`. Never commit secrets.**

---

### `/backend/app/config.py`

```python
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: str
    JWT_SECRET_KEY: str
    GOOGLE_GEMINI_API_KEY: str
    STOCKFISH_PATH: str = "/usr/local/bin/stockfish"
    STOCKFISH_MAX_DEPTH: int = 15
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]
    RATE_LIMIT_DRILLS_FREE_PER_DAY: int = 5

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
```

---

### `/backend/app/db/base.py`

```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

---

### `/backend/app/db/session.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:  # type: ignore[return]
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

---

### `/backend/app/db/models/user.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, unique=True, nullable=True)
    firebase_uid: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    guest_token: Mapped[str | None] = mapped_column(
        String, unique=True, index=True, nullable=True
    )
    lichess_username: Mapped[str | None] = mapped_column(
        String, index=True, nullable=True
    )
    target_elo: Mapped[int] = mapped_column(Integer, default=1200)
    preferred_language: Mapped[str] = mapped_column(String, default="en")
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("target_elo BETWEEN 800 AND 3000", name="ck_user_elo_range"),
    )
```

---

### `/backend/app/db/models/opening.py`

```python
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
```

---

### `/backend/app/db/models/user_repertoire.py`

```python
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
```

---

### `/backend/app/db/models/sparring_session.py`

```python
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
```

---

### `/backend/app/db/models/lichess_game.py`

```python
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
```

---

### `/backend/app/db/models/glitch_report.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Text
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
```

---

### `/backend/app/db/models/lichess_rating_snapshot.py`

```python
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
```

---

### `/backend/app/db/models/user_move_mastery.py`

```python
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
    expected_move: Mapped[str] = mapped_column(String)      # SAN notation
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
        UniqueConstraint(
            "user_id", "move_sequence_hash", name="uq_user_move_hash"
        ),
    )
```

---

### `/backend/app/db/models/user_stats.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class UserStats(Base):
    __tablename__ = "user_stats"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True, index=True
    )
    consecutive_sparring_losses: Mapped[int] = mapped_column(Integer, default=0)
    last_sparring_loss_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

---

### `/backend/app/db/models/opening_cache.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String
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
    elo_bucket: Mapped[int] = mapped_column(Integer)        # e.g. 1200
    moves: Mapped[list] = mapped_column(JSON, default=list)
    # Each: {uci, san, frequency, win_rate}
    cached_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime)
```

---

### `/backend/app/db/models/coach_analysis.py`

```python
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
```

---

### `/backend/app/db/models/subscription.py`

```python
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    stripe_subscription_id: Mapped[str] = mapped_column(String, unique=True)
    stripe_customer_id: Mapped[str] = mapped_column(String, index=True)
    plan: Mapped[str] = mapped_column(String)       # 'monthly' | 'annual'
    status: Mapped[str] = mapped_column(String)     # 'active' | 'cancelled' | 'past_due'
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
```

---

### `/backend/app/db/models/__init__.py`

**CRITICAL:** All models must be imported here so Alembic autogenerate detects them.

```python
from app.db.models.user import User
from app.db.models.opening import Opening
from app.db.models.user_repertoire import UserRepertoire
from app.db.models.sparring_session import SparringSession
from app.db.models.lichess_game import LichessGame
from app.db.models.glitch_report import GlitchReport
from app.db.models.lichess_rating_snapshot import LichessRatingSnapshot
from app.db.models.user_move_mastery import UserMoveMastery
from app.db.models.user_stats import UserStats
from app.db.models.opening_cache import OpeningCache
from app.db.models.coach_analysis import CoachAnalysis
from app.db.models.subscription import Subscription

__all__ = [
    "User",
    "Opening",
    "UserRepertoire",
    "SparringSession",
    "LichessGame",
    "GlitchReport",
    "LichessRatingSnapshot",
    "UserMoveMastery",
    "UserStats",
    "OpeningCache",
    "CoachAnalysis",
    "Subscription",
]
```

---

### `/backend/app/core/security.py`

```python
from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from app.config import get_settings

settings = get_settings()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Create a signed JWT. subject = user.id (str)."""
    expire = datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=ALGORITHM)


def decode_jwt(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT. Returns payload dict or None if invalid."""
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None
```

---

### `/backend/app/core/exceptions.py`

```python
from fastapi import HTTPException, status


class NotFoundError(HTTPException):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


class UnauthorizedError(HTTPException):
    def __init__(self, detail: str = "Not authenticated") -> None:
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(HTTPException):
    def __init__(self, detail: str = "Grandmaster tier required") -> None:
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class BadRequestError(HTTPException):
    def __init__(self, detail: str = "Bad request") -> None:
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
```

---

### `/backend/app/dependencies.py`

Skeleton only. Auth business logic comes in D-003.

```python
from typing import AsyncGenerator

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_jwt
from app.db.session import get_db
from app.db.models.user import User

bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Dependency for protected endpoints.
    Full implementation in D-003 (Auth).
    This skeleton raises 401 for all requests — replaced in D-003.
    """
    if not credentials:
        raise UnauthorizedError()
    payload = decode_jwt(credentials.credentials)
    if not payload:
        raise UnauthorizedError("Invalid token")
    # Full DB lookup implemented in D-003
    raise UnauthorizedError("Auth service not yet initialized")


async def require_pro(user: User = Depends(get_current_user)) -> User:
    """Dependency for Pro-gated endpoints."""
    if not user.is_pro:
        from app.core.exceptions import ForbiddenError
        raise ForbiddenError()
    return user
```

---

### `/backend/app/utils/cache.py`

```python
from redis.asyncio import Redis

from app.config import get_settings

settings = get_settings()

_redis_client: Redis | None = None


def get_redis() -> Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client
```

---

### `/backend/app/api/v1/router.py`

```python
from fastapi import APIRouter

# Routers will be imported and included here as features are built.
# D-003 will add: from app.api.v1.endpoints.auth import router as auth_router

v1_router = APIRouter()

# Placeholder — each directive adds its router here.
```

---

### `/backend/app/main.py`

```python
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.config import get_settings
from app.utils.cache import get_redis

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Validate Redis connection on startup
    redis = get_redis()
    await redis.ping()
    yield
    await redis.aclose()


app = FastAPI(
    title="NeonGambit API",
    version="5.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/v1")


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok", "version": "5.1.0"}
```

---

### `/backend/alembic/env.py`

```python
import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import get_settings
from app.db.base import Base

# Import all models so Alembic detects them
import app.db.models  # noqa: F401

settings = get_settings()
config = context.config
fileConfig(config.config_file_name)  # type: ignore[arg-type]

# Use sync psycopg2 driver for Alembic (not asyncpg)
sync_url = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
config.set_main_option("sqlalchemy.url", sync_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),  # type: ignore[arg-type]
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

### `/backend/alembic.ini`

Standard Alembic ini. Set `script_location = alembic`. Leave `sqlalchemy.url` blank (set programmatically in env.py).

```ini
[alembic]
script_location = alembic
prepend_sys_path = .
version_path_separator = os

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

---

## TDD: Tests (Write BEFORE Implementation)

### `/backend/tests/conftest.py`

```python
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.base import Base
from app.main import app
from app.db.session import get_db

# Use in-memory SQLite for tests — never touch production DB
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(engine):
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

**Note:** `aiosqlite` must be added to requirements.txt:
```
aiosqlite==0.20.0
```

---

### `/backend/tests/test_health.py`

**Write this FIRST. Run it. Confirm it FAILS. Then implement `main.py`. Then confirm it PASSES.**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "5.1.0"


@pytest.mark.anyio
async def test_health_does_not_require_auth(client: AsyncClient) -> None:
    """Health endpoint must be accessible without any token."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_v1_prefix_404_on_unknown_route(client: AsyncClient) -> None:
    """Unknown v1 routes must 404, not 500."""
    response = await client.get("/v1/does-not-exist")
    assert response.status_code == 404
```

---

## Alembic Migration (DO NOT RUN — show output only)

After all models are created, run:

```bash
cd backend
alembic revision --autogenerate -m "initial_schema"
```

**STOP.** Show the generated migration file content to the human before proceeding. Do NOT run `alembic upgrade head`. The human will review and confirm.

---

## Commit Sequence

```
feat: initialize backend project structure and requirements
feat: add SQLAlchemy async session and Base model
feat: add all MVP database models (users, sessions, openings, drills, reports, subscriptions)
feat: add Pydantic settings config with env var validation
feat: add JWT security utilities (create_access_token, decode_jwt)
feat: add FastAPI app factory with CORS, lifespan, health endpoint
feat: add Redis cache utility
feat: add skeleton auth dependencies (full impl in D-003)
feat: add Alembic configuration with async-to-sync driver bridge
test: add conftest.py with async SQLite test fixtures
test: add test_health.py (TDD — write before implementation)
docs: add .env.example with all required variables
```

---

## Acceptance Criteria

All of the following must be true before marking D-001 complete:

- [ ] `/backend/` directory exists with the full structure above
- [ ] All 12 MVP models exist with correct fields, types, constraints, and relationships
- [ ] `app/db/models/__init__.py` imports all 12 models
- [ ] `alembic/env.py` uses `+psycopg2` (sync) not `+asyncpg` for migrations
- [ ] `app/main.py` has `/health` endpoint returning `{"status": "ok", "version": "5.1.0"}`
- [ ] `tests/test_health.py` exists and was written BEFORE `main.py`
- [ ] `pytest tests/test_health.py` passes (3 tests green)
- [ ] `black --check app/` passes with no formatting errors
- [ ] `ruff app/` passes with no lint errors
- [ ] No `.env` file committed (only `.env.example`)
- [ ] No hardcoded secrets anywhere
- [ ] Alembic revision has been generated and shown to human (not executed)
- [ ] All commits use conventional commit format
- [ ] Branch is `agent/backend-scaffold` — NOT merged yet

---

## What NOT to Do

- ❌ Do NOT create `/frontend/` — that is D-002
- ❌ Do NOT implement auth service logic — that is D-003
- ❌ Do NOT create Phase 2 tables: `conversion_failures`, `endgame_drill_cards`, `achievements`
- ❌ Do NOT run `alembic upgrade head` — show migration, wait for human confirmation
- ❌ Do NOT push to `master` or `main`
- ❌ Do NOT hardcode any value from `.env.example`
- ❌ Do NOT add `async def` functions that call sync I/O

---

## Human Review Required After D-001 Completes

Before merging `agent/backend-scaffold` → `develop`:
1. Review the Alembic-generated migration for correctness (all 12 tables present, correct constraints)
2. Confirm no secrets in any committed file
3. Confirm all 3 health tests pass
4. Then run: `alembic upgrade head` against your local/staging DB only
