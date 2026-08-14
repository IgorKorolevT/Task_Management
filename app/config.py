from functools import lru_cache

from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )

    # Database
    DB_USER: str = "taskuser"
    DB_PASSWORD: str = "taskpass"
    DB_NAME: str = "taskdb"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    # JWT
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Logging
    LOG_LEVEL: str = "INFO"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Background tasks
    OVERDUE_TASK_CHECK_INTERVAL: int = 60

    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+asyncpg://"
            f"{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()