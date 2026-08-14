from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=255, description="Username")
    email: EmailStr = Field(..., description="User email")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password (min 8 characters)")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=255)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=8)


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., description="Refresh token")


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
