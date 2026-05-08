from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import ChatData, ChatRequest, ChatResponse, ClarifyData, ClarifyOption, ClarifyResponse
from app.services.chat_history_service import save_assistant_message, save_user_message
from app.services.chat_service import generate_chat_response
from rag.pipeline import search_with_options

router = APIRouter()
logger = logging.getLogger(__name__)


def _resolve_user_document_ids(db: Session, user_id: int, requested_ids: list[int] | None) -> list[int]:
    """Return the document filter that keeps RAG retrieval inside one user's data."""
    owned_ids = {
        row.id
        for row in db.query(Document.id)
        .filter(Document.user_id == user_id)
        .all()
    }

    if requested_ids is None:
        return sorted(owned_ids)

    requested_set = set(requested_ids)
    unauthorized_ids = requested_set - owned_ids
    if unauthorized_ids:
        logger.warning(
            "Unauthorized chat document access attempt: user_id=%s, document_ids=%s",
            user_id,
            sorted(unauthorized_ids),
        )
        raise HTTPException(status_code=403, detail="해당 문서에 접근할 권한이 없습니다.")

    return requested_ids


@router.post(
    "/clarify",
    response_model=ClarifyResponse,
    summary="Search documents and return options",
    description="Run vector search and return grouped document options for the user to choose from before generating an answer.",
)
def clarify(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ClarifyResponse:
    logger.info("Clarify request received: user_id=%s, question=%s", current_user.id, request.question)
    try:
        document_ids = _resolve_user_document_ids(db, current_user.id, request.document_ids)
        result = search_with_options(request.question, document_ids=document_ids)
        options = [ClarifyOption(**opt) for opt in result["options"]]
        return ClarifyResponse(
            message="Document options retrieved successfully",
            data=ClarifyData(
                question=request.question,
                options=options,
                document_ids=result.get("document_ids", document_ids),
                context_question=result.get("context_question"),
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Clarify server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc


@router.post(
    "",
    response_model=ChatResponse,
    summary="Generate a chat answer",
    description="Accept a user question, store the chat history, query the RAG pipeline, and return an answer with sources.",
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatResponse:
    """Return a standardized chat response for the frontend."""
    logger.info("Chat request received: user_id=%s, question=%s", current_user.id, request.question)
    try:
        document_ids = _resolve_user_document_ids(db, current_user.id, request.document_ids)
        try:
            save_user_message(db, current_user.id, request.question, document_ids=document_ids)
        except ValueError as exc:
            logger.warning("User message validation error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SQLAlchemyError as exc:
            # Chat should still work even if history storage fails.
            logger.error("User message save failed: %s", exc, exc_info=True)

        chat_data: ChatData = generate_chat_response(
            request.question,
            document_ids=document_ids,
            top_k=request.top_k,
            db=db,
            user_id=current_user.id,
            approach_hint=request.approach_hint,
        )

        try:
            save_assistant_message(
                db,
                current_user.id,
                chat_data.answer,
                document_ids=document_ids,
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
