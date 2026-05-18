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
    curriculum_year: int | None = None
    college: str | None = None
    department: str | None = None
    source_file: str | None = None
    processing_status: Literal["uploaded", "processing", "completed", "failed"] = "completed"
    page_log_count: int = 0
    subject_count: int = 0
    validation_failed_count: int = 0
    embedding_status: Literal["success", "failed"] = "success"
    embedding_message: str | None = None


class PageLogItem(BaseModel):
    id: int
    page_id: str
    page_number: int
    page_type: Literal["A", "B", "C", "D"]
    process_method: Literal["pymupdf", "gemini"]
    validation_status: Literal["pending", "passed", "failed", "manual_required"]
    failure_reason: str | None = None
    processed_at: datetime


class SubjectItem(BaseModel):
    id: int
    page_id: str
    curriculum_year: int | None = None
    college: str | None = None
    department: str | None = None
    subject_code: str
    subject_name: str
    category: str | None = None
    credit: int | None = None
    semester: str | None = None
    raw_json: dict | None = None
    validation_status: Literal["passed", "failed", "manual_required"]
    created_at: datetime


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
    curriculum_year: int | None = None
    college: str | None = None
    department: str | None = None
    source_file: str | None = None
    processing_status: Literal["uploaded", "processing", "completed", "failed"] = "uploaded"
    chunks: list[DocumentChunkItem] = Field(default_factory=list)
    page_logs: list[PageLogItem] = Field(default_factory=list)
    subjects: list[SubjectItem] = Field(default_factory=list)


class DocumentListItem(BaseModel):
    id: int
    file_name: str
    page_count: int
    chunk_count: int
    curriculum_year: int | None = None
    college: str | None = None
    department: str | None = None
    source_file: str | None = None
    processing_status: Literal["uploaded", "processing", "completed", "failed"] = "uploaded"
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
