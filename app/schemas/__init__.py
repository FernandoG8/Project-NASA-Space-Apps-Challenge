# app/schemas/__init__.py
from pydantic import BaseModel, EmailStr
from typing import List, Optional

# ==== Roles/Usuarios ====
class RoleOut(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class UserOut(BaseModel):
    id: int
    email: EmailStr
    roles: List[RoleOut] = []
    class Config: from_attributes = True

# ==== Tokens ====
class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None

# ==== Historial de login ====
class LoginEventOut(BaseModel):
    when: str
    ip: str
    user_agent: str
    success: bool

# (Si ya tienes otros schemas como AnalyzeRequest en analyze_req.py,
# no pasa nada: puedes importarlos con `from app.schemas.analyze_req import AnalyzeRequest`)
