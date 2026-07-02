from functools import lru_cache

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


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

    GROQ_API_KEY: str

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    MAX_CONCURRENT_EMAILS: int = 5

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings():
    return Settings()