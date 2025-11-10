"""Security helpers for password hashing and JWT token management."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Iterable

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password using bcrypt."""

    return _pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""

    return _pwd_context.verify(plain_password, hashed_password)


def create_access_token(sub: str, roles: Iterable[str]) -> tuple[str, int]:
    """Create a signed JWT access token and return the token plus its TTL in seconds."""

    expires_delta = timedelta(minutes=settings.access_min)
    exp = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": sub, "roles": list(roles), "exp": exp}
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algo)
    return token, int(expires_delta.total_seconds())


def create_refresh_token(sub: str) -> str:
    """Create a signed refresh token for the given subject."""

    expires_delta = timedelta(days=settings.refresh_days)
    exp = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": sub, "type": "refresh", "exp": exp}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algo)


def decode_token(token: str) -> dict:
    """Decode a JWT token and return its payload."""

    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algo])


__all__ = [
    "hash_password",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "decode_token",
]
