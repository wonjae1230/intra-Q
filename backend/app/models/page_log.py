from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class PageLog(Base):
    """Track page-level processing and validation state for curriculum PDFs."""

    __tablename__ = "page_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    page_type: Mapped[str] = mapped_column(String(10), nullable=False, default="A")
    process_method: Mapped[str] = mapped_column(String(30), nullable=False, default="pymupdf")
    validation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="pending")
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="page_logs")
