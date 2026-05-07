from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.chat import ChatData, ChatRequest, ChatResponse
from app.services.chat_history_service import save_assistant_message, save_user_message
from app.services.chat_service import generate_chat_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Generate a chat answer",
    description="Accept a user question, store the chat history, query the RAG pipeline, and return an answer with sources.",
)
def chat(request: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    """Return a standardized chat response for the frontend."""
    logger.info("Chat request received: %s", request.question)
    try:
        try:
            save_user_message(db, request.question, document_ids=request.document_ids)
        except ValueError as exc:
            logger.warning("User message validation error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SQLAlchemyError as exc:
            # Chat should still work even if history storage fails.
            logger.error("User message save failed: %s", exc, exc_info=True)

        chat_data: ChatData = generate_chat_response(
            request.question,
            document_ids=request.document_ids,
            top_k=request.top_k,
        )

        try:
            save_assistant_message(
                db,
                chat_data.answer,
                document_ids=request.document_ids,
                latency_ms=chat_data.latency_ms,
            )
        except SQLAlchemyError as exc:
            # Assistant history storage is best-effort so a DB write failure does not break chat responses.
            logger.error("Assistant message save failed: %s", exc, exc_info=True)

        return ChatResponse(message="Chat response generated successfully", data=chat_data)
    except ValueError as exc:
        logger.warning("Chat validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc
