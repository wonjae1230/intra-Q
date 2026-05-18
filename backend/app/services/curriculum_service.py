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


def resolve_curriculum_years(db: Session, *, admission_year: int, department: str) -> list[int]:
    """Resolve curriculum years for a department/admission year pair with latest-year fallback."""
    normalized_year = normalize_admission_year(admission_year)
    normalized_department = department.strip()
    logger.info(
        "Curriculum mapping lookup: admission_year=%s, department=%s",
        normalized_year,
        normalized_department,
    )

    mapping = (
        db.query(CurriculumMapping)
        .filter(
            CurriculumMapping.admission_year == normalized_year,
            CurriculumMapping.department == normalized_department,
        )
        .order_by(CurriculumMapping.updated_at.desc(), CurriculumMapping.id.desc())
        .first()
    )
    if mapping:
        years = sorted({int(year) for year in mapping.curriculum_years})
        logger.info(
            "Curriculum mapping resolved: admission_year=%s, department=%s, curriculum_years=%s",
            normalized_year,
            normalized_department,
            years,
        )
        return years

    fallback_year = _latest_curriculum_year(db, normalized_department)
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


def _latest_curriculum_year(db: Session, department: str) -> int | None:
    document_latest = (
        db.query(func.max(Document.curriculum_year))
        .filter(Document.curriculum_year.isnot(None), Document.department == department)
        .scalar()
    )
    if document_latest is not None:
        return int(document_latest)

    mappings = db.query(CurriculumMapping.curriculum_years).filter(CurriculumMapping.department == department).all()
    years: list[int] = []
    for row in mappings:
        years.extend(int(year) for year in (row.curriculum_years or []))
    return max(years) if years else None
