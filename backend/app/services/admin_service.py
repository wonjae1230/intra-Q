from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy.orm import Query, Session

from app.models.page_log import PageLog


ALLOWED_VALIDATION_STATUSES = {"pending", "passed", "failed", "manual_required"}
ALLOWED_PAGE_TYPES = {"A", "B", "C", "D"}


def query_page_logs(
    db: Session,
    *,
    document_id: int | None = None,
    validation_status: str | None = None,
    page_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[PageLog]:
    """Return page logs with admin filters applied."""
    query = _base_page_log_query(db, document_id=document_id)
    if validation_status:
        query = query.filter(PageLog.validation_status == validation_status)
    if page_type:
        query = query.filter(PageLog.page_type == page_type)

    # Sort by latest processing time first so recent failures/retries are visible first.
    return query.order_by(PageLog.processed_at.desc(), PageLog.id.desc()).offset(offset).limit(limit).all()


def query_failed_pages(
    db: Session,
    *,
    document_id: int | None = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[PageLog]:
    """Return only pages requiring attention."""
    query = _base_page_log_query(db, document_id=document_id).filter(
        PageLog.validation_status.in_(["failed", "manual_required"])
    )
    # Sort by latest processing time first so recent failures/retries are visible first.
    return query.order_by(PageLog.processed_at.desc(), PageLog.id.desc()).offset(offset).limit(limit).all()


def _base_page_log_query(db: Session, *, document_id: int | None = None) -> Query:
    query = db.query(PageLog)
    if document_id is not None:
        query = query.filter(PageLog.document_id == document_id)
    return query
