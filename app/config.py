# app/config.py
from __future__ import annotations
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",  # ignora variables que no declares aquí
    )

    app_env: str = "dev"
    app_port: int = 8000
    allow_origins: Union[str, List[str]] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    http_timeout: int = 15
    cors_enabled: bool = True

    @field_validator("allow_origins")
    @classmethod
    def _normalize_allow_origins(cls, v):
        if isinstance(v, list):
            return v
        s = str(v).strip()
        if not s:
            return []
        # intenta parsear JSON primero
        try:
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except Exception:
            pass
        # fallback: CSV
        return [p.strip() for p in s.split(",") if p.strip()]

settings = Settings()
