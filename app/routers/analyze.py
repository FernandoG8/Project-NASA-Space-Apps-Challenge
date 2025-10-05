# routers/analyze.py
from fastapi import APIRouter, HTTPException
from app.schemas.analyze_req import AnalyzeReq
from app.services.analyze_service import AnalyzeService

router = APIRouter(tags=["analyze"])
svc = AnalyzeService()  # podrías inyectar deps si quieres

@router.post("/analyze")
def analyze(req: AnalyzeReq):
    try:
        return svc.run(
            lat=req.latitude, lon=req.longitude,
            month=req.month, day=req.day,
            start_year=req.start_year, end_year=req.end_year,
            half_window_days=req.half_window_days,
            factors=req.factors
        )
    except Exception as e:
        raise HTTPException(424, detail=str(e))
