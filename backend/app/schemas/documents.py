from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponseBase


class DocumentUploadData(BaseModel):
    document_id: int
    file_name: str
    page_count: int
    chunk_count: int
    embedding_status: Literal["success", "failed"] = "success"
    embedding_message: str | None = None


class DocumentChunkItem(BaseModel):
    id: int
    page_number: int
    preview: str
    len: int = Field(description="Original chunk length")
    created_at: datetime | None = None


class DocumentDetailData(BaseModel):
    document_id: int
    file_name: str
    page_count: int
    chunks: list[DocumentChunkItem] = Field(default_factory=list)


class DocumentListItem(BaseModel):
    id: int
    file_name: str
    page_count: int
    chunk_count: int
    uploaded_at: datetime


class DocumentListData(BaseModel):
    items: list[DocumentListItem] = Field(default_factory=list)


class DocumentDeleteData(BaseModel):
    document_id: int
    deleted_chunks: int


class DocumentUploadResponse(ApiResponseBase):
    data: DocumentUploadData


class DocumentDetailResponse(ApiResponseBase):
    data: DocumentDetailData


class DocumentListResponse(ApiResponseBase):
    data: list[DocumentListItem]


class DocumentDeleteResponse(ApiResponseBase):
    data: DocumentDeleteData
