from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.chunk import Chunk
from app.models.document import Document
from app.schemas.chat import ChatResponse, SourceItem


@dataclass(frozen=True)
class RankedChunk:
    """Internal helper used to rank chunks without tying the code to embeddings."""

    score: int
    document: str
    page: int
    preview: str
    content: str
    content_length: int


_KOREAN_SUFFIXES = ("은", "는", "이", "가", "을", "를", "에", "와", "과", "도", "로", "으로")
_QUESTION_STOPWORDS = {
    "회사",
    "정책",
    "어떻게",
    "되나요",
    "무엇",
    "무슨",
    "있나요",
    "알려",
    "주세요",
}


def _normalize_token(token: str) -> str:
    """Strip a few common Korean particles so search behaves less rigidly."""
    normalized = token.strip().lower()
    if len(normalized) <= 1:
        return normalized

    for suffix in _KOREAN_SUFFIXES:
        if normalized.endswith(suffix) and len(normalized) > len(suffix):
            return normalized[: -len(suffix)]
    return normalized


def _tokenize(text: str) -> set[str]:
    """Split a question into simple search tokens.

    This mock implementation uses basic token overlap so the structure can later
    be replaced with embedding/vector search without changing the API contract.
    """
    tokens: set[str] = set()
    for token in re.findall(r"[0-9A-Za-z가-힣]+", text.lower()):
        normalized = _normalize_token(token)
        if normalized:
            tokens.add(normalized)
            tokens.add(token)
    return tokens


def _score_chunk(question_tokens: set[str], content: str) -> int:
    """Score a chunk by simple token overlap and substring matches."""
    lowered = content.lower()
    score = 0
    for token in question_tokens:
        if token in lowered:
            score += 1
    return score


def _build_preview(content: str, question_tokens: set[str], window: int = 80) -> str:
    """Return a short snippet around the most relevant matched term."""
    lowered = content.lower()
    matched_terms = [token for token in question_tokens if token and token in lowered]
    if not matched_terms:
        return content[: window * 2].strip()

    # Prefer longer matches so the preview anchors around the more specific term.
    matched_terms.sort(key=len, reverse=True)
    match_index = -1
    matched_term = matched_terms[0]
    for term in matched_terms:
        match_index = lowered.find(term)
        if match_index >= 0:
            matched_term = term
            break

    start = max(0, match_index - window)
    end = min(len(content), match_index + len(matched_term) + window)
    snippet = content[start:end].strip()

    if start > 0:
        snippet = f"...{snippet}"
    if end < len(content):
        snippet = f"{snippet}..."
    return snippet


def _build_answer_from_source(content: str, question_tokens: set[str]) -> str:
    """Build a short answer from the most relevant sentence in the source chunk."""
    sentences = [segment.strip() for segment in re.split(r"(?<=[.!?。！？])\s+|\n+", content) if segment.strip()]
    if not sentences:
        return content.strip()

    meaningful_tokens = {token for token in question_tokens if token not in _QUESTION_STOPWORDS}
    if not meaningful_tokens:
        meaningful_tokens = question_tokens

    best_sentence = sentences[0]
    best_score = -1
    for sentence in sentences:
        lowered = sentence.lower()
        score = sum(1 for token in meaningful_tokens if token and token in lowered)
        if len(sentence) < 25:
            score -= 2
        if score > best_score or (score == best_score and len(sentence) > len(best_sentence)):
            best_score = score
            best_sentence = sentence

    return best_sentence


def _rank_chunks(db: Session, question: str, limit: int = 3) -> list[RankedChunk]:
    """Fetch chunks from SQLite and rank them with a lightweight mock search."""
    question_tokens = _tokenize(question)
    if not question_tokens:
        return []

    rows = (
        db.query(Chunk, Document.file_name)
        .join(Document, Chunk.document_id == Document.id)
        .all()
    )

    ranked: list[RankedChunk] = []
    for chunk, file_name in rows:
        score = _score_chunk(question_tokens, chunk.content)
        if score <= 0:
            continue

        ranked.append(
            RankedChunk(
                score=score,
                document=file_name,
                page=chunk.page_number,
                preview=_build_preview(chunk.content, question_tokens),
                content=chunk.content,
                content_length=len(chunk.content),
            )
        )

    ranked.sort(key=lambda item: (-item.score, item.document.lower(), item.page, -item.content_length))
    return ranked[:limit]


def generate_chat_response(question: str, db: Session) -> ChatResponse:
    """Generate a mock RAG response that can later be replaced by a real LLM call."""
    cleaned_question = question.strip()
    if not cleaned_question:
        raise ValueError("질문은 비어 있을 수 없습니다.")

    # Keep only the single most relevant chunk so the response stays focused.
    ranked_chunks = _rank_chunks(db, cleaned_question, limit=1)
    if not ranked_chunks:
        return ChatResponse(
            answer="관련 문서를 찾지 못했습니다. 다른 표현으로 질문해 주세요.",
            sources=[],
        )

    top_source = ranked_chunks[0]
    sources = [SourceItem(document=top_source.document, page=top_source.page, preview=top_source.preview)]

    answer = (
        f"{_build_answer_from_source(top_source.content, _tokenize(cleaned_question))} "
        f"(참고문서: {top_source.document} {top_source.page}페이지)"
    )
    return ChatResponse(answer=answer, sources=sources)
