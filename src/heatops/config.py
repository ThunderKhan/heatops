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
    heatops_provider: Literal["mock"] = "mock"
    heatops_mock_grid_size: int = Field(default=8, ge=2, le=50)
    fortyguard_api_key: str | None = None
    fortyguard_base_url: str = "https://api.fortyguard.com"


@lru_cache
def get_settings() -> Settings:
    return Settings()

