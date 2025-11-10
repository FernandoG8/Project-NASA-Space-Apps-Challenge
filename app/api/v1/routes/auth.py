"""Authentication endpoints."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.db import Base, engine
from app.db.models import LoginEvent, RefreshToken, Role, User, UserRole
from app.schemas import (
    LogoutResponse,
    RegisterData,
    RegisterPayload,
    RegisterResponse,
    TokenData,
    TokenResponse,
    UserData,
    UserResponse,
)
from app.schemas.response import envelope

router = APIRouter(prefix="/auth", tags=["auth"])

Base.metadata.create_all(bind=engine)


def _get_or_create_default_role(db: Session) -> Role:
    role = db.query(Role).filter(Role.name == "user").first()
    if role:
        return role
    role = Role(name="user")
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


def _issue_tokens(user: User) -> TokenData:
    roles = [role.name for role in (user.roles or [])]
    access_token, expires_in = create_access_token(sub=user.email, roles=roles)
    refresh_token = create_refresh_token(sub=user.email)
    return TokenData(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


def _register_login_event(db: Session, user: User | None, request: Request, success: bool) -> None:
    ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "-")
    db.add(LoginEvent(user_id=user.id if user else None, ip=ip, user_agent=user_agent, success=success))
    db.commit()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un nuevo usuario",
)
def register(payload: RegisterPayload, db: Session = Depends(get_db)) -> dict:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "El usuario ya existe"},
        )

    hashed = hash_password(payload.password)
    user = User(email=payload.email, hashed_password=hashed, is_active=True)
    db.add(user)
    db.commit()
    db.refresh(user)

    default_role = _get_or_create_default_role(db)
    db.add(UserRole(user_id=user.id, role_id=default_role.id))
    db.commit()

    data = RegisterData(user_id=user.id)
    return envelope(success=True, message="Usuario registrado", data=data)


@router.post(
    "/token-json",
    response_model=TokenResponse,
    summary="Autenticación usando JSON",
)
def login_json(payload: RegisterPayload, request: Request, db: Session = Depends(get_db)) -> dict:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password) or not user.is_active:
        _register_login_event(db, user, request, success=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Credenciales inválidas"},
        )

    token_data = _issue_tokens(user)
    db.add(RefreshToken(user_id=user.id, token=token_data.refresh_token))
    _register_login_event(db, user, request, success=True)
    return envelope(success=True, message="Login exitoso", data=token_data)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Autenticación usando formulario OAuth2",
)
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict:
    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password) or not user.is_active:
        _register_login_event(db, user, request, success=False)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Credenciales inválidas"},
        )

    token_data = _issue_tokens(user)
    db.add(RefreshToken(user_id=user.id, token=token_data.refresh_token))
    _register_login_event(db, user, request, success=True)
    return envelope(success=True, message="Login exitoso", data=token_data)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Renueva el token de acceso usando el refresh token",
)
def refresh_token(payload: dict, db: Session = Depends(get_db)) -> dict:
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Falta refresh_token"},
        )

    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == token, RefreshToken.revoked.is_(False))
        .first()
    )
    if not row:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Refresh inválido o revocado"},
        )

    payload_data = decode_token(token)
    email = payload_data.get("sub")
    user = db.query(User).filter(User.email == email, User.is_active.is_(True)).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Usuario no encontrado o inactivo"},
        )

    token_data = _issue_tokens(user)
    return envelope(success=True, message="Token renovado", data=token_data)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Revoca un refresh token",
)
def logout(payload: dict, current: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict:
    token = payload.get("refresh_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Falta refresh_token"},
        )

    row = (
        db.query(RefreshToken)
        .filter(RefreshToken.token == token, RefreshToken.revoked.is_(False))
        .first()
    )
    if not row or row.user_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Refresh token no válido para este usuario"},
        )

    row.revoked = True
    db.commit()
    return envelope(success=True, message="Sesión finalizada", data=None)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Obtiene el perfil del usuario actual",
)
def me(current: User = Depends(get_current_user)) -> dict:
    data = UserData.model_validate(current)
    return envelope(success=True, message="Perfil recuperado", data=data)
