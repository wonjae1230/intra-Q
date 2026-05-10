from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponseBase


ChatRole = Literal["user", "assistant", "system"]


class ChatMessageResponse(BaseModel):
    """Serialized chat message used by the history APIs."""

    id: int
    session_id: int | None = None
    role: ChatRole
    content: str
    content_length: int
    created_at: datetime
    document_ids: list[int] | None = None
    latency_ms: int | None = None


class ChatHistoryResponse(ApiResponseBase):
    """Envelope for chat history list responses."""

    data: list[ChatMessageResponse] = Field(default_factory=list)


class ChatHistoryDeleteData(BaseModel):
    deleted_count: int


class ChatHistoryDeleteResponse(ApiResponseBase):
    """Envelope for chat history delete responses."""

    data: ChatHistoryDeleteData
