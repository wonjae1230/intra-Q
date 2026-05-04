from __future__ import annotations

from typing import Any

import fitz
from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()


def extract_pdf_pages(pdf_bytes: bytes) -> list[dict[str, Any]]:
    """PDF 파일을 페이지 단위로 열고 텍스트를 추출한다."""
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
async def upload_document(file: UploadFile = File(...)) -> dict[str, Any]:
    """multipart/form-data로 업로드된 PDF에서 텍스트를 추출해 반환한다."""
    is_pdf_content_type = file.content_type == "application/pdf"
    is_pdf_extension = (file.filename or "").lower().endswith(".pdf")

    if not is_pdf_content_type and not is_pdf_extension:
        raise HTTPException(status_code=400, detail="PDF 파일만 업로드할 수 있습니다.")

    pdf_bytes = await file.read()
    pages = extract_pdf_pages(pdf_bytes)

    return {"file_name": file.filename, "pages": pages}
