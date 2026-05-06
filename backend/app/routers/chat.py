from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat import ChatData, ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Generate a chat answer",
    description="Accept a user question, perform mock RAG retrieval from SQLite chunks, and return an answer with sources.",
)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Return a standardized chat response for the frontend."""
    logger.info("Chat request received: %s", request.question)
    try:
        chat_data: ChatData = generate_chat_response(request.question, db)
        return ChatResponse(message="Chat response generated successfully", data=chat_data)
    except ValueError as exc:
        logger.warning("Chat validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except SQLAlchemyError as exc:
        logger.error("Chat DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="DB 조회 실패") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc
