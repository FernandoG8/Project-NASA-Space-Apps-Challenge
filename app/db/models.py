"""Database models for the WeatherAPI project.

The models were previously spread across multiple modules under ``app/models``.
They are consolidated here to simplify imports and to align with the new project
layout where SQLAlchemy models live alongside the connection utilities.
"""
from __future__ import annotations

import enum
from datetime import datetime, timezone
from typing import List

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.connection import Base


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    users: Mapped[List["User"]] = relationship(
        "User", secondary="user_roles", back_populates="roles"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    roles: Mapped[List[Role]] = relationship(
        "Role", secondary="user_roles", back_populates="users"
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )
    login_events: Mapped[List["LoginEvent"]] = relationship(
        "LoginEvent", back_populates="user"
    )


class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True, index=True
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id"), primary_key=True, index=True
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    token: Mapped[str] = mapped_column(String(512), unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship("User", back_populates="refresh_tokens")


class LoginEvent(Base):
    __tablename__ = "login_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    when: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    ip: Mapped[str] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(Text)
    success: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship("User", back_populates="login_events")


class AnalyzeStatus(str, enum.Enum):
    ok = "ok"
    error = "error"
    running = "running"


class AnalyzeResult(Base):
    __tablename__ = "analyze_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[AnalyzeStatus] = mapped_column(
        Enum(AnalyzeStatus), default=AnalyzeStatus.ok
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    params_json: Mapped[dict | None] = mapped_column(JSON)
    result_json: Mapped[dict | None] = mapped_column(JSON)
    result_uri: Mapped[str | None] = mapped_column(String(512))
    result_hash: Mapped[str | None] = mapped_column(String(64))

    model_version: Mapped[str | None] = mapped_column(String(64))
    dataset_version: Mapped[str | None] = mapped_column(String(64))
    request_id: Mapped[str | None] = mapped_column(String(64))
    response_status: Mapped[int | None] = mapped_column(Integer)

    user: Mapped[User] = relationship("User")


__all__ = [
    "Role",
    "User",
    "UserRole",
    "RefreshToken",
    "LoginEvent",
    "AnalyzeResult",
    "AnalyzeStatus",
]
