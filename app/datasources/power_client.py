from datetime import date, timedelta
import pandas as pd
from app.utils.http import get_json
from app.utils.timewin import to_yyyymmdd

BASE = "https://power.larc.nasa.gov/api/temporal/daily/point"

def build_url(lat, lon, start_yyyymmdd, end_yyyymmdd, params):
    return (f"{BASE}?parameters={','.join(params)}&community=RE"
            f"&latitude={lat}&longitude={lon}&start={start_yyyymmdd}&end={end_yyyymmdd}&format=JSON")

def parse_power_json(payload: dict) -> pd.DataFrame:
    p = payload["properties"]["parameter"]
    any_var = next(iter(p))
    rows = []
    for day_key in p[any_var].keys():
        row = {"date": day_key}
        for var, series in p.items():
            row[var] = series.get(day_key, None)
        rows.append(row)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    return df.sort_values("date").reset_index(drop=True)

def fetch_window_all_years(lat, lon, month, day, start_year, end_year, half_window_days, params):
    import datetime as dt
    rows = []
    for y in range(start_year, end_year+1):
        c = date(y, month, day)
        start = (c - dt.timedelta(days=half_window_days)).strftime("%Y%m%d")
        end = (c + dt.timedelta(days=half_window_days)).strftime("%Y%m%d")
        url = build_url(lat, lon, start, end, params)
        payload = get_json(url)
        df = parse_power_json(payload)
        df["year"] = y
        rows.append(df)
    out = pd.concat(rows, ignore_index=True)
    out["lat"] = lat; out["lon"] = lon
    return out
