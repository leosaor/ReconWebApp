from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "ReconWebApp"
    environment: str = "development"
    debug: bool = False

    secret_key: str = Field(default="change-me-in-prod", min_length=8)

    database_url: str = "postgresql+psycopg://recon:recon@postgres:5432/recon"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None

    cors_origins: list[str] = ["http://localhost:3000"]

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
