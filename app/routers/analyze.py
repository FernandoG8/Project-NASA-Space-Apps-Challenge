# app/routers/analyze.py
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query, Request
from sqlalchemy.orm import Session
from time import perf_counter
import hashlib, json

from app.schemas.analyze_req import AnalyzeReq
from app.schemas.analyze_resp import (
    AnalyzeCreateOut, AnalyzeResultOut, AnalyzeHistoryOut, AnalyzeHistoryItem
)
from app.services.analyze_service import AnalyzeService
from app.deps import get_db, get_current_user
from app.models import AnalyzeResult, AnalyzeStatus, User
from app.db import Base, engine

router = APIRouter(tags=["analyze"])
svc = AnalyzeService()

# crea tablas si no existen (demo; en prod usa Alembic)
Base.metadata.create_all(bind=engine)

def _sha256(d: dict) -> str:
    return hashlib.sha256(json.dumps(d, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

@router.post("/analyze", response_model=AnalyzeCreateOut, summary="Ejecuta análisis y lo guarda")
def analyze(req: AnalyzeReq,
            bt: BackgroundTasks,
            request: Request,
            db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    # 1) Pre-crear fila "running"
    t0 = perf_counter()
    row = AnalyzeResult(
        user_id=user.id,
        status=AnalyzeStatus.running,
        params_json=req.model_dump(),
        model_version="v1",
        dataset_version="POWER-2024",
        request_id=request.headers.get("X-Request-ID"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    # 2) Ejecutar en background y guardar resultado
    def do_work(analysis_id: int, payload: AnalyzeReq):
        session = get_db().__next__()  # nueva sesión para el hilo de background
        try:
            result = svc.run(
                lat=payload.latitude, lon=payload.longitude,
                month=payload.month, day=payload.day,
                start_year=payload.start_year, end_year=payload.end_year,
                half_window_days=payload.half_window_days,
                factors=payload.factors
            )
            dur_ms = int((perf_counter() - t0) * 1000)
            row2 = session.get(AnalyzeResult, analysis_id)
            row2.status = AnalyzeStatus.ok
            row2.result_json = result
            row2.result_hash = _sha256(result)
            row2.duration_ms = dur_ms
            row2.response_status = 200
            session.commit()
        except Exception as e:
            row2 = session.get(AnalyzeResult, analysis_id)
            row2.status = AnalyzeStatus.error
            row2.result_json = {"error": str(e)}
            row2.response_status = 500
            session.commit()
        finally:
            session.close()

    bt.add_task(do_work, row.id, req)

    return {"analysis_id": row.id, "status": "ok"}

@router.get("/analyze/{analysis_id}", response_model=AnalyzeResultOut, summary="Detalle de un análisis")
def get_analysis(analysis_id: int,
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    row = db.get(AnalyzeResult, analysis_id)
    if not row or row.user_id != user.id:
        raise HTTPException(status_code=404, detail="No encontrado")
    return {
        "id": row.id,
        "status": row.status.value,
        "created_at": row.created_at.isoformat(),
        "params_json": row.params_json,
        "result_json": row.result_json,
        "result_uri": row.result_uri
    }

@router.get("/analyze/history", response_model=AnalyzeHistoryOut, summary="Historial del usuario (paginado)")
def history_list(page: int = Query(1, ge=1),
                page_size: int = Query(20, ge=1, le=100),
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    q = (db.query(AnalyzeResult)
        .filter(AnalyzeResult.user_id == user.id)
        .order_by(AnalyzeResult.created_at.desc()))
    total = q.count()
    rows = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "page": page, "page_size": page_size, "total": total,
        "items": [
            AnalyzeHistoryItem(
                id=r.id,
                status=r.status.value,
                created_at=r.created_at.isoformat(),
                result_uri=r.result_uri
            ).model_dump()
            for r in rows
        ]
    }
