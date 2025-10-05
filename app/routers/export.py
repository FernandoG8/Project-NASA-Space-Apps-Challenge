# app/routers/export.py
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List
from io import StringIO
from app.services.powerClient import power_same_day_many_years

router = APIRouter(tags=["export"])

ALLOWED_VARS = {"T2M","T2M_MAX","T2M_MIN","RH2M","WS10M","WS10M_MAX","WS10M_MIN"}

class SameDayCSVReq(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    start_year: int = Field(..., ge=1981)
    end_year: int = Field(..., ge=1981)
    variables: List[str] = Field(default=["T2M","RH2M","WS10M"])

@router.post("/export/sameday.csv")
def export_same_day_csv(req: SameDayCSVReq):
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

    # Asegura columnas ordenadas
    cols_base = ["date","year","month","day","lat","lon"]
    var_cols = [c for c in vars_req if c in df.columns]
    out_df = df[cols_base + var_cols].sort_values(["year","date"])

    # CSV en memoria
    buf = StringIO()
    out_df.to_csv(buf, index=False)
    buf.seek(0)

    filename = f"sameday_{req.month:02d}{req.day:02d}_{req.start_year}-{req.end_year}_{req.latitude:.3f}_{req.longitude:.3f}.csv"
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"'
    }
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)
