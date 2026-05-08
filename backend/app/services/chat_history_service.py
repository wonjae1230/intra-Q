from __future__ import annotations

import json
import logging
from typing import Literal

from sqlalchemy import asc, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.chat_message import ChatMessage
from app.schemas.chat_history import ChatMessageResponse


logger = logging.getLogger(__name__)

MAX_CHAT_MESSAGE_CONTENT_LENGTH = 5000
ChatRole = Literal["user", "assistant", "system"]


def _serialize_document_ids(document_ids: list[int] | None) -> str | None:
    if document_ids is None:
        return None
    return json.dumps(document_ids, ensure_ascii=False)


def _deserialize_document_ids(raw_value: str | None) -> list[int] | None:
    if raw_value is None:
        return None

    try:
        value = json.loads(raw_value)
    except json.JSONDecodeError:
        logger.warning("Stored chat message has invalid document_ids JSON: %s", raw_value)
        return None

    if not isinstance(value, list):
        return None

    document_ids: list[int] = []
    for item in value:
        try:
            document_ids.append(int(item))
        except (TypeError, ValueError):
            logger.warning("Skipping invalid document_id in stored chat message: %s", item)
    return document_ids


def _prepare_content_for_role(role: ChatRole, content: str) -> tuple[str, int]:
    if not content or not content.strip():
        raise ValueError("메시지는 비어 있을 수 없습니다.")

    cleaned_content = content
    if role == "user" and len(cleaned_content) > MAX_CHAT_MESSAGE_CONTENT_LENGTH:
        logger.warning(
            "Chat message content length exceeded maximum: role=%s, length=%s, max=%s",
            role,
            len(cleaned_content),
            MAX_CHAT_MESSAGE_CONTENT_LENGTH,
        )
        raise ValueError(f"메시지는 {MAX_CHAT_MESSAGE_CONTENT_LENGTH}자를 초과할 수 없습니다.")

    if role == "assistant" and len(cleaned_content) > MAX_CHAT_MESSAGE_CONTENT_LENGTH:
        # Assistant messages are truncated for storage so long answers still keep the chat flow.
        logger.warning(
            "Assistant message truncated for storage: original_length=%s, max=%s",
            len(cleaned_content),
            MAX_CHAT_MESSAGE_CONTENT_LENGTH,
        )
        cleaned_content = cleaned_content[:MAX_CHAT_MESSAGE_CONTENT_LENGTH]

    return cleaned_content, len(cleaned_content)


def _to_response_model(message: ChatMessage) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=message.id,
        role=message.role,
        content=message.content,
        content_length=message.content_length,
        created_at=message.created_at,
        document_ids=_deserialize_document_ids(message.document_ids),
        latency_ms=message.latency_ms,
    )


def save_chat_message(
    db: Session,
    user_id: int,
    role: ChatRole,
    content: str,
    document_ids: list[int] | None = None,
    latency_ms: int | None = None,
) -> ChatMessage:
    """Persist one chat message and return the ORM row."""

    cleaned_content, content_length = _prepare_content_for_role(role, content)
    message_row = ChatMessage(
        user_id=user_id,
        role=role,
        content=cleaned_content,
        content_length=content_length,
        document_ids=_serialize_document_ids(document_ids),
        latency_ms=latency_ms,
    )

    try:
        db.add(message_row)
        db.commit()
        db.refresh(message_row)
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Chat message save failed: role=%s, error=%s", role, exc, exc_info=True)
        raise

    logger.info(
        "Chat message saved: id=%s, role=%s, content_length=%s, has_document_ids=%s",
        message_row.id,
        role,
        message_row.content_length,
        document_ids is not None,
    )
    return message_row


def save_user_message(db: Session, user_id: int, content: str, document_ids: list[int] | None = None) -> ChatMessage:
    return save_chat_message(db, user_id, "user", content, document_ids=document_ids, latency_ms=None)


def save_assistant_message(
    db: Session,
    user_id: int,
    content: str,
    document_ids: list[int] | None = None,
    latency_ms: int | None = None,
) -> ChatMessage:
    return save_chat_message(db, user_id, "assistant", content, document_ids=document_ids, latency_ms=latency_ms)


def list_chat_history(
    db: Session,
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    order: Literal["asc", "desc"] = "asc",
) -> list[ChatMessageResponse]:
    """Return chat history in the requested order."""

    sort_order = asc(ChatMessage.created_at) if order == "asc" else desc(ChatMessage.created_at)
    secondary_order = ChatMessage.id.asc() if order == "asc" else ChatMessage.id.desc()
    rows = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == user_id)
        .order_by(sort_order, secondary_order)
        .offset(offset)
        .limit(limit)
        .all()
    )
    logger.info(
        "Chat history retrieved: user_id=%s, limit=%s, offset=%s, order=%s, rows=%s",
        user_id,
        limit,
        offset,
        order,
        len(rows),
    )
    return [_to_response_model(row) for row in rows]


def delete_chat_history(db: Session, user_id: int) -> int:
    """Delete all stored chat messages and return the affected row count."""

    try:
        deleted_count = db.query(ChatMessage).filter(ChatMessage.user_id == user_id).delete(synchronize_session=False)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Chat history delete failed: %s", exc, exc_info=True)
        raise

    logger.info("Chat history deleted: user_id=%s, deleted_count=%s", user_id, deleted_count)
    return int(deleted_count)
