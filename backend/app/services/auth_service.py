from __future__ import annotations

import logging

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


logger = logging.getLogger(__name__)


def register_user(db: Session, request: RegisterRequest) -> User:
    """Create a user after checking email uniqueness and hashing the password."""
    try:
        existing_user = db.query(User).filter(User.email == request.email).first()
    except SQLAlchemyError as exc:
        logger.error("User registration lookup DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    if existing_user:
        logger.warning("User registration failed: duplicate email=%s", request.email)
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.")

    user = User(
        email=str(request.email),
        password_hash=hash_password(request.password),
        nickname=request.nickname,
    )

    try:
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError as exc:
        db.rollback()
        logger.warning("User registration failed by integrity constraint: email=%s", request.email)
        raise HTTPException(status_code=409, detail="이미 가입된 이메일입니다.") from exc
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("User registration DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info("User registered successfully: user_id=%s, email=%s", user.id, user.email)
    return user


def authenticate_user(db: Session, request: LoginRequest) -> tuple[User, str]:
    """Validate credentials and return the user plus a JWT access token."""
    try:
        user = db.query(User).filter(User.email == request.email).first()
    except SQLAlchemyError as exc:
        logger.error("Login lookup DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    if user is None or not verify_password(request.password, user.password_hash):
        logger.warning("Login failed: email=%s", request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(subject=str(user.id))
    logger.info("Login successful: user_id=%s, email=%s", user.id, user.email)
    return user, access_token
