import random

def compute_empirical_probabilities(factor: str, lat: float, lon: float, window_days: int, radius_km: float):
    # TODO: aquí conectarías a NASA/NOAA, descargar series históricas y calcular terciles
    random.seed(hash((factor, round(lat,2), round(lon,2))) % 10_000)
    p_below = round(random.uniform(0.2, 0.4), 3)
    p_above = round(random.uniform(0.2, 0.4), 3)
    p_normal = round(1 - p_below - p_above, 3)
    median = round(random.uniform(3, 6), 2)

    units = {
        "temperature": "°C",
        "precipitation": "mm/day",
        "windspeed": "m/s",
        "dust": "µg/m³"
    }.get(factor, "")

    dataset = {
        "temperature":"ERA5-Land",
        "precipitation":"IMERG",
        "windspeed":"ERA5",
        "dust":"MERRA-2"
    }.get(factor, "unknown")

    return {
        "n_years": 24,
        "terciles": {"p_below": p_below, "p_normal": p_normal, "p_above": p_above},
        "median": median,
        "units": units,
        "dataset": dataset,
        "baseline": "1991-2020",
        "method": "empirical"
    }
