from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from datetime import date
import uuid
from app.services.climate import compute_empirical_probabilities

router = APIRouter(tags=["compare"])

class Point(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    radius_km: float = Field(0, ge=0, le=50)

class CompareReq(BaseModel):
    factor: str
    date: date
    window_days: int = Field(30, ge=7, le=60)
    left: Point
    right: Point

@router.post("/compare/inline")
def compare_inline(req: CompareReq):
    allowed = {"temperature","precipitation","windspeed","dust"}
    if req.factor not in allowed:
        raise HTTPException(400, detail=f"Unsupported factor")

    left = compute_empirical_probabilities(req.factor, req.left.lat, req.left.lon, req.window_days, req.left.radius_km)
    right = compute_empirical_probabilities(req.factor, req.right.lat, req.right.lon, req.window_days, req.right.radius_km)

    def diff_metric(name: str, units: str=""):
        l = left["terciles"][name] if name in left["terciles"] else left.get(name)
        r = right["terciles"][name] if name in right["terciles"] else right.get(name)
        return {"metric": name, "left": l, "right": r, "delta": round((r-l), 3), "units": units}

    units = left["units"]
    return {
        "compare_id": str(uuid.uuid4()),
        "factor": req.factor,
        "date": req.date.isoformat(),
        "baseline": left["baseline"],
        "dataset": left["dataset"],
        "left":  {"lat": req.left.lat,  "lon": req.left.lon,  **left},
        "right": {"lat": req.right.lat, "lon": req.right.lon, **right},
        "diff": [
            diff_metric("p_below"),
            diff_metric("p_normal"),
            diff_metric("p_above"),
            diff_metric("median", units),
        ]
    }
