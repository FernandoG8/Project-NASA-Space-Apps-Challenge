"""Application configuration powered by Pydantic settings."""
from __future__ import annotations

import json
from functools import lru_cache
from typing import List, Sequence

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # --- General -----------------------------------------------------------------
    app_name: str = Field("WeatherAPI", alias="APP_NAME")
    app_env: str = Field("dev", alias="APP_ENV")
    app_port: int = Field(8000, alias="APP_PORT")
    cors_enabled: bool = Field(True, alias="CORS_ENABLED")
    http_timeout: int = Field(15, alias="HTTP_TIMEOUT")

    # --- CORS ---------------------------------------------------------------------
    allow_origins: Sequence[str] | str = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        alias="ALLOW_ORIGINS",
    )

    @field_validator("allow_origins")
    @classmethod
    def _normalise_allow_origins(cls, value: Sequence[str] | str) -> List[str]:
        if isinstance(value, (list, tuple)):
            return [str(v) for v in value]
        string_value = str(value).strip()
        if not string_value:
            return []
        try:
            parsed = json.loads(string_value)
            if isinstance(parsed, list):
                return [str(v) for v in parsed]
        except json.JSONDecodeError:
            pass
        return [part.strip() for part in string_value.split(",") if part.strip()]

    # --- JWT ----------------------------------------------------------------------
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algo: str = Field("HS256", alias="JWT_ALGO")
    access_min: int = Field(15, alias="ACCESS_MIN")
    refresh_days: int = Field(30, alias="REFRESH_DAYS")

    # --- Base de datos ------------------------------------------------------------
    database_url: str = Field(
        "mysql+pymysql://fernando:password@localhost/weatherAPI",
        alias="DATABASE_URL",
    )

    # --- Utilidades ---------------------------------------------------------------
    @property
    def is_dev(self) -> bool:
        return self.app_env.lower() == "dev"

    @property
    def is_prod(self) -> bool:
        return self.app_env.lower() == "prod"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached Settings instance."""

    return Settings()


settings = get_settings()

__all__ = ["settings", "get_settings", "Settings"]
