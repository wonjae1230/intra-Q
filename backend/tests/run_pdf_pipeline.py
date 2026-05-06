from __future__ import annotations

import json
import sys
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.db.init_db import init_db
from app.db.session import SessionLocal
from app.models.chunk import Chunk
from app.models.document import Document
from app.routers.documents import extract_pdf_pages
from app.services.chat_service import generate_chat_response
from app.services.chunk_service import build_page_chunks


def run(pdf_path: Path) -> None:
    """Run the end-to-end PDF workflow against a real PDF file."""
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    init_db()

    pdf_bytes = pdf_path.read_bytes()
    pages = extract_pdf_pages(pdf_bytes)
    chunks = build_page_chunks(pages)

    db = SessionLocal()
    try:
        db.query(Chunk).delete()
        db.query(Document).delete()
        db.commit()

        document = Document(file_name=pdf_path.name, page_count=len(pages))
        db.add(document)
        db.flush()

        for chunk in chunks:
            db.add(
                Chunk(
                    document_id=document.id,
                    page_number=chunk["page_number"],
                    content=chunk["content"],
                )
            )

        db.commit()

        chat_response = generate_chat_response("회사 연차 정책은 어떻게 되나요?", db)

        output = {
            "upload_response": {
                "document_id": document.id,
                "file_name": document.file_name,
                "page_count": document.page_count,
                "chunk_count": len(chunks),
            },
            "chat_response": chat_response.model_dump(),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    default_pdf = base_dir / "fixtures" / "hr_policy.pdf"
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else default_pdf
    run(input_path)
