from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(default=True)

    roles = relationship("Role", secondary="user_roles", back_populates="users")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
    login_events = relationship("LoginEvent", back_populates="user")
