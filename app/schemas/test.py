"""Schemas used only for documentation/test endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.response import BaseResponse


class EchoIn(BaseModel):
    message: str = Field(..., examples=["Hola mundo"], description="Mensaje a eco")
    factors: List[str] = Field(
        default_factory=list,
        examples=[["temperature", "precipitation"]],
        description="Factores opcionales para pruebas",
    )


class EchoData(BaseModel):
    echoed: str
    user: Optional[str] = None
    roles: Optional[List[str]] = None


class EchoResponse(BaseResponse[EchoData]):
    data: EchoData
