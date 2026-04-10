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
