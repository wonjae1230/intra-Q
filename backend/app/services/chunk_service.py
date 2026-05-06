from __future__ import annotations

import re
from typing import Any


def split_text_into_chunks(text: str, min_size: int = 300, max_size: int = 500, target_size: int = 400) -> list[str]:
    """Split text into chunks sized around 300~500 characters.

    The splitter prefers paragraph, sentence, or whitespace boundaries first.
    If no natural break exists, it falls back to a hard character boundary and
    then merges an undersized tail chunk into the previous chunk when possible.
    """
    normalized = text.strip()
    if not normalized:
        return []

    if len(normalized) <= max_size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    total_length = len(normalized)

    while start < total_length:
        remaining = total_length - start
        if remaining <= max_size:
            tail = normalized[start:].strip()
            if tail:
                if chunks and len(tail) < min_size and len(chunks[-1]) + 1 + len(tail) <= max_size:
                    chunks[-1] = f"{chunks[-1]} {tail}"
                else:
                    chunks.append(tail)
            break

        window_end = min(start + max_size, total_length)
        window = normalized[start:window_end]

        break_point = -1
        search_candidates = [
            window.rfind("\n", min_size),
            window.rfind(". ", min_size),
            window.rfind("? ", min_size),
            window.rfind("! ", min_size),
            window.rfind(" ", min_size),
            window.rfind("\t", min_size),
        ]

        for candidate in search_candidates:
            if candidate > break_point:
                break_point = candidate

        if break_point >= min_size:
            end = start + break_point + 1
        else:
            end = min(start + target_size, window_end)
            if end - start < min_size:
                end = window_end

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end

    # Merge the last chunk into the previous one when it is too small and still fits.
    if len(chunks) >= 2 and len(chunks[-1]) < min_size and len(chunks[-2]) + 1 + len(chunks[-1]) <= max_size:
        chunks[-2] = f"{chunks[-2]} {chunks[-1]}"
        chunks.pop()

    return chunks


def _split_into_paragraphs(text: str) -> list[str]:
    """Split text into coarse sections using blank lines and normalize spacing."""
    sections = [section.strip() for section in re.split(r"\n\s*\n+", text.strip()) if section.strip()]
    if not sections:
        return []

    paragraphs: list[str] = []
    index = 0
    while index < len(sections):
        current = re.sub(r"[ \t]+", " ", sections[index]).strip()
        if not current:
            index += 1
            continue

        next_section = re.sub(r"[ \t]+", " ", sections[index + 1]).strip() if index + 1 < len(sections) else ""
        is_heading_like = len(current) <= 30 and not re.search(r"[.!?。！？]", current)
        if is_heading_like and next_section:
            paragraphs.append(f"{current}\n\n{next_section}")
            index += 2
            continue

        paragraphs.append(current)
        index += 1
    return paragraphs


def build_page_chunks(pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert extracted page text into database-ready chunk records."""
    chunk_rows: list[dict[str, Any]] = []

    for page in pages:
        page_number = int(page["page"])
        text = str(page.get("text", ""))
        for paragraph in _split_into_paragraphs(text):
            for content in split_text_into_chunks(paragraph):
                chunk_rows.append({"page_number": page_number, "content": content})

    return chunk_rows
