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
    ) -> list[SearchResult]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        config = get_config()
        query_embedding = self.embedder.embed_text(question)
        k = top_k or config.top_k

        where: dict | None = None
        if document_ids:
            if len(document_ids) == 1:
                where = {"document_id": document_ids[0]}
            else:
                where = {"document_id": {"$in": document_ids}}

        results = self.store.query_by_embedding(query_embedding, top_k=k, where=where)

        limit = max_chunks_per_doc if max_chunks_per_doc is not None else config.max_chunks_per_doc
        return _cap_per_document(results, limit)


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
) -> list[SearchResult]:
    return Retriever().retrieve(question, top_k=top_k, document_ids=document_ids)
