# app/services/power_client.py
from __future__ import annotations
import time
from datetime import date, timedelta
from typing import Iterable, Tuple, Dict

import requests
import pandas as pd
import numpy as np

POWER_BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"
DEFAULT_PARAMS = ("T2M", "T2M_MAX", "T2M_MIN", "RH2M", "WS10M")  # °C en POWER

class PowerAPIError(Exception):
    pass

def _power_get(url: str, timeout: int = 30, retries: int = 3, backoff: float = 1.5) -> dict:
    """
    GET con reintentos/backoff exponencial. Lanza PowerAPIError si falla.
    """
    last_err = None
    for i in range(retries):
        try:
            r = requests.get(url, timeout=timeout)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            if i < retries - 1:
                time.sleep(backoff ** (i+1))
            else:
                raise PowerAPIError(f"POWER request failed after {retries} attempts: {e}") from e
    # no debería llegar aquí
    raise PowerAPIError(f"Unreachable: {last_err}")

def _build_url(lat: float, lon: float, start_yyyymmdd: str, end_yyyymmdd: str,
               params: Iterable[str] = DEFAULT_PARAMS) -> str:
    return (
        f"{POWER_BASE}?parameters={','.join(params)}"
        f"&community=RE&latitude={lat}&longitude={lon}"
        f"&start={start_yyyymmdd}&end={end_yyyymmdd}&format=JSON"
    )

def _parse_power_payload(payload: dict) -> pd.DataFrame:
    """
    POWER devuelve: properties.parameter -> {VAR: {YYYYMMDD: value}}
    Lo convertimos a DataFrame con columnas: date, VAR1, VAR2...
    """
    param_dict: Dict[str, Dict[str, float]] = payload["properties"]["parameter"]
    # claves de fecha (YYYYMMDD) vienen replicadas por variable
    # tomamos cualquiera para iterar fechas
    any_var = next(iter(param_dict))
    rows = []
    for day_key in param_dict[any_var].keys():
        row = {"date": day_key}
        for var, series in param_dict.items():
            row[var] = series.get(day_key, None)
        rows.append(row)
    df = pd.DataFrame(rows)
    # normaliza tipos
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    # orden cronológico
    df = df.sort_values("date").reset_index(drop=True)
    return df

# -------------------------------------------------------------------
# 1) MISMO DÍA (DOY) PARA MÚLTIPLES AÑOS
# -------------------------------------------------------------------
def power_same_day_many_years(
    lat: float,
    lon: float,
    month: int,
    day: int,
    start_year: int,
    end_year: int,
    params: Iterable[str] = DEFAULT_PARAMS,
) -> pd.DataFrame:
    rows = []
    for y in range(start_year, end_year + 1):
        yyyymmdd = f"{y}{month:02d}{day:02d}"
        url = _build_url(lat, lon, yyyymmdd, yyyymmdd, params=params)
        payload = _power_get(url)
        df = _parse_power_payload(payload)   # -> columnas: date, VAR...
        df["year"] = y
        df["month"] = month
        df["day"] = day
        df["lat"] = lat
        df["lon"] = lon
        rows.append(df)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
# -------------------------------------------------------------------
# 2) VENTANA ±N DÍAS ALREDEDOR DEL DÍA (MEJOR ESTABILIDAD)
# -------------------------------------------------------------------
def power_window_many_years(
    lat: float,
    lon: float,
    month: int,
    day: int,
    start_year: int,
    end_year: int,
    half_window_days: int = 10,
    params: Iterable[str] = DEFAULT_PARAMS,
) -> pd.DataFrame:
    """
    Descarga ventana de fechas [DOY-±half_window_days] en N años.
    Retorna DataFrame con: date, year, (params...).
    """
    rows = []
    for y in range(start_year, end_year + 1):
        center = date(y, month, day)
        start = (center - timedelta(days=half_window_days)).strftime("%Y%m%d")
        end = (center + timedelta(days=half_window_days)).strftime("%Y%m%d")
        url = _build_url(lat, lon, start, end, params=params)
        payload = _power_get(url)
        df = _parse_power_payload(payload)
        df["year"] = y
        rows.append(df)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    return out

# -------------------------------------------------------------------
# 3) PERCENTILES + ETIQUETA (very hot/cold)
# -------------------------------------------------------------------
def temperature_percentiles_and_label(
    temps: pd.Series,
    value_strategy: str = "median",  # "median"|"mean" (cómo resumir ventana)
    p_low: float = 10.0,
    p_high: float = 90.0,
) -> Tuple[float, float, float, str]:
    """
    Calcula p10/p90 y etiqueta 'very cold' / 'very hot' / 'normal'
    a partir de una serie de temperaturas (°C).
    Retorna: (p10, p90, value, label)
    """
    # Limpia nulos
    data = pd.to_numeric(temps, errors="coerce").dropna()
    if data.empty:
        return (np.nan, np.nan, np.nan, "insufficient-data")

    p10 = float(np.percentile(data, p_low))
    p90 = float(np.percentile(data, p_high))
    value = float(data.median() if value_strategy == "median" else data.mean())

    if value <= p10:
        label = "very cold"
    elif value >= p90:
        label = "very hot"
    else:
        label = "normal"

    return (round(p10, 2), round(p90, 2), round(value, 2), label)

# -------------------------------------------------------------------
# 4) UTILIDAD: CÁLCULO RÁPIDO COMBINADO (MISMO DÍA)
# -------------------------------------------------------------------
def fetch_and_label_temperature_same_day(
    lat: float,
    lon: float,
    month: int,
    day: int,
    start_year: int,
    end_year: int,
) -> dict:
    """
    Pipeline completo para el MISMO día (varios años):
      - Descarga T2M (°C) del día exacto en cada año.
      - Calcula p10/p90 y etiqueta 'very hot/cold/normal' sobre T2M.
    Retorna dict listo para API/JSON.
    """
    df = power_same_day_many_years(lat, lon, month, day, start_year, end_year, params=("T2M",))
    if df.empty:
        return {"ok": False, "message": "No data", "results": None}

    p10, p90, value, label = temperature_percentiles_and_label(df["T2M"])
    return {
        "ok": True,
        "location": {"lat": lat, "lon": lon},
        "target_day": {"month": month, "day": day},
        "years": {"start": start_year, "end": end_year, "count": int(df["date"].dt.year.nunique())},
        "metrics": {"p10": p10, "p90": p90, "typical_value": value},
        "classification": label,
        "notes": "NASA POWER daily point; temperature in °C.",
    }

# -------------------------------------------------------------------
# 5) UTILIDAD: CÁLCULO RÁPIDO COMBINADO (VENTANA ±N DÍAS)
# -------------------------------------------------------------------
def fetch_and_label_temperature_window(
    lat: float,
    lon: float,
    month: int,
    day: int,
    start_year: int,
    end_year: int,
    half_window_days: int = 10,
) -> dict:
    """
    Pipeline para ventana ±N días (más estable):
      - Descarga T2M (°C) en la ventana para cada año.
      - Calcula p10/p90 y etiqueta 'very hot/cold/normal' sobre T2M.
    """
    df = power_window_many_years(
        lat, lon, month, day, start_year, end_year, half_window_days, params=("T2M",)
    )
    if df.empty:
        return {"ok": False, "message": "No data", "results": None}

    # Resumen por año (median) para evitar sobre-representar años con más días
    yearly = df.groupby("year")["T2M"].median().reset_index(drop=False)
    p10, p90, value, label = temperature_percentiles_and_label(yearly["T2M"])
    return {
        "ok": True,
        "location": {"lat": lat, "lon": lon},
        "target_day": {"month": month, "day": day, "half_window_days": half_window_days},
        "years": {"start": start_year, "end": end_year, "count": int(yearly["year"].nunique())},
        "metrics": {"p10": p10, "p90": p90, "typical_value": value},
        "classification": label,
        "notes": "Windowed (±N days) median per year; NASA POWER daily point; °C.",
    }
