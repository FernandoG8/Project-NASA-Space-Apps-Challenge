import numpy as np
import pandas as pd

def percentiles(series: pd.Series, qs=(10, 33.3, 66.6, 90)):
    data = pd.to_numeric(series, errors="coerce").dropna().values
    if data.size == 0: return {}
    vals = np.percentile(data, qs)
    return {f"p{int(q if q.is_integer() else q)}": float(round(v, 3)) for q, v in zip(qs, vals)}

def classify_temperature(value, p10, p90):
    if any(np.isnan([value, p10, p90])): return "insufficient-data"
    if value <= p10: return "very cold"
    if value >= p90: return "very hot"
    return "normal"

def classify_wind(value, p90):
    if any(np.isnan([value, p90])): return "insufficient-data"
    return "very windy" if value >= p90 else "normal"

def classify_humidity(value, p90):
    if any(np.isnan([value, p90])): return "insufficient-data"
    return "very wet (humidity)" if value >= p90 else "normal"

def simple_heat_index_c(t2m_c, rh_pct):
    if any(np.isnan([t2m_c, rh_pct])): return np.nan
    return float(round(t2m_c + 0.2 * (rh_pct - 40) / 10.0, 2))

def classify_comfort(value_hi, p10, p90):
    if any(np.isnan([value_hi, p10, p90])): return "insufficient-data"
    if value_hi <= p10: return "very uncomfortable (cold)"
    if value_hi >= p90: return "very uncomfortable (hot)"
    return "comfortable/normal"

def analyze_multifactor(df: pd.DataFrame, factors, half_window_days: int):
    results = {}
    per_year = df.groupby("year").median(numeric_only=True).reset_index()

    if "T2M" in df.columns and "temperature" in factors:
        p = percentiles(per_year["T2M"], qs=(10, 90))
        typical = float(round(per_year["T2M"].median(), 2))
        results["temperature"] = {
            "units": "°C",
            "n_years": int(per_year["year"].nunique()),
            "typical": typical,
            "percentiles": p,
            "label": classify_temperature(typical, p.get("p10", np.nan), p.get("p90", np.nan)),
        }

    if "WS10M" in df.columns and "windspeed" in factors:
        p = percentiles(per_year["WS10M"], qs=(90,))
        typical = float(round(per_year["WS10M"].median(), 2))
        results["windspeed"] = {
            "units": "m/s",
            "n_years": int(per_year["year"].nunique()),
            "typical": typical,
            "percentiles": p,
            "label": classify_wind(typical, p.get("p90", np.nan)),
        }

    if "RH2M" in df.columns and "humidity" in factors:
        p = percentiles(per_year["RH2M"], qs=(90,))
        typical = float(round(per_year["RH2M"].median(), 1))
        results["humidity"] = {
            "units": "%",
            "n_years": int(per_year["year"].nunique()),
            "typical": typical,
            "percentiles": p,
            "label": classify_humidity(typical, p.get("p90", np.nan)),
        }

    if "PRECTOTCORR" in df.columns and "precipitation" in factors:
        values = pd.to_numeric(df["PRECTOTCORR"], errors="coerce").dropna()
        th = 1.0
        n_days = int(values.size)
        p_wet = round(float((values >= th).mean()), 3) if n_days else np.nan
        rainy = values[values >= th]
        p_int = percentiles(rainy, qs=(50, 90)) if rainy.size else {}
        label = "very wet (rain)" if rainy.size and rainy.median() >= p_int.get("p90", np.inf) else "normal"
        results["precipitation"] = {
            "units": "mm/day",
            "n_years": int(df["year"].nunique()),
            "window_days": half_window_days,
            "n_days_total": n_days,
            "wet_threshold_mm": th,
            "prob_wet_day": p_wet,
            "intensity_percentiles": p_int,
            "label": label,
        }

    if "comfort" in factors and {"T2M","RH2M"}.issubset(per_year.columns):
        per_year["HI"] = per_year.apply(lambda r: simple_heat_index_c(r["T2M"], r["RH2M"]), axis=1)
        p = percentiles(per_year["HI"], qs=(10, 90))
        typical = float(round(per_year["HI"].median(), 2))
        results["comfort"] = {
            "units": "°C (HI)",
            "n_years": int(per_year["year"].nunique()),
            "typical": typical,
            "percentiles": p,
            "label": classify_comfort(typical, p.get("p10", np.nan), p.get("p90", np.nan)),
        }

    return results
