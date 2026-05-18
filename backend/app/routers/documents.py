from __future__ import annotations

import logging
import re
from typing import Any

import fitz
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.page_log import PageLog
from app.models.subject import Subject
from app.models.user import User
from app.schemas.documents import (
    DocumentChunkItem,
    DocumentDeleteData,
    DocumentDeleteResponse,
    DocumentDetailData,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    PageLogItem,
    SubjectItem,
    DocumentUploadData,
    DocumentUploadResponse,
)
from app.services.chunk_service import build_page_chunks
from app.services.page_log_service import create_page_log, update_page_log_validation
from app.services.validation_service import ALLOWED_CATEGORIES, ALLOWED_SEMESTERS, validate_subject
from rag.pipeline import delete_document_embeddings, embed_chunks

router = APIRouter()
logger = logging.getLogger(__name__)


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract page-by-page text from a PDF file."""
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.warning("PDF extraction failed: %s", exc)
        raise HTTPException(status_code=422, detail="PDF 텍스트 추출 실패") from exc

    pages: list[dict[str, Any]] = []
    with document:
        for index, page in enumerate(document, start=1):
            pages.append({"page": index, "text": page.get_text("text").strip()})

    return pages


def build_page_id(curriculum_year: int | None, page_number: int) -> str:
    """Build a stable page identifier for curriculum processing logs."""
    year_prefix = str(curriculum_year) if curriculum_year else "unknown"
    return f"{year_prefix}_p{page_number}"


def extract_subject_payloads_from_page(
    page: dict[str, Any],
    *,
    page_id: str,
    curriculum_year: int | None,
    college: str | None,
    department: str | None,
) -> list[dict[str, Any]]:
    """Build conservative rule-based subject payloads until AI extraction is added.

    This is intentionally simple: it only emits rows for lines containing a 6-digit
    subject code. Missing fields are left empty so validation can flag them.
    """
    payloads: list[dict[str, Any]] = []
    for line in str(page.get("text") or "").splitlines():
        tokens = line.strip().split()
        if not tokens:
            continue

        for index, token in enumerate(tokens):
            if not re.fullmatch(r"\d{6}", token):
                continue

            tail = tokens[index + 1 :]
            subject_name = tail[0] if tail else "UNKNOWN_SUBJECT"
            category = next((value for value in tail if value in ALLOWED_CATEGORIES), None)
            semester = next((value for value in tail if value in ALLOWED_SEMESTERS), None)
            credit_token = next((value for value in tail if re.fullmatch(r"[1-6]", value)), None)
            credit = int(credit_token) if credit_token else None

            payload = {
                "page_id": page_id,
                "curriculum_year": curriculum_year,
                "college": college,
                "department": department,
                "subject_code": token,
                "subject_name": subject_name,
                "category": category,
                "credit": credit,
                "semester": semester,
            }
            payloads.append(payload)
            break

    return payloads


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a PDF document",
    description="Upload a PDF file, extract text page by page, split into chunks, and store the document and chunks in SQLite.",
)
async def upload_document(
    file: UploadFile = File(...),
    curriculum_year: int | None = Form(default=None),
    college: str | None = Form(default=None),
    department: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentUploadResponse:
    """Upload a PDF, extract its text, split it into chunks, and persist everything."""
    logger.info(
        "Upload request received: user_id=%s, filename=%s, content_type=%s",
        current_user.id,
        file.filename,
        file.content_type,
    )
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_extension = (file.filename or "").lower().endswith(".pdf")

    if not is_pdf_content_type and not is_pdf_extension:
        logger.warning("Invalid file upload rejected: filename=%s, content_type=%s", file.filename, file.content_type)
        raise HTTPException(status_code=400, detail="잘못된 파일 업로드입니다. PDF 파일만 업로드할 수 있습니다.")

    pdf_bytes = await file.read()
    page_log_count = 0
    subject_count = 0
    validation_failed_count = 0
    document_row: Document | None = None
    document_id: int | None = None
    try:
        pages = extract_pdf_pages(pdf_bytes)
        chunks = build_page_chunks(pages)
        source_file = file.filename or "unknown.pdf"

        # Persist the document first so chunk rows can reference its id.
        document_row = Document(
            user_id=current_user.id,
            file_name=source_file,
            page_count=len(pages),
            curriculum_year=curriculum_year,
            college=college,
            department=department,
            source_file=source_file,
            processing_status="uploaded",
        )
        db.add(document_row)
        db.commit()
        db.refresh(document_row)
        document_id = document_row.id
        logger.info(
            "Document registered: user_id=%s, document_id=%s, source_file=%s",
            current_user.id,
            document_row.id,
            source_file,
        )

        document_row.processing_status = "processing"
        db.commit()
        db.refresh(document_row)
        logger.info("Document processing_status changed: document_id=%s, status=processing", document_row.id)

        for chunk in chunks:
            db.add(
                Chunk(
                    document_id=document_row.id,
                    page_number=chunk["page_number"],
                    content=chunk["content"],
                )
            )

        for page in pages:
            page_number = int(page["page"])
            page_id = build_page_id(curriculum_year, page_number)
            page_log = create_page_log(
                db,
                document_id=document_row.id,
                page_id=page_id,
                page_number=page_number,
                page_type="A",
                process_method="pymupdf",
            )
            page_log_count += 1

            subject_payloads = extract_subject_payloads_from_page(
                page,
                page_id=page_id,
                curriculum_year=curriculum_year,
                college=college,
                department=department,
            )
            page_errors: list[str] = []

            for payload in subject_payloads:
                validation = validate_subject(payload)
                validation_status = "passed" if validation["valid"] else "failed"
                if validation["valid"]:
                    logger.info(
                        "Subject validation passed: document_id=%s, page_id=%s, subject_code=%s",
                        document_row.id,
                        page_id,
                        payload["subject_code"],
                    )
                else:
                    validation_failed_count += 1
                    error_text = "; ".join(validation["errors"])
                    page_errors.append(f"{payload['subject_code']}: {error_text}")
                    logger.warning(
                        "Subject validation failed: document_id=%s, page_id=%s, subject_code=%s, errors=%s",
                        document_row.id,
                        page_id,
                        payload["subject_code"],
                        validation["errors"],
                    )

                db.add(
                    Subject(
                        document_id=document_row.id,
                        page_id=page_id,
                        curriculum_year=payload.get("curriculum_year"),
                        college=payload.get("college"),
                        department=payload.get("department"),
                        subject_code=payload["subject_code"],
                        subject_name=payload["subject_name"],
                        category=payload.get("category"),
                        credit=payload.get("credit"),
                        semester=payload.get("semester"),
                        raw_json=payload,
                        validation_status=validation_status,
                    )
                )
                subject_count += 1
                logger.info(
                    "Subject saved: document_id=%s, page_id=%s, subject_code=%s, validation_status=%s",
                    document_row.id,
                    page_id,
                    payload["subject_code"],
                    validation_status,
                )

            if page_errors:
                update_page_log_validation(
                    page_log,
                    validation_status="failed",
                    failure_reason=" | ".join(page_errors),
                )
            else:
                update_page_log_validation(page_log, validation_status="passed")

        document_row.processing_status = "completed"
        logger.info("Document processing_status changed: document_id=%s, status=completed", document_row.id)

        db.commit()
        db.refresh(document_row)
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        if document_id is not None:
            try:
                db.query(Document).filter(Document.id == document_id).update({"processing_status": "failed"})
                db.commit()
                logger.info("Document processing_status changed: document_id=%s, status=failed", document_id)
            except SQLAlchemyError:
                db.rollback()
                logger.exception("Failed to mark document as failed: document_id=%s", document_id)
        logger.error("Upload DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc
    except HTTPException:
        db.rollback()
        if document_id is not None:
            try:
                db.query(Document).filter(Document.id == document_id).update({"processing_status": "failed"})
                db.commit()
                logger.info("Document processing_status changed: document_id=%s, status=failed", document_id)
            except SQLAlchemyError:
                db.rollback()
                logger.exception("Failed to mark document as failed: document_id=%s", document_id)
        raise
    except Exception as exc:
        db.rollback()
        if document_id is not None:
            try:
                db.query(Document).filter(Document.id == document_id).update({"processing_status": "failed"})
                db.commit()
                logger.info("Document processing_status changed: document_id=%s, status=failed", document_id)
            except SQLAlchemyError:
                db.rollback()
                logger.exception("Failed to mark document as failed: document_id=%s", document_id)
        logger.exception("Upload server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc

    embedding_status = "success"
    embedding_message = None
    # 파일명(확장자 제외)을 청크 앞에 prefix로 붙여 임베딩에 포함시킴.
    # 파일명에만 있는 문서 식별 키워드(예: '인초강', '강민준')가 벡터 검색에 반영되도록.
    stem = document_row.file_name.rsplit(".", 1)[0]
    embedding_payload = [
        {
            "content": f"[{stem}]\n{chunk['content']}",
            "document_id": document_row.id,
            "file_name": document_row.file_name,
            "page": chunk["page_number"],
        }
        for chunk in chunks
    ]

    try:
        embedding_result = embed_chunks(embedding_payload)
        logger.info(
            "RAG embedding succeeded: document_id=%s, stored_count=%s, ids=%s",
            document_row.id,
            embedding_result.get("stored_count"),
            embedding_result.get("ids"),
        )
    except Exception as exc:
        embedding_status = "failed"
        embedding_message = "RAG embedding failed; document stored in SQLite only."
        logger.error("RAG embedding failed: document_id=%s, error=%s", document_row.id, exc, exc_info=True)

    logger.info(
        "Upload succeeded: user_id=%s, document_id=%s, filename=%s, chunks=%s",
        current_user.id,
        document_row.id,
        document_row.file_name,
        len(chunks),
    )
    return DocumentUploadResponse(
        message="Document uploaded successfully",
        data=DocumentUploadData(
            document_id=document_row.id,
            file_name=document_row.file_name,
            page_count=document_row.page_count,
            chunk_count=len(chunks),
            curriculum_year=document_row.curriculum_year,
            college=document_row.college,
            department=document_row.department,
            source_file=document_row.source_file,
            processing_status=document_row.processing_status,
            page_log_count=page_log_count,
            subject_count=subject_count,
            validation_failed_count=validation_failed_count,
            embedding_status=embedding_status,
            embedding_message=embedding_message,
        ),
    )


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List uploaded documents",
    description="Return all uploaded documents ordered by latest upload first, including chunk counts for the frontend list view.",
)
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentListResponse:
    """Return the uploaded document list for the frontend management screen."""
    try:
        rows = (
            db.query(
                Document.id,
                Document.file_name,
                Document.page_count,
                Document.curriculum_year,
                Document.college,
                Document.department,
                Document.source_file,
                Document.processing_status,
                Document.uploaded_at,
                func.count(Chunk.id).label("chunk_count"),
            )
            .outerjoin(Chunk, Chunk.document_id == Document.id)
            .filter(Document.user_id == current_user.id)
            .group_by(
                Document.id,
                Document.file_name,
                Document.page_count,
                Document.curriculum_year,
                Document.college,
                Document.department,
                Document.source_file,
                Document.processing_status,
                Document.uploaded_at,
            )
            .order_by(Document.uploaded_at.desc(), Document.id.desc())
            .all()
        )
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("List documents DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    logger.info("User documents retrieved: user_id=%s, rows=%s", current_user.id, len(rows))
    return DocumentListResponse(
        message="Documents retrieved successfully",
        data=[
            DocumentListItem(
                id=row.id,
                file_name=row.file_name,
                page_count=row.page_count,
                chunk_count=int(row.chunk_count),
                curriculum_year=row.curriculum_year,
                college=row.college,
                department=row.department,
                source_file=row.source_file,
                processing_status=row.processing_status,
                uploaded_at=row.uploaded_at,
            )
            for row in rows
        ],
    )



@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    summary="Get a document with chunk previews",
    description="Return one stored document and its chunk previews for debugging and frontend display.",
)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDetailResponse:
    """Return document metadata and its chunks from the database."""
    try:
        document = db.query(Document).filter(Document.id == document_id).first()
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Get document DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    if not document:
        logger.info("Document not found: document_id=%s", document_id)
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    if document.user_id != current_user.id:
        logger.warning(
            "Unauthorized document access attempt: user_id=%s, document_id=%s, owner_user_id=%s",
            current_user.id,
            document_id,
            document.user_id,
        )
        raise HTTPException(status_code=403, detail="해당 문서에 접근할 권한이 없습니다.")

    try:
        chunks = (
            db.query(Chunk)
            .filter(Chunk.document_id == document.id)
            .order_by(Chunk.page_number, Chunk.id)
            .all()
        )
        page_logs = (
            db.query(PageLog)
            .filter(PageLog.document_id == document.id)
            .order_by(PageLog.page_number, PageLog.id)
            .all()
        )
        subjects = (
            db.query(Subject)
            .filter(Subject.document_id == document.id)
            .order_by(Subject.page_id, Subject.id)
            .all()
        )
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Get document chunk query DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    # Return only a preview of each chunk's content to keep responses small.
    PREVIEW_LEN = 200
    return DocumentDetailResponse(
        message="Document retrieved successfully",
        data=DocumentDetailData(
            document_id=document.id,
            file_name=document.file_name,
            page_count=document.page_count,
            curriculum_year=document.curriculum_year,
            college=document.college,
            department=document.department,
            source_file=document.source_file,
            processing_status=document.processing_status,
            chunks=[
                DocumentChunkItem(
                    id=c.id,
                    page_number=c.page_number,
                    preview=c.content[:PREVIEW_LEN],
                    len=len(c.content),
                    created_at=c.created_at,
                )
                for c in chunks
            ],
            page_logs=[
                PageLogItem(
                    id=log.id,
                    page_id=log.page_id,
                    page_number=log.page_number,
                    page_type=log.page_type,
                    process_method=log.process_method,
                    validation_status=log.validation_status,
                    failure_reason=log.failure_reason,
                    processed_at=log.processed_at,
                )
                for log in page_logs
            ],
            subjects=[
                SubjectItem(
                    id=subject.id,
                    page_id=subject.page_id,
                    curriculum_year=subject.curriculum_year,
                    college=subject.college,
                    department=subject.department,
                    subject_code=subject.subject_code,
                    subject_name=subject.subject_name,
                    category=subject.category,
                    credit=subject.credit,
                    semester=subject.semester,
                    raw_json=subject.raw_json,
                    validation_status=subject.validation_status,
                    created_at=subject.created_at,
                )
                for subject in subjects
            ],
        ),
    )


@router.delete(
    "/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document and its chunks",
    description="Delete the selected document and all related chunks from SQLite. The response includes the number of deleted chunks.",
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentDeleteResponse:
    """Delete a document and its related chunks in a transaction-safe order."""
    logger.info("Delete request received: user_id=%s, document_id=%s", current_user.id, document_id)

    try:
        document = db.query(Document).filter(Document.id == document_id).first()
    except (OperationalError, SQLAlchemyError) as exc:
        logger.error("Delete document lookup DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc

    if not document:
        logger.info("Delete request for missing document: document_id=%s", document_id)
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    if document.user_id != current_user.id:
        logger.warning(
            "Unauthorized document delete attempt: user_id=%s, document_id=%s, owner_user_id=%s",
            current_user.id,
            document_id,
            document.user_id,
        )
        raise HTTPException(status_code=403, detail="해당 문서에 접근할 권한이 없습니다.")

    deleted_document_id = document.id

    try:
        db.query(Subject).filter(Subject.document_id == deleted_document_id).delete(synchronize_session=False)
        db.query(PageLog).filter(PageLog.document_id == deleted_document_id).delete(synchronize_session=False)
        deleted_chunks = db.query(Chunk).filter(Chunk.document_id == deleted_document_id).delete(synchronize_session=False)

        db.query(Document).filter(Document.id == deleted_document_id).delete(synchronize_session=False)

        db.commit()
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        logger.error("Delete DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail="DB 삭제 실패") from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Delete server error")
        raise HTTPException(status_code=500, detail="내부 서버 오류") from exc

    try:
        deleted_embeddings = delete_document_embeddings(deleted_document_id)
        logger.info(
            "RAG embedding cleanup succeeded: document_id=%s, deleted_embeddings=%s",
            deleted_document_id,
            deleted_embeddings.get("deleted_count"),
        )
    except Exception as exc:
        logger.error("RAG embedding cleanup failed: document_id=%s, error=%s", deleted_document_id, exc, exc_info=True)

    logger.info("Delete succeeded: document_id=%s, deleted_chunks=%s", deleted_document_id, deleted_chunks)
    return DocumentDeleteResponse(
        message="Document deleted successfully",
        data=DocumentDeleteData(document_id=deleted_document_id, deleted_chunks=int(deleted_chunks)),
    )
