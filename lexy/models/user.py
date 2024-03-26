from datetime import datetime
from typing import Optional

from pydantic import EmailStr
from sqlalchemy import Column, DateTime, func
from sqlmodel import AutoString, Field, SQLModel

from lexy.core.security import get_password_hash


class UserBase(SQLModel):
    email: EmailStr = Field(index=True, nullable=False, unique=True, sa_type=AutoString)
    full_name: Optional[str] = None


class User(UserBase, table=True):
    __tablename__ = "users"
    user_id: int = Field(default=None, primary_key=True, index=True)
    hashed_password: str
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    created_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now()),
    )
    updated_at: datetime = Field(
        sa_column=Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()),
    )

    @classmethod
    def create(cls, email: str, password: str, **kwargs):
        hashed_password = get_password_hash(password)
        return cls(email=email, hashed_password=hashed_password, **kwargs)


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str


# Additional properties to return via API
class UserRead(UserBase):
    user_id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime


# Properties to receive via API on update
class UserUpdate(UserBase):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
