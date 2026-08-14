from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=255,
        description="Username",
    )

    email: EmailStr = Field(
        ...,
        description="User email",
    )

    full_name: str | None = Field(
        default=None,
        max_length=255,
        description="Full name",
    )


class UserCreate(UserBase):
    password: str = Field(
        ...,
        min_length=8,
        description="Password",
    )


class UserLogin(BaseModel):
    username: str = Field(
        ...,
        description="Username or email",
    )

    password: str = Field(
        ...,
        description="Password",
    )


class UserUpdate(BaseModel):
    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=255,
    )

    email: EmailStr | None = None

    full_name: str | None = Field(
        default=None,
        max_length=255,
    )

    password: str | None = Field(
        default=None,
        min_length=8,
    )


class UserResponse(UserBase):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(
        ...,
        description="Refresh token",
    )


class TokenRefreshResponse(BaseModel):
    access_token: str
    token_type: str