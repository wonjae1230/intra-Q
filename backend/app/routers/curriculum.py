from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.curriculum_mapping import CurriculumMapping
from app.models.user import User
from app.schemas.curriculum import (
    AdmissionYearExtractData,
    AdmissionYearExtractResponse,
    CurriculumMappingCreate,
    CurriculumMappingItem,
    CurriculumMappingListResponse,
    CurriculumMappingResponse,
    CurriculumResolveData,
    CurriculumResolveResponse,
)
from app.services.curriculum_service import (
    extract_admission_year,
    normalize_admission_year,
    resolve_curriculum_years,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/mappings",
    response_model=CurriculumMappingResponse,
    summary="Create or update a curriculum year mapping",
    description="Store the curriculum years that apply to a department and admission year.",
)
def upsert_curriculum_mapping(
    payload: CurriculumMappingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumMappingResponse:
    """Create or update a mapping row for operational curriculum filtering."""
    admission_year = normalize_admission_year(payload.admission_year)
    department = payload.department.strip()
    curriculum_years = sorted({int(year) for year in payload.curriculum_years})

    if not department:
        raise HTTPException(status_code=400, detail="학과명은 비어 있을 수 없습니다.")

    try:
        mapping = (
            db.query(CurriculumMapping)
            .filter(
                CurriculumMapping.admission_year == admission_year,
                CurriculumMapping.department == department,
            )
            .first()
        )
        if mapping:
            mapping.curriculum_years = curriculum_years
            logger.info(
                "Curriculum mapping updated: user_id=%s, admission_year=%s, department=%s, curriculum_years=%s",
                current_user.id,
                admission_year,
                department,
                curriculum_years,
            )
        else:
            mapping = CurriculumMapping(
                admission_year=admission_year,
                department=department,
                curriculum_years=curriculum_years,
            )
            db.add(mapping)
            logger.info(
                "Curriculum mapping created: user_id=%s, admission_year=%s, department=%s, curriculum_years=%s",
                current_user.id,
                admission_year,
                department,
                curriculum_years,
            )

        db.commit()
        db.refresh(mapping)
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        logger.error("Curriculum mapping save DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    return CurriculumMappingResponse(
        message="Curriculum mapping saved successfully",
        data=_to_mapping_item(mapping),
    )


@router.get(
    "/mappings",
    response_model=CurriculumMappingListResponse,
    summary="List curriculum mappings",
    description="Return stored curriculum mappings, optionally filtered by department.",
)
def list_curriculum_mappings(
    department: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumMappingListResponse:
    """List mapping rows for backend verification and Swagger-driven operation."""
    try:
        query = db.query(CurriculumMapping)
        if department:
            query = query.filter(CurriculumMapping.department == department.strip())
        rows = query.order_by(CurriculumMapping.department, CurriculumMapping.admission_year.desc()).all()
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Curriculum mapping list DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info("Curriculum mappings listed: user_id=%s, rows=%s", current_user.id, len(rows))
    return CurriculumMappingListResponse(
        message="Curriculum mappings retrieved successfully",
        data=[_to_mapping_item(row) for row in rows],
    )


@router.get(
    "/resolve",
    response_model=CurriculumResolveResponse,
    summary="Resolve curriculum years for an admission year",
    description="Return curriculum years for a department/admission year pair, falling back to the latest known year.",
)
def resolve_curriculum_year_filter(
    admission_year: int = Query(...),
    department: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CurriculumResolveResponse:
    """Resolve the curriculum year filter that can later be applied to RAG retrieval."""
    normalized_year = normalize_admission_year(admission_year)
    years = resolve_curriculum_years(db, admission_year=normalized_year, department=department)
    mapping_exists = (
        db.query(CurriculumMapping.id)
        .filter(
            CurriculumMapping.admission_year == normalized_year,
            CurriculumMapping.department == department.strip(),
        )
        .first()
        is not None
    )
    logger.info(
        "Curriculum years resolved via API: user_id=%s, admission_year=%s, department=%s, years=%s, fallback=%s",
        current_user.id,
        normalized_year,
        department,
        years,
        not mapping_exists,
    )
    return CurriculumResolveResponse(
        message="Curriculum years resolved successfully",
        data=CurriculumResolveData(
            admission_year=normalized_year,
            department=department.strip(),
            curriculum_years=years,
            used_fallback=not mapping_exists,
        ),
    )


@router.get(
    "/extract-admission-year",
    response_model=AdmissionYearExtractResponse,
    summary="Extract admission year from a question",
    description="Regex-based extraction for phrases such as '23학번'.",
)
def extract_admission_year_from_question(
    question: str = Query(...),
    current_user: User = Depends(get_current_user),
) -> AdmissionYearExtractResponse:
    """Expose the admission-year regex helper for Swagger verification."""
    admission_year = extract_admission_year(question)
    logger.info(
        "Admission year extracted via API: user_id=%s, admission_year=%s",
        current_user.id,
        admission_year,
    )
    return AdmissionYearExtractResponse(
        message="Admission year extracted successfully",
        data=AdmissionYearExtractData(question=question, admission_year=admission_year),
    )


def _to_mapping_item(mapping: CurriculumMapping) -> CurriculumMappingItem:
    return CurriculumMappingItem(
        id=mapping.id,
        admission_year=mapping.admission_year,
        department=mapping.department,
        curriculum_years=[int(year) for year in mapping.curriculum_years],
        created_at=mapping.created_at,
        updated_at=mapping.updated_at,
    )
