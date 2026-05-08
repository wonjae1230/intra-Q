from __future__ import annotations

import logging
import time
from typing import Any

from app.schemas.chat import ChatData, SourceItem
from rag.pipeline import query as rag_query


logger = logging.getLogger(__name__)


def _coerce_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _map_source_item(source: dict[str, Any]) -> SourceItem:
    document_id = _coerce_int(source.get("document_id"))
    document_name = source.get("document_name") or source.get("file_name") or "unknown.pdf"
    chunk_text = source.get("chunk_text") or source.get("content") or ""
    distance = _coerce_float(source.get("distance"))
    similarity_score = _coerce_float(source.get("similarity_score"))
    if similarity_score is None:
        similarity_score = _coerce_float(source.get("score"))
    if similarity_score is None and distance is not None:
        similarity_score = max(0.0, 1.0 - distance)

    return SourceItem(
        document_id=document_id,
        document_name=str(document_name),
        file_name=str(source.get("file_name")) if source.get("file_name") else None,
        page=_coerce_int(source.get("page")),
        chunk_text=str(chunk_text),
        similarity_score=similarity_score,
        content=str(source.get("content")) if source.get("content") else None,
        distance=distance,
    )


def generate_chat_response(
    question: str,
    document_ids: list[int] | None = None,
    top_k: int | None = None,
) -> ChatData:
    """Generate a RAG response from the vector store and LLM pipeline."""
    started_at = time.perf_counter()
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("질문은 비어 있을 수 없습니다.")

    if document_ids == []:
        return ChatData(
            answer="현재 사용자의 검색 가능한 문서가 없습니다. 먼저 PDF 문서를 업로드해 주세요.",
            sources=[],
            latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
        )

    if document_ids is not None:
        logger.info("Chat document filter requested: document_ids=%s", document_ids)

    rag_result = rag_query(cleaned_question, top_k=top_k, document_ids=document_ids)
    answer = str(rag_result.get("answer") or "")
    sources = [_map_source_item(source) for source in rag_result.get("sources", []) if isinstance(source, dict)]

    if not answer.strip():
        answer = "관련 문서를 찾지 못했습니다. 다른 표현으로 질문해 주세요."

    return ChatData(
        answer=answer,
        sources=sources,
        latency_ms=max(1, int((time.perf_counter() - started_at) * 1000)),
    )
