# app/routers/metadata.py
from fastapi import APIRouter
from app.services.mapper import FACTOR_TO_POWER_VARS, FACTOR_UNITS

router = APIRouter(tags=["metadata"])

@router.get("/factors")
def list_factors():
    """
    Lista de factores disponibles para /v1/analyze.
    """
    # comfort no usa variable directa de POWER, pero está soportado
    factors = sorted(set(list(FACTOR_TO_POWER_VARS.keys()) + ["comfort"]))
    return {"factors": factors}

@router.get("/metadata")
def get_metadata():
    """
    Metadatos básicos: unidades, variables POWER por factor, fuentes.
    """
    # pequeñas descripciones
    source_by_factor = {
        "temperature": "NASA POWER (MERRA-2 derived)",
        "precipitation": "NASA POWER (IMERG-derived daily precip)",
        "windspeed": "NASA POWER (10m wind)",
        "humidity": "NASA POWER (2m RH)",
        "comfort": "Derived from temperature+humidity (Heat Index simplified)",
    }
    return {
        "factors": sorted(set(list(FACTOR_TO_POWER_VARS.keys()) + ["comfort"])),
        "units": FACTOR_UNITS,
        "power_variables": FACTOR_TO_POWER_VARS,
        "sources": source_by_factor,
    }
