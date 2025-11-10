"""Metadata endpoints."""
from fastapi import APIRouter

from app.schemas import (
    FactorListData,
    FactorListResponse,
    MetadataData,
    MetadataResponse,
)
from app.schemas.response import envelope
from app.services.mapper import FACTOR_TO_POWER_VARS, FACTOR_UNITS

router = APIRouter(prefix="/metadata", tags=["metadata"])

_SOURCES = {
    "temperature": "NASA POWER (MERRA-2 derived)",
    "precipitation": "NASA POWER (IMERG daily)",
    "windspeed": "NASA POWER (10m wind)",
    "humidity": "NASA POWER (2m RH)",
    "comfort": "Derived from temperature and humidity (Heat Index)",
}


@router.get(
    "/factors",
    response_model=FactorListResponse,
    summary="Factores disponibles para los análisis",
)
def list_factors() -> dict:
    factors = sorted({*FACTOR_TO_POWER_VARS.keys(), "comfort"})
    data = FactorListData(factors=factors)
    return envelope(success=True, message="Factores soportados", data=data)


@router.get(
    "/metadata",
    response_model=MetadataResponse,
    summary="Metadatos detallados de los factores",
)
def get_metadata() -> dict:
    factors = sorted({*FACTOR_TO_POWER_VARS.keys(), "comfort"})
    data = MetadataData(
        factors=factors,
        units=FACTOR_UNITS,
        power_variables=FACTOR_TO_POWER_VARS,
        sources={name: _SOURCES[name] for name in factors},
    )
    return envelope(success=True, message="Metadatos de factores", data=data)
