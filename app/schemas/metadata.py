"""Schemas for metadata endpoints."""
from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class FactorListData(BaseModel):
    factors: List[str]


class MetadataData(BaseModel):
    factors: List[str]
    units: Dict[str, str]
    power_variables: Dict[str, List[str]]
    sources: Dict[str, str]


class FactorListResponse(BaseResponse[FactorListData]):
    data: FactorListData


class MetadataResponse(BaseResponse[MetadataData]):
    data: MetadataData
