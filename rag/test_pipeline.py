"""Run a small end-to-end RAG check with sample HR policy chunks."""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.pipeline import embed_chunks, query  # noqa: E402


SAMPLE_CHUNKS = [
    {
        "content": "연차는 입사 1년 후 15일이 발생한다.",
        "document_id": 1,
        "file_name": "인사규정.pdf",
        "page": 3,
    },
    {
        "content": "병가는 연간 60일 이내로 사용 가능하다.",
        "document_id": 1,
        "file_name": "인사규정.pdf",
        "page": 5,
    },
]


def main() -> None:
    google_api_key = os.getenv("GOOGLE_API_KEY", "").strip()
    if not google_api_key or google_api_key == "AIza...":
        raise SystemExit("GOOGLE_API_KEY를 rag/.env에 실제 키로 설정한 뒤 실행하세요.")

    print(embed_chunks(SAMPLE_CHUNKS))
    print(query("연차는 몇 일이야?"))


if __name__ == "__main__":
    main()
