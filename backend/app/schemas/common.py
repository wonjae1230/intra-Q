from __future__ import annotations

from pydantic import BaseModel, Field


class ApiResponseBase(BaseModel):
    """Common envelope for JSON API responses."""

    success: bool = Field(default=True)
    message: str


class HealthResponse(BaseModel):
    """Minimal operational health check response."""

    status: str = "ok"
