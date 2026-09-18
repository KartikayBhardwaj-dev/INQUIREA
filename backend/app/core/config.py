from enum import Enum
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[3]

load_dotenv(BASE_DIR / ".env")


class EmailCategory(str, Enum):
    OPPORTUNITY = "opportunity"
    DEADLINE = "deadline"
    FINANCE = "finance"
    JOB = "job"
    INTERNSHIP = "internship"
    MEETING = "meeting"
    REPLY_REQUIRED = "reply_required"
    PROMOTION = "promotion"
    AUTOMATED_NOTIFICATION = "automated_notification"
    PERSONAL = "personal"
    OTHER = "other"


class Settings(BaseSettings):
    # ----------------------------------------
    # Application
    # ----------------------------------------

    APP_NAME: str = "Inquirea"
    APP_VERSION: str = "0.1.0"

    APP_ENV: str = "development"
    DEBUG: bool = False

    # ----------------------------------------
    # Frontend / CORS
    # ----------------------------------------

    FRONTEND_URL: str = "http://localhost:3000"
    CORS_ORIGINS: str = "http://localhost:3000"

    # ----------------------------------------
    # Database
    # ----------------------------------------

    DATABASE_URL: str
    CHECKPOINT_DATABASE_URL: str

    # ----------------------------------------
    # Authentication / Security
    # ----------------------------------------

    SECRET_KEY: str
    SESSION_SECRET_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ----------------------------------------
    # Google OAuth / Gmail
    # ----------------------------------------

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # ----------------------------------------
    # LLM
    # ----------------------------------------

    GROQ_API_KEY: str

    LLM_PROVIDER: str = "groq"
    LLM_MODEL: str = "openai/gpt-oss-120b"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 2048

    # ----------------------------------------
    # Email Processing
    # ----------------------------------------

    MAX_CONCURRENT_EMAILS: int = 5

    EMAIL_QUEUE_SIZE: int = 500
    EMAIL_WORKERS: int = 2
    EMAIL_RETRY_LIMIT: int = 5
    EMAIL_BATCH_SIZE: int = 10
    QUEUE_POLL_INTERVAL: float = 0.5

    # ----------------------------------------
    # Embeddings
    # ----------------------------------------

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"

    # ----------------------------------------
    # LLM Rate Limiting
    # ----------------------------------------

    LLM_MAX_CONCURRENT_REQUESTS: int = 5
    LLM_MAX_RETRIES: int = 5
    LLM_INITIAL_BACKOFF: float = 2.0
    LLM_MAX_BACKOFF: float = 30.0

    LLM_TOKENS_PER_MINUTE: int = 250000
    LLM_REQUESTS_PER_MINUTE: int = 1000

    # ----------------------------------------
    # LLM Batch Scheduling
    # ----------------------------------------

    LLM_BATCH_SIZE: int = 10
    LLM_BATCH_WAIT_MS: int = 50

    # ----------------------------------------
    # Adaptive Concurrency
    # ----------------------------------------

    LLM_MIN_CONCURRENT_REQUESTS: int = 2
    LLM_MAX_CONCURRENT_LIMIT: int = 10
    LLM_ENABLE_ADAPTIVE_CONCURRENCY: bool = True

    # ----------------------------------------
    # LangSmith
    # ----------------------------------------

    LANGCHAIN_TRACING_V2: bool = False
    LANGCHAIN_API_KEY: str | None = None
    LANGCHAIN_PROJECT: str = "INQUIREA"
    LANGCHAIN_ENDPOINT: str = "https://api.smith.langchain.com"

    # ----------------------------------------
    # Redis / Celery
    # ----------------------------------------

    REDIS_URL: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]

    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True

    CELERY_MAX_RETRIES: int = 5
    CELERY_RETRY_BACKOFF: bool = True
    CELERY_RETRY_BACKOFF_MAX: int = 600
    CELERY_RETRY_JITTER: bool = True

    # ----------------------------------------
    # Celery Worker
    # ----------------------------------------

    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()