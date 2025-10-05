# app/routers/daily.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List
from app.services.powerClient import power_same_day_many_years

router = APIRouter(tags=["daily"])

ALLOWED_VARS = {"T2M","T2M_MAX","T2M_MIN","RH2M","WS10M","WS10M_MAX","WS10M_MIN"}

class SameDayReq(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    start_year: int = Field(..., ge=1981)
    end_year: int = Field(..., ge=1981)
    variables: List[str] = Field(default=["T2M","T2M_MAX","T2M_MIN","RH2M","WS10M"])

@router.post("/daily/sameday")
def daily_same_day(req: SameDayReq):
    # valida variables
    vars_req = [v for v in req.variables if v in ALLOWED_VARS]
    if not vars_req:
        raise HTTPException(400, detail=f"variables must be in {sorted(list(ALLOWED_VARS))}")
    if req.end_year < req.start_year:
        raise HTTPException(400, detail="end_year must be >= start_year")

    df = power_same_day_many_years(
        lat=req.latitude, lon=req.longitude,
        month=req.month, day=req.day,
        start_year=req.start_year, end_year=req.end_year,
        params=vars_req
    )
    if df.empty:
        raise HTTPException(424, detail="No data returned from POWER")

    # jsonify
    records = df.sort_values("date").to_dict(orient="records")
    return {
        "ok": True,
        "count": len(records),
        "variables": vars_req,
        "rows": records
    }
