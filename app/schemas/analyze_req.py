"""Request schemas for analyze endpoints."""
from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator

ALLOWED_FACTORS = {
    "temperature",
    "precipitation",
    "windspeed",
    "humidity",
    "comfort",
}


class AnalyzeReq(BaseModel):
    latitude: float = Field(
        ..., ge=-90, le=90, description="Latitud del punto de interés", examples=[19.43]
    )
    longitude: float = Field(
        ..., ge=-180, le=180, description="Longitud del punto de interés", examples=[-99.13]
    )
    month: int = Field(..., ge=1, le=12, description="Mes del año", examples=[5])
    day: int = Field(..., ge=1, le=31, description="Día del mes", examples=[10])
    start_year: int = Field(
        ..., ge=1981, description="Primer año histórico a considerar", examples=[2000]
    )
    end_year: int = Field(
        ..., ge=1981, description="Último año histórico a considerar", examples=[2020]
    )
    half_window_days: int = Field(
        10,
        ge=0,
        le=30,
        description="Ventana móvil a cada lado del día objetivo",
        examples=[5],
    )
    factors: List[str] = Field(
        default=["temperature", "precipitation", "windspeed", "humidity"],
        description="Factores a analizar",
        examples=[["temperature", "humidity"]],
    )

    @field_validator("factors")
    @classmethod
    def validate_factors(cls, v: List[str]) -> List[str]:
        bad = [f for f in v if f not in ALLOWED_FACTORS]
        if bad:
            raise ValueError(f"Unsupported factors: {bad}")
        return v
