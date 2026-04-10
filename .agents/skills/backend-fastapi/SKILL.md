# Skill: backend-fastapi

FastAPI patterns for NeonGambit backend (Python 3.11+, async).

## Project Structure (Section 2)

```
backend/app/
├── main.py          # FastAPI factory + lifespan + CORS + /health
├── config.py        # Pydantic Settings (all env vars typed, lru_cache)
├── dependencies.py  # get_current_user, require_pro, get_db
├── core/            # security.py, exceptions.py, middleware.py, rate_limiter.py
├── db/              # base.py, session.py, models/
├── schemas/         # Pydantic V2 — API contracts only
├── api/v1/          # Thin routers — no business logic
├── services/        # All business logic lives here
├── workers/         # Background tasks (lichess_import, glitch_report)
└── utils/           # cache.py, fen_utils.py, pgn_utils.py
```

## FastAPI App Factory (Section 3)

```python
# app/main.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
    firebase_admin.initialize_app(cred)
    await redis_client.ping()
    yield
    await redis_client.aclose()

app = FastAPI(title="NeonGambit API", version="5.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.CORS_ORIGINS, ...)
app.include_router(v1_router, prefix="/v1")

@app.get("/health")
async def health():
    return {"status": "ok", "version": "5.1.0"}
```

## Config (Section 3)

```python
class Settings(BaseSettings):
    DATABASE_URL: str          # postgresql+asyncpg://...
    REDIS_URL: str
    FIREBASE_PROJECT_ID: str
    JWT_SECRET_KEY: str
    GOOGLE_GEMINI_API_KEY: str
    STOCKFISH_PATH: str = "/usr/local/bin/stockfish"
    STOCKFISH_MAX_DEPTH: int = 15
    STRIPE_SECRET_KEY: str
    RATE_LIMIT_DRILLS_FREE_PER_DAY: int = 5
    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings: return Settings()
```

## Database Session (Section 3)

```python
engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
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

## Auth Dependencies (Section 3)

```python
async def get_current_user(credentials=Depends(bearer), db=Depends(get_db)) -> User:
    payload = decode_jwt(credentials.credentials)
    if not payload: raise HTTPException(401, "Invalid token")
    user = await db.execute(select(User).where(User.id == payload["sub"]))
    return user.scalar_one_or_none() or raise HTTPException(401, "User not found")

async def require_pro(user=Depends(get_current_user)) -> User:
    if not user.is_pro: raise HTTPException(403, "Grandmaster tier required")
    return user
```

## Router Pattern (Section 7)

Routers are **thin** — no business logic. Always delegate to services.

```python
router = APIRouter(prefix="/auth", tags=["auth"])
auth_svc = AuthService()

@router.post("/guest", response_model=TokenResponse)
async def create_guest(db: AsyncSession = Depends(get_db)):
    user, token = await auth_svc.create_guest(db)
    return {"access_token": token, "token_type": "bearer"}
```

## Code Standards

- PEP 8 + Black formatting
- Type hints on ALL function signatures
- All async functions use async/await — no sync I/O in async context
- All DB operations go through `get_db()` dependency
- Conventional commits: `feat:`, `fix:`, `test:`, `docs:`, `refactor:`

## Endpoints That Skip Auth

Only `/auth/guest` and `/auth/validate` bypass `get_current_user`.
