from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponseBase
from app.schemas.curriculum import CurriculumMappingItem


class AdminPageLogItem(BaseModel):
    id: int
    page_id: str
    document_id: int
    page_number: int
    page_type: Literal["A", "B", "C", "D"]
    process_method: Literal["pymupdf", "gemini"]
    validation_status: Literal["pending", "passed", "failed", "manual_required"]
    failure_reason: str | None = None
    processed_at: datetime


class AdminPageLogListResponse(ApiResponseBase):
    data: list[AdminPageLogItem]


class PageRetryData(BaseModel):
    page_id: str
    document_id: int
    validation_status: Literal["passed", "failed", "manual_required"]
    failure_reason: str | None = None


class PageRetryResponse(ApiResponseBase):
    data: PageRetryData


class CurriculumMappingPatch(BaseModel):
    department: str | None = None
    curriculum_years: list[int] | None = Field(default=None, min_length=1)


class AdminCurriculumMappingResponse(ApiResponseBase):
    data: CurriculumMappingItem


class AdminCurriculumMappingListResponse(ApiResponseBase):
    data: list[CurriculumMappingItem]
