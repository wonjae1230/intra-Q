from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Any

import fitz

from rag.test_pipeline import extract_chunks_from_pdf


KOREAN_FONT_PATHS = [
    Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
    Path("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
]


def _insert_text(page: fitz.Page, point: tuple[float, float], text: str, font_name: str | None, font_size: int) -> None:
    options: dict[str, Any] = {"fontsize": font_size}
    if font_name:
        options["fontname"] = font_name
    page.insert_text(point, text, **options)


def _write_table_pdf(pdf_path: Path) -> dict[str, Any]:
    font_path = next((path for path in KOREAN_FONT_PATHS if path.exists()), None)
    use_korean = font_path is not None

    if use_korean:
        narrative = "연차 정책: 입사 1년 후 기본 연차 15일이 부여됩니다."
        intro = "아래 표는 직급별 복지포인트와 교육예산 기준입니다."
        footer = "표 하단 안내: 복지포인트는 매년 1월 지급됩니다."
        rows = [
            ["직급", "복지포인트", "교육예산"],
            ["사원", "100만원", "50만원"],
            ["대리", "150만원", "80만원"],
            ["과장", "200만원", "120만원"],
        ]
        expected = {
            "header": "| 직급 | 복지포인트 | 교육예산 |",
            "row": "| 대리 | 150만원 | 80만원 |",
            "text_keyword": "연차",
            "table_row_keyword": "대리",
            "table_value_keyword": "150만원",
            "shared_keyword": "복지포인트",
            "footer_keyword": "매년 1월",
            "cell_only_values": ["150만원", "80만원", "120만원"],
        }
    else:
        narrative = "Annual leave policy: employees receive 15 days after one year."
        intro = "The table below defines Benefit Points and Training Budget by Role."
        footer = "Footer note: Benefit Points are paid every January."
        rows = [
            ["Role", "Benefit Points", "Training Budget"],
            ["Staff", "1000", "500"],
            ["Assistant Manager", "1500", "800"],
            ["Manager", "2000", "1200"],
        ]
        expected = {
            "header": "| Role | Benefit Points | Training Budget |",
            "row": "| Assistant Manager | 1500 | 800 |",
            "text_keyword": "Annual leave",
            "table_row_keyword": "Assistant Manager",
            "table_value_keyword": "1500",
            "shared_keyword": "Benefit Points",
            "footer_keyword": "every January",
            "cell_only_values": ["1500", "800", "1200"],
        }

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    font_name = None
    if font_path:
        font_name = "EvalFont"
        page.insert_font(fontname=font_name, fontfile=str(font_path))

    _insert_text(page, (72, 72), narrative, font_name, 11)
    _insert_text(page, (72, 98), intro, font_name, 11)

    x0, y0 = 72, 140
    col_widths = [120, 120, 120]
    row_height = 32
    x_positions = [x0]
    for width in col_widths:
        x_positions.append(x_positions[-1] + width)
    y_positions = [y0 + row_height * index for index in range(len(rows) + 1)]

    for x in x_positions:
        page.draw_line((x, y_positions[0]), (x, y_positions[-1]), color=(0, 0, 0), width=0.8)
    for y in y_positions:
        page.draw_line((x_positions[0], y), (x_positions[-1], y), color=(0, 0, 0), width=0.8)

    for row_index, row in enumerate(rows):
        for col_index, cell in enumerate(row):
            _insert_text(page, (x_positions[col_index] + 8, y_positions[row_index] + 20), cell, font_name, 10)

    _insert_text(page, (72, 310), footer, font_name, 11)
    doc.save(pdf_path)
    doc.close()
    return expected


class TableDetectionTest(unittest.TestCase):
    def test_extract_chunks_detects_tables_and_separates_keyword_hits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = Path(temp_dir) / "table_detection_eval.pdf"
            expected = _write_table_pdf(pdf_path)

            chunks = extract_chunks_from_pdf(str(pdf_path), chunk_size=500, overlap=50)

        table_chunks = [chunk for chunk in chunks if chunk.get("content_type") == "table"]
        text_chunks = [chunk for chunk in chunks if chunk.get("content_type") == "text"]

        self.assertEqual(len(table_chunks), 1)
        self.assertGreaterEqual(len(text_chunks), 2)
        self.assertIn(expected["header"], table_chunks[0]["content"])
        self.assertIn("| --- | --- | --- |", table_chunks[0]["content"])
        self.assertIn(expected["row"], table_chunks[0]["content"])

        text_blob = "\n".join(chunk["content"] for chunk in text_chunks)
        for value in expected["cell_only_values"]:
            self.assertNotIn(value, text_blob)

        def hit_types(keyword: str) -> list[str]:
            return [chunk.get("content_type") for chunk in chunks if keyword in chunk["content"]]

        self.assertEqual(set(hit_types(expected["text_keyword"])), {"text"})
        self.assertEqual(set(hit_types(expected["table_row_keyword"])), {"table"})
        self.assertEqual(set(hit_types(expected["table_value_keyword"])), {"table"})
        self.assertIn("text", hit_types(expected["shared_keyword"]))
        self.assertIn("table", hit_types(expected["shared_keyword"]))
        self.assertEqual(set(hit_types(expected["footer_keyword"])), {"text"})


if __name__ == "__main__":
    unittest.main()
