"""크로마 DB"""

from __future__ import annotations

from rag.config import get_config
from rag.embeddings.embedder import OpenAITextEmbedder
from rag.vectorstore.store import ChromaVectorStore, SearchResult


class Retriever:
    def __init__(
        self,
        embedder: OpenAITextEmbedder | None = None,
        store: ChromaVectorStore | None = None,
    ) -> None:
        self.embedder = embedder or OpenAITextEmbedder()
        self.store = store or ChromaVectorStore()

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        document_ids: list[int] | None = None,
        max_chunks_per_doc: int | None = None,
        curriculum_years: list[int] | None = None,
    ) -> list[SearchResult]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        config = get_config()
        query_embedding = self.embedder.embed_text(question)
        k = top_k or config.top_k

        where = _build_where_filter(document_ids, curriculum_years)
        results = self.store.query_by_embedding(query_embedding, top_k=k, where=where)

        limit = max_chunks_per_doc if max_chunks_per_doc is not None else config.max_chunks_per_doc
        return _cap_per_document(results, limit)


def _build_where_filter(
    document_ids: list[int] | None,
    curriculum_years: list[int] | None,
) -> dict | None:
    """Chroma where 필터 조합. document_ids와 curriculum_years를 $and로 결합."""
    conditions = []

    if document_ids:
        if len(document_ids) == 1:
            conditions.append({"document_id": document_ids[0]})
        else:
            conditions.append({"document_id": {"$in": document_ids}})

    if curriculum_years:
        if len(curriculum_years) == 1:
            conditions.append({"curriculum_year": curriculum_years[0]})
        else:
            conditions.append({"curriculum_year": {"$in": curriculum_years}})

    if not conditions:
        return None
    if len(conditions) == 1:
        return conditions[0]
    return {"$and": conditions}


def _cap_per_document(results: list[SearchResult], max_per_doc: int) -> list[SearchResult]:
    """문서별 chunk 수를 max_per_doc으로 제한해 한 문서 독식을 방지."""
    counts: dict = {}
    capped: list[SearchResult] = []
    for result in results:
        doc_id = result.get("document_id")
        counts[doc_id] = counts.get(doc_id, 0) + 1
        if counts[doc_id] <= max_per_doc:
            capped.append(result)
    return capped


def retrieve(
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
    curriculum_years: list[int] | None = None,
) -> list[SearchResult]:
    return Retriever().retrieve(
        question,
        top_k=top_k,
        document_ids=document_ids,
        curriculum_years=curriculum_years,
    )
