# app/schemas/analyze_resp.py
from pydantic import BaseModel
from typing import Optional

class AnalyzeCreateOut(BaseModel):
    analysis_id: int
    status: str = "ok"

class AnalyzeResultOut(BaseModel):
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

class AnalyzeHistoryOut(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[AnalyzeHistoryItem]
