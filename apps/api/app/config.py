from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_secret_key: str = "development-only-change-me"
    admin_api_token: str = ""
    database_url: str = "sqlite:///./doctranslator.db"
    redis_url: str = "redis://localhost:6379/0"
    storage_root: Path = Path("./storage")
    file_retention_days: int = 30
    max_upload_mb: int = 100
    max_page_count: int = 500
    default_target_language: str = "en"
    ocr_confidence_threshold: float = 0.80
    provider_secret_encryption_key: str = ""
    allowed_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def origins(self) -> list[str]:
        return [value.strip() for value in self.allowed_origins.split(",") if value.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()

