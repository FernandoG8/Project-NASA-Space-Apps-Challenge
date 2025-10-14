# app/schemas.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional

class RoleOut(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    roles: List[RoleOut] = []
    class Config: from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

class LoginEventOut(BaseModel):
    when: str
    ip: str
    user_agent: str
    success: bool
