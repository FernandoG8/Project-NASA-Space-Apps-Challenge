# services/analyze_service.py
from typing import List, Dict
from app.services.mapper import FACTOR_TO_POWER_VARS, FACTOR_UNITS
from app.datasources.power_client import fetch_window_all_years
from app.domain.stats import analyze_multifactor

class AnalyzeService:
    def run(self, lat, lon, month, day, start_year, end_year, half_window_days, factors: List[str]) -> Dict:
        needed_vars = set()
        for f in factors:
            needed_vars.update(FACTOR_TO_POWER_VARS.get(f, []))
            if f == "comfort":
                needed_vars.update(["T2M", "RH2M"])
        needed_vars = sorted(needed_vars)

        df = fetch_window_all_years(
            lat, lon, month, day, start_year, end_year, half_window_days, needed_vars
        )
        if df.empty:
            return {"ok": False, "message": "No data from POWER"}

        results = analyze_multifactor(df, factors, half_window_days)
        return {
            "ok": True,
            "location": {"lat": lat, "lon": lon},
            "target_day": {"month": month, "day": day, "half_window_days": half_window_days},
            "years": {"start": start_year, "end": end_year, "count": int(df['year'].nunique())},
            "power_variables": needed_vars,
            "factors": factors,
            "results": results
        }
