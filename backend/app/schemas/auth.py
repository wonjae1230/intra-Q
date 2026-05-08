from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import ApiResponseBase


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    nickname: str = Field(..., min_length=1, max_length=100)

    @field_validator("nickname")
    @classmethod
    def validate_nickname(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("nickname은 비어 있을 수 없습니다.")
        return cleaned


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class UserData(BaseModel):
    id: int
    email: str
    nickname: str


class RegisterData(BaseModel):
    user_id: int
    email: str
    nickname: str


class TokenData(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserData


class RegisterResponse(ApiResponseBase):
    data: RegisterData


class LoginResponse(ApiResponseBase):
    data: TokenData


class MeResponse(ApiResponseBase):
    data: UserData
