# app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.db import Base, engine
from app.models import User, Role, UserRole, RefreshToken, LoginEvent
from app.schemas import TokenOut, UserOut, LoginEventOut
from app.security import (
    verify_password, hash_password,
    create_access_token, create_refresh_token, decode_token
)
from app.deps import get_db, get_current_user

router = APIRouter(prefix="/v1/auth", tags=["auth"])

# Crea tablas si no existen (demo; en producción usa Alembic)
Base.metadata.create_all(bind=engine)

from pydantic import BaseModel, EmailStr

# --------- Schema de entrada para registro ---------
class RegisterIn(BaseModel):
    email: EmailStr
    password: str

@router.post(
    "/register",
    summary="Registrar nuevo usuario",
    description="Crea un nuevo usuario en el sistema. Por defecto, asigna rol 'user'.",
    status_code=201
)
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    # Verificar si ya existe
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    # Crear nuevo usuario
    hashed = hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    # Asignar rol por defecto
    default_role = db.query(Role).filter(Role.name == "user").first()
    if not default_role:
        default_role = Role(name="user")
        db.add(default_role)
        db.commit()
        db.refresh(default_role)

    db.add(UserRole(user_id=user.id, role_id=default_role.id))
    db.commit()

    return {"status": "ok", "message": "Usuario registrado", "user_id": user.id}
class LoginIn(BaseModel):
    email: EmailStr
    password: str

from pydantic import BaseModel, EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post(
    "/token-json",
    response_model=TokenOut,
    summary="Login con JSON (email + password)",
    description="Alternativa a /token (form). Envía JSON con email y password."
)
def login_json(
    payload: LoginIn,
    request: Request,
    db: Session = Depends(get_db)
):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "-")

    # 1) Buscar usuario por email
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password) or not user.is_active:
        # registra intento fallido y retorna 400
        db.add(LoginEvent(user_id=user.id if user else None, ip=ip, user_agent=ua, success=False))
        db.commit()
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    # 2) Emitir tokens
    role_names = [r.name for r in (user.roles or [])]
    access, expires_in = create_access_token(sub=user.email, roles=role_names)
    refresh = create_refresh_token(sub=user.email)

    # 3) Guardar refresh + evento de login
    db.add(RefreshToken(user_id=user.id, token=refresh))
    db.add(LoginEvent(user_id=user.id, ip=ip, user_agent=ua, success=True))
    db.commit()

    # 4) ¡Siempre retornar el objeto con el shape de TokenOut!
    return {
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": expires_in,
        "token_type": "bearer",
    }


@router.post(
    "/token",
    response_model=TokenOut,
    summary="Login con usuario/contraseña (emite Access+Refresh)",
    responses={
        200: {"description": "Login exitoso"},
        400: {"description": "Credenciales inválidas"},
        429: {"description": "Rate limit alcanzado"},
    },
)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == form.username).first()
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "-")

    if not user or not verify_password(form.password, user.hashed_password) or not user.is_active:
        db.add(LoginEvent(user_id=user.id if user else None, ip=ip, user_agent=ua, success=False))
        db.commit()
        raise HTTPException(status_code=400, detail="Credenciales inválidas")

    role_names = [r.name for r in (user.roles or [])]
    access, expires_in = create_access_token(sub=user.email, roles=role_names)
    refresh = create_refresh_token(sub=user.email)

    db.add(RefreshToken(user_id=user.id, token=refresh))
    db.add(LoginEvent(user_id=user.id, ip=ip, user_agent=ua, success=True))
    db.commit()

    return {
        "access_token": access,
        "refresh_token": refresh,
        "expires_in": expires_in,
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenOut)
def refresh_token(payload: dict, db: Session = Depends(get_db)):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Falta refresh_token")

    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == token, RefreshToken.revoked == False)
        .first()
    )
    if not row:
        raise HTTPException(status_code=401, detail="Refresh inválido o revocado")

    data = decode_token(token)
    email = data.get("sub")
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="Usuario no encontrado/activo")

    role_names = [r.name for r in (user.roles or [])]
    access, expires_in = create_access_token(sub=user.email, roles=role_names)
    return {"access_token": access, "token_type": "bearer", "expires_in": expires_in}


@router.post("/logout")
def logout(
    payload: dict,
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(status_code=400, detail="Falta refresh_token")

    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == token, RefreshToken.revoked == False)
        .first()
    )
    if not row or row.user_id != current.id:
        raise HTTPException(status_code=400, detail="Refresh token no válido para este usuario")

    row.revoked = True
    db.commit()
    return {"status": "ok"}


@router.get("/me", response_model=UserOut)
def me(current: User = Depends(get_current_user)):
    return current


@router.get("/history", response_model=list[LoginEventOut])
def login_history(
    current: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    events = (
        db.query(LoginEvent)
        .filter(LoginEvent.user_id == current.id)
        .order_by(LoginEvent.when.desc())
        .limit(50)
        .all()
    )
    return [
        LoginEventOut(
            when=e.when.isoformat(),
            ip=e.ip,
            user_agent=e.user_agent,
            success=e.success,
        )
        for e in events
    ]
