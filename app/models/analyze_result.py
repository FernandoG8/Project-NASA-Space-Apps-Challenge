# app/models/analyze_result.py
from sqlalchemy import Integer, String, DateTime, ForeignKey, JSON, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.db import Base
import enum

class AnalyzeStatus(str, enum.Enum):
    ok = "ok"
    error = "error"
    running = "running"

class AnalyzeResult(Base):
    __tablename__ = "analyze_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[AnalyzeStatus] = mapped_column(Enum(AnalyzeStatus), default=AnalyzeStatus.ok)
    created_at: Mapped["DateTime"] = mapped_column(DateTime, server_default=func.now())
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    params_json: Mapped[dict | None] = mapped_column(JSON)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    result_uri: Mapped[str | None] = mapped_column(String(512))
    result_hash: Mapped[str | None] = mapped_column(String(64))

    model_version: Mapped[str | None] = mapped_column(String(64))
    dataset_version: Mapped[str | None] = mapped_column(String(64))
    request_id: Mapped[str | None] = mapped_column(String(64))
    response_status: Mapped[int | None] = mapped_column(Integer)

    user = relationship("User")
