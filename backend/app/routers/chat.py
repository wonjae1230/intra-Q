from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.document import Document
from app.models.user import User
from app.schemas.chat import (
    ChatData,
    ChatSessionCreateRequest,
    ChatSessionDeleteResponse,
    ChatSessionListResponse,
    ChatSessionMessagesResponse,
    ChatSessionResponse,
    ChatSessionUpdateRequest,
    ChatSessionUpdateResponse,
    ClarifyRequest,
    ChatRequest,
    ChatResponse,
    ClarifyData,
    ClarifyOption,
    ClarifyResponse,
    RecentChatResponse,
)
from app.services.chat_history_service import (
    list_recent_chat_history,
    list_session_messages,
    save_assistant_message,
    save_user_message,
)
from app.services.chat_service import generate_chat_response
from app.services.chat_session_service import (
    create_chat_session,
    delete_chat_session,
    get_owned_chat_session,
    list_chat_sessions,
    touch_chat_session,
    update_chat_session_title,
)
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
    "/sessions",
    response_model=ChatSessionResponse,
    summary="Create a chat session",
    description="Create a new chat session owned by the current authenticated user.",
)
def create_session(
    request: ChatSessionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionResponse:
    logger.info("Chat session create request received: user_id=%s", current_user.id)
    try:
        data = create_chat_session(db, user_id=current_user.id, title=request.title)
        return ChatSessionResponse(message="Chat session created successfully", data=data)
    except SQLAlchemyError as exc:
        logger.error("Chat session create DB error: user_id=%s, error=%s", current_user.id, exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 저장 실패") from exc


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List chat sessions",
    description="Return the current authenticated user's chat sessions ordered by most recent activity.",
)
def get_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionListResponse:
    logger.info("Chat sessions list request received: user_id=%s", current_user.id)
    try:
        sessions = list_chat_sessions(db, user_id=current_user.id)
        return ChatSessionListResponse(message="Chat sessions retrieved successfully", data=sessions)
    except SQLAlchemyError as exc:
        logger.error("Chat sessions list DB error: user_id=%s, error=%s", current_user.id, exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 조회 실패") from exc


@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatSessionMessagesResponse,
    summary="List messages in a chat session",
    description="Return messages that belong only to the requested session after validating user ownership.",
)
def get_session_messages(
    session_id: int,
    limit: int = Query(default=50, ge=1, le=100, description="한 번에 조회할 메시지 수"),
    offset: int = Query(default=0, ge=0, description="조회 시작 위치"),
    order: Literal["asc", "desc"] = Query(default="asc", description="정렬 방향"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionMessagesResponse:
    logger.info("Session messages request received: user_id=%s, session_id=%s", current_user.id, session_id)
    try:
        get_owned_chat_session(db, user_id=current_user.id, session_id=session_id)
        messages = list_session_messages(
            db,
            user_id=current_user.id,
            session_id=session_id,
            limit=limit,
            offset=offset,
            order=order,
        )
        return ChatSessionMessagesResponse(message="Session messages retrieved successfully", data=messages)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "Session messages DB error: user_id=%s, session_id=%s, error=%s",
            current_user.id,
            session_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=503, detail="DB 조회 실패") from exc


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionUpdateResponse,
    summary="Update a chat session title",
    description="Update the title of a chat session owned by the current authenticated user.",
)
def update_session(
    session_id: int,
    request: ChatSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionUpdateResponse:
    logger.info("Chat session update request received: user_id=%s, session_id=%s", current_user.id, session_id)
    try:
        data = update_chat_session_title(db, user_id=current_user.id, session_id=session_id, title=request.title)
        return ChatSessionUpdateResponse(message="Chat session updated successfully", data=data)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "Chat session update DB error: user_id=%s, session_id=%s, error=%s",
            current_user.id,
            session_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=503, detail="DB 저장 실패") from exc


@router.delete(
    "/sessions/{session_id}",
    response_model=ChatSessionDeleteResponse,
    summary="Delete a chat session",
    description="Delete one owned chat session and all messages stored inside that session.",
)
def delete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ChatSessionDeleteResponse:
    logger.info("Chat session delete request received: user_id=%s, session_id=%s", current_user.id, session_id)
    try:
        data = delete_chat_session(db, user_id=current_user.id, session_id=session_id)
        return ChatSessionDeleteResponse(message="Chat session deleted successfully", data=data)
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        logger.error(
            "Chat session delete DB error: user_id=%s, session_id=%s, error=%s",
            current_user.id,
            session_id,
            exc,
            exc_info=True,
        )
        raise HTTPException(status_code=503, detail="DB 삭제 실패") from exc


@router.get(
    "/recent",
    response_model=RecentChatResponse,
    summary="Get recent chat history (deprecated)",
    description=(
        "Deprecated compatibility endpoint. Return messages from the current user's most recently updated session. "
        "Prefer GET /api/chat/sessions/{session_id}/messages for session-scoped history."
    ),
)
def get_recent_chat_history(
    limit: int = Query(default=50, ge=1, le=100, description="최근 조회할 메시지 수, 최대 100개"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RecentChatResponse:
    """Return recent stored messages for the logged-in user's single chat view."""
    logger.info("Recent chat history request received: user_id=%s, limit=%s", current_user.id, limit)
    try:
        history = list_recent_chat_history(db, user_id=current_user.id, limit=limit)
        logger.info("Recent chat history query succeeded: user_id=%s, rows=%s", current_user.id, len(history))
        return RecentChatResponse(message="Recent chat history retrieved successfully", data=history)
    except SQLAlchemyError as exc:
        logger.error("Recent chat history DB error: user_id=%s, error=%s", current_user.id, exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 조회 실패") from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Recent chat history server error: user_id=%s", current_user.id)
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc


@router.post(
    "/clarify",
    response_model=ClarifyResponse,
    summary="Search documents and return options",
    description="Run vector search and return grouped document options for the user to choose from before generating an answer.",
)
def clarify(
    request: ClarifyRequest,
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
    logger.info(
        "Chat request received: user_id=%s, session_id=%s, question=%s",
        current_user.id,
        request.session_id,
        request.question,
    )
    try:
        get_owned_chat_session(db, user_id=current_user.id, session_id=request.session_id)
        document_ids = _resolve_user_document_ids(db, current_user.id, request.document_ids)
        try:
            save_user_message(
                db,
                current_user.id,
                request.session_id,
                request.question,
                document_ids=document_ids,
            )
        except ValueError as exc:
            logger.warning("User message validation error: %s", exc)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except SQLAlchemyError as exc:
            logger.error(
                "User message save failed: user_id=%s, session_id=%s, error=%s",
                current_user.id,
                request.session_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(status_code=503, detail="채팅 메시지 저장 실패") from exc

        chat_data: ChatData = generate_chat_response(
            request.question,
            document_ids=document_ids,
            top_k=request.top_k,
            db=db,
            user_id=current_user.id,
            session_id=request.session_id,
            approach_hint=request.approach_hint,
        )

        try:
            save_assistant_message(
                db,
                current_user.id,
                request.session_id,
                chat_data.answer,
                document_ids=document_ids,
                latency_ms=chat_data.latency_ms,
            )
            touch_chat_session(db, user_id=current_user.id, session_id=request.session_id)
            logger.info(
                "Chat messages saved successfully: user_id=%s, session_id=%s",
                current_user.id,
                request.session_id,
            )
        except SQLAlchemyError as exc:
            logger.error(
                "Assistant message save failed: user_id=%s, session_id=%s, error=%s",
                current_user.id,
                request.session_id,
                exc,
                exc_info=True,
            )
            raise HTTPException(status_code=503, detail="채팅 메시지 저장 실패") from exc

        return ChatResponse(message="Chat response generated successfully", data=chat_data)
    except ValueError as exc:
        logger.warning("Chat validation error: %s", exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Chat server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc
