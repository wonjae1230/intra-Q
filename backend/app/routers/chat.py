from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from app.schemas.chat import ChatData, ChatRequest, ChatResponse
from app.services.chat_service import generate_chat_response

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=ChatResponse,
    summary="Generate a chat answer",
    description="Accept a user question, query the RAG pipeline, and return an answer with sources.",
)
def chat(request: ChatRequest) -> ChatResponse:
    """Return a standardized chat response for the frontend."""
    logger.info("Chat request received: %s", request.question)
    try:
        chat_data: ChatData = generate_chat_response(
            request.question,
            document_ids=request.document_ids,
            top_k=request.top_k,
        )
        return ChatResponse(message="Chat response generated successfully", data=chat_data)
    except ValueError as exc:
        logger.warning("Chat validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc
