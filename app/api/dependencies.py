"""Common dependencies shared across API routers."""
from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.connection import SessionLocal
from app.db.models import User


def get_db() -> Session:
    """Provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Return the authenticated user for the provided bearer token."""
    try:
        payload = decode_token(token)
    except Exception as exc:  # pragma: no cover - jose raises various exceptions
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token inválido", "errors": [str(exc)]},
        ) from exc

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token inválido", "errors": ["sub missing"]},
        )

    user = (
        db.query(User)
        .filter(User.email == email, User.is_active.is_(True))
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Usuario no encontrado o inactivo"},
        )
    return user


def require_roles(*required: str) -> Callable[[User], User]:
    """Dependency that enforces at least one of the provided roles."""

    required_set = {r.lower() for r in required}

    def _dep(user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name.lower() for r in (user.roles or [])}
        if required_set and user_roles.isdisjoint(required_set):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"message": "Permisos insuficientes (rol requerido)"},
            )
        return user

    return _dep


__all__ = ["get_db", "get_current_user", "require_roles", "oauth2_scheme"]
