"""Schemas for the health endpoint."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class HealthData(BaseModel):
    status: str
    timestamp: datetime


class HealthResponse(BaseResponse[HealthData]):
    data: HealthData
