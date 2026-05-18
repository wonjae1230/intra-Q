from __future__ import annotations

import logging
import re

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.curriculum_mapping import CurriculumMapping
from app.models.document import Document

logger = logging.getLogger(__name__)


def extract_admission_year(question: str) -> int | None:
    """Extract a four-digit admission year from Korean student-number phrasing."""
    text = question or ""
    match = re.search(r"(?<!\d)(\d{2}|\d{4})\s*학번", text)
    if not match:
        logger.info("Admission year extraction result: question=%s, admission_year=None", text)
        return None

    raw_year = int(match.group(1))
    admission_year = 2000 + raw_year if raw_year < 100 else raw_year
    logger.info("Admission year extraction result: question=%s, admission_year=%s", text, admission_year)
    return admission_year


def resolve_curriculum_years(db: Session, *, admission_year: int, department: str | None = None) -> list[int]:
    """Resolve curriculum years for a department/admission year pair with latest-year fallback."""
    normalized_year = normalize_admission_year(admission_year)
    normalized_department = department.strip() if department else None
    logger.info(
        "Curriculum mapping lookup: admission_year=%s, department=%s",
        normalized_year,
        normalized_department,
    )

    query = db.query(CurriculumMapping).filter(CurriculumMapping.admission_year == normalized_year)
    if normalized_department:
        query = query.filter(CurriculumMapping.department == normalized_department)
    mapping = query.order_by(CurriculumMapping.updated_at.desc(), CurriculumMapping.id.desc()).first()
    if mapping:
        years = sorted({int(year) for year in mapping.curriculum_years})
        logger.info(
            "Curriculum mapping resolved: admission_year=%s, department=%s, curriculum_years=%s",
            normalized_year,
            normalized_department,
            years,
        )
        return years

    fallback_year = latest_curriculum_year(db, normalized_department)
    logger.info(
        "Curriculum mapping fallback used: admission_year=%s, department=%s, fallback_year=%s",
        normalized_year,
        normalized_department,
        fallback_year,
    )
    return [fallback_year] if fallback_year is not None else []


def normalize_admission_year(admission_year: int) -> int:
    """Normalize 23-style admission years to 2023."""
    return 2000 + admission_year if 0 <= admission_year < 100 else admission_year


def curriculum_mapping_exists(db: Session, *, admission_year: int, department: str | None = None) -> bool:
    """Return whether an explicit mapping exists for the supplied filter input."""
    normalized_year = normalize_admission_year(admission_year)
    normalized_department = department.strip() if department else None
    query = db.query(CurriculumMapping.id).filter(CurriculumMapping.admission_year == normalized_year)
    if normalized_department:
        query = query.filter(CurriculumMapping.department == normalized_department)
    return query.first() is not None


def latest_curriculum_year(db: Session, department: str | None = None) -> int | None:
    """Return the latest known curriculum year, optionally scoped to a department."""
    normalized_department = department.strip() if department else None
    document_query = db.query(func.max(Document.curriculum_year)).filter(Document.curriculum_year.isnot(None))
    if normalized_department:
        document_query = document_query.filter(Document.department == normalized_department)
    document_latest = document_query.scalar()
    if document_latest is not None:
        return int(document_latest)

    mapping_query = db.query(CurriculumMapping.curriculum_years)
    if normalized_department:
        mapping_query = mapping_query.filter(CurriculumMapping.department == normalized_department)
    mappings = mapping_query.all()
    years: list[int] = []
    for row in mappings:
        years.extend(int(year) for year in (row.curriculum_years or []))
    return max(years) if years else None
