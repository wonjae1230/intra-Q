from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ApiResponseBase


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

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


class ChatData(BaseModel):
    """Chat payload returned to the frontend."""

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
