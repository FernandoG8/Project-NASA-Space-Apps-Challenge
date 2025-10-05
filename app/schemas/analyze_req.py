from pydantic import BaseModel, Field, field_validator
from typing import List

ALLOWED_FACTORS = {"temperature","precipitation","windspeed","humidity","comfort"}

class AnalyzeReq(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    start_year: int = Field(..., ge=1981)
    end_year: int = Field(..., ge=1981)
    half_window_days: int = Field(10, ge=0, le=30)
    factors: List[str] = Field(default=["temperature","precipitation","windspeed","humidity"])

    @field_validator("factors")
    @classmethod
    def validate_factors(cls, v: List[str]) -> List[str]:
        bad = [f for f in v if f not in ALLOWED_FACTORS]
        if bad: raise ValueError(f"Unsupported factors: {bad}")
        return v
