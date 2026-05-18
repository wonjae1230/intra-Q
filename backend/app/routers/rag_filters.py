from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.rag_filters import RagFilterResolveData, RagFilterResolveRequest, RagFilterResolveResponse
from app.services.curriculum_service import (
    curriculum_mapping_exists,
    extract_admission_year,
    latest_curriculum_year,
    normalize_admission_year,
    resolve_curriculum_years,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/resolve",
    response_model=RagFilterResolveResponse,
    summary="Resolve RAG curriculum filters",
    description="Calculate curriculum_year filters from a question, admission year, and optional department.",
)
def resolve_rag_filters(
    payload: RagFilterResolveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RagFilterResolveResponse:
    """Return filter values for RAG retrieval without modifying the RAG query path."""
    logger.info(
        "RAG filter resolve requested: user_id=%s, admission_year=%s, department=%s, question=%s",
        current_user.id,
        payload.admission_year,
        payload.department,
        payload.question,
    )
    try:
        admission_year = payload.admission_year
        if admission_year is None and payload.question:
            admission_year = extract_admission_year(payload.question)
        normalized_year = normalize_admission_year(admission_year) if admission_year is not None else None

        if normalized_year is not None:
            curriculum_years = resolve_curriculum_years(
                db,
                admission_year=normalized_year,
                department=payload.department,
            )
            explicit_mapping = curriculum_mapping_exists(
                db,
                admission_year=normalized_year,
                department=payload.department,
            )
            fallback_used = not explicit_mapping
        else:
            latest_year = latest_curriculum_year(db, payload.department)
            curriculum_years = [latest_year] if latest_year is not None else []
            fallback_used = True

    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("RAG filter resolve DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info(
        "RAG filters resolved: user_id=%s, admission_year=%s, department=%s, years=%s, fallback_used=%s",
        current_user.id,
        normalized_year,
        payload.department,
        curriculum_years,
        fallback_used,
    )
    return RagFilterResolveResponse(
        message="RAG filters resolved successfully",
        data=RagFilterResolveData(
            admission_year=normalized_year,
            department=payload.department.strip() if payload.department else None,
            curriculum_years=curriculum_years,
            fallback_used=fallback_used,
        ),
    )
