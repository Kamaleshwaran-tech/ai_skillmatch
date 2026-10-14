"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    """Base user schema attributes."""
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for registering a new user."""
    password: str = Field(..., min_length=6, description="User password, minimum 6 characters")


class UserLogin(BaseModel):
    """Schema for user login credentials."""
    email: EmailStr
    password: str


class UserOut(UserBase):
    """Schema for returning user data in API responses."""
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TokenPayload(BaseModel):
    """JWT token decoded payload."""
    sub: Optional[str] = None
    exp: Optional[int] = None
