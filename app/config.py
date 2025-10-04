# app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    app_env: str = Field(default="dev")
    app_port: int = Field(default=8000)
    allow_origins_csv: str = Field(default="http://localhost:3000")  # <- string
    http_timeout: int = Field(default=15)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allow_origins(self) -> list[str]:
        return [s.strip() for s in self.allow_origins_csv.split(",") if s.strip()]

settings = Settings()
