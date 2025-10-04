from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import uuid
from app.services.climate import compute_empirical_probabilities

router = APIRouter(tags=["probability"])

class ProbabilityReq(BaseModel):
    factor: str = Field(..., examples=["precipitation","temperature","windspeed","dust"])
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    date: date
    radius_km: float = Field(0, ge=0, le=50)
    window_days: int = Field(30, ge=7, le=60)

# almacenamiento en memoria para demo (luego DB)
_QUERIES: dict[str, dict] = {}

@router.post("/probability")
def probability(req: ProbabilityReq):
    # Validación de factor permitido (opcionalmente toma del /factors)
    allowed = {"temperature","precipitation","windspeed","dust"}
    if req.factor not in allowed:
        raise HTTPException(400, detail=f"Unsupported factor {req.factor}")

    result = compute_empirical_probabilities(req.factor, req.lat, req.lon, req.window_days, req.radius_km)
    qid = str(uuid.uuid4())
    payload = {
        "query_id": qid,
        "factor": req.factor,
        "lat": req.lat,
        "lon": req.lon,
        "date": req.date,
        "result": result
    }
    _QUERIES[qid] = payload
    return payload

@router.get("/queries/{query_id}")
def get_query(query_id: str):
    if query_id not in _QUERIES:
        raise HTTPException(404, detail="Query not found")
    return _QUERIES[query_id]
