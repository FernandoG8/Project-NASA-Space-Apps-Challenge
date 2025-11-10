from __future__ import annotations

import hashlib
import json
from time import perf_counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.db import Base, engine
from app.db.connection import SessionLocal
from app.db.models import AnalyzeResult, AnalyzeStatus, User
from app.schemas import (
    AnalyzeCreateData,
    AnalyzeCreateResponse,
    AnalyzeHistoryData,
    AnalyzeHistoryItem,
    AnalyzeHistoryResponse,
    AnalyzeReq,
    AnalyzeResultData,
    AnalyzeResultResponse,
)
from app.schemas.response import envelope
from app.services.analyze_service import AnalyzeService

router = APIRouter(prefix="/analyze", tags=["analyze"])

Base.metadata.create_all(bind=engine)
_service = AnalyzeService()


def _sha256(payload: dict) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _enqueue_analysis(row_id: int, payload: AnalyzeReq, started_at: float) -> None:
    session = SessionLocal()
    try:
        result = _service.run(
            lat=payload.latitude,
            lon=payload.longitude,
            month=payload.month,
            day=payload.day,
            start_year=payload.start_year,
            end_year=payload.end_year,
            half_window_days=payload.half_window_days,
            factors=payload.factors,
        )
        duration_ms = int((perf_counter() - started_at) * 1000)
        row = session.get(AnalyzeResult, row_id)
        if not row:
            return
        row.status = AnalyzeStatus.ok
        row.result_json = result
        row.result_hash = _sha256(result)
        row.duration_ms = duration_ms
        row.response_status = status.HTTP_200_OK
        session.commit()
    except Exception as exc:  # pragma: no cover - background best effort
        row = session.get(AnalyzeResult, row_id)
        if not row:
            return
        row.status = AnalyzeStatus.error
        row.result_json = {"error": str(exc)}
        row.response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        session.commit()
    finally:
        session.close()


@router.post(
    "/",
    response_model=AnalyzeCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Ejecuta un análisis y programa el procesamiento",
)
def analyze(
    payload: AnalyzeReq,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = AnalyzeResult(
        user_id=user.id,
        status=AnalyzeStatus.running,
        params_json=payload.model_dump(),
        model_version="v1",
        dataset_version="POWER-2024",
        request_id=request.headers.get("X-Request-ID"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    background_tasks.add_task(_enqueue_analysis, row.id, payload, perf_counter())

    data = AnalyzeCreateData(analysis_id=row.id)
    return envelope(success=True, message="Análisis en ejecución", data=data)


@router.get(
    "/{analysis_id}",
    response_model=AnalyzeResultResponse,
    summary="Obtiene el estado y resultado de un análisis",
)
def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    row = db.get(AnalyzeResult, analysis_id)
    if not row or row.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"message": "Análisis no encontrado"},
        )

    data = AnalyzeResultData(
        id=row.id,
        status=row.status.value,
        created_at=row.created_at.isoformat() if row.created_at else None,
        params_json=row.params_json,
        result_json=row.result_json,
        result_uri=row.result_uri,
    )
    return envelope(success=True, message="Detalle del análisis", data=data)


@router.get(
    "/history",
    response_model=AnalyzeHistoryResponse,
    summary="Historial de análisis del usuario",
)
def history_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    query = (
        db.query(AnalyzeResult)
        .filter(AnalyzeResult.user_id == user.id)
        .order_by(AnalyzeResult.created_at.desc())
    )
    total = query.count()
    rows = query.offset((page - 1) * page_size).limit(page_size).all()

    items = [
        AnalyzeHistoryItem(
            id=r.id,
            status=r.status.value,
            created_at=r.created_at.isoformat() if r.created_at else "",
            result_uri=r.result_uri,
        )
        for r in rows
    ]

    data = AnalyzeHistoryData(
        page=page,
        page_size=page_size,
        total=total,
        items=items,
    )
    return envelope(success=True, message="Historial recuperado", data=data)
