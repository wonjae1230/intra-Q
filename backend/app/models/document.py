from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.page_log import PageLog
from app.models.subject import Subject
from app.models.user import User


class Document(Base):
    """Store basic metadata for each uploaded PDF document."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    curriculum_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    college: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_file: Mapped[str | None] = mapped_column(String(255), nullable=True)
    processing_status: Mapped[str] = mapped_column(String(30), default="uploaded", nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user: Mapped[User | None] = relationship()
    chunks: Mapped[list["Chunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    page_logs: Mapped[list["PageLog"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    subjects: Mapped[list["Subject"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
