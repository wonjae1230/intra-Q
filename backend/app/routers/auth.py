from __future__ import annotations

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    MeResponse,
    RegisterData,
    RegisterRequest,
    RegisterResponse,
    TokenData,
    UserData,
)
from app.services.auth_service import authenticate_user, register_user


router = APIRouter()
logger = logging.getLogger(__name__)


def _to_user_data(user: User) -> UserData:
    return UserData(id=user.id, email=user.email, nickname=user.nickname)


@router.post("/register", response_model=RegisterResponse, summary="Register a user")
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> RegisterResponse:
    user = register_user(db, request)
    return RegisterResponse(
        message="User registered successfully",
        data=RegisterData(user_id=user.id, email=user.email, nickname=user.nickname),
    )


@router.post("/login", response_model=LoginResponse, summary="Login and issue a JWT")
def login(request: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user, access_token = authenticate_user(db, request)
    return LoginResponse(
        message="Login successful",
        data=TokenData(access_token=access_token, token_type="bearer", user=_to_user_data(user)),
    )


@router.get("/me", response_model=MeResponse, summary="Get current user")
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    logger.info("Current user retrieved successfully: user_id=%s", current_user.id)
    return MeResponse(message="Current user retrieved successfully", data=_to_user_data(current_user))
