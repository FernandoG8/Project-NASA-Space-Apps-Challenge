# app/config.py
from __future__ import annotations
from typing import List, Union
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    # --- Configuración general ---
    app_name: str = Field("WeatherAPI", alias="APP_NAME")
    app_env: str = Field("dev", alias="APP_ENV")
    app_port: int = Field(8000, alias="APP_PORT")
    cors_enabled: bool = True
    http_timeout: int = Field(15, alias="HTTP_TIMEOUT")

    # --- CORS ---
    allow_origins: Union[str, List[str]] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000"],
        alias="ALLOW_ORIGINS"
    )

    @field_validator("allow_origins")
    @classmethod
    def _normalize_allow_origins(cls, v):
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if not s:
            return []
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        return [p.strip() for p in s.split(",") if p.strip()]

    # --- JWT ---
    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_algo: str = Field("HS256", alias="JWT_ALGO")
    access_min: int = Field(15, alias="ACCESS_MIN")
    refresh_days: int = Field(30, alias="REFRESH_DAYS")

    # --- Base de datos ---
    database_url: str = Field(
        "mysql+pymysql://fernando:password@localhost/tallerFirestone",
        alias="DATABASE_URL"
    )

# Instancia global
settings = Settings()
