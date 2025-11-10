"""Schemas for series endpoints."""
from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class SeriesPoint(BaseModel):
    year: int
    value: float


class SeriesMeta(BaseModel):
    factor: str
    units: str
    lat: float
    lon: float
    month: int
    day: int
    half_window_days: int
    agg: str
    count: int
    range_years: Optional[List[int]] = None


class SeriesJSONData(BaseModel):
    points: List[SeriesPoint]
    meta: Dict[str, object]


class SeriesJSONResponse(BaseResponse[SeriesJSONData]):
    data: SeriesJSONData
