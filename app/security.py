# app/security.py
from datetime import datetime, timedelta, timezone
from typing import List
from jose import jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(sub: str, roles: List[str]) -> tuple[str, int]:
    # ⚠️ usa minúsculas: access_min, jwt_secret, jwt_algo
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.access_min)
    payload = {"sub": sub, "roles": roles, "exp": exp}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algo)
    return token, settings.access_min * 60

def create_refresh_token(sub: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(days=settings.refresh_days)
    payload = {"sub": sub, "type": "refresh", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algo)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algo])
