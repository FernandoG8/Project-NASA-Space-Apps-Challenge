"""Time series endpoints."""
from __future__ import annotations

from io import BytesIO, StringIO
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.datasources.power_client import fetch_window_all_years
from app.schemas import SeriesJSONData, SeriesJSONResponse
from app.schemas.response import envelope

router = APIRouter(prefix="/series", tags=["series"])

FACTOR_TO_VAR = {
    "temperature": ("T2M", "°C"),
    "humidity": ("RH2M", "%"),
    "windspeed": ("WS10M", "m/s"),
    "precipitation": ("PRECTOTCORR", "mm/día"),
}


class SeriesReq(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, examples=[19.43])
    longitude: float = Field(..., ge=-180, le=180, examples=[-99.13])
    month: int = Field(..., ge=1, le=12, examples=[5])
    day: int = Field(..., ge=1, le=31, examples=[10])
    start_year: int = Field(..., ge=1981, examples=[2000])
    end_year: int = Field(..., ge=1981, examples=[2020])
    half_window_days: int = Field(0, ge=0, le=30, examples=[5])
    factor: Literal["temperature", "humidity", "windspeed", "precipitation"]
    agg: Literal["median", "mean"] = Field(
        "median", description="Método de agregación por año"
    )
    trend: bool = Field(False, description="Añade tendencia lineal al gráfico")


def _aggregate_series(df: pd.DataFrame, var: str, agg: str) -> pd.Series:
    grouped = df.groupby("year")[var]
    if agg == "median":
        series = grouped.median(numeric_only=True)
    else:
        series = grouped.mean(numeric_only=True)
    return series.sort_index()


def _fetch_series(req: SeriesReq) -> tuple[pd.Series, str]:
    var, units = FACTOR_TO_VAR[req.factor]
    df = fetch_window_all_years(
        lat=req.latitude,
        lon=req.longitude,
        month=req.month,
        day=req.day,
        start_year=req.start_year,
        end_year=req.end_year,
        half_window_days=req.half_window_days,
        params=[var],
    )
    if df.empty or var not in df.columns:
        raise HTTPException(status_code=424, detail={"message": "No data returned from POWER"})
    series = _aggregate_series(df, var, req.agg)
    return series, units


@router.post(
    "/csv",
    summary="Genera CSV con la serie anual",
    responses={424: {"description": "No data returned from POWER"}},
)
def series_csv(req: SeriesReq) -> StreamingResponse:
    series, units = _fetch_series(req)
    out = pd.DataFrame(
        {
            "year": series.index.astype(int),
            f"{req.factor}": series.values,
            "lat": req.latitude,
            "lon": req.longitude,
            "month": req.month,
            "day": req.day,
            "half_window_days": req.half_window_days,
            "units": units,
            "agg": req.agg,
        }
    )
    buf = StringIO()
    out.to_csv(buf, index=False)
    buf.seek(0)

    filename = (
        f"{req.factor}_series_{req.month:02d}{req.day:02d}_"
        f"{req.start_year}-{req.end_year}_win{req.half_window_days}_{req.agg}.csv"
    )
    headers = {
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-WeatherAPI-Message": "Serie generada correctamente",
    }
    return StreamingResponse(iter([buf.getvalue()]), media_type="text/csv", headers=headers)


@router.post(
    "/plot.png",
    summary="Genera un gráfico PNG de la serie",
    responses={424: {"description": "No data returned from POWER"}},
)
def series_plot(req: SeriesReq) -> StreamingResponse:
    series, units = _fetch_series(req)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(series.index.values, series.values, marker="o")
    ax.set_xlabel("Año")
    ax.set_ylabel(f"{req.factor} ({units})")
    window_txt = (
        f"±{req.half_window_days} días, {req.agg}" if req.half_window_days else "día exacto"
    )
    ax.set_title(
        f"{req.factor.capitalize()} — {req.month:02d}-{req.day:02d} ({window_txt})\n"
        f"lat={req.latitude:.3f}, lon={req.longitude:.3f} | {req.start_year}-{req.end_year}"
    )

    if req.trend and len(series) >= 2:
        years = series.index.values.astype(float)
        values = series.values.astype(float)
        slope, intercept = np.polyfit(years, values, 1)
        ax.plot(years, slope * years + intercept, linestyle="--")
        ax.text(0.01, 0.02, f"Tendencia: {slope:+.3f} {units}/año", transform=ax.transAxes)

    ax.grid(True, alpha=0.3)
    plt.tight_layout()

    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=130)
    plt.close(fig)
    buffer.seek(0)

    filename = (
        f"{req.factor}_plot_{req.month:02d}{req.day:02d}_"
        f"{req.start_year}-{req.end_year}_win{req.half_window_days}_{req.agg}"
        f"{'_trend' if req.trend else ''}.png"
    )
    headers = {
        "Content-Disposition": f'inline; filename="{filename}"',
        "X-WeatherAPI-Message": "Gráfico generado correctamente",
    }
    return StreamingResponse(buffer, media_type="image/png", headers=headers)


@router.post(
    "/json",
    response_model=SeriesJSONResponse,
    summary="Serie anual agregada en formato JSON",
    responses={424: {"description": "No data returned from POWER"}},
)
def series_json(req: SeriesReq) -> dict:
    series, units = _fetch_series(req)

    points = [{"year": int(y), "value": float(v)} for y, v in series.items()]
    data = SeriesJSONData(
        points=points,
        meta={
            "factor": req.factor,
            "units": units,
            "lat": req.latitude,
            "lon": req.longitude,
            "month": req.month,
            "day": req.day,
            "half_window_days": req.half_window_days,
            "agg": req.agg,
            "count": len(points),
            "range_years": [int(series.index.min()), int(series.index.max())]
            if len(series)
            else None,
        },
    )
    return envelope(success=True, message="Serie generada", data=data)
