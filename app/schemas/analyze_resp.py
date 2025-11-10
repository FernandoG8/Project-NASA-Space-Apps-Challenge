"""Schemas for analyze related responses."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class AnalyzeCreateData(BaseModel):
    analysis_id: int
    status: str = "ok"


class AnalyzeResultData(BaseModel):
    id: int
    status: str
    created_at: str
    params_json: Optional[dict] = None
    result_json: Optional[dict] = None
    result_uri: Optional[str] = None


class AnalyzeHistoryItem(BaseModel):
    id: int
    status: str
    created_at: str
    result_uri: Optional[str] = None


class AnalyzeHistoryData(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AnalyzeHistoryItem]


class AnalyzeCreateResponse(BaseResponse[AnalyzeCreateData]):
    data: Optional[AnalyzeCreateData] = None


class AnalyzeResultResponse(BaseResponse[AnalyzeResultData]):
    data: Optional[AnalyzeResultData] = None


class AnalyzeHistoryResponse(BaseResponse[AnalyzeHistoryData]):
    data: Optional[AnalyzeHistoryData] = None
