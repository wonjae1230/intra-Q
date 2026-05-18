from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.page_log import PageLog

logger = logging.getLogger(__name__)


def create_page_log(
    db: Session,
    *,
    document_id: int,
    page_id: str,
    page_number: int,
    page_type: str = "A",
    process_method: str = "pymupdf",
    validation_status: str = "pending",
) -> PageLog:
    """Create a page processing log row."""
    row = PageLog(
        document_id=document_id,
        page_id=page_id,
        page_number=page_number,
        page_type=page_type,
        process_method=process_method,
        validation_status=validation_status,
        processed_at=datetime.utcnow(),
    )
    db.add(row)
    db.flush()
    logger.info(
        "Page log created: document_id=%s, page_id=%s, page_number=%s, page_type=%s, method=%s",
        document_id,
        page_id,
        page_number,
        page_type,
        process_method,
    )
    return row


def update_page_log_validation(
    page_log: PageLog,
    *,
    validation_status: str,
    failure_reason: str | None = None,
) -> None:
    """Update page validation status and failure reason after subject validation."""
    page_log.validation_status = validation_status
    page_log.failure_reason = failure_reason
    page_log.processed_at = datetime.utcnow()
    logger.info(
        "Page log validation updated: page_id=%s, status=%s, failure_reason=%s",
        page_log.page_id,
        validation_status,
        failure_reason,
    )
