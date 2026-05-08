from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.chat_history import ChatHistoryDeleteData, ChatHistoryDeleteResponse, ChatHistoryResponse
from app.services.chat_history_service import delete_chat_history, list_chat_history


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    response_model=ChatHistoryResponse,
    summary="List chat history",
    description="Return stored chat messages in chronological order with paging support.",
)
def get_chat_history(
    limit: int = Query(default=50, ge=1, le=100, description="한 번에 조회할 메시지 수"),
    offset: int = Query(default=0, ge=0, description="조회 시작 위치"),
    order: Literal["asc", "desc"] = Query(default="asc", description="정렬 방향"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryResponse:
    try:
        history = list_chat_history(db, user_id=current_user.id, limit=limit, offset=offset, order=order)
        logger.info("User chat history retrieved: user_id=%s, rows=%s", current_user.id, len(history))
        return ChatHistoryResponse(message="Chat history retrieved successfully", data=history)
    except SQLAlchemyError as exc:
        logger.error("Chat history query DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 조회 실패") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat history query server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc


@router.delete(
    "",
    response_model=ChatHistoryDeleteResponse,
    summary="Delete chat history",
    description="Delete all stored chat messages so the frontend can reset the conversation state.",
)
def clear_chat_history(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatHistoryDeleteResponse:
    logger.info("Chat history delete request received: user_id=%s", current_user.id)
    try:
        deleted_count = delete_chat_history(db, user_id=current_user.id)
        return ChatHistoryDeleteResponse(
            message="Chat history deleted successfully",
            data=ChatHistoryDeleteData(deleted_count=deleted_count),
        )
    except SQLAlchemyError as exc:
        logger.error("Chat history delete DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="DB 삭제 실패") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat history delete server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc
