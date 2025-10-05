from fastapi import APIRouter, Query
from app.services.precip_openmeteo import prob_lluvia

router = APIRouter(prefix="/precip", tags=["precip"])
@router.get("/prob_openmeteo")
def prob_openmeteo(
    lat: float = Query(...), lon: float = Query(...),
    fecha: str = Query(...),
    anio_ini: int = 2000, anio_fin: int = 2024,
    k: int = 5, umbral_mm: float = 1.0,
    tz: str = "America/Mexico_City"
):
    return prob_lluvia(lat, lon, fecha, y0=anio_ini, y1=anio_fin, k=k, umbral=umbral_mm, tz=tz)
