"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Backend configuration. Secrets stay on the server only."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    openai_timeout_seconds: float = 30.0
    openai_max_tokens: int = 1200
    # Abuse / spend soft controls for /api/analyze-shade (in-memory; per process).
    openai_rate_limit_per_ip_hour: int = 10
    openai_daily_request_cap: int = 200
    # Include 127.0.0.1 — browsers treat it as a different origin than localhost.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def has_openai_key(self) -> bool:
        return bool(self.openai_api_key and self.openai_api_key != "sk-your-key-here")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
