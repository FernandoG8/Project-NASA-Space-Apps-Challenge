# app/routers/series.py
from __future__ import annotations
from io import StringIO, BytesIO
from typing import Literal

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from pydantic import BaseModel
from typing import List, Optional


from app.datasources.power_client import fetch_window_all_years

router = APIRouter(tags=["series"])

# Mapeo factor -> variable POWER y unidades
FACTOR_TO_VAR = {
    "temperature": ("T2M", "°C"),          # temperatura 2 m (diario)
    "humidity": ("RH2M", "%"),             # humedad relativa 2 m
    "windspeed": ("WS10M", "m/s"),         # viento 10 m
    "precipitation": ("PRECTOTCORR", "mm/día"),  # precipitación diaria corregida
}

class SeriesReq(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    month: int = Field(..., ge=1, le=12)
    day: int = Field(..., ge=1, le=31)
    start_year: int = Field(..., ge=1981)
    end_year: int = Field(..., ge=1981)
    half_window_days: int = Field(0, ge=0, le=30)        # 0 = solo el día exacto
    factor: Literal["temperature", "humidity", "windspeed", "precipitation"]
    agg: Literal["median", "mean"] = "median"            # cómo resumir la ventana por año
    trend: bool = False                                  # (solo para plot) añade línea de tendencia

def _aggregate_series(df: pd.DataFrame, var: str, agg: str) -> pd.Series:
    """
    Agrega por año:
      - si half_window_days > 0 → usa mediana o media de la ventana
      - si == 0 → toma la mediana por seguridad (por si hay duplicados raros)
    Retorna pd.Series index=año, values=valor
    """
    # df ya contiene múltiplos días por año si half_window_days>0
    if agg == "median":
        series = df.groupby("year")[var].median(numeric_only=True)
    else:
        series = df.groupby("year")[var].mean(numeric_only=True)
    # orden cronológico
    return series.sort_index()

@router.post("/series/csv")
def series_csv(req: SeriesReq):
    var, units = FACTOR_TO_VAR[req.factor]

    df = fetch_window_all_years(
        lat=req.latitude, lon=req.longitude,
        month=req.month, day=req.day,
        start_year=req.start_year, end_year=req.end_year,
        half_window_days=req.half_window_days,
        params=[var],
    )
    if df.empty or var not in df.columns:
        raise HTTPException(424, detail="No data returned from POWER")

    series = _aggregate_series(df, var, req.agg)

    out = pd.DataFrame({
        "year": series.index.astype(int),
        f"{req.factor}": series.values,
        "lat": req.latitude,
        "lon": req.longitude,
        "month": req.month,
        "day": req.day,
        "half_window_days": req.half_window_days,
        "units": units,
        "agg": req.agg,
    })

    buf = StringIO()
    out.to_csv(buf, index=False)
    buf.seek(0)

    filename = (f"{req.factor}_series_{req.month:02d}{req.day:02d}_"
                f"{req.start_year}-{req.end_year}_win{req.half_window_days}_{req.agg}.csv")
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)

@router.post("/series/plot.png")
def series_plot(req: SeriesReq):
    var, units = FACTOR_TO_VAR[req.factor]

    df = fetch_window_all_years(
        lat=req.latitude, lon=req.longitude,
        month=req.month, day=req.day,
        start_year=req.start_year, end_year=req.end_year,
        half_window_days=req.half_window_days,
        params=[var],
    )
    if df.empty or var not in df.columns:
        raise HTTPException(424, detail="No data returned from POWER")

    series = _aggregate_series(df, var, req.agg)

    # --- Plot ---
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(series.index.values, series.values, marker="o")
    ax.set_xlabel("Año")
    ax.set_ylabel(f"{req.factor} ({units})")
    win_txt = f"±{req.half_window_days} días, {req.agg}" if req.half_window_days > 0 else "día exacto"
    ax.set_title(f"{req.factor.capitalize()} — {req.month:02d}-{req.day:02d} ({win_txt})\n"
                 f"lat={req.latitude:.3f}, lon={req.longitude:.3f} | {req.start_year}-{req.end_year}")

    # (Opcional) línea de tendencia lineal
    if req.trend and len(series) >= 2:
        years = series.index.values.astype(float)
        vals = series.values.astype(float)
        # ajuste lineal y = m*x + b
        m, b = np.polyfit(years, vals, 1)
        y_hat = m * years + b
        ax.plot(years, y_hat, linestyle="--")  # sin especificar color (deja el default)
        # pequeña leyenda en la esquina
        ax.text(0.01, 0.02, f"Tendencia: {m:+.3f} {units}/año",
                transform=ax.transAxes)

    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=130)
    plt.close(fig)
    buf.seek(0)

    filename = (f"{req.factor}_plot_{req.month:02d}{req.day:02d}_"
                f"{req.start_year}-{req.end_year}_win{req.half_window_days}_{req.agg}"
                f"{'_trend' if req.trend else ''}.png")
    headers = {"Content-Disposition": f'inline; filename="{filename}"'}
    return StreamingResponse(buf, media_type="image/png", headers=headers)



class SeriesPoint(BaseModel):
    year: int
    value: float

class SeriesJSON(BaseModel):
    points: List[SeriesPoint]
    meta: dict

@router.post(
    "/series/json",
    response_model=SeriesJSON,
    tags=["series"],
    summary="Serie anual en JSON",
    description=(
        "Devuelve una serie anual agregada por año para el factor seleccionado. "
        "Útil para graficar en clientes (iOS/SwiftUI, web, etc.)."
    ),
    responses={424: {"description": "No data returned from POWER"}}
)
def series_json(req: SeriesReq):
    var, units = FACTOR_TO_VAR[req.factor]

    df = fetch_window_all_years(
        lat=req.latitude, lon=req.longitude,
        month=req.month, day=req.day,
        start_year=req.start_year, end_year=req.end_year,
        half_window_days=req.half_window_days,
        params=[var],
    )
    if df.empty or var not in df.columns:
        raise HTTPException(424, detail="No data returned from POWER")

    series = _aggregate_series(df, var, req.agg)

    points = [SeriesPoint(year=int(y), value=float(v)) for y, v in series.items()]
    meta = {
        "factor": req.factor,
        "units": units,
        "lat": req.latitude,
        "lon": req.longitude,
        "month": req.month,
        "day": req.day,
        "half_window_days": req.half_window_days,
        "agg": req.agg,
        "count": len(points),
        "range_years": [int(series.index.min()), int(series.index.max())] if len(series) else None,
    }
    return {"points": points, "meta": meta}

