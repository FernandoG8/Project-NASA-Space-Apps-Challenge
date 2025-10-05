# app/routers/health.py
from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["health"])

@router.get("/health")
def health():
    return {
        "status": "ok",
        "message": "Campeche Weather API running",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
