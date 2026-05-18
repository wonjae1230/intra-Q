from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class CurriculumMapping(Base):
    """Map an admission year and department to applicable curriculum years."""

    __tablename__ = "curriculum_mappings"
    __table_args__ = (
        Index("ix_curriculum_mappings_department_admission_year", "department", "admission_year"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    admission_year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    curriculum_years: Mapped[list[int]] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
