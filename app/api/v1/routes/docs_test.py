"""Endpoints para pruebas y documentación."""
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, require_roles
from app.db.models import User
from app.schemas import EchoData, EchoIn, EchoResponse
from app.schemas.response import envelope

router = APIRouter(prefix="/test", tags=["test"])


@router.get(
    "/public",
    response_model=EchoResponse,
    summary="Ping público",
)
def public_ping() -> dict:
    data = EchoData(echoed="public-ok")
    return envelope(success=True, message="Servicio público disponible", data=data)


@router.post(
    "/public/echo",
    response_model=EchoResponse,
    summary="Echo público",
)
def public_echo(payload: EchoIn) -> dict:
    data = EchoData(echoed=payload.message)
    return envelope(success=True, message="Echo público", data=data)


@router.get(
    "/protected",
    response_model=EchoResponse,
    summary="Ping protegido",
)
def protected_ping(user: User = Depends(get_current_user)) -> dict:
    roles = [role.name for role in (user.roles or [])]
    data = EchoData(echoed="protected-ok", user=user.email, roles=roles)
    return envelope(success=True, message="Echo protegido", data=data)


@router.post(
    "/protected/echo",
    response_model=EchoResponse,
    summary="Echo protegido",
)
def protected_echo(payload: EchoIn, user: User = Depends(get_current_user)) -> dict:
    roles = [role.name for role in (user.roles or [])]
    data = EchoData(echoed=payload.message, user=user.email, roles=roles)
    return envelope(success=True, message="Echo protegido", data=data)


@router.delete(
    "/admin/only",
    response_model=EchoResponse,
    summary="Solo administradores",
)
def admin_only(_: User = Depends(require_roles("admin"))) -> dict:
    data = EchoData(echoed="admin-ok")
    return envelope(success=True, message="Acceso de administrador", data=data)
