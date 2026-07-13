from enum import Enum
from functools import lru_cache
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

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
    APP_NAME: str = "Inquirea"
    APP_VERSION: str = "0.1.0"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: str
    CHECKPOINT_DATABASE_URL: str

    SECRET_KEY: str
    SESSION_SECRET_KEY: str

    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str

    # ----------------------------------------
    # LLM Configuration
    # ----------------------------------------
    GOOGLE_API_KEY: str
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_OUTPUT_TOKENS: int = 2048

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_CONCURRENT_EMAILS: int = 5

    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    CHROMA_PATH: str = "backend/app/memory/chroma"
    CHROMA_COLLECTION: str = "email_memory"

    EMAIL_QUEUE_SIZE: int = 500
    EMAIL_WORKERS: int = 2
    EMAIL_RETRY_LIMIT: int = 5
    EMAIL_BATCH_SIZE: int = 10
    QUEUE_POLL_INTERVAL: float = 0.5

    # ----------------------------------------
    # LLM Rate Limiting
    # ----------------------------------------
    LLM_MAX_CONCURRENT_REQUESTS: int = 5
    LLM_MAX_RETRIES: int = 5
    LLM_INITIAL_BACKOFF: float = 2.0
    LLM_MAX_BACKOFF: float = 30.0
    LLM_TOKENS_PER_MINUTE: int = 250000

    # Provider limits
    LLM_REQUESTS_PER_MINUTE: int = 1000

    # Batch scheduling
    LLM_BATCH_SIZE: int = 10
    LLM_BATCH_WAIT_MS: int = 50

    # Adaptive concurrency
    LLM_MIN_CONCURRENT_REQUESTS: int = 2
    LLM_MAX_CONCURRENT_LIMIT: int = 10
    LLM_ENABLE_ADAPTIVE_CONCURRENCY: bool = True
    GROQ_API_KEY: str | None = None

    # ----------------------------------------
    # Celery
    # ----------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = REDIS_URL
    CELERY_RESULT_BACKEND: str = REDIS_URL
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_ACCEPT_CONTENT: list[str] = ["json"]
    CELERY_TIMEZONE: str = "UTC"
    CELERY_ENABLE_UTC: bool = True
    CELERY_MAX_RETRIES: int = 5
    CELERY_RETRY_BACKOFF: bool = True
    CELERY_RETRY_BACKOFF_MAX: int = 600
    CELERY_RETRY_JITTER: bool = True

    # Worker Configuration
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = 1
    CELERY_TASK_ACKS_LATE: bool = True
    CELERY_TASK_TRACK_STARTED: bool = True

    # Beat
    CELERY_BEAT_SCHEDULE_ENABLED: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()