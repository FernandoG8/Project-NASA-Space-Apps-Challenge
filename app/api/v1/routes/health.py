"""Health check endpoint."""
from datetime import datetime, timezone

from fastapi import APIRouter

from app.schemas import HealthData, HealthResponse
from app.schemas.response import envelope

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Verifica el estado del servicio",
    responses={200: {"description": "El servicio está disponible"}},
)
def health() -> dict:
    """Return a simple heartbeat payload."""

    payload = HealthData(status="ok", timestamp=datetime.now(timezone.utc))
    return envelope(success=True, message="Campeche Weather API en línea", data=payload)
