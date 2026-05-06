from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ApiResponseBase


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    question: str = Field(..., description="사용자 질문")

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("질문은 비어 있을 수 없습니다.")
        return cleaned


class SourceItem(BaseModel):
    """Source item returned to the frontend for traceability."""

    document: str
    page: int
    preview: str


class ChatData(BaseModel):
    """Chat payload returned to the frontend."""

    answer: str
    sources: list[SourceItem] = Field(default_factory=list)


class ChatResponse(ApiResponseBase):
    """Envelope for chat API responses."""

    data: ChatData
