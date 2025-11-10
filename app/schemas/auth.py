"""Schemas for authentication endpoints."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.response import BaseResponse


class RoleData(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


class UserData(BaseModel):
    id: int
    email: EmailStr
    roles: List[RoleData] = Field(default_factory=list)

    class Config:
        from_attributes = True


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, examples=["Secret123!"])


class RegisterData(BaseModel):
    user_id: int


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class LoginEventData(BaseModel):
    when: str
    ip: str
    user_agent: str
    success: bool


class RegisterResponse(BaseResponse[RegisterData]):
    data: Optional[RegisterData] = None


class TokenResponse(BaseResponse[TokenData]):
    data: Optional[TokenData] = None


class LogoutResponse(BaseResponse[None]):
    data: Optional[None] = None


class UserResponse(BaseResponse[UserData]):
    data: Optional[UserData] = None
