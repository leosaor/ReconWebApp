from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_SECRET = "change-me-in-prod"
_MIN_PROD_SECRET_LEN = 32


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    app_name: str = "ReconWebApp"
    environment: str = "development"
    debug: bool = False

    secret_key: str = Field(default=_INSECURE_SECRET, min_length=8)

    database_url: str = "postgresql+psycopg://recon:recon@postgres:5432/recon"

    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    recon_output_dir: str = "scan-output"

    # Em produção a app é servida pelo nginx (mesma origem), então CORS pode ser
    # restrito. Em dev o browser fala com o Next (localhost:3000) que faz rewrite
    # server-side para a API — também mesma origem do ponto de vista do browser.
    cors_origins: list[str] = ["http://localhost:3000"]

    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7

    @property
    def is_production(self) -> bool:
        return self.environment.strip().lower() in {"production", "prod"}

    @property
    def cookie_secure(self) -> bool:
        """Cookies de sessão só viajam por HTTPS em produção."""
        return self.is_production

    @property
    def broker_url(self) -> str:
        return self.celery_broker_url or self.redis_url

    @property
    def result_backend(self) -> str:
        return self.celery_result_backend or self.redis_url

    @model_validator(mode="after")
    def _validate_production_secrets(self) -> "Settings":
        if not self.is_production:
            return self
        if self.secret_key == _INSECURE_SECRET:
            raise ValueError(
                "SECRET_KEY precisa ser definido (não use o default) quando ENVIRONMENT=production"
            )
        if len(self.secret_key) < _MIN_PROD_SECRET_LEN:
            raise ValueError(
                f"SECRET_KEY deve ter pelo menos {_MIN_PROD_SECRET_LEN} caracteres em produção"
            )
        if "*" in self.cors_origins:
            raise ValueError("CORS_ORIGINS não pode conter '*' em produção")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
