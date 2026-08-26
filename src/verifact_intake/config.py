from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration loaded from environment variables or `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    verifact_env: Literal["development", "test", "production"] = "development"
    verifact_asset_root: Path | None = None
    verifact_database_url: str = "sqlite:///./data/runtime/verifact.db"
    verifact_extraction_provider: Literal["fixture", "nutrient"] = "fixture"
    nutrient_api_key: SecretStr | None = None
    nutrient_api_base_url: str = "https://api.nutrient.io"
    llm_provider: str = "disabled"
    llm_api_key: SecretStr | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
