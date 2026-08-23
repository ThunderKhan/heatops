from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    heatops_environment: Literal["development", "test", "production"] = "development"
    heatops_provider: Literal["auto", "mock", "fortyguard"] = "auto"
    heatops_mock_grid_size: int = Field(default=8, ge=2, le=50)
    fortyguard_api_key: str | None = None
    fortyguard_base_url: str = "https://api.fortyguard.com"
    fortyguard_timeout_seconds: float = Field(default=45.0, gt=0, le=180)
    fortyguard_poll_interval_seconds: float = Field(default=1.0, ge=0.1, le=10)
    groq_api_key: str | None = None
    heatops_groq_model: str = "qwen/qwen3.6-27b"
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_timeout_seconds: float = Field(default=20.0, gt=0, le=60)
    heatops_cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origins(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.heatops_cors_origins.split(",")
            if origin.strip()
        ]


@lru_cache
def get_settings() -> Settings:
    return Settings()
