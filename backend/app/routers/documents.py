from __future__ import annotations

import logging
from typing import Any

import fitz
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.database.session import get_db
from app.models.chunk import Chunk
from app.models.document import Document
from app.models.user import User
from app.schemas.documents import (
    DocumentChunkItem,
    DocumentDeleteData,
    DocumentDeleteResponse,
    DocumentDetailData,
    DocumentDetailResponse,
    DocumentListItem,
    DocumentListResponse,
    DocumentUploadData,
    DocumentUploadResponse,
)
from app.services.chunk_service import build_page_chunks
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


@router.post(
    "/upload",
    response_model=DocumentUploadResponse,
    summary="Upload a PDF document",
    description="Upload a PDF file, extract text page by page, split into chunks, and store the document and chunks in SQLite.",
)
async def upload_document(
    file: UploadFile = File(...),
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
    try:
        pages = extract_pdf_pages(pdf_bytes)
        chunks = build_page_chunks(pages)

        # Persist the document first so chunk rows can reference its id.
        document_row = Document(
            user_id=current_user.id,
            file_name=file.filename or "unknown.pdf",
            page_count=len(pages),
        )
        db.add(document_row)
        db.flush()

        for chunk in chunks:
            db.add(
                Chunk(
                    document_id=document_row.id,
                    page_number=chunk["page_number"],
                    content=chunk["content"],
                )
            )

        db.commit()
        db.refresh(document_row)
    except (OperationalError, SQLAlchemyError) as exc:
        db.rollback()
        logger.error("Upload DB error: %s", exc, exc_info=True)
        raise HTTPException(status_code=503, detail="DB 연결 실패") from exc
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
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
                Document.uploaded_at,
                func.count(Chunk.id).label("chunk_count"),
            )
            .outerjoin(Chunk, Chunk.document_id == Document.id)
            .filter(Document.user_id == current_user.id)
            .group_by(Document.id, Document.file_name, Document.page_count, Document.uploaded_at)
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
