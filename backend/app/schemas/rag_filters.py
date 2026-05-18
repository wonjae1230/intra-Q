from __future__ import annotations

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import ApiResponseBase


class RagFilterResolveRequest(BaseModel):
    question: str | None = None
    department: str | None = None
    admission_year: int | None = Field(default=None, description="Both 23 and 2023 are accepted.")

    @model_validator(mode="after")
    def require_question_or_admission_year(self) -> "RagFilterResolveRequest":
        if self.admission_year is None and not (self.question or "").strip():
            raise ValueError("question 또는 admission_year 중 하나는 필요합니다.")
        return self


class RagFilterResolveData(BaseModel):
    admission_year: int | None = None
    department: str | None = None
    curriculum_years: list[int]
    fallback_used: bool


class RagFilterResolveResponse(ApiResponseBase):
    data: RagFilterResolveData
