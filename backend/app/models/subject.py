from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Subject(Base):
    """Store normalized curriculum subject rows extracted from PDF pages."""

    __tablename__ = "subjects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False, index=True)
    page_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    curriculum_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    college: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    subject_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    subject_name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    credit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    semester: Mapped[str | None] = mapped_column(String(20), nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(30), nullable=False, default="manual_required")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    document: Mapped["Document"] = relationship(back_populates="subjects")
