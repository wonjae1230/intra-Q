from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.page_log import PageLog
from app.models.subject import Subject
from app.services.page_processor import process_page
from app.services.validation_service import validate_subject

logger = logging.getLogger(__name__)


def retry_page_processing(db: Session, *, page_id: str) -> PageLog | None:
    """Retry one failed/manual page with a mock processing payload.

    TODO: Replace the mock page content with stored source PDF page re-extraction
    when original PDF storage is introduced. Gemini Vision must remain disabled
    until an explicit integration task enables it.
    """
    page_log = db.query(PageLog).filter(PageLog.page_id == page_id).first()
    if not page_log:
        return None

    document = db.query(Document).filter(Document.id == page_log.document_id).first()
    if not document:
        page_log.validation_status = "failed"
        page_log.failure_reason = "Document not found for retry"
        page_log.processed_at = datetime.utcnow()
        logger.warning("Retry failed: page_id=%s, document_id=%s missing", page_id, page_log.document_id)
        return page_log

    logger.info(
        "Retry requested: page_id=%s, document_id=%s, page_type=%s",
        page_id,
        page_log.document_id,
        page_log.page_type,
    )
    mock_content = _build_mock_page_content(page_log, document)
    result = process_page(page_log.page_type, mock_content)
    page_log.process_method = result["method"]
    page_log.processed_at = datetime.utcnow()

    db.query(Subject).filter(
        Subject.document_id == page_log.document_id,
        Subject.page_id == page_log.page_id,
    ).delete(synchronize_session=False)

    if result.get("requires_gemini"):
        page_log.validation_status = "manual_required"
        page_log.failure_reason = result.get("failure_reason") or "Gemini Vision required"
        logger.info("Retry completed with manual_required: page_id=%s", page_id)
        return page_log

    payload = _build_mock_subject_payload(page_log, document)
    validation = validate_subject(payload)
    if validation["valid"]:
        db.add(
            Subject(
                document_id=page_log.document_id,
                page_id=page_log.page_id,
                curriculum_year=document.curriculum_year,
                college=document.college,
                department=document.department,
                subject_code=payload["subject_code"],
                subject_name=payload["subject_name"],
                category=payload["category"],
                credit=payload["credit"],
                semester=payload["semester"],
                raw_json=payload,
                validation_status="passed",
            )
        )
        page_log.validation_status = "passed"
        page_log.failure_reason = None
        logger.info("Retry completed successfully: page_id=%s", page_id)
    else:
        page_log.validation_status = "failed"
        page_log.failure_reason = "; ".join(validation["errors"])
        logger.warning("Retry validation failed: page_id=%s, errors=%s", page_id, validation["errors"])

    return page_log


def _build_mock_page_content(page_log: PageLog, document: Document) -> dict:
    return {
        "page": page_log.page_number,
        "text": f"{page_log.page_id} retry mock page for {document.file_name}",
    }


def _build_mock_subject_payload(page_log: PageLog, document: Document) -> dict:
    subject_code = f"{page_log.page_number % 1000000:06d}"
    if subject_code == "000000":
        subject_code = "000001"
    return {
        "page_id": page_log.page_id,
        "curriculum_year": document.curriculum_year,
        "college": document.college,
        "department": document.department,
        "subject_code": subject_code,
        "subject_name": "재처리 Mock 과목",
        "category": "전공선택",
        "credit": 3,
        "semester": "1학기",
    }
