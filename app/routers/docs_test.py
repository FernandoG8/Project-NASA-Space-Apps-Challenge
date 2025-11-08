from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Literal
from app.deps import get_current_user, require_roles
from app.models import User

router = APIRouter(prefix="/v1/test", tags=["test"])

# ======== Schemas para swagger de prueba ========
class EchoIn(BaseModel):
    message: str = Field(..., examples=["Hola mundo"])
    factors: List[Literal["temperature","precipitation","windspeed","humidity","comfort"]] = Field(
        default_factory=list,
        description="Factores del análisis",
        examples=[["temperature","precipitation"]]
    )

class EchoOut(BaseModel):
    echoed: str
    user: str | None = None
    roles: List[str] | None = None

# ======== Endpoints ========

@router.get("/public", response_model=dict, summary="Ping público", description="Endpoint abierto para verificar que el servicio responde.")
def public_ping():
    return {"status": "public-ok"}

@router.post(
    "/public/echo",
    response_model=EchoOut,
    summary="Echo público (sin auth)",
    responses={
        200: {"description": "Devuelve el mensaje tal cual"},
    },
)
def public_echo(payload: EchoIn):
    return {"echoed": payload.message}

@router.get(
    "/protected",
    response_model=EchoOut,
    summary="Ping protegido (requiere Bearer)",
    description="Devuelve info del usuario autenticado."
)
def protected_ping(user: User = Depends(get_current_user)):
    roles = [r.name for r in (user.roles or [])]
    return {"echoed": "protected-ok", "user": user.email, "roles": roles}

@router.post(
    "/protected/echo",
    response_model=EchoOut,
    summary="Echo protegido (requiere Bearer)",
    description="Echo que asocia el mensaje al usuario autenticado."
)
def protected_echo(payload: EchoIn, user: User = Depends(get_current_user)):
    roles = [r.name for r in (user.roles or [])]
    return {"echoed": payload.message, "user": user.email, "roles": roles}

@router.delete(
    "/admin/only",
    summary="Solo admin",
    description="Endpoint de prueba que requiere rol admin.",
    responses={403: {"description": "Permisos insuficientes"}}
)
def admin_only(_: User = Depends(require_roles("admin"))):
    return {"status": "admin-ok"}
