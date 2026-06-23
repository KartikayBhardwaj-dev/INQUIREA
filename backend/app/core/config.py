from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Inquirea"
    APP_VERSION: str = "0.1.0"

    DEBUG: bool = True

    model_config = {
        "env_file": ".env",
        "extra": "ignore",
    }


@lru_cache
def get_settings():
    return Settings()