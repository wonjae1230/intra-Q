from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponseBase


class DocumentUploadData(BaseModel):
    document_id: int
    file_name: str
    page_count: int
    chunk_count: int


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


class DocumentUploadResponse(ApiResponseBase):
    data: DocumentUploadData


class DocumentDetailResponse(ApiResponseBase):
    data: DocumentDetailData
