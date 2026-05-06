"""End-to-end RAG test: PDF 파일을 읽어 임베딩 후 대화형 질의응답."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import fitz  # PyMuPDF

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from rag.pipeline import embed_chunks, query  # noqa: E402


# ── PDF 파싱 ──────────────────────────────────────────────────────────────────

BBox = tuple[float, float, float, float]


def _as_bbox(raw_bbox: Any) -> BBox:
    values = tuple(float(value) for value in raw_bbox[:4])
    if len(values) != 4:
        raise ValueError("bbox must contain four values")
    return values


def _bbox_area(bbox: BBox) -> float:
    x0, y0, x1, y1 = bbox
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _intersection_area(first: BBox, second: BBox) -> float:
    x0 = max(first[0], second[0])
    y0 = max(first[1], second[1])
    x1 = min(first[2], second[2])
    y1 = min(first[3], second[3])
    return max(0.0, x1 - x0) * max(0.0, y1 - y0)


def _is_inside_table(block_bbox: BBox, table_bboxes: list[BBox]) -> bool:
    block_area = _bbox_area(block_bbox)
    if block_area == 0:
        return False

    center_x = (block_bbox[0] + block_bbox[2]) / 2
    center_y = (block_bbox[1] + block_bbox[3]) / 2

    for table_bbox in table_bboxes:
        is_center_inside = (
            table_bbox[0] <= center_x <= table_bbox[2]
            and table_bbox[1] <= center_y <= table_bbox[3]
        )
        if is_center_inside or _intersection_area(block_bbox, table_bbox) / block_area > 0.5:
            return True
    return False


def _clean_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().replace("|", r"\|")


def _format_table_as_markdown(rows: list[list[Any]]) -> str:
    normalized_rows = [[_clean_cell(cell) for cell in row] for row in rows]
    normalized_rows = [row for row in normalized_rows if any(row)]
    if not normalized_rows:
        return ""

    column_count = max(len(row) for row in normalized_rows)
    padded_rows = [row + [""] * (column_count - len(row)) for row in normalized_rows]

    if len(padded_rows) == 1:
        header = [f"Column {index}" for index in range(1, column_count + 1)]
        body_rows = padded_rows
    else:
        header = padded_rows[0]
        body_rows = padded_rows[1:]
        if not any(header):
            header = [f"Column {index}" for index in range(1, column_count + 1)]

    def render_row(row: list[str]) -> str:
        return "| " + " | ".join(cell or " " for cell in row) + " |"

    separator = ["---"] * column_count
    return "\n".join([render_row(header), render_row(separator), *(render_row(row) for row in body_rows)])


def _extract_tables(page: fitz.Page) -> list[dict[str, Any]]:
    if not hasattr(page, "find_tables"):
        return []

    try:
        table_finder = page.find_tables()
    except (RuntimeError, ValueError):
        return []

    table_items: list[dict[str, Any]] = []
    for table_index, table in enumerate(getattr(table_finder, "tables", []), start=1):
        markdown = _format_table_as_markdown(table.extract())
        if not markdown:
            continue

        table_items.append(
            {
                "kind": "table",
                "bbox": _as_bbox(table.bbox),
                "content": f"[표 {table_index}]\n{markdown}",
            }
        )
    return table_items


def _extract_page_items(page: fitz.Page) -> list[dict[str, Any]]:
    table_items = _extract_tables(page)
    table_bboxes = [item["bbox"] for item in table_items]

    text_items: list[dict[str, Any]] = []
    for block in page.get_text("blocks"):
        if len(block) < 5:
            continue

        block_type = block[6] if len(block) > 6 else 0
        if block_type != 0:
            continue

        text = re.sub(r"[ \t]+", " ", str(block[4])).strip()
        if not text:
            continue

        block_bbox = _as_bbox(block)
        if _is_inside_table(block_bbox, table_bboxes):
            continue

        text_items.append({"kind": "text", "bbox": block_bbox, "content": text})

    return sorted([*text_items, *table_items], key=lambda item: (item["bbox"][1], item["bbox"][0]))


def _split_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be greater than or equal to 0 and less than chunk_size")

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append(chunk_text)
        start += chunk_size - overlap
    return chunks


def extract_chunks_from_pdf(pdf_path: str, chunk_size: int = 500, overlap: int = 50) -> list[dict]:
    """PDF에서 텍스트와 표를 추출하고 청크로 분할한다."""
    doc = fitz.open(pdf_path)
    file_name = Path(pdf_path).name
    chunks: list[dict] = []
    document_id = abs(hash(file_name)) % 100000

    try:
        for page_num, page in enumerate(doc, start=1):
            for item in _extract_page_items(page):
                for chunk_text in _split_text(item["content"], chunk_size, overlap):
                    chunks.append({
                        "content": chunk_text,
                        "document_id": document_id,
                        "file_name": file_name,
                        "page": page_num,
                        "content_type": item["kind"],
                    })
    finally:
        doc.close()
    return chunks


# ── 메인 ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not os.getenv("GOOGLE_API_KEY", "").strip():
        raise SystemExit("GOOGLE_API_KEY를 rag/.env에 설정하세요.")

    # PDF 경로 입력
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
    else:
        pdf_path = input("테스트할 PDF 경로를 입력하세요: ").strip()

    if not Path(pdf_path).exists():
        raise SystemExit(f"파일을 찾을 수 없습니다: {pdf_path}")

    # 1. PDF → 청크 추출
    print(f"\n[1] PDF 파싱 중: {pdf_path}")
    chunks = extract_chunks_from_pdf(pdf_path)
    print(f"    → 총 {len(chunks)}개 청크 추출 완료")

    # 2. 임베딩 → Chroma 저장
    print("\n[2] 임베딩 생성 및 벡터 DB 저장 중...")
    result = embed_chunks(chunks)
    print(f"    → {result['stored_count']}개 청크 저장 완료")

    # 3. 대화형 질의응답
    print("\n[3] 질문을 입력하세요. 종료: 'q' 또는 'exit'\n")
    while True:
        question = input("질문 > ").strip()
        if question.lower() in ("q", "exit", "quit", "종료"):
            print("종료합니다.")
            break
        if not question:
            continue

        result = query(question)
        print(f"\n답변: {result['answer']}")
        if result["sources"]:
            print("출처:")
            for s in result["sources"]:
                print(f"  - {s['file_name']} p.{s['page']}")
        else:
            print("출처: 관련 문서를 찾지 못했습니다.")
        print()


if __name__ == "__main__":
    main()
