from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ApiResponseBase

ChatRole = Literal["user", "assistant", "system"]


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    session_id: int = Field(..., gt=0, description="채팅 세션 ID")
    question: str = Field(..., description="사용자 질문")
    document_ids: list[int] | None = Field(default=None, description="검색할 문서 ID 목록")
    top_k: int | None = Field(default=None, gt=0, description="검색 결과 개수")
    approach_hint: str | None = Field(default=None, description="AI가 제시한 답변 방향 힌트")

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("질문은 비어 있을 수 없습니다.")
        return cleaned

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None

        cleaned_ids: list[int] = []
        seen_ids: set[int] = set()
        for document_id in value:
            if document_id <= 0:
                raise ValueError("document_ids는 1 이상의 정수여야 합니다.")
            if document_id in seen_ids:
                continue
            seen_ids.add(document_id)
            cleaned_ids.append(document_id)

        return cleaned_ids


class ClarifyRequest(BaseModel):
    """Request body for the pre-answer clarification endpoint."""

    question: str = Field(..., description="사용자 질문")
    document_ids: list[int] | None = Field(default=None, description="검색할 문서 ID 목록")

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("질문은 비어 있을 수 없습니다.")
        return cleaned

    @field_validator("document_ids")
    @classmethod
    def validate_document_ids(cls, value: list[int] | None) -> list[int] | None:
        return ChatRequest.validate_document_ids(value)


class SourceItem(BaseModel):
    """Source item returned to the frontend for traceability."""

    document_id: int | None = None
    document_name: str
    file_name: str | None = None
    page: int | None = None
    chunk_text: str
    similarity_score: float | None = None
    content: str | None = None
    distance: float | None = None

    @property
    def document(self) -> str:
        """Backward-compatible alias used by older tests and clients."""
        return self.document_name

    @property
    def text(self) -> str:
        """Backward-compatible alias used by older tests and clients."""
        return self.chunk_text

    @property
    def score(self) -> float | None:
        """Backward-compatible alias used by older tests and clients."""
        return self.similarity_score


class ChatData(BaseModel):
    """Chat payload returned to the frontend."""

    session_id: int
    answer: str
    sources: list[SourceItem] = Field(default_factory=list)
    latency_ms: int


class ChatResponse(ApiResponseBase):
    """Envelope for chat API responses."""

    data: ChatData


class ClarifyOption(BaseModel):
    id: str
    label: str
    description: str


class ClarifyData(BaseModel):
    question: str
    options: list[ClarifyOption]
    document_ids: list[int] = Field(default_factory=list)
    context_question: str | None = None


class ClarifyResponse(ApiResponseBase):
    data: ClarifyData


class RecentChatMessage(BaseModel):
    """A compact stored chat message used to restore the current user's chat screen."""

    id: int
    session_id: int | None = None
    role: ChatRole
    content: str
    created_at: datetime
    latency_ms: int | None = None


class RecentChatResponse(ApiResponseBase):
    """Envelope for the recent chat history restore API."""

    data: list[RecentChatMessage] = Field(default_factory=list)


class ChatSessionCreateRequest(BaseModel):
    """Create a user-owned chat session."""

    title: str | None = Field(default=None, max_length=100, description="채팅 세션 제목")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title은 빈 문자열일 수 없습니다.")
        return cleaned[:100]


class ChatSessionUpdateRequest(BaseModel):
    """Update a user-owned chat session title."""

    title: str = Field(..., max_length=100, description="새 채팅 세션 제목")

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title은 빈 문자열일 수 없습니다.")
        return cleaned


class ChatSessionResponseData(BaseModel):
    session_id: int
    title: str
    created_at: datetime


class ChatSessionResponse(ApiResponseBase):
    data: ChatSessionResponseData


class ChatSessionListItem(BaseModel):
    session_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message: str | None = None


class ChatSessionListResponse(ApiResponseBase):
    data: list[ChatSessionListItem] = Field(default_factory=list)


class SessionChatMessage(BaseModel):
    id: int
    session_id: int
    role: ChatRole
    content: str
    created_at: datetime
    latency_ms: int | None = None


class ChatSessionMessagesResponse(ApiResponseBase):
    data: list[SessionChatMessage] = Field(default_factory=list)


class ChatSessionUpdateResponseData(BaseModel):
    session_id: int
    title: str
    updated_at: datetime


class ChatSessionUpdateResponse(ApiResponseBase):
    data: ChatSessionUpdateResponseData


class ChatSessionDeleteData(BaseModel):
    session_id: int
    deleted_messages: int


class ChatSessionDeleteResponse(ApiResponseBase):
    data: ChatSessionDeleteData
