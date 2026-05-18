from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import ApiResponseBase


class CurriculumMappingCreate(BaseModel):
    admission_year: int = Field(description="Admission year. Both 23 and 2023 are accepted.")
    department: str
    curriculum_years: list[int] = Field(min_length=1)


class CurriculumMappingItem(BaseModel):
    id: int
    admission_year: int
    department: str
    curriculum_years: list[int]
    created_at: datetime
    updated_at: datetime


class CurriculumResolveData(BaseModel):
    admission_year: int
    department: str
    curriculum_years: list[int]
    used_fallback: bool = False


class AdmissionYearExtractData(BaseModel):
    question: str
    admission_year: int | None = None


class CurriculumMappingResponse(ApiResponseBase):
    data: CurriculumMappingItem


class CurriculumMappingListResponse(ApiResponseBase):
    data: list[CurriculumMappingItem]


class CurriculumResolveResponse(ApiResponseBase):
    data: CurriculumResolveData


class AdmissionYearExtractResponse(ApiResponseBase):
    data: AdmissionYearExtractData
