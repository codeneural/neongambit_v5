# NeonGambit Backend Implementation Guide

> **Version:** 5.1 — MVP-Scoped · Stockfish WASM (Client) · Template-First Coach · i18n · Hostinger Deploy
> **Stack:** FastAPI (Python 3.11+) · Neon PostgreSQL · Upstash Redis · Hostinger KVM VPS (PM2 + nginx)
> **Master Guide:** v5.1 (single source of truth for all product decisions)
> **Swagger docs:** `https://api.neongambit.com/docs` (auto-generated, always current)
> **Last Updated:** April 2026

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Project Structure](#2-project-structure)
3. [Environment & Configuration](#3-environment--configuration)
4. [Database Models](#4-database-models)
5. [Schemas (Pydantic V2)](#5-schemas-pydantic-v2)
6. [Core Services](#6-core-services)
   - [6.1 Auth Service](#61-auth-service)
   - [6.2 Chess Service](#62-chess-service)
   - [6.3 Stockfish Service (Glitch Report ONLY)](#63-stockfish-service)
   - [6.4 Lichess Service](#64-lichess-service)
   - [6.5 Coach Service (Template-First + Gemini)](#65-coach-service)
   - [6.6 Session Service (No Server-Side Stockfish)](#66-session-service)
   - [6.7 Lichess Analyzer (Glitch Report + Collapse Classification)](#67-lichess-analyzer-glitch-report)
   - [6.8 SRS Service (Neural Drill)](#68-srs-service-neural-drill)
   - [6.9 Analytics Service (MVP)](#69-analytics-service)
   - [6.10 Subscription Service](#610-subscription-service)
7. [API Routers](#7-api-routers)
   - [7.1 Auth](#71-auth-router)
   - [7.2 Lichess Import](#72-lichess-router)
   - [7.3 Glitch Report](#73-glitch-report-router)
   - [7.4 Sessions (Sparring)](#74-sessions-router)
   - [7.5 Drill](#75-drill-router)
   - [7.6 Analytics & Dashboard](#76-analytics-router)
   - [7.7 Webhooks](#77-webhooks-router)
8. [Background Workers](#8-background-workers)
9. [Caching Strategy](#9-caching-strategy)
10. [Cost Optimization Rules](#10-cost-optimization-rules)
11. [Administration (No Backoffice)](#11-administration)
12. [Testing](#11-testing)
13. [Deployment & Ops (Hostinger VPS)](#12-deployment--ops)
14. [Antigravity Mission Plan](#13-antigravity-mission-plan)
15. [Phase 2 Deferred Services](#14-phase-2-deferred-services)

---

## 1. Architecture Overview

### Philosophy

The backend is the **source of truth** for everything. The frontend is a rendering layer. It sends user intent; the backend validates, processes, and returns authoritative state.

This matters most for chess: the frontend may optimistically render a move, but if the backend rejects it, the board reverts. The backend's word is final.

### System Diagram

```
Frontend (Next.js PWA)
        │
        ├── stockfish.wasm (Web Worker)  ← Client-side: real-time move eval during sparring
        │
        ▼  HTTPS / Bearer JWT
FastAPI Application (Hostinger KVM VPS · PM2 + nginx)
        │
        ├── Redis (Upstash)          ← Hot cache: opening positions, sessions, rate limits
        ├── PostgreSQL (Neon)        ← Source of truth: all persistent state
        ├── Stockfish (native binary) ← Server-side: Glitch Report collapse analysis ONLY
        ├── Lichess API (external)   ← Game history import + Explorer opening data
        └── Gemini 1.5 Flash (API)  ← Glitch Report narratives + session summaries (20% of coaching)

NOTE: In-game coaching during sparring is handled by the NEON template library (server-side,
no LLM call). Move quality evaluation is handled by stockfish.wasm (client-side, no server
Stockfish call). The server's role during sparring is: validate legality → return opponent
move → track game state. All lightweight operations.
```

### Key Design Decisions

**Async everywhere.** All I/O — database, Redis, Lichess HTTP, Gemini — is async. FastAPI + SQLAlchemy async + httpx means the server never blocks on I/O.

**Services own business logic. Routers own nothing.** Routers are thin: validate request → call service → return response. All logic (move validation, SM-2 calculation, template selection, rate limiting) lives in service classes. This makes services independently testable and agents can reason about them without reading router code.

**Stockfish split: client for sparring, server for reports.** Real-time move evaluation during sparring runs client-side via stockfish.wasm (Web Worker). The server NEVER runs Stockfish during a sparring session. Server-side Stockfish is used exclusively for Glitch Report generation (async background worker). See Master Guide ADR-002.

**Template-first coaching.** In-game NEON coaching uses a curated YAML template library (~200 messages, bilingual EN/ES). Gemini is called only for Glitch Report narratives and post-session summaries. No LLM calls during gameplay. See Master Guide ADR-004.

**Background workers for expensive operations.** Lichess import (fetching 200 games + Stockfish analysis on 5 of them) cannot be synchronous. These run as background tasks, tracked by job ID, polled by the frontend.

**Cache aggressively, invalidate carefully.** Opening position data from Lichess Explorer is cached in Redis (30-day TTL) then promoted to Postgres for long-term persistence. This makes 90%+ of opponent moves return from cache in <50ms.

**No backoffice.** All administration via Neon Console (SQL), Stripe Dashboard, and CLI scripts. See Section 11.

---

## 2. Project Structure

```
backend/
├── app/
│   ├── main.py                         # FastAPI app factory, router registration, lifespan
│   ├── config.py                       # Pydantic Settings — all env vars typed
│   ├── dependencies.py                 # Shared FastAPI dependencies (DB, auth, rate limit)
│   │
│   ├── core/
│   │   ├── security.py                 # JWT create/decode, password hashing
│   │   ├── exceptions.py               # Custom HTTPException subclasses
│   │   ├── middleware.py               # CORS config, request logging
│   │   └── rate_limiter.py             # Redis-backed sliding window rate limiter
│   │
│   ├── db/
│   │   ├── base.py                     # SQLAlchemy DeclarativeBase
│   │   ├── session.py                  # Async engine + session factory
│   │   └── models/
│   │       ├── __init__.py             # Re-exports all models (Alembic needs this)
│   │       ├── user.py
│   │       ├── opening.py
│   │       ├── user_repertoire.py
│   │       ├── sparring_session.py
│   │       ├── lichess_game.py
│   │       ├── glitch_report.py
│   │       ├── lichess_rating_snapshot.py
│   │       ├── user_move_mastery.py
│   │       ├── user_stats.py
│   │       ├── opening_cache.py
│   │       ├── coach_analysis.py
│   │       └── subscription.py
│   │
│   ├── schemas/                        # Pydantic V2 models — API contracts
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── lichess.py
│   │   ├── glitch_report.py
│   │   ├── opening.py
│   │   ├── drill.py
│   │   └── analytics.py
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py             # APIRouter aggregator for v1
│   │       ├── auth.py
│   │       ├── user.py
│   │       ├── lichess.py
│   │       ├── glitch_report.py
│   │       ├── repertoire.py
│   │       ├── sessions.py
│   │       ├── drill.py
│   │       ├── analytics.py
│   │       └── webhooks.py
│   │
│   ├── services/
│   │   ├── auth_service.py             # Firebase token validation + JWT issuance
│   │   ├── chess_service.py            # python-chess wrapper (move parsing, FEN hashing)
│   │   ├── stockfish_service.py        # Stockfish wrapper — ONLY for Glitch Report (async)
│   │   ├── lichess_service.py          # Lichess REST + Explorer API client
│   │   ├── coach_service.py            # Template library + Gemini fallback (NEON persona)
│   │   ├── coach_templates.py          # Template selection engine (quality × pattern × ELO × locale)
│   │   ├── session_service.py          # Sparring session state machine (no Stockfish)
│   │   ├── lichess_analyzer.py         # Glitch Report generation + collapse type classification
│   │   ├── srs_service.py              # SM-2 spaced repetition algorithm
│   │   ├── analytics_service.py        # Dashboard aggregation (single-call endpoint)
│   │   └── subscription_service.py     # Stripe webhooks + pro status management
│   │
│   ├── workers/
│   │   ├── lichess_import_worker.py    # Background: game fetch + ECO parsing
│   │   └── glitch_report_worker.py     # Background: Stockfish analysis + Gemini narrative
│   │
│   └── utils/
│       ├── cache.py                    # Redis client + typed get/set/delete helpers
│       ├── fen_utils.py                # FEN normalization + MD5 hashing
│       └── pgn_utils.py                # PGN parsing helpers
│
├── data/
│   └── neon_templates.yaml             # NEON coaching template library (EN + ES)
│
├── alembic/
│   ├── versions/                       # Migration files (auto-generated)
│   └── env.py                          # Alembic async config
│
├── tests/
│   ├── conftest.py                     # Pytest fixtures (test DB, test client, mocks)
│   ├── test_auth.py
│   ├── test_sessions.py
│   ├── test_session_service.py
│   ├── test_chess_service.py
│   ├── test_srs_service.py
│   ├── test_lichess_analyzer.py
│   ├── test_coach_templates.py
│   └── test_analytics_service.py
│
├── scripts/
│   ├── seed_openings.py                # Populate openings table from curated JSON
│   ├── admin_queries.py                # CLI admin utilities (user lookup, metrics, pro toggle)
│   └── cleanup_old_data.py             # Free-tier data pruning job (run via cron)
│
├── .env.example
├── .env.test                           # Test environment (SQLite or test Neon branch)
├── requirements.txt
├── requirements-dev.txt                # pytest, httpx, factory-boy, etc.
├── ecosystem.config.js                 # PM2 config for Hostinger deployment
├── nginx.conf                          # nginx reverse proxy config template
├── Dockerfile
├── docker-compose.yml                  # Local dev: app + Redis
├── pytest.ini
└── README.md
```

---

## 3. Environment & Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str                   # postgresql+asyncpg://...
    DATABASE_URL_SYNC: str = ""         # postgresql://... (Alembic sync fallback)

    # Cache
    REDIS_URL: str                      # redis://...

    # Firebase
    FIREBASE_PROJECT_ID: str
    FIREBASE_CREDENTIALS_PATH: str = "./firebase-admin-key.json"

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days

    # AI
    GOOGLE_GEMINI_API_KEY: str

    # i18n
    SUPPORTED_LANGUAGES: list[str] = ["en", "es"]
    DEFAULT_LANGUAGE: str = "en"

    # Lichess
    LICHESS_API_TOKEN: str = ""         # Authenticated: higher rate limits
    LICHESS_BASE_URL: str = "https://lichess.org"

    # Stockfish
    STOCKFISH_PATH: str = "/usr/local/bin/stockfish"
    STOCKFISH_MAX_DEPTH: int = 15

    # Stripe
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str
    STRIPE_PRICE_ID_MONTHLY: str
    STRIPE_PRICE_ID_YEARLY: str

    # Rate limits
    RATE_LIMIT_MOVES_PER_MINUTE: int = 60
    RATE_LIMIT_ANALYSES_FREE_PER_DAY: int = 3
    RATE_LIMIT_DRILLS_FREE_PER_DAY: int = 5
    RATE_LIMIT_LICHESS_IMPORT_PER_DAY: int = 3  # Prevent abuse

    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine
from app.db.base import Base
from app.api.v1 import router as v1_router
from app.utils.cache import redis_client
import firebase_admin
from firebase_admin import credentials

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    await redis_client.ping()
    yield
    # Shutdown
    await redis_client.aclose()

app = FastAPI(
    title="NeonGambit API",
    version="5.1.0",
    docs_url="/docs",
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

@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.1.0"}
```

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

```python
# app/dependencies.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.core.security import decode_jwt
from app.db.models.user import User
from sqlalchemy import select

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_jwt(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user

async def require_pro(user: User = Depends(get_current_user)) -> User:
    if not user.is_pro:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Grandmaster tier required")
    return user
```

---

## 4. Database Models

```python
# app/db/models/user.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, DateTime, func, CheckConstraint
from app.db.base import Base
import uuid

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    firebase_uid: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    guest_token: Mapped[str | None] = mapped_column(String, unique=True, index=True)
    lichess_username: Mapped[str | None] = mapped_column(String, index=True)
    target_elo: Mapped[int] = mapped_column(Integer, default=1200)
    play_style: Mapped[str | None] = mapped_column(String)  # 'tactical'|'positional'|None
    preferred_language: Mapped[str] = mapped_column(String, default="en")  # 'en'|'es'
    is_pro: Mapped[bool] = mapped_column(Boolean, default=False)
    pro_expires_at: Mapped[DateTime | None] = mapped_column(DateTime)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    last_active_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())

    __table_args__ = (
        CheckConstraint("target_elo BETWEEN 800 AND 3000", name="valid_elo"),
    )
```

```python
# app/db/models/sparring_session.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, JSON, func, CheckConstraint
from app.db.base import Base
import uuid

class SparringSession(Base):
    __tablename__ = "sparring_sessions"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    opening_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("openings.id"))
    player_color: Mapped[str] = mapped_column(String)
    opponent_elo: Mapped[int] = mapped_column(Integer)
    current_fen: Mapped[str] = mapped_column(String)
    move_history: Mapped[list] = mapped_column(JSON, default=list)
    accuracy_score: Mapped[float] = mapped_column(Float, default=100.0)
    theory_integrity: Mapped[float] = mapped_column(Float, default=100.0)
    theory_exit_move: Mapped[int | None] = mapped_column(Integer)
    excellent_moves: Mapped[int] = mapped_column(Integer, default=0)
    good_moves: Mapped[int] = mapped_column(Integer, default=0)
    inaccuracies: Mapped[int] = mapped_column(Integer, default=0)
    mistakes: Mapped[int] = mapped_column(Integer, default=0)
    blunders: Mapped[int] = mapped_column(Integer, default=0)
    session_status: Mapped[str] = mapped_column(String, default="active")
    result: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[DateTime | None] = mapped_column(DateTime)

    __table_args__ = (
        CheckConstraint("session_status IN ('active','completed','abandoned')", name="valid_status"),
        CheckConstraint("accuracy_score >= 0 AND accuracy_score <= 100", name="valid_accuracy"),
    )
```

```python
# app/db/models/glitch_report.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Boolean, Text, func
from app.db.base import Base
import uuid

class GlitchReport(Base):
    __tablename__ = "glitch_reports"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    generated_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    games_analyzed: Mapped[int] = mapped_column(Integer)
    rating_at_generation: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String, default="lichess")  # 'lichess'|'sessions'
    critical_openings: Mapped[list] = mapped_column(JSON, default=list)
    # [{eco_code, opening_name, games, wins, losses, win_rate, avg_collapse_move,
    #   collapse_type ('opening_error'|'tactical_blunder'|'positional_drift'|'time_pressure'),
    #   neon_diagnosis, is_critical, linked_opening_id, training_unlocked}]
    strengths: Mapped[list] = mapped_column(JSON, default=list)
    overall_pattern: Mapped[str | None] = mapped_column(Text)
    is_current: Mapped[bool] = mapped_column(Boolean, default=True)
```

```python
# app/db/models/user_move_mastery.py
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Float, Integer, DateTime, ForeignKey, func
from sqlalchemy import PrimaryKeyConstraint
from app.db.base import Base
import uuid

class UserMoveMastery(Base):
    __tablename__ = "user_move_mastery"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    opening_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("openings.id", ondelete="CASCADE"))
    move_sequence_hash: Mapped[str] = mapped_column(String)
    move_number: Mapped[int] = mapped_column(Integer)
    expected_move: Mapped[str] = mapped_column(String)
    fen_before: Mapped[str] = mapped_column(String)
    easiness_factor: Mapped[float] = mapped_column(Float, default=2.5)
    interval_days: Mapped[int] = mapped_column(Integer, default=0)
    repetitions: Mapped[int] = mapped_column(Integer, default=0)
    next_review: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())
    last_reviewed: Mapped[DateTime | None] = mapped_column(DateTime)
    correct_count: Mapped[int] = mapped_column(Integer, default=0)
    incorrect_count: Mapped[int] = mapped_column(Integer, default=0)

    __table_args__ = (
        PrimaryKeyConstraint("user_id", "move_sequence_hash"),
    )
```

---

## 5. Schemas (Pydantic V2)

```python
# app/schemas/session.py
from pydantic import BaseModel, Field
from typing import Literal, Optional
import uuid

MoveQuality = Literal["excellent", "good", "inaccuracy", "mistake", "blunder"]

class CreateSessionRequest(BaseModel):
    opening_id: uuid.UUID
    player_color: Literal["white", "black"]
    opponent_elo: int = Field(ge=800, le=2000)

class CreateSessionResponse(BaseModel):
    session_id: uuid.UUID
    current_fen: str
    player_color: str
    opponent_elo: int
    opening_name: str
    theory_integrity: float
    neon_intro: str

class MakeMoveRequest(BaseModel):
    from_square: str = Field(alias="from", min_length=2, max_length=2)
    to_square: str = Field(alias="to", min_length=2, max_length=2)
    promotion: Optional[Literal["q", "r", "b", "n"]] = None
    # Client reports previous move's quality (evaluated client-side via stockfish.wasm)
    prev_move_quality: Optional[MoveQuality] = None
    prev_move_eval_cp: Optional[int] = None

    model_config = {"populate_by_name": True}

class MakeMoveResponse(BaseModel):
    """Server validates legality and tracks theory. Move quality comes from client."""
    valid: bool
    new_fen: Optional[str] = None
    theory_integrity: Optional[float] = None
    theory_exit_detected: Optional[bool] = None
    theory_exit_move: Optional[int] = None
    out_of_book: Optional[bool] = None
    coach_message: Optional[str] = None  # Template-driven, instant
    # Error case
    error: Optional[str] = None
    legal_moves: Optional[list[str]] = None

class OpponentMoveResponse(BaseModel):
    move: dict  # {from, to, san, uci}
    new_fen: str
    thinking_time_ms: int
    out_of_book: bool
    source: Literal["lichess_cache", "lichess_api", "fallback"]
```

```python
# app/schemas/glitch_report.py
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

class CriticalOpening(BaseModel):
    eco_code: str
    opening_name: str
    games: int
    wins: int
    losses: int
    win_rate: float
    avg_collapse_move: Optional[int]
    collapse_type: Optional[str]  # 'opening_error'|'tactical_blunder'|'positional_drift'|'time_pressure'
    neon_diagnosis: str
    is_critical: bool
    linked_opening_id: Optional[uuid.UUID]
    training_unlocked: bool  # True if user can train this opening (Free: top 2, Pro: all)

class StrengthEntry(BaseModel):
    eco_code: str
    opening_name: str
    games: int
    win_rate: float

class GlitchReportResponse(BaseModel):
    id: uuid.UUID
    games_analyzed: int
    rating_at_generation: Optional[int]
    generated_at: datetime
    source: str  # 'lichess' or 'sessions'
    critical_openings: list[CriticalOpening]
    strengths: list[StrengthEntry]
    overall_pattern: Optional[str]

class GenerateJobResponse(BaseModel):
    job_id: str
    status: str
    message: str
    estimated_seconds: Optional[int] = None
```

```python
# app/schemas/analytics.py
from pydantic import BaseModel
from typing import Optional
import uuid

class LichessRatingData(BaseModel):
    current: int
    delta_30_day: int
    trend: list[int]  # 8 weekly snapshots

class WeekSummary(BaseModel):
    sessions: int
    drill_cards_reviewed: int
    win_rate: float
    avg_accuracy: float

class OpeningImprovement(BaseModel):
    eco_code: str
    opening_name: str
    baseline_win_rate: float
    current_win_rate: float
    delta: float
    status: str  # 'improving' | 'stable' | 'declining'

class RecommendedSession(BaseModel):
    opening_id: uuid.UUID
    opening_name: str
    reason: str

class DashboardResponse(BaseModel):
    lichess_rating: Optional[LichessRatingData]
    this_week: WeekSummary
    opening_improvements: list[OpeningImprovement]
    drill_queue_count: int
    streak: int
    tilt_detected: bool
    has_glitch_report: bool
    critical_opening_count: int
    recommended_session: Optional[RecommendedSession]
    estimated_drill_minutes: int
```

---

## 6. Core Services

### 6.1 Auth Service

```python
# app/services/auth_service.py
import uuid
from datetime import datetime, timedelta
from firebase_admin import auth as firebase_auth
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.db.models.user import User

class AuthService:

    def create_jwt(self, user_id: str) -> str:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(
            {"sub": str(user_id), "exp": expire},
            settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
        )

    def decode_jwt(self, token: str) -> dict | None:
        try:
            return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            return None

    async def create_guest(self, db: AsyncSession) -> tuple[User, str]:
        guest_token = str(uuid.uuid4())
        user = User(guest_token=guest_token)
        db.add(user)
        await db.flush()
        token = self.create_jwt(str(user.id))
        return user, token

    async def validate_firebase(self, firebase_token: str, db: AsyncSession) -> tuple[User, str]:
        decoded = firebase_auth.verify_id_token(firebase_token)
        firebase_uid = decoded["uid"]
        email = decoded.get("email")

        result = await db.execute(select(User).where(User.firebase_uid == firebase_uid))
        user = result.scalar_one_or_none()

        if not user:
            user = User(firebase_uid=firebase_uid, email=email)
            db.add(user)
            await db.flush()

        token = self.create_jwt(str(user.id))
        return user, token

    async def link_account(self, guest_user: User, firebase_token: str, db: AsyncSession) -> tuple[User, str]:
        decoded = firebase_auth.verify_id_token(firebase_token)
        guest_user.firebase_uid = decoded["uid"]
        guest_user.email = decoded.get("email")
        guest_user.guest_token = None  # No longer a guest
        token = self.create_jwt(str(guest_user.id))
        return guest_user, token
```

### 6.2 Chess Service

```python
# app/services/chess_service.py
import chess
import hashlib
from typing import Optional

class ChessService:

    def parse_move(
        self, board: chess.Board, from_sq: str, to_sq: str, promotion: Optional[str] = None
    ) -> Optional[chess.Move]:
        try:
            promo_piece = chess.Piece.from_symbol(promotion.upper()).piece_type if promotion else None
            move = chess.Move(
                chess.parse_square(from_sq),
                chess.parse_square(to_sq),
                promotion=promo_piece
            )
            # If not legal, try without promotion (handles ambiguous pawn moves)
            if move not in board.legal_moves and promo_piece is None:
                # Auto-promote to queen if pawn reaches last rank
                pawn_promo = chess.Move(
                    chess.parse_square(from_sq),
                    chess.parse_square(to_sq),
                    promotion=chess.QUEEN
                )
                if pawn_promo in board.legal_moves:
                    return pawn_promo
            return move if move in board.legal_moves else None
        except (ValueError, KeyError):
            return None

    def is_in_theory(self, board: chess.Board, opening_moves: list[str]) -> bool:
        """Check if current board position matches the expected opening line."""
        test_board = chess.Board()
        for san in opening_moves:
            try:
                test_board.push_san(san)
            except Exception:
                return False
            if test_board.fen().split(" ")[0] == board.fen().split(" ")[0]:
                return True  # Current position exists in the opening line
        # Compare position hashes
        return test_board.fen().split(" ")[0] == board.fen().split(" ")[0]

    def hash_fen(self, fen: str) -> str:
        """MD5 of position-only FEN (strip move clocks for cache key stability)."""
        position_only = fen.split(" ")[0]
        return hashlib.md5(position_only.encode()).hexdigest()

    def get_legal_moves_uci(self, board: chess.Board) -> list[str]:
        return [m.uci() for m in board.legal_moves]

    def is_game_over(self, board: chess.Board) -> tuple[bool, Optional[str]]:
        """Returns (is_over, result) where result is 'win'|'loss'|'draw'|None."""
        if board.is_game_over():
            outcome = board.outcome()
            if outcome.winner is None:
                return True, "draw"
            return True, "win" if outcome.winner == chess.WHITE else "loss"
        return False, None

    def move_sequence_hash(self, moves: list[str]) -> str:
        """Stable hash for a sequence of moves — used as SRS card key."""
        return hashlib.md5("|".join(moves).encode()).hexdigest()
```

### 6.3 Stockfish Service (Glitch Report ONLY)

```python
# app/services/stockfish_service.py
"""
IMPORTANT: This service is ONLY used for Glitch Report generation (async background worker).
It is NEVER called during sparring sessions. Move evaluation during sparring runs
client-side via stockfish.wasm. See Master Guide ADR-002.
"""
import asyncio
from typing import Optional
from app.config import settings

class StockfishService:
    """
    Async wrapper around Stockfish subprocess.
    Uses a single persistent process per service instance.
    Depth capped at STOCKFISH_MAX_DEPTH (15) to limit CPU usage.
    """

    def __init__(self):
        self._process: Optional[asyncio.subprocess.Process] = None
        self._lock = asyncio.Lock()

    async def _ensure_process(self):
        if self._process is None or self._process.returncode is not None:
            self._process = await asyncio.create_subprocess_exec(
                settings.STOCKFISH_PATH,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await self._send("uci")
            await self._read_until("uciok")

    async def _send(self, command: str):
        self._process.stdin.write(f"{command}\n".encode())
        await self._process.stdin.drain()

    async def _read_until(self, token: str) -> list[str]:
        lines = []
        while True:
            line = (await self._process.stdout.readline()).decode().strip()
            lines.append(line)
            if token in line:
                return lines

    async def analyze(self, fen: str, depth: int = 15) -> dict:
        """
        Analyzes a position. Returns centipawn score and best move.
        Depth capped at STOCKFISH_MAX_DEPTH.
        """
        depth = min(depth, settings.STOCKFISH_MAX_DEPTH)
        async with self._lock:
            await self._ensure_process()
            await self._send(f"position fen {fen}")
            await self._send(f"go depth {depth}")
            lines = await self._read_until("bestmove")

        score_cp = 0
        best_move = ""
        for line in lines:
            if "score cp" in line:
                parts = line.split("score cp")
                score_cp = int(parts[1].strip().split()[0])
            if line.startswith("bestmove"):
                best_move = line.split()[1]

        return {"score_cp": score_cp, "best_move": best_move}

    async def analyze_game_collapse(self, pgn_moves: str) -> Optional[int]:
        """
        Given a PGN move list, find the move number where evaluation
        swings decisively against the user. Used in Glitch Report.
        Returns the move number of the collapse, or None.
        """
        import chess.pgn
        import io
        game = chess.pgn.read_game(io.StringIO(pgn_moves))
        if not game:
            return None

        board = game.board()
        prev_eval = 0
        collapse_move = None

        for i, move in enumerate(game.mainline_moves()):
            board.push(move)
            if i % 2 == 0 and i > 4:  # Only analyze user's moves, skip opening
                result = await self.analyze(board.fen(), depth=12)
                eval_cp = result["score_cp"]
                swing = prev_eval - eval_cp
                if swing > 150:  # Significant swing against white
                    collapse_move = (i // 2) + 1
                    break
                prev_eval = eval_cp

        return collapse_move
```

### 6.4 Lichess Service

```python
# app/services/lichess_service.py
import httpx
import json
from typing import Optional
from app.config import settings
from app.utils.cache import redis_client
from app.utils.fen_utils import hash_fen

class LichessService:

    def __init__(self):
        self.base_url = settings.LICHESS_BASE_URL
        self.headers = {}
        if settings.LICHESS_API_TOKEN:
            self.headers["Authorization"] = f"Bearer {settings.LICHESS_API_TOKEN}"

    async def fetch_user_games(self, username: str, max_games: int = 200) -> list[dict]:
        """
        Fetch recent games for a Lichess user via NDJSON streaming API.
        Returns list of parsed game dicts with eco, result, moves, pgn.
        Cost: ~0 (free Lichess API, no auth required for public games).
        """
        url = f"{self.base_url}/api/games/user/{username}"
        params = {
            "max": max_games,
            "opening": "true",
            "pgnInJson": "true",
            "clocks": "false",
            "evals": "false",
        }
        games = []
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("GET", url, params=params, headers=self.headers) as r:
                r.raise_for_status()
                async for line in r.aiter_lines():
                    if line.strip():
                        try:
                            games.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
        return games

    async def fetch_current_rating(self, username: str) -> Optional[int]:
        """Fetch user's current rapid rating from Lichess public API."""
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{self.base_url}/api/user/{username}", headers=self.headers)
            if r.status_code != 200:
                return None
            data = r.json()
            return data.get("perfs", {}).get("rapid", {}).get("rating")

    async def get_explorer_moves(
        self, fen: str, rating_range: list[int], speeds: list[str]
    ) -> list[dict]:
        """
        Fetch candidate moves from Lichess Explorer for a given position and ELO range.
        Returns list of {move, uci, san, white_wins, draws, black_wins, probability}.
        Checks Redis cache first. Cache hit returns in <10ms.
        """
        elo_bucket = (rating_range[0] // 200) * 200
        cache_key = f"opening:{hash_fen(fen)}:{elo_bucket}"

        cached = await redis_client.get(cache_key)
        if cached:
            return json.loads(cached)

        url = f"{self.base_url}/api/opening-explorer/lichess"
        params = {
            "fen": fen,
            "ratings": ",".join(str(r) for r in range(rating_range[0], rating_range[1] + 1, 200)),
            "speeds": ",".join(speeds),
            "moves": 10,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, params=params, headers=self.headers)
            if r.status_code != 200:
                return []
            data = r.json()

        moves = data.get("moves", [])
        total = sum(m["white"] + m["draws"] + m["black"] for m in moves) or 1
        result = [
            {
                "move": m["san"],
                "uci": m["uci"],
                "san": m["san"],
                "white_wins": m["white"],
                "draws": m["draws"],
                "black_wins": m["black"],
                "probability": (m["white"] + m["draws"] + m["black"]) / total,
            }
            for m in moves
        ]

        if result:
            await redis_client.setex(cache_key, 2592000, json.dumps(result))  # 30-day TTL

        return result
```

### 6.5 Coach Service (Template-First + Gemini)

```python
# app/services/coach_templates.py
"""
NEON coaching template library — loaded from data/neon_templates.yaml at startup.
~200 templates across patterns, ELO ranges, and locales (EN + ES).
Every blunder/mistake template follows: consequence → pattern name → forward seed.
See Master Guide ADR-004 for rationale.
"""
import yaml
from pathlib import Path
from typing import Optional

_templates: dict = {}

def load_templates():
    global _templates
    path = Path(__file__).parent.parent.parent / "data" / "neon_templates.yaml"
    with open(path) as f:
        _templates = yaml.safe_load(f)

def get_template(
    pattern: str,        # e.g. 'blunder_hanging_piece', 'excellent_double_threat'
    elo_tier: str,       # 'low' | 'mid' | 'high'
    locale: str = "en",  # 'en' | 'es'
) -> Optional[str]:
    """
    Look up a coaching template by pattern, ELO tier, and locale.
    Returns template string with {placeholders} for dynamic values, or None.
    """
    entry = _templates.get(pattern, {})
    localized = entry.get(locale, entry.get("en", {}))
    return localized.get(elo_tier, localized.get("all"))

def select_pattern(
    move_quality: str,
    eval_before_cp: int,
    eval_after_cp: int,
    theory_exit: bool,
) -> str:
    """
    Determine which template pattern to use based on position features.
    In MVP, uses centipawn swing to infer tactical pattern type.
    """
    if theory_exit:
        return "theory_exit"

    cp_loss = abs(eval_before_cp - eval_after_cp)

    if move_quality == "blunder":
        if cp_loss > 300:
            return "blunder_hanging_piece"  # Material loss
        elif cp_loss > 200:
            return "blunder_fork"           # Tactical pattern
        else:
            return "blunder_positional"
    elif move_quality == "mistake":
        return "mistake_tempo_loss"
    elif move_quality == "inaccuracy":
        return "mistake_positional_drift"
    elif move_quality == "excellent":
        return "excellent_double_threat"
    return "generic_good"

def elo_tier(elo: int) -> str:
    if elo < 1200: return "low"
    if elo < 1500: return "mid"
    return "high"
```

```python
# app/services/coach_service.py
"""
NEON coaching: template-first (80%), Gemini fallback (20%).
In-game coaching is ALWAYS template-driven — zero LLM latency during gameplay.
Gemini is used ONLY for:
  - Glitch Report narrative (neon_diagnosis + overall_pattern)
  - Post-session summary
Both are async, non-blocking, and cached.
"""
import json
import google.generativeai as genai
from app.config import settings
from app.services.coach_templates import (
    get_template, select_pattern, elo_tier, load_templates
)
from typing import Optional

NEON_BASE_PROMPT = """You are NEON — an AI chess coach with a cyberpunk persona.
Direct, efficient, slightly cryptic. A grandmaster who's also a hacker.
Never condescending. Never sycophantic. Always precise.
Use cyberpunk language sparingly: "calculated", "glitch", "system error".
Never use generic praise like "good job" or "well done".
Name the specific consequence, never the shame."""

FALLBACK_MESSAGES = {
    "blunder":    "Critical error. Opponent gains decisive advantage.",
    "mistake":    "Suboptimal. A stronger continuation exists.",
    "inaccuracy": "Minor imprecision. Slight edge surrendered.",
    "excellent":  "Clean. Optimal continuation executed.",
    "theory_exit": "Off-book. Apply positional principles from here.",
}

class CoachService:

    def __init__(self):
        genai.configure(api_key=settings.GOOGLE_GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-1.5-flash")
        load_templates()

    def get_coaching_message(
        self,
        move_quality: str,
        eval_before_cp: int,
        eval_after_cp: int,
        user_elo: int,
        theory_exit: bool,
        locale: str = "en",
    ) -> Optional[str]:
        """
        Returns instant coaching text from template library.
        NO LLM call. Used during sparring for every significant move.
        Returns None for 'good' moves (no coaching needed).
        """
        if move_quality == "good":
            return None

        pattern = select_pattern(move_quality, eval_before_cp, eval_after_cp, theory_exit)
        tier = elo_tier(user_elo)
        template = get_template(pattern, tier, locale)

        if template:
            # In MVP, return template with minimal substitution
            # Full {piece}, {square} substitution requires position analysis (Phase 2)
            return template
        return FALLBACK_MESSAGES.get(move_quality, "Position noted.")

    async def generate_diagnosis(
        self, eco_code: str, opening_name: str, stats: dict,
        user_elo: int, collapse_type: str, locale: str = "en"
    ) -> str:
        """
        Generate a NEON diagnosis for a specific opening weakness.
        Used in Glitch Report generation. Gemini call (cached).
        """
        lang_instruction = f"Respond in {'Spanish' if locale == 'es' else 'English'}."
        prompt = f"""{NEON_BASE_PROMPT}

{lang_instruction}
Generate a diagnosis for this opening weakness. Return ONLY the diagnosis string,
no JSON, no quotes. Maximum 40 words. Use NEON's analytical scouting-report voice.
Address the root cause based on the collapse type.

Opening: {opening_name} ({eco_code})
User ELO: {user_elo}
Games played: {stats['games']}
Win rate: {stats['win_rate']:.0f}%
Average collapse move: {stats.get('avg_collapse_move', 'unknown')}
Collapse type: {collapse_type}"""

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()[:300]
        except Exception:
            return f"You lose {100 - stats['win_rate']:.0f}% of {opening_name} games. This is fixable."

    async def generate_overall_pattern(
        self, critical_openings: list[dict], user_elo: int, locale: str = "en"
    ) -> str:
        """Generate the Glitch Report's 2-sentence overall pattern summary."""
        lang_instruction = f"Respond in {'Spanish' if locale == 'es' else 'English'}."
        opening_list = ", ".join(
            f"{o['opening_name']} ({o['win_rate']:.0f}% WR, collapse: {o.get('collapse_type', 'unknown')})"
            for o in critical_openings[:3]
        )
        prompt = f"""{NEON_BASE_PROMPT}

{lang_instruction}
Write a 2-sentence pattern summary for this user's overall chess weakness.
Use NEON's analytical voice. Maximum 60 words total. No JSON.

User ELO: {user_elo}
Critical openings: {opening_list}"""

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()[:500]
        except Exception:
            return "Your opening theory is adequate. The middlegame transition is where you consistently lose the thread."

    async def generate_session_intro(
        self, opening_name: str, user_win_rate: Optional[float],
        user_elo: int, locale: str = "en"
    ) -> str:
        """Short NEON intro message when a sparring session starts."""
        if user_win_rate is not None:
            context = f"User has a {user_win_rate:.0f}% win rate in this opening."
        else:
            context = "User has no recorded games in this opening."

        lang_instruction = f"Respond in {'Spanish' if locale == 'es' else 'English'}."
        prompt = f"""{NEON_BASE_PROMPT}

{lang_instruction}
Generate a 1-sentence session intro. Maximum 15 words. Use NEON's direct voice.
Opening: {opening_name}. {context}. User ELO: {user_elo}.
No JSON — return plain text only."""

        try:
            response = await self.model.generate_content_async(prompt)
            return response.text.strip()[:200]
        except Exception:
            return f"{opening_name}. Let's run the pattern."
```

### 6.6 Session Service (No Server-Side Stockfish)

```python
# app/services/session_service.py
"""
Sparring session state machine.
KEY CHANGE (v5.1): Server does NOT run Stockfish during sparring.
- Move quality evaluation runs CLIENT-SIDE via stockfish.wasm.
- Server validates legality, tracks theory integrity, returns opponent move.
- Client reports prev_move_quality on the next move for stats tracking.
See Master Guide ADR-002.
"""
import chess
import random
from typing import Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.sparring_session import SparringSession
from app.db.models.opening import Opening
from app.db.models.user_stats import UserStats
from app.services.chess_service import ChessService
from app.services.lichess_service import LichessService
from app.services.coach_service import CoachService

chess_svc = ChessService()
lichess_svc = LichessService()
coach_svc = CoachService()

class SessionService:

    async def create(
        self, user_id: str, opening_id: str, player_color: str,
        opponent_elo: int, db: AsyncSession
    ) -> SparringSession:
        result = await db.execute(select(Opening).where(Opening.id == opening_id))
        opening = result.scalar_one_or_none()
        if not opening:
            raise ValueError("Opening not found")

        session = SparringSession(
            user_id=user_id,
            opening_id=opening_id,
            player_color=player_color,
            opponent_elo=opponent_elo,
            current_fen=chess.STARTING_FEN,
        )
        db.add(session)
        await db.flush()
        return session, opening

    async def validate_and_apply_move(
        self,
        session: SparringSession,
        opening: Opening,
        from_sq: str,
        to_sq: str,
        promotion: Optional[str],
        user_elo: int,
        locale: str,
        prev_move_quality: Optional[str],
        prev_move_eval_cp: Optional[int],
        db: AsyncSession,
    ) -> dict:
        board = chess.Board(session.current_fen)
        move = chess_svc.parse_move(board, from_sq, to_sq, promotion)

        if not move or move not in board.legal_moves:
            return {
                "valid": False,
                "error": f"Illegal move: {from_sq} to {to_sq}",
                "legal_moves": chess_svc.get_legal_moves_uci(board),
            }

        # Record previous move's quality (reported by client)
        if prev_move_quality:
            self._increment_quality_counter(session, prev_move_quality)

        # Detect theory exit BEFORE applying move
        move_number = board.fullmove_number
        theory_exit_detected = False
        if session.theory_exit_move is None:
            board_copy = chess.Board(session.current_fen)
            board_copy.push(move)
            in_theory = chess_svc.is_in_theory(board_copy, opening.starting_moves)
            if not in_theory and move_number >= 5:
                theory_exit_detected = True
                session.theory_exit_move = move_number

        # Apply move
        board.push(move)
        new_fen = board.fen()

        # Update session state
        session.current_fen = new_fen
        session.move_history.append({
            "move": move.uci(), "san": board.san(move),
            "from": from_sq, "to": to_sq,
            "quality": prev_move_quality,  # Client-reported for stats
            "timestamp": datetime.utcnow().isoformat(),
        })

        # Generate coaching from template library (instant, no LLM)
        coach_message = None
        if theory_exit_detected:
            coach_message = coach_svc.get_coaching_message(
                "theory_exit", 0, 0, user_elo, True, locale
            )
        elif prev_move_quality in ("blunder", "mistake", "inaccuracy"):
            coach_message = coach_svc.get_coaching_message(
                prev_move_quality,
                prev_move_eval_cp or 0, 0,
                user_elo, False, locale
            )

        return {
            "valid": True,
            "new_fen": new_fen,
            "theory_integrity": session.theory_integrity,
            "theory_exit_detected": theory_exit_detected,
            "theory_exit_move": session.theory_exit_move if theory_exit_detected else None,
            "out_of_book": False,
            "coach_message": coach_message,
        }

    async def get_opponent_move(self, session: SparringSession) -> dict:
        """Unchanged from v4 — probabilistic move from Lichess Explorer."""
        elo_bucket = (session.opponent_elo // 200) * 200
        moves = await lichess_svc.get_explorer_moves(
            fen=session.current_fen,
            rating_range=[elo_bucket - 100, elo_bucket + 100],
            speeds=["blitz", "rapid"],
        )

        if not moves:
            board = chess.Board(session.current_fen)
            legal = list(board.legal_moves)
            fallback = random.choice(legal)
            board_copy = chess.Board(session.current_fen)
            board_copy.push(fallback)
            return {
                "move": {"from": chess.square_name(fallback.from_square),
                         "to": chess.square_name(fallback.to_square),
                         "san": board.san(fallback), "uci": fallback.uci()},
                "new_fen": board_copy.fen(),
                "thinking_time_ms": random.randint(800, 2000),
                "out_of_book": True,
                "source": "fallback",
            }

        weights = [m["probability"] for m in moves]
        total = sum(weights)
        r = random.random() * total
        chosen = moves[0]
        cumulative = 0
        for move in moves:
            cumulative += move["probability"]
            if r <= cumulative:
                chosen = move
                break

        board = chess.Board(session.current_fen)
        chess_move = chess.Move.from_uci(chosen["uci"])
        board.push(chess_move)

        base_think = int(2000 * (1 - chosen["probability"]))
        thinking_time = max(400, min(2500, base_think + random.randint(-200, 200)))

        return {
            "move": {"from": chess.square_name(chess_move.from_square),
                     "to": chess.square_name(chess_move.to_square),
                     "san": chosen["san"], "uci": chosen["uci"]},
            "new_fen": board.fen(),
            "thinking_time_ms": thinking_time,
            "out_of_book": False,
            "source": "lichess_cache",
        }

    def _increment_quality_counter(self, session: SparringSession, quality: str):
        counter_map = {
            "excellent": "excellent_moves", "good": "good_moves",
            "inaccuracy": "inaccuracies", "mistake": "mistakes", "blunder": "blunders",
        }
        attr = counter_map.get(quality)
        if attr:
            setattr(session, attr, getattr(session, attr) + 1)
```

### 6.7 Lichess Analyzer (Glitch Report + Collapse Classification)

```python
# app/services/lichess_analyzer.py
"""
Glitch Report generation pipeline.
v5.1: Added collapse_type classification per opening.
"""
from collections import defaultdict
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models.glitch_report import GlitchReport
from app.db.models.lichess_game import LichessGame
from app.db.models.user_repertoire import UserRepertoire
from app.services.stockfish_service import StockfishService
from app.services.coach_service import CoachService
from sqlalchemy import select, update
import chess
import chess.pgn
import io

stockfish_svc = StockfishService()
coach_svc = CoachService()

# Collapse type classification thresholds
MATERIAL_SWING_THRESHOLD = 150  # 1.5 pawns for tactical blunder
DRIFT_THRESHOLD = 150           # 1.5 pawns over multiple moves

class LichessAnalyzer:

    async def generate_report(
        self, user_id: str, user_elo: int, locale: str, db: AsyncSession
    ) -> GlitchReport:
        result = await db.execute(
            select(LichessGame).where(LichessGame.user_id == user_id)
        )
        games = result.scalars().all()
        if not games:
            raise ValueError("No games imported. Run lichess/import first.")

        stats = self._aggregate_by_eco(games)

        critical, strengths = [], []
        for eco_code, data in stats.items():
            if data["games"] < 3:
                continue
            win_rate = (data["wins"] / data["games"]) * 100
            data["win_rate"] = win_rate
            if win_rate < 40:
                critical.append((eco_code, data))
            elif win_rate >= 55:
                strengths.append((eco_code, data))

        critical.sort(key=lambda x: x[1]["win_rate"])
        strengths.sort(key=lambda x: -x[1]["win_rate"])

        # Run Stockfish + collapse type classification on worst games per critical opening
        for eco_code, data in critical[:4]:
            worst_games = sorted(
                [g for g in games if g.eco_code == eco_code and g.result == "loss"],
                key=lambda g: g.played_at or 0
            )[:5]
            collapse_moves = []
            collapse_types = []
            for game in worst_games:
                if game.pgn:
                    collapse = await stockfish_svc.analyze_game_collapse(game.pgn)
                    if collapse:
                        collapse_moves.append(collapse)
                    # Classify collapse type
                    ctype = await self._classify_collapse(game.pgn, game.user_color)
                    if ctype:
                        collapse_types.append(ctype)

            data["avg_collapse_move"] = (
                int(sum(collapse_moves) / len(collapse_moves)) if collapse_moves else None
            )
            # Dominant collapse type
            if collapse_types:
                from collections import Counter
                data["collapse_type"] = Counter(collapse_types).most_common(1)[0][0]
            else:
                data["collapse_type"] = "positional_drift"  # Default

        # Generate NEON diagnoses (Gemini call — includes collapse type)
        critical_openings = []
        for i, (eco_code, data) in enumerate(critical[:4]):
            diagnosis = await coach_svc.generate_diagnosis(
                eco_code, data["opening_name"], data, user_elo,
                data.get("collapse_type", "unknown"), locale
            )
            linked_id = await self._find_opening_id(eco_code, db)
            # Free tier: top 2 openings are unlocked for training
            training_unlocked = (i < 2)  # Pro users override this in the router
            critical_openings.append({
                "eco_code": eco_code,
                "opening_name": data["opening_name"],
                "games": data["games"],
                "wins": data["wins"],
                "losses": data["losses"],
                "win_rate": data["win_rate"],
                "avg_collapse_move": data.get("avg_collapse_move"),
                "collapse_type": data.get("collapse_type"),
                "neon_diagnosis": diagnosis,
                "is_critical": True,
                "linked_opening_id": str(linked_id) if linked_id else None,
                "training_unlocked": training_unlocked,
            })

        strength_list = [
            {"eco_code": ec, "opening_name": d["opening_name"], "games": d["games"], "win_rate": d["win_rate"]}
            for ec, d in strengths[:5]
        ]

        overall_pattern = await coach_svc.generate_overall_pattern(critical_openings, user_elo, locale)

        # Invalidate previous current report
        await db.execute(
            update(GlitchReport)
            .where(GlitchReport.user_id == user_id, GlitchReport.is_current == True)
            .values(is_current=False)
        )

        report = GlitchReport(
            user_id=user_id,
            games_analyzed=len(games),
            rating_at_generation=user_elo,
            source="lichess",
            critical_openings=critical_openings,
            strengths=strength_list,
            overall_pattern=overall_pattern,
            is_current=True,
        )
        db.add(report)
        await db.flush()

        # Auto-assign top critical openings to user's repertoire
        for opening_data in critical_openings:
            if opening_data.get("linked_opening_id") and opening_data["training_unlocked"]:
                await self._auto_assign_repertoire(user_id, opening_data["linked_opening_id"], db)

        return report

    async def _classify_collapse(self, pgn_text: str, user_color: str) -> Optional[str]:
        """
        Classify the type of collapse in a lost game.
        Returns: 'opening_error', 'tactical_blunder', 'positional_drift', or 'time_pressure'.
        """
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if not game:
            return None

        board = game.board()
        user_is_white = (user_color == "white")
        user_sign = 1 if user_is_white else -1
        prev_eval = 0
        max_single_swing = 0
        cumulative_drift = 0
        moves_analyzed = 0

        for i, move in enumerate(game.mainline_moves()):
            board.push(move)
            # Only analyze every 3rd move after move 5 to control cost
            if i > 10 and i % 3 == 0 and moves_analyzed < 5:
                result = await stockfish_svc.analyze(board.fen(), depth=10)
                current_eval = result["score_cp"] * user_sign
                swing = prev_eval - current_eval
                if swing > max_single_swing:
                    max_single_swing = swing
                cumulative_drift += max(0, swing)
                prev_eval = current_eval
                moves_analyzed += 1

        # Classification logic
        if max_single_swing >= MATERIAL_SWING_THRESHOLD:
            return "tactical_blunder"
        elif cumulative_drift >= DRIFT_THRESHOLD and max_single_swing < 100:
            return "positional_drift"
        else:
            return "opening_error"  # Default for collapses in early game

    def _aggregate_by_eco(self, games: list[LichessGame]) -> dict:
        stats = defaultdict(lambda: {"games": 0, "wins": 0, "losses": 0, "draws": 0, "opening_name": ""})
        for game in games:
            if not game.eco_code:
                continue
            eco = game.eco_code
            stats[eco]["games"] += 1
            stats[eco]["opening_name"] = game.opening_name or eco
            if game.result == "win":   stats[eco]["wins"] += 1
            elif game.result == "loss": stats[eco]["losses"] += 1
            else:                       stats[eco]["draws"] += 1
        return dict(stats)

    async def _find_opening_id(self, eco_code: str, db: AsyncSession):
        from app.db.models.opening import Opening
        result = await db.execute(select(Opening.id).where(Opening.eco_code == eco_code))
        return result.scalar_one_or_none()

    async def _auto_assign_repertoire(self, user_id: str, opening_id: str, db: AsyncSession):
        """Auto-add a critical opening to user's repertoire after Glitch Report."""
        existing = await db.execute(
            select(UserRepertoire).where(
                UserRepertoire.user_id == user_id,
                UserRepertoire.opening_id == opening_id,
            )
        )
        if not existing.scalar_one_or_none():
            db.add(UserRepertoire(
                user_id=user_id, opening_id=opening_id, source="glitch_report"
            ))
```

### 6.8 SRS Service (Neural Drill)

```python
# app/services/srs_service.py
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.user_move_mastery import UserMoveMastery
from app.db.models.opening import Opening
from app.services.chess_service import ChessService
import chess

chess_svc = ChessService()

class SRSService:

    def calculate_next_review(
        self, repetitions: int, easiness: float, interval: int, quality: int
    ) -> dict:
        """
        SM-2 algorithm implementation.
        quality: 0=complete blackout, 5=perfect recall, 3=correct with hint.
        """
        if quality < 3:
            repetitions = 0
            interval = 1
        else:
            if repetitions == 0:   interval = 1
            elif repetitions == 1: interval = 6
            else:                  interval = round(interval * easiness)
            repetitions += 1

        easiness = max(1.3, easiness + 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))

        return {
            "interval_days": interval,
            "repetitions": repetitions,
            "easiness_factor": round(easiness, 3),
            "next_review": datetime.utcnow() + timedelta(days=interval),
        }

    async def get_due_cards(
        self, user_id: str, limit: int, db: AsyncSession
    ) -> list[UserMoveMastery]:
        """Fetch moves due for review, ordered by most overdue first."""
        result = await db.execute(
            select(UserMoveMastery)
            .where(
                UserMoveMastery.user_id == user_id,
                UserMoveMastery.next_review <= datetime.utcnow(),
            )
            .order_by(UserMoveMastery.next_review)
            .limit(limit)
        )
        return result.scalars().all()

    async def record_review(
        self, user_id: str, move_sequence_hash: str, quality: int, db: AsyncSession
    ) -> UserMoveMastery:
        result = await db.execute(
            select(UserMoveMastery).where(
                UserMoveMastery.user_id == user_id,
                UserMoveMastery.move_sequence_hash == move_sequence_hash,
            )
        )
        card = result.scalar_one_or_none()
        if not card:
            raise ValueError("Drill card not found")

        next_state = self.calculate_next_review(
            card.repetitions, card.easiness_factor, card.interval_days, quality
        )
        card.interval_days = next_state["interval_days"]
        card.repetitions = next_state["repetitions"]
        card.easiness_factor = next_state["easiness_factor"]
        card.next_review = next_state["next_review"]
        card.last_reviewed = datetime.utcnow()
        if quality >= 3:
            card.correct_count += 1
        else:
            card.incorrect_count += 1

        return card

    async def populate_cards_for_opening(
        self, user_id: str, opening_id: str, depth: int, db: AsyncSession
    ):
        """
        When user adds an opening to their repertoire, create SRS cards
        for each move in the opening's theory line up to `depth` moves.
        """
        result = await db.execute(select(Opening).where(Opening.id == opening_id))
        opening = result.scalar_one_or_none()
        if not opening:
            return

        board = chess.Board()
        move_sequence = []

        for i, san in enumerate(opening.starting_moves[:depth]):
            try:
                move = board.parse_san(san)
            except Exception:
                break

            # Only create cards for the user's color moves
            is_users_turn = (board.turn == chess.WHITE) == (opening.color == "white")
            if is_users_turn:
                move_sequence_hash = chess_svc.move_sequence_hash(move_sequence + [san])
                # Check if card already exists
                existing = await db.execute(
                    select(UserMoveMastery).where(
                        UserMoveMastery.user_id == user_id,
                        UserMoveMastery.move_sequence_hash == move_sequence_hash,
                    )
                )
                if not existing.scalar_one_or_none():
                    card = UserMoveMastery(
                        user_id=user_id,
                        opening_id=opening_id,
                        move_sequence_hash=move_sequence_hash,
                        move_number=board.fullmove_number,
                        expected_move=san,
                        fen_before=board.fen(),
                    )
                    db.add(card)

            board.push(move)
            move_sequence.append(san)

        await db.flush()
```

### 6.9 Analytics Service (MVP)

```python
# app/services/analytics_service.py
"""
MVP Dashboard: simplified. No conversion failure counts, no mission system.
Drill queue IS the daily mission.
"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from app.db.models.user import User
from app.db.models.sparring_session import SparringSession
from app.db.models.user_move_mastery import UserMoveMastery
from app.db.models.glitch_report import GlitchReport
from app.db.models.lichess_rating_snapshot import LichessRatingSnapshot
from app.db.models.user_stats import UserStats
from app.schemas.analytics import DashboardResponse, WeekSummary, OpeningImprovement

class AnalyticsService:

    async def get_dashboard(self, user: User, db: AsyncSession) -> DashboardResponse:
        rating_data = await self._get_rating_trend(user.id, db)
        week_stats = await self._get_week_stats(user.id, db)
        improvements = await self._get_opening_improvements(user.id, db)

        # Drill queue count (opening drills only in MVP)
        drill_count = (await db.execute(
            select(func.count()).select_from(UserMoveMastery).where(
                UserMoveMastery.user_id == user.id,
                UserMoveMastery.next_review <= datetime.utcnow(),
            )
        )).scalar() or 0

        # Streak + tilt
        stats_result = await db.execute(select(UserStats).where(UserStats.user_id == user.id))
        user_stats = stats_result.scalar_one_or_none()
        streak = user_stats.current_streak if user_stats else 0
        tilt_detected = self._check_tilt(user_stats)

        # Glitch report status
        report_result = await db.execute(
            select(GlitchReport).where(GlitchReport.user_id == user.id, GlitchReport.is_current == True)
        )
        report = report_result.scalar_one_or_none()
        critical_count = len([o for o in (report.critical_openings or []) if o.get("is_critical")]) if report else 0

        # Recommended session (weakest opening from Glitch Report)
        recommended = None
        if report and report.critical_openings:
            worst = min(report.critical_openings, key=lambda o: o["win_rate"])
            if worst.get("linked_opening_id"):
                recommended = {
                    "opening_id": worst["linked_opening_id"],
                    "opening_name": worst["opening_name"],
                    "reason": "Your weakest opening this week"
                }

        return DashboardResponse(
            lichess_rating=rating_data,
            this_week=week_stats,
            opening_improvements=improvements,
            drill_queue_count=drill_count,
            streak=streak,
            tilt_detected=tilt_detected,
            has_glitch_report=report is not None,
            critical_opening_count=critical_count,
            recommended_session=recommended,
            estimated_drill_minutes=max(1, int(drill_count * 0.75)),
        )

    def _check_tilt(self, user_stats) -> bool:
        if not user_stats:
            return False
        if user_stats.consecutive_sparring_losses < 3:
            return False
        if not user_stats.last_sparring_loss_at:
            return False
        minutes_since = (datetime.utcnow() - user_stats.last_sparring_loss_at).total_seconds() / 60
        return minutes_since <= 25

    async def _get_rating_trend(self, user_id, db) -> dict | None:
        result = await db.execute(
            select(LichessRatingSnapshot)
            .where(LichessRatingSnapshot.user_id == user_id)
            .order_by(LichessRatingSnapshot.snapshotted_at.desc())
            .limit(8)
        )
        snapshots = result.scalars().all()
        if not snapshots:
            return None
        trend = [s.rating for s in reversed(snapshots)]
        current = trend[-1]
        month_ago = trend[0] if len(trend) >= 4 else current
        return {"current": current, "delta_30_day": current - month_ago, "trend": trend}

    async def _get_week_stats(self, user_id, db) -> WeekSummary:
        week_ago = datetime.utcnow() - timedelta(days=7)
        result = await db.execute(
            select(SparringSession).where(
                SparringSession.user_id == user_id,
                SparringSession.created_at >= week_ago,
                SparringSession.session_status == "completed",
            )
        )
        sessions = result.scalars().all()
        wins = sum(1 for s in sessions if s.result == "win")
        avg_acc = sum(s.accuracy_score for s in sessions) / len(sessions) if sessions else 0.0
        win_rate = (wins / len(sessions) * 100) if sessions else 0.0

        drill_result = await db.execute(
            select(func.sum(UserMoveMastery.correct_count + UserMoveMastery.incorrect_count))
            .where(UserMoveMastery.user_id == user_id, UserMoveMastery.last_reviewed >= week_ago)
        )
        drill_count = drill_result.scalar() or 0
        return WeekSummary(sessions=len(sessions), drill_cards_reviewed=drill_count,
                           win_rate=round(win_rate, 1), avg_accuracy=round(avg_acc, 1))

    async def _get_opening_improvements(self, user_id, db) -> list[OpeningImprovement]:
        report_result = await db.execute(
            select(GlitchReport).where(GlitchReport.user_id == user_id, GlitchReport.is_current == True)
        )
        report = report_result.scalar_one_or_none()
        if not report:
            return []

        improvements = []
        month_ago = datetime.utcnow() - timedelta(days=30)
        for opening_data in (report.critical_openings or []):
            eco = opening_data["eco_code"]
            baseline = opening_data["win_rate"]
            result = await db.execute(
                select(SparringSession).where(
                    SparringSession.user_id == user_id,
                    SparringSession.created_at >= month_ago,
                    SparringSession.session_status == "completed",
                )
            )
            recent_sessions = result.scalars().all()
            if not recent_sessions:
                continue
            wins = sum(1 for s in recent_sessions if s.result == "win")
            current_wr = (wins / len(recent_sessions) * 100) if recent_sessions else baseline
            delta = current_wr - baseline
            status = "improving" if delta > 5 else "declining" if delta < -5 else "stable"
            improvements.append(OpeningImprovement(
                eco_code=eco, opening_name=opening_data["opening_name"],
                baseline_win_rate=baseline, current_win_rate=round(current_wr, 1),
                delta=round(delta, 1), status=status,
            ))
        return improvements
```

### 6.10 Subscription Service

```python
# app/services/subscription_service.py
import stripe
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.db.models.user import User
from app.db.models.subscription import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

class SubscriptionService:

    async def create_checkout_session(self, user: User, plan: str) -> str:
        price_id = (settings.STRIPE_PRICE_ID_MONTHLY if plan == "monthly"
                    else settings.STRIPE_PRICE_ID_YEARLY)
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url="https://neongambit.com/dashboard?upgraded=true",
            cancel_url="https://neongambit.com/dashboard",
            client_reference_id=str(user.id),
            customer_email=user.email,
        )
        return session.url

    async def handle_webhook(self, payload: bytes, sig_header: str, db: AsyncSession):
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except Exception:
            raise ValueError("Invalid webhook signature")

        event_type = event["type"]
        data = event["data"]["object"]

        if event_type in ("customer.subscription.created", "customer.subscription.updated"):
            await self._upsert_subscription(data, db, active=data["status"] == "active")
        elif event_type in ("customer.subscription.deleted", "invoice.payment_failed"):
            await self._upsert_subscription(data, db, active=False)

    async def _upsert_subscription(self, data: dict, db: AsyncSession, active: bool):
        # Find user by Stripe customer ID or client_reference_id
        # Update users.is_pro and subscriptions table
        pass  # Full implementation in production
```

---

## 7. API Routers

### 7.1 Auth Router

```python
# app/api/v1/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.auth_service import AuthService
from app.schemas.auth import TokenResponse, FirebaseTokenRequest

router = APIRouter(prefix="/auth", tags=["auth"])
auth_svc = AuthService()

@router.post("/guest", response_model=TokenResponse)
async def create_guest(db: AsyncSession = Depends(get_db)):
    user, token = await auth_svc.create_guest(db)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/validate", response_model=TokenResponse)
async def validate_firebase(request: FirebaseTokenRequest, db: AsyncSession = Depends(get_db)):
    user, token = await auth_svc.validate_firebase(request.firebase_token, db)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/link-account", response_model=TokenResponse)
async def link_account(
    request: FirebaseTokenRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user, token = await auth_svc.link_account(current_user, request.firebase_token, db)
    return {"access_token": token, "token_type": "bearer"}
```

### 7.2 Lichess Router

```python
# app/api/v1/lichess.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.lichess_service import LichessService
from app.workers.lichess_import_worker import start_import_job, get_job_status

router = APIRouter(prefix="/lichess", tags=["lichess"])
lichess_svc = LichessService()

@router.post("/import")
async def import_games(
    request: dict,  # {lichess_username, max_games}
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    username = request.get("lichess_username", "").strip()
    if not username:
        raise HTTPException(400, "lichess_username is required")

    max_games = min(request.get("max_games", 50), 200 if current_user.is_pro else 20)
    job_id = await start_import_job(background_tasks, current_user.id, username, max_games, db)

    # Store username on user profile
    current_user.lichess_username = username

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Fetching up to {max_games} games from Lichess...",
        "estimated_seconds": max_games // 5,
    }

@router.get("/import/status")
async def import_status(job_id: str):
    status = await get_job_status(job_id)
    if not status:
        raise HTTPException(404, "Job not found")
    return status
```

### 7.3 Glitch Report Router

```python
# app/api/v1/glitch_report.py
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies import get_current_user
from app.db.models.glitch_report import GlitchReport
from app.workers.glitch_report_worker import start_report_job, get_report_job_status
from app.schemas.glitch_report import GlitchReportResponse

router = APIRouter(prefix="/glitch-report", tags=["glitch-report"])

@router.post("/generate")
async def generate_report(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.lichess_username:
        raise HTTPException(400, "Connect your Lichess account first via /lichess/import")

    job_id = await start_report_job(background_tasks, current_user, db)
    return {"job_id": job_id, "status": "processing", "message": "Analyzing your game history..."}

@router.get("/status")
async def report_status(job_id: str):
    return await get_report_job_status(job_id)

@router.get("/current", response_model=GlitchReportResponse)
async def get_current_report(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(GlitchReport).where(
            GlitchReport.user_id == current_user.id,
            GlitchReport.is_current == True,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(404, "No Glitch Report found. Run /glitch-report/generate first.")

    # v5.1: ALL critical openings visible in Free tier (the "aha" moment).
    # Pro users get training_unlocked=True on ALL openings.
    critical = report.critical_openings or []
    if current_user.is_pro:
        for opening in critical:
            opening["training_unlocked"] = True
    # Free tier: training_unlocked was already set by the analyzer (top 2 only)

    return {**report.__dict__, "critical_openings": critical}
```

### 7.4 Sessions Router

```python
# app/api/v1/sessions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.dependencies import get_current_user
from app.db.models.sparring_session import SparringSession
from app.db.models.opening import Opening
from app.schemas.session import CreateSessionRequest, CreateSessionResponse, MakeMoveRequest, MakeMoveResponse
from app.services.session_service import SessionService
from app.services.coach_service import CoachService

router = APIRouter(prefix="/sessions", tags=["sessions"])
session_svc = SessionService()
coach_svc = CoachService()

@router.post("", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    session, opening = await session_svc.create(
        str(current_user.id), str(request.opening_id),
        request.player_color, request.opponent_elo, db,
    )

    # Generate NEON intro (use Glitch Report win rate if available)
    neon_intro = await ai_svc.generate_session_intro(
        opening.name, None, current_user.target_elo
    )

    return CreateSessionResponse(
        session_id=session.id,
        current_fen=session.current_fen,
        player_color=session.player_color,
        opponent_elo=session.opponent_elo,
        opening_name=opening.name,
        theory_integrity=100.0,
        neon_intro=neon_intro,
    )

@router.post("/{session_id}/moves", response_model=MakeMoveResponse)
async def make_move(
    session_id: str,
    request: MakeMoveRequest,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SparringSession, Opening)
        .join(Opening, SparringSession.opening_id == Opening.id)
        .where(SparringSession.id == session_id, SparringSession.user_id == current_user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(404, "Session not found")
    session, opening = row

    if session.session_status != "active":
        raise HTTPException(400, "Session is not active")

    return await session_svc.validate_and_apply_move(
        session, opening,
        request.from_square, request.to_square, request.promotion,
        current_user.target_elo, current_user.preferred_language,
        request.prev_move_quality, request.prev_move_eval_cp, db,
    )

@router.post("/{session_id}/opponent-move")
async def get_opponent_move(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(SparringSession).where(
            SparringSession.id == session_id,
            SparringSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404, "Session not found")

    return await session_svc.get_opponent_move(session)

@router.post("/{session_id}/resign")
async def resign_session(
    session_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    result = await db.execute(
        select(SparringSession).where(
            SparringSession.id == session_id,
            SparringSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(404)
    session.session_status = "completed"
    session.result = "loss"
    session.completed_at = datetime.utcnow()

    # Update tilt tracking
    from app.db.models.user_stats import UserStats
    stats_result = await db.execute(select(UserStats).where(UserStats.user_id == current_user.id))
    user_stats = stats_result.scalar_one_or_none()
    if user_stats:
        user_stats.consecutive_sparring_losses += 1
        user_stats.last_sparring_loss_at = datetime.utcnow()

    return {"status": "completed", "result": "loss"}
```

### 7.5 Drill Router

```python
# app/api/v1/drill.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.srs_service import SRSService
from app.db.models.user_move_mastery import UserMoveMastery
from datetime import datetime

router = APIRouter(prefix="/drill", tags=["drill"])
srs_svc = SRSService()

@router.get("/queue")
async def get_drill_queue(
    limit: int = 8,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Free tier cap
    cap = 5 if not current_user.is_pro else limit
    cards = await srs_svc.get_due_cards(str(current_user.id), cap, db)
    return [
        {
            "opening_id": str(c.opening_id),
            "move_number": c.move_number,
            "expected_move": c.expected_move,
            "fen_before_move": c.fen_before,
            "move_sequence_hash": c.move_sequence_hash,
            "repetitions": c.repetitions,
            "correct_count": c.correct_count,
        }
        for c in cards
    ]

@router.get("/queue/count")
async def get_drill_count(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(func.count()).select_from(UserMoveMastery).where(
            UserMoveMastery.user_id == current_user.id,
            UserMoveMastery.next_review <= datetime.utcnow(),
        )
    )
    return {"count": result.scalar() or 0}

@router.post("/review")
async def record_review(
    request: dict,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    quality = request.get("quality", 0)
    hash_key = request.get("move_sequence_hash")
    if quality not in range(6):
        raise HTTPException(400, "Quality must be 0-5")
    card = await srs_svc.record_review(str(current_user.id), hash_key, quality, db)
    return {
        "next_review": card.next_review.isoformat(),
        "interval_days": card.interval_days,
        "repetitions": card.repetitions,
    }

@router.get("/mastery/{opening_id}")
async def get_mastery(
    opening_id: str,
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserMoveMastery).where(
            UserMoveMastery.user_id == current_user.id,
            UserMoveMastery.opening_id == opening_id,
        )
    )
    cards = result.scalars().all()
    mastered = sum(1 for c in cards if c.repetitions >= 3 and c.easiness_factor >= 2.0)
    return {
        "opening_id": opening_id,
        "total_moves": len(cards),
        "mastered_moves": mastered,
        "mastery_percent": int((mastered / len(cards) * 100)) if cards else 0,
        "next_due_at": min((c.next_review for c in cards), default=None),
    }
```

### 7.6 Analytics Router

```python
# app/api/v1/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.dependencies import get_current_user
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_svc = AnalyticsService()

@router.get("/dashboard")
async def get_dashboard(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Single endpoint — returns everything needed for the Mission Control screen."""
    return await analytics_svc.get_dashboard(current_user, db)

@router.get("/rating-trend")
async def get_rating_trend(
    current_user=Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.db.models.lichess_rating_snapshot import LichessRatingSnapshot
    from sqlalchemy import select
    result = await db.execute(
        select(LichessRatingSnapshot)
        .where(LichessRatingSnapshot.user_id == current_user.id)
        .order_by(LichessRatingSnapshot.snapshotted_at)
    )
    snapshots = result.scalars().all()
    return {"snapshots": [{"rating": s.rating, "snapshotted_at": s.snapshotted_at.isoformat()} for s in snapshots]}
```

### 7.7 Webhooks Router

```python
# app/api/v1/webhooks.py
from fastapi import APIRouter, Request, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from fastapi import Depends
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
subscription_svc = SubscriptionService()

@router.post("/stripe")
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """Stripe sends raw body — do NOT use request.json() here. Read raw bytes."""
    payload = await request.body()
    if not stripe_signature:
        raise HTTPException(400, "Missing Stripe-Signature header")
    try:
        await subscription_svc.handle_webhook(payload, stripe_signature, db)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"received": True}
```

---

## 8. Background Workers

```python
# app/workers/lichess_import_worker.py
"""
Manages async background jobs for Lichess game import.
Job status tracked in Redis for frontend polling.
"""
import uuid
import json
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.cache import redis_client
from app.services.lichess_service import LichessService
from app.db.models.lichess_game import LichessGame
from app.db.models.lichess_rating_snapshot import LichessRatingSnapshot
from app.db.session import AsyncSessionLocal
from datetime import datetime

lichess_svc = LichessService()

async def start_import_job(
    background_tasks: BackgroundTasks,
    user_id: str,
    username: str,
    max_games: int,
    db: AsyncSession,
) -> str:
    job_id = str(uuid.uuid4())
    await redis_client.setex(
        f"job:{job_id}",
        3600,  # 1-hour TTL
        json.dumps({"status": "processing", "message": "Starting import...", "games_imported": 0})
    )
    background_tasks.add_task(_run_import, job_id, user_id, username, max_games)
    return job_id

async def get_job_status(job_id: str) -> dict | None:
    data = await redis_client.get(f"job:{job_id}")
    return json.loads(data) if data else None

async def _run_import(job_id: str, user_id: str, username: str, max_games: int):
    async with AsyncSessionLocal() as db:
        try:
            await redis_client.setex(
                f"job:{job_id}", 3600,
                json.dumps({"status": "processing", "message": f"Fetching games for @{username}..."})
            )

            games = await lichess_svc.fetch_user_games(username, max_games)

            # Also snapshot current rating
            rating = await lichess_svc.fetch_current_rating(username)
            if rating:
                db.add(LichessRatingSnapshot(user_id=user_id, lichess_username=username, rating=rating))

            imported = 0
            for game_data in games:
                eco = game_data.get("opening", {}).get("eco")
                opening_name = game_data.get("opening", {}).get("name")
                players = game_data.get("players", {})
                user_color = "white" if players.get("white", {}).get("user", {}).get("name", "").lower() == username.lower() else "black"
                winner = game_data.get("winner")
                result = "draw" if not winner else ("win" if winner == user_color else "loss")

                db.add(LichessGame(
                    user_id=user_id,
                    lichess_game_id=game_data.get("id", str(uuid.uuid4())),
                    eco_code=eco,
                    opening_name=opening_name,
                    result=result,
                    user_color=user_color,
                    opponent_rating=players.get("black" if user_color == "white" else "white", {}).get("rating"),
                    pgn=game_data.get("pgn"),
                    played_at=datetime.fromtimestamp(game_data.get("lastMoveAt", 0) / 1000) if game_data.get("lastMoveAt") else None,
                ))
                imported += 1

            await db.commit()

            await redis_client.setex(
                f"job:{job_id}", 3600,
                json.dumps({
                    "status": "done",
                    "message": f"Imported {imported} games.",
                    "games_imported": imported,
                })
            )

        except Exception as e:
            await db.rollback()
            await redis_client.setex(
                f"job:{job_id}", 3600,
                json.dumps({"status": "error", "message": str(e)})
            )
```

```python
# app/workers/glitch_report_worker.py
import uuid
import json
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.cache import redis_client
from app.services.lichess_analyzer import LichessAnalyzer
from app.db.session import AsyncSessionLocal
from app.db.models.user import User

analyzer = LichessAnalyzer()

async def start_report_job(background_tasks: BackgroundTasks, user: User, db: AsyncSession) -> str:
    job_id = str(uuid.uuid4())
    await redis_client.setex(
        f"report_job:{job_id}", 3600,
        json.dumps({"status": "processing", "message": "Analyzing game patterns..."})
    )
    background_tasks.add_task(_run_report, job_id, str(user.id), user.target_elo)
    return job_id

async def get_report_job_status(job_id: str) -> dict | None:
    data = await redis_client.get(f"report_job:{job_id}")
    return json.loads(data) if data else None

async def _run_report(job_id: str, user_id: str, user_elo: int):
    async with AsyncSessionLocal() as db:
        try:
            await redis_client.setex(
                f"report_job:{job_id}", 3600,
                json.dumps({"status": "processing", "message": "Running position analysis..."})
            )
            report = await analyzer.generate_report(user_id, user_elo, db)
            await db.commit()
            await redis_client.setex(
                f"report_job:{job_id}", 3600,
                json.dumps({"status": "done", "message": "Report ready", "report_id": str(report.id)})
            )
        except Exception as e:
            await db.rollback()
            await redis_client.setex(
                f"report_job:{job_id}", 3600,
                json.dumps({"status": "error", "message": str(e)})
            )
```

---

## 9. Caching Strategy

```python
# app/utils/cache.py
import redis.asyncio as aioredis
import json
from typing import Any, Optional
from app.config import settings

redis_client = aioredis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)

# Key patterns — document all key formats here for maintainability
CACHE_KEYS = {
    # Opening Explorer responses: 30-day TTL
    "opening_position": "opening:{fen_hash}:{elo_bucket}",
    # Background job status: 1-hour TTL
    "import_job":       "job:{job_id}",
    "report_job":       "report_job:{job_id}",
    # Rate limiting: sliding window per user
    "rate_moves":       "rate:moves:{user_id}:{minute}",
    "rate_analyses":    "rate:analyses:{user_id}:{day}",
    "rate_drills":      "rate:drills:{user_id}:{day}",
    # Session locking: prevent concurrent moves on same session
    "session_lock":     "lock:session:{session_id}",
}
```

**Cache TTLs by data type:**

| Data | TTL | Reason |
|------|-----|--------|
| Lichess Explorer moves | 30 days | Changes very slowly; free API |
| Background job status | 1 hour | Frontend polls for ~30s max |
| Session lock | 5 seconds | Prevents double-move race conditions |
| Rate limit counters | 60s / 24h | Sliding windows |
| User rating snapshot | None (DB) | Permanent historical record |

---

## 10. Cost Optimization Rules

These rules are **enforced in code**, not just documented.

**Rule 1 — Stockfish: client-side for sparring, server-side for reports only.**
The server NEVER runs Stockfish during a sparring session. Move quality evaluation runs client-side via stockfish.wasm (Web Worker). The server's role during sparring is: validate legality → look up Explorer data → return opponent move → track game state. See Master Guide ADR-002.

**Rule 2 — NEON coaching: templates first, Gemini second.**
In-game coaching uses the template library (instant, no network call). Gemini is called only for Glitch Report narratives (~1 call per import) and post-session summaries (~1 call per session end). At 100 DAU, that's ~200 Gemini calls/day — well within free tier.

**Rule 3 — Lichess Explorer: Redis before HTTP.**
All Explorer calls check Redis first. On cache miss, result is stored immediately with 30-day TTL. After 2–3 weeks of usage, >90% of common positions are cached.

**Rule 4 — Glitch Report: Stockfish on sample only.**
`lichess_analyzer.py` runs Stockfish collapse detection + collapse type classification on a maximum of 5 worst games per opening. Server-side Stockfish runs on native binary on the Hostinger VPS — no container overhead.

**Rule 5 — Free tier data pruning (cleanup_old_data.py):**
```python
# Run weekly via cron on Hostinger VPS
# Delete lichess_games rows older than 90 days for free users (keep ECO stats in user_stats)
# Delete completed sparring_sessions older than 30 days for free users
# Keep all data for Pro users indefinitely
```

**Rule 6 — Hosting cost is $0/month.**
FastAPI runs on the existing Hostinger KVM VPS (already paid for Singular Mind). Neon free tier, Upstash free tier, Vercel free tier. First dollar of revenue is pure margin.

---

## 11. Testing

```python
# tests/conftest.py
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.db.base import Base
from app.dependencies import get_db

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()

@pytest_asyncio.fixture
async def db_session(test_engine):
    Session = async_sessionmaker(test_engine, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    async with AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

**Key test cases — every mission must pass these:**

```
test_auth.py:
  ✓ POST /auth/guest → returns JWT
  ✓ JWT decodes to valid user_id
  ✓ Invalid token → 401

test_sessions.py:
  ✓ POST /sessions → returns session_id + FEN + neon_intro
  ✓ POST /sessions/{id}/moves with legal move → valid=true, FEN updated
  ✓ POST /sessions/{id}/moves with illegal move → valid=false, legal_moves returned
  ✓ Blunder → move_quality=blunder, coach_message populated
  ✓ Theory exit detected at correct move number
  ✓ POST /sessions/{id}/opponent-move → returns move dict + thinking_time_ms

test_session_service.py:
  ✓ _classify_cp_loss(0) → ("excellent", 0)
  ✓ _classify_cp_loss(30) → ("inaccuracy", -5)
  ✓ _classify_cp_loss(200) → ("blunder", -30)
  ✓ accuracy_score clamps at 0 (no negative accuracy)

test_chess_service.py:
  ✓ parse_move handles valid UCI moves
  ✓ parse_move returns None for illegal moves
  ✓ hash_fen is stable across equivalent positions
  ✓ is_in_theory correctly identifies book positions

test_srs_service.py:
  ✓ calculate_next_review(0, 2.5, 0, 5) → interval=1, repetitions=1
  ✓ calculate_next_review(1, 2.5, 1, 5) → interval=6, repetitions=2
  ✓ quality < 3 resets repetitions to 0
  ✓ easiness_factor never drops below 1.3
  ✓ get_due_cards respects free tier cap of 5

test_lichess_analyzer.py:
  ✓ _aggregate_by_eco groups correctly by ECO code
  ✓ Win rate < 40% flagged as critical
  ✓ Win rate >= 55% flagged as strength
  ✓ generate_report with mocked games returns valid GlitchReport
```

```ini
# pytest.ini
[pytest]
asyncio_mode = auto
testpaths = tests
```

---

## 12. Deployment & Ops (Hostinger VPS)

### Dockerfile (for local dev only — production uses PM2 directly)

```dockerfile
FROM python:3.11-slim

# Install Stockfish (for Glitch Report generation)
RUN apt-get update && apt-get install -y stockfish && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
```

### PM2 Ecosystem Config (Hostinger VPS)

```javascript
// ecosystem.config.js
module.exports = {
  apps: [{
    name: 'neongambit-api',
    script: 'uvicorn',
    args: 'app.main:app --host 127.0.0.1 --port 8000',
    interpreter: 'python3',
    cwd: '/var/www/neongambit/backend',
    env: {
      ENVIRONMENT: 'production'
    },
    max_memory_restart: '500M',
    instances: 1,
    autorestart: true,
    watch: false,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
  }]
};
```

### nginx Configuration

```nginx
# /etc/nginx/sites-available/neongambit-api
server {
    listen 443 ssl http2;
    server_name api.neongambit.com;

    ssl_certificate /etc/letsencrypt/live/api.neongambit.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.neongambit.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed in Phase 2)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Rate limiting at nginx level
    limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
    limit_req zone=api burst=50 nodelay;
}

server {
    listen 80;
    server_name api.neongambit.com;
    return 301 https://$server_name$request_uri;
}
```

### Deploy Script

```bash
#!/bin/bash
# scripts/deploy.sh — run from Hostinger VPS
set -e

cd /var/www/neongambit/backend
git pull origin main
pip install -r requirements.txt --break-system-packages
alembic upgrade head
pm2 restart neongambit-api
echo "Deployed successfully."
```

### Cron Jobs (Hostinger)

```cron
# Weekly data pruning (Sunday 3am UTC)
0 3 * * 0 cd /var/www/neongambit/backend && python3 scripts/cleanup_old_data.py

# SSL certificate renewal
0 0 1 * * certbot renew --quiet
```

### requirements.txt

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy[asyncio]==2.0.25
alembic==1.13.1
asyncpg==0.29.0
aiosqlite==0.19.0            # Test database
pydantic==2.5.3
pydantic-settings==2.1.0
python-chess==1.999
redis[hiredis]==5.0.1
httpx==0.26.0
python-jose[cryptography]==3.3.0
firebase-admin==6.3.0
google-generativeai==0.3.2
pyyaml==6.0.1                       # NEON template library
stripe==7.11.0
pytest==7.4.4
pytest-asyncio==0.23.3
```

### Alembic Setup

```python
# alembic/env.py — async-compatible config
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.db.base import Base
from app.db import models  # Import all models so Alembic detects them
from app.config import settings
import asyncio

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", "+psycopg2"))
# Note: Alembic uses sync driver for migrations

target_metadata = Base.metadata

def run_migrations_online():
    connectable = config.attributes.get("connection", None)
    # ... standard async migration runner
```

### Deployment Checklist (Hostinger VPS)

```
1. SSH into VPS: ssh user@your-hostinger-ip
2. Clone repo: git clone https://github.com/your/neongambit.git /var/www/neongambit
3. Install dependencies: pip install -r backend/requirements.txt
4. Install Stockfish: apt install stockfish
5. Copy .env to /var/www/neongambit/backend/.env
6. Run migrations: cd backend && alembic upgrade head
7. Seed openings: python3 scripts/seed_openings.py
8. Start PM2: pm2 start ecosystem.config.js
9. Configure nginx: cp nginx.conf /etc/nginx/sites-available/neongambit-api
10. Enable site: ln -s /etc/nginx/sites-available/neongambit-api /etc/nginx/sites-enabled/
11. SSL: certbot --nginx -d api.neongambit.com
12. Verify: curl https://api.neongambit.com/health → {"status": "ok", "version": "5.1.0"}
```

---

## 13. Antigravity Mission Plan

Each mission is a directive for Antigravity's **Agent Manager**. The agent plans, codes, tests via `pytest`, and produces artifacts autonomously.

### Mission 1 — Foundation & Schema (4h)
```
Task: Set up FastAPI project structure per Section 2.
Create app/main.py, app/config.py, app/dependencies.py.
Create all SQLAlchemy models per Section 4 (MVP tables only — no conversion_failures, no endgame_drill_cards, no achievements).
User model includes preferred_language field.
Set up Alembic with async-compatible env.py.
Run initial migration against Neon DB.
Create app/utils/cache.py with Redis client.
Create ecosystem.config.js for PM2.
Create nginx.conf template.
Implement GET /health endpoint.
Verify: alembic upgrade head succeeds. GET /health returns {"status": "ok", "version": "5.1.0"}.
Verify: All MVP tables exist in Neon DB.
```

### Mission 2 — Auth + User Profile (3h)
```
Task: Implement AuthService per Section 6.1.
Implement all /auth/* endpoints per Section 7.1.
Implement GET /user/profile and PATCH /user/profile (includes preferred_language).
Implement core.security.py: JWT create/decode.
Implement dependencies.py: get_current_user, require_pro.
Write tests: test_auth.py — all assertions in Section 11.
Verify: POST /auth/guest returns JWT. Token decodes to user_id.
Verify: Authenticated request with invalid token → 401.
Verify: GET /user/profile with valid token returns user data including preferred_language.
```

### Mission 3 — Lichess Import + Background Worker (4h)
```
Task: Implement LichessService.fetch_user_games and fetch_current_rating per Section 6.4.
Implement lichess_import_worker.py per Section 8:
  - start_import_job stores job status in Redis
  - _run_import runs as FastAPI BackgroundTask
  - Parses NDJSON stream from Lichess API
  - Saves LichessGame rows + LichessRatingSnapshot
  - NO conversion failure analysis (Phase 2)
Implement Lichess API degraded mode: cache-first, retry queue, graceful fallback.
Implement /lichess/import and /lichess/import/status endpoints per Section 7.2.
Verify: POST /lichess/import with a real username → job_id returned.
Verify: Poll /lichess/import/status → status transitions processing → done.
Verify: LichessGame rows created in DB with correct eco_code and result.
```

### Mission 4 — Glitch Report Engine (5h)
```
Task: Implement StockfishService per Section 6.3 (server-side ONLY, for Glitch Report).
Implement LichessAnalyzer per Section 6.7:
  - _aggregate_by_eco: group games by ECO, calculate win rates
  - Identify critical openings (win_rate < 40%)
  - Run Stockfish collapse detection on 5 worst games per critical opening
  - Classify collapse_type per opening: opening_error, tactical_blunder, positional_drift, time_pressure
  - Call CoachService.generate_diagnosis (Gemini, includes collapse_type + locale)
  - Call CoachService.generate_overall_pattern
  - Auto-assign top 2 critical openings to user's repertoire (Free) or all (Pro)
Implement glitch_report_worker.py per Section 8.
Implement /glitch-report/generate and /glitch-report/current per Section 7.3.
  - Free tier: ALL critical openings visible, training_unlocked=True only for top 2
  - Pro tier: ALL openings have training_unlocked=True
Write tests: test_lichess_analyzer.py — all assertions in Section 11.
Verify: Generate report for username with 20+ games → GlitchReport row created.
Verify: Critical openings have win_rate < 40%, collapse_type populated.
Verify: neon_diagnosis is under 40 words. overall_pattern is under 60 words.
```

### Mission 5 — Sparring Sessions + NEON Templates (5h)
```
Task: Implement ChessService per Section 6.2.
Create data/neon_templates.yaml with ~200 coaching templates in EN + ES.
  Each blunder/mistake template follows: consequence → pattern name → forward seed.
Implement coach_templates.py: template selection engine per Section 6.5.
Implement CoachService per Section 6.5 (template lookup + Gemini for narratives).
Implement SessionService per Section 6.6:
  - NO server-side Stockfish during sparring (ADR-002)
  - Server validates legality, tracks theory, returns opponent move
  - Accepts prev_move_quality from client for stats tracking
  - Coaching messages from template library (instant, no LLM)
Implement LichessService.get_explorer_moves per Section 6.4 with Redis cache.
Implement all /sessions/* endpoints per Section 7.4.
  - Tilt tracking: increment consecutive_sparring_losses on loss, reset on win/draw.
Write tests: test_sessions.py, test_session_service.py, test_coach_templates.py.
Verify: POST /sessions creates session with valid FEN and neon_intro.
Verify: Legal move → valid=true, FEN updated, theory_integrity tracked.
Verify: Illegal move → valid=false, legal_moves list returned.
Verify: Theory exit at move 9 → theory_exit_detected=true, coach_message from template.
Verify: Blunder with prev_move_quality → coach_message from template library (instant).
Verify: POST /sessions/{id}/opponent-move → returns move + thinking_time_ms.
Verify: Template returns Spanish text when locale='es'.
```

### Mission 6 — Neural Drill + SRS (3h)
```
Task: Implement SRSService per Section 6.8 (SM-2 algorithm + card management).
Implement simplified repertoire endpoints: GET /repertoire, POST /repertoire.
Wire POST /repertoire → srs_service.populate_cards_for_opening to auto-create SRS cards.
Implement all /drill/* endpoints per Section 7.5.
Write tests: test_srs_service.py — all SM-2 assertions in Section 11.
Verify: Adding opening to repertoire creates correct number of SRS cards.
Verify: GET /drill/queue returns only due cards, respecting free-tier cap of 5.
Verify: POST /drill/review with quality=5 doubles interval. quality=1 resets to 1 day.
Verify: easiness_factor never drops below 1.3.
```

### Mission 7 — Analytics + Dashboard (3h)
```
Task: Implement AnalyticsService per Section 6.9 (MVP: simplified, no conversion failures).
Implement all /analytics/* endpoints per Section 7.6.
Implement streak tracking in user_stats (increment on drill completion or session win).
Implement GET /user/tilt-status endpoint.
Verify: GET /analytics/dashboard returns all fields including tilt_detected and recommended_session.
Verify: Streak increments on session completion. Resets after 2-day gap.
Verify: tilt_detected=true when consecutive_sparring_losses >= 3 and within 25 minutes.
```

### Mission 8 — Webhooks + Subscriptions + Deploy (2h)
```
Task: Implement SubscriptionService per Section 6.10.
Implement /subscriptions/checkout, /webhooks/stripe per Section 7.7.
Wire Stripe webhook to update user.is_pro and subscriptions table.
Deploy to Hostinger VPS per Section 12:
  - PM2 + nginx + SSL (Let's Encrypt)
  - Stockfish binary installed: apt install stockfish
Push to GitHub → manual deploy via scripts/deploy.sh.
Verify: GET /health returns ok on deployed URL.
Verify: POST /auth/guest works against production DB.
Verify: Full sparring session flow works end-to-end via production API.
```

---

## 14. Phase 2 Deferred Services

The following services are fully designed in Master Guide v5.1 Phase 2 Roadmap but NOT implemented in MVP. They will be added when triggered by user validation signals.

| Service | Trigger | Notes |
|---------|---------|-------|
| ConversionFailureService | Users asking about endgames | Full code in v4 backend guide can be referenced |
| EndgameDrillCard model + endpoints | Same trigger | SM-2 infrastructure already built, just needs new card source |
| MissionService | Drill queue alone isn't driving daily return | Thin orchestration over analytics |
| AchievementService | D7 retention needs gamification | Catalog defined in v4, implementation straightforward |
| Full Repertoire Builder | Users wanting openings beyond Glitch Report | Browse + search + manual add |
| Game Review / Debrief | Users wanting move-by-move analysis | Gemini per-move narration (expensive) |

---

*End of NeonGambit Backend Implementation Guide v5.1*
*The API serves the user. The templates own the coaching. The client owns the engine.*
