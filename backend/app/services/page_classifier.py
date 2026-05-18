from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def classify_page(page_text: str, metadata: dict[str, Any] | None = None) -> dict[str, str]:
    """Classify a PDF page into the A/B/C/D processing route with simple heuristics."""
    metadata = metadata or {}
    text = page_text or ""
    text_length = int(metadata.get("text_length") or len(text))
    image_count = int(metadata.get("image_count") or 0)
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    if image_count > 0 and text_length < 100:
        result = {"page_type": "A", "reason": "image-heavy page with little extractable text"}
    elif _has_complex_table_pattern(text):
        result = {"page_type": "B", "reason": "complex or merged-cell table pattern detected"}
    elif _table_score(lines) >= 3:
        result = {"page_type": "C", "reason": "table detected"}
    else:
        result = {"page_type": "D", "reason": "general text page"}

    logger.info(
        "Page classified: page_number=%s, page_type=%s, reason=%s",
        metadata.get("page_number"),
        result["page_type"],
        result["reason"],
    )
    return result


def _has_complex_table_pattern(text: str) -> bool:
    complex_keywords = ("병합", "merged", "rowspan", "colspan", "비고", "영역별", "트랙별")
    if any(keyword in text for keyword in complex_keywords):
        return True
    return bool(re.search(r"교과목\s*번호.*이수\s*구분.*학점", text, flags=re.DOTALL))


def _table_score(lines: list[str]) -> int:
    score = 0
    table_keywords = ("교과목", "학점", "이수구분", "학기", "과목명", "전공필수", "전공선택")
    for line in lines:
        if "\t" in line:
            score += 1
        if len(re.findall(r"\s{2,}", line)) >= 2:
            score += 1
        if sum(1 for keyword in table_keywords if keyword in line) >= 2:
            score += 1
    return score
