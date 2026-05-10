from __future__ import annotations

import logging
from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.models.chat_session import ChatSession
from app.schemas.chat import (
    ChatSessionDeleteData,
    ChatSessionListItem,
    ChatSessionResponseData,
    ChatSessionUpdateResponseData,
)


logger = logging.getLogger(__name__)
DEFAULT_CHAT_SESSION_TITLE = "새 채팅"
MAX_LAST_MESSAGE_LENGTH = 120


def _clean_title(title: str | None) -> str:
    cleaned = (title or DEFAULT_CHAT_SESSION_TITLE).strip()
    return cleaned[:100] or DEFAULT_CHAT_SESSION_TITLE


def get_owned_chat_session(db: Session, user_id: int, session_id: int) -> ChatSession:
    """Return a session after checking both existence and user ownership."""
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
    if session is None:
        logger.warning("Chat session not found: user_id=%s, session_id=%s", user_id, session_id)
        raise HTTPException(status_code=404, detail="채팅 세션을 찾을 수 없습니다.")

    if session.user_id != user_id:
        logger.warning(
            "Unauthorized chat session access attempt: user_id=%s, owner_user_id=%s, session_id=%s",
            user_id,
            session.user_id,
            session_id,
        )
        raise HTTPException(status_code=403, detail="해당 채팅 세션에 접근할 권한이 없습니다.")

    return session


def create_chat_session(db: Session, user_id: int, title: str | None = None) -> ChatSessionResponseData:
    """Create a new user-owned chat session."""
    session = ChatSession(user_id=user_id, title=_clean_title(title))
    try:
        db.add(session)
        db.commit()
        db.refresh(session)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Chat session create DB error: user_id=%s", user_id)
        raise

    logger.info("Chat session created: user_id=%s, session_id=%s", user_id, session.id)
    return ChatSessionResponseData(session_id=session.id, title=session.title, created_at=session.created_at)


def list_chat_sessions(db: Session, user_id: int) -> list[ChatSessionListItem]:
    """Return the current user's sessions ordered by most recently updated."""
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .all()
    )

    items: list[ChatSessionListItem] = []
    for session in sessions:
        message_count = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id, ChatMessage.session_id == session.id)
            .count()
        )
        last_message = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id, ChatMessage.session_id == session.id)
            .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
            .first()
        )
        last_content = last_message.content[:MAX_LAST_MESSAGE_LENGTH] if last_message else None
        items.append(
            ChatSessionListItem(
                session_id=session.id,
                title=session.title,
                created_at=session.created_at,
                updated_at=session.updated_at,
                message_count=message_count,
                last_message=last_content,
            )
        )

    logger.info("Chat sessions retrieved: user_id=%s, rows=%s", user_id, len(items))
    return items


def update_chat_session_title(
    db: Session,
    user_id: int,
    session_id: int,
    title: str,
) -> ChatSessionUpdateResponseData:
    """Update a session title after ownership verification."""
    session = get_owned_chat_session(db, user_id=user_id, session_id=session_id)
    session.title = _clean_title(title)
    session.updated_at = datetime.utcnow()

    try:
        db.commit()
        db.refresh(session)
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Chat session title update DB error: user_id=%s, session_id=%s", user_id, session_id)
        raise

    logger.info("Chat session title updated: user_id=%s, session_id=%s", user_id, session_id)
    return ChatSessionUpdateResponseData(session_id=session.id, title=session.title, updated_at=session.updated_at)


def touch_chat_session(db: Session, user_id: int, session_id: int) -> None:
    """Mark a session as recently active after new messages are stored."""
    session = get_owned_chat_session(db, user_id=user_id, session_id=session_id)
    session.updated_at = datetime.utcnow()
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Chat session touch DB error: user_id=%s, session_id=%s", user_id, session_id)
        raise


def delete_chat_session(db: Session, user_id: int, session_id: int) -> ChatSessionDeleteData:
    """Delete one owned session and all messages inside it."""
    session = get_owned_chat_session(db, user_id=user_id, session_id=session_id)
    try:
        deleted_messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.user_id == user_id, ChatMessage.session_id == session_id)
            .delete(synchronize_session=False)
        )
        db.delete(session)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Chat session delete DB error: user_id=%s, session_id=%s", user_id, session_id)
        raise

    logger.info(
        "Chat session deleted: user_id=%s, session_id=%s, deleted_messages=%s",
        user_id,
        session_id,
        deleted_messages,
    )
    return ChatSessionDeleteData(session_id=session_id, deleted_messages=int(deleted_messages))
