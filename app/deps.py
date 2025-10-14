# app/deps.py
from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import User
from app.security import decode_token

# Swagger vive en /api, así que el tokenUrl debe ser absoluto a ese mount
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (sin sub)")
    user = db.query(User).filter(User.email == email, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no encontrado/activo")
    return user

def require_roles(*required: str) -> Callable:
    """
    Dependency para exigir al menos uno de los roles indicados.
    Uso: @router.get(..., dependencies=[Depends(require_roles('admin','operator'))])
    """
    required_set = {r.lower() for r in required}
    def _dep(user: User = Depends(get_current_user)) -> User:
        user_roles = {r.name.lower() for r in (user.roles or [])}
        if user_roles.isdisjoint(required_set):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permisos insuficientes (rol requerido)")
        return user
    return _dep
