from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def process_page(page_type: str, page_content: dict[str, Any]) -> dict[str, Any]:
    """Route a classified page through the matching processing branch.

    Type A only marks that Gemini is required. No Gemini API call is made here.
    """
    page_number = page_content.get("page")
    logger.info("process_page called: page_number=%s, page_type=%s", page_number, page_type)

    if page_type == "A":
        logger.info("Type A processing selected: page_number=%s", page_number)
        return {
            "processed_text": page_content.get("text") or "",
            "method": "gemini",
            "requires_gemini": True,
            "failure_reason": "Gemini Vision required; actual Gemini call is disabled",
        }
    if page_type == "B":
        logger.info("Type B processing selected: page_number=%s", page_number)
        return {
            "processed_text": merged_cell_restore(page_content.get("text") or ""),
            "method": "pymupdf",
            "requires_gemini": False,
            "failure_reason": None,
        }
    if page_type == "C":
        logger.info("Type C processing selected: page_number=%s", page_number)
        return {
            "processed_text": table_to_markdown(page_content.get("text") or ""),
            "method": "pymupdf",
            "requires_gemini": False,
            "failure_reason": None,
        }

    logger.info("Type D processing selected: page_number=%s", page_number)
    return {
        "processed_text": normalize_text(page_content.get("text") or ""),
        "method": "pymupdf",
        "requires_gemini": False,
        "failure_reason": None,
    }


def normalize_text(text: str) -> str:
    """Normalize plain text pages without changing semantic content."""
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def table_to_markdown(text: str) -> str:
    """Mock table extraction branch for Type C pages."""
    normalized = normalize_text(text)
    return f"[table_to_markdown]\n{normalized}" if normalized else ""


def merged_cell_restore(text: str) -> str:
    """Mock merged-cell restoration branch for Type B pages."""
    normalized = normalize_text(text)
    return f"[merged_cell_restore]\n{normalized}" if normalized else ""
