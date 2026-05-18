from __future__ import annotations

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.curriculum_mapping import CurriculumMapping
from app.models.user import User
from app.schemas.admin import (
    AdminCurriculumMappingListResponse,
    AdminCurriculumMappingResponse,
    AdminPageLogItem,
    AdminPageLogListResponse,
    CurriculumMappingPatch,
    PageRetryData,
    PageRetryResponse,
)
from app.schemas.curriculum import CurriculumMappingItem
from app.services.admin_service import (
    ALLOWED_PAGE_TYPES,
    ALLOWED_VALIDATION_STATUSES,
    query_failed_pages,
    query_page_logs,
)
from app.services.curriculum_service import normalize_admission_year
from app.services.retry_service import retry_page_processing

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "/page-logs",
    response_model=AdminPageLogListResponse,
    summary="Admin page log list",
    description="Return page-level PDF processing logs with optional filters. Requires login; TODO: restrict to admin role.",
)
def list_page_logs(
    document_id: int | None = Query(default=None),
    validation_status: str | None = Query(default=None),
    page_type: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminPageLogListResponse:
    """List page logs for administrators. TODO: enforce admin role when roles exist."""
    if validation_status and validation_status not in ALLOWED_VALIDATION_STATUSES:
        raise HTTPException(status_code=400, detail="잘못된 validation_status 값입니다.")
    if page_type and page_type not in ALLOWED_PAGE_TYPES:
        raise HTTPException(status_code=400, detail="잘못된 page_type 값입니다.")

    try:
        rows = query_page_logs(
            db,
            document_id=document_id,
            validation_status=validation_status,
            page_type=page_type,
            limit=limit,
            offset=offset,
        )
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Admin page_log query DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info(
        "Page logs retrieved: user_id=%s, document_id=%s, validation_status=%s, page_type=%s, rows=%s",
        current_user.id,
        document_id,
        validation_status,
        page_type,
        len(rows),
    )
    return AdminPageLogListResponse(
        message="Page logs retrieved successfully",
        data=[_to_page_log_item(row) for row in rows],
    )


@router.get(
    "/failed-pages",
    response_model=AdminPageLogListResponse,
    summary="Admin failed page list",
    description="Return pages with failed or manual_required validation status. Requires login; TODO: restrict to admin role.",
)
def list_failed_pages(
    document_id: int | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminPageLogListResponse:
    """List pages needing administrator attention. TODO: enforce admin role when roles exist."""
    try:
        rows = query_failed_pages(db, document_id=document_id, limit=limit, offset=offset)
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Admin failed page query DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info("Failed pages retrieved: user_id=%s, document_id=%s, rows=%s", current_user.id, document_id, len(rows))
    return AdminPageLogListResponse(
        message="Failed pages retrieved successfully",
        data=[_to_page_log_item(row) for row in rows],
    )


@router.post(
    "/pages/{page_id}/retry",
    response_model=PageRetryResponse,
    summary="Retry a failed page",
    description="Retry one page with the mock backend processing pipeline. No Gemini API call is made.",
)
def retry_page(
    page_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PageRetryResponse:
    """Retry page processing. TODO: enforce admin role when roles exist."""
    logger.info("Retry request received: user_id=%s, page_id=%s", current_user.id, page_id)
    try:
        page_log = retry_page_processing(db, page_id=page_id)
        if not page_log:
            logger.info("Retry page not found: user_id=%s, page_id=%s", current_user.id, page_id)
            raise HTTPException(status_code=404, detail="page_id를 찾을 수 없습니다.")
        db.commit()
        db.refresh(page_log)
    except HTTPException:
        db.rollback()
        raise
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        logger.error("Retry page DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info(
        "Retry completed: user_id=%s, page_id=%s, status=%s, failure_reason=%s",
        current_user.id,
        page_id,
        page_log.validation_status,
        page_log.failure_reason,
    )
    return PageRetryResponse(
        message="Page retry completed",
        data=PageRetryData(
            page_id=page_log.page_id,
            document_id=page_log.document_id,
            validation_status=page_log.validation_status,
            failure_reason=page_log.failure_reason,
        ),
    )


@router.get(
    "/curriculum-mappings",
    response_model=AdminCurriculumMappingListResponse,
    summary="Admin curriculum mapping list",
    description="Return curriculum mappings filtered by department and/or admission year.",
)
def list_admin_curriculum_mappings(
    department: str | None = Query(default=None),
    admission_year: int | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminCurriculumMappingListResponse:
    """List curriculum mappings. TODO: enforce admin role when roles exist."""
    try:
        query = db.query(CurriculumMapping)
        if department:
            query = query.filter(CurriculumMapping.department == department.strip())
        if admission_year is not None:
            query = query.filter(CurriculumMapping.admission_year == normalize_admission_year(admission_year))
        rows = query.order_by(CurriculumMapping.department, CurriculumMapping.admission_year.desc()).all()
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Admin curriculum mapping query DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info(
        "Curriculum mappings retrieved: user_id=%s, department=%s, admission_year=%s, rows=%s",
        current_user.id,
        department,
        admission_year,
        len(rows),
    )
    return AdminCurriculumMappingListResponse(
        message="Curriculum mappings retrieved successfully",
        data=[_to_mapping_item(row) for row in rows],
    )


@router.patch(
    "/curriculum-mappings/{mapping_id}",
    response_model=AdminCurriculumMappingResponse,
    summary="Update a curriculum mapping",
    description="Update department and/or curriculum_years for one mapping row.",
)
def update_admin_curriculum_mapping(
    mapping_id: int,
    payload: CurriculumMappingPatch,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AdminCurriculumMappingResponse:
    """Patch a curriculum mapping. TODO: enforce admin role when roles exist."""
    try:
        mapping = db.query(CurriculumMapping).filter(CurriculumMapping.id == mapping_id).first()
        if not mapping:
            raise HTTPException(status_code=404, detail="mapping id를 찾을 수 없습니다.")

        if payload.department is not None:
            department = payload.department.strip()
            if not department:
                raise HTTPException(status_code=400, detail="학과명은 비어 있을 수 없습니다.")
            mapping.department = department

        if payload.curriculum_years is not None:
            if not payload.curriculum_years:
                raise HTTPException(status_code=400, detail="curriculum_years는 비어 있을 수 없습니다.")
            mapping.curriculum_years = sorted({int(year) for year in payload.curriculum_years})

        mapping.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(mapping)
    except HTTPException:
        db.rollback()
        raise
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        logger.error("Admin curriculum mapping update DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info(
        "Curriculum mapping updated: user_id=%s, mapping_id=%s, department=%s, curriculum_years=%s",
        current_user.id,
        mapping.id,
        mapping.department,
        mapping.curriculum_years,
    )
    return AdminCurriculumMappingResponse(
        message="Curriculum mapping updated successfully",
        data=_to_mapping_item(mapping),
    )


def _to_page_log_item(row) -> AdminPageLogItem:
    return AdminPageLogItem(
        id=row.id,
        page_id=row.page_id,
        document_id=row.document_id,
        page_number=row.page_number,
        page_type=row.page_type,
        process_method=row.process_method,
        validation_status=row.validation_status,
        failure_reason=row.failure_reason,
        processed_at=row.processed_at,
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
