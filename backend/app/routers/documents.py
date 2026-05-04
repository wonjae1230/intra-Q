from __future__ import annotations

from typing import Any

import fitz
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chunk_service import build_page_chunks

router = APIRouter()


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """Extract page-by-page text from a PDF file."""
    try:
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise HTTPException(status_code=400, detail="유효한 PDF 파일이 아닙니다.") from exc

    pages: list[dict[str, Any]] = []
    with document:
        for index, page in enumerate(document, start=1):
            pages.append({"page": index, "text": page.get_text("text").strip()})

    return pages


@router.post("/upload")
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict[str, Any]:
    """Upload a PDF, extract its text, split it into chunks, and persist everything."""
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_extension = (file.filename or "").lower().endswith(".pdf")

    if not is_pdf_content_type and not is_pdf_extension:
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    pdf_bytes = await file.read()
    pages = extract_pdf_pages(pdf_bytes)
    chunks = build_page_chunks(pages)

    try:
        # Persist the document first so chunk rows can reference its id.
        document_row = Document(
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
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="문서 저장 중 오류가 발생했습니다.") from exc

    return {
        "document_id": document_row.id,
        "file_name": document_row.file_name,
        "page_count": document_row.page_count,
        "chunk_count": len(chunks),
    }



@router.get("/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    """Return document metadata and its chunks from the database."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다.")

    chunks = (
        db.query(Chunk)
        .filter(Chunk.document_id == document.id)
        .order_by(Chunk.page_number, Chunk.id)
        .all()
    )

    # Return only a preview of each chunk's content to keep responses small.
    PREVIEW_LEN = 200
    return {
        "document_id": document.id,
        "file_name": document.file_name,
        "page_count": document.page_count,
        "chunks": [
            {
                "id": c.id,
                "page_number": c.page_number,
                "preview": c.content[:PREVIEW_LEN],
                "len": len(c.content),
                "created_at": c.created_at.isoformat() if c.created_at else None,
            }
            for c in chunks
        ],
    }
