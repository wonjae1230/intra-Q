"""Question-time retrieval over the Chroma vector store."""

from __future__ import annotations

from rag.config import get_config
from rag.embeddings.embedder import GeminiTextEmbedder
from rag.vectorstore.store import ChromaVectorStore, SearchResult


class Retriever:
    def __init__(
        self,
        embedder: GeminiTextEmbedder | None = None,
        store: ChromaVectorStore | None = None,
    ) -> None:
        self.embedder = embedder or GeminiTextEmbedder()
        self.store = store or ChromaVectorStore()

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        document_ids: list[int] | None = None,
    ) -> list[SearchResult]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        config = get_config()
        query_embedding = self.embedder.embed_text(question)
        search_limit = top_k or config.top_k
        if document_ids:
            search_limit = max(search_limit, len(document_ids) * 5)

        results = self.store.query_by_embedding(query_embedding, top_k=search_limit)
        if not document_ids:
            return results[: top_k or config.top_k]

        allowed_ids = {str(document_id) for document_id in document_ids}
        filtered_results = [result for result in results if str(result.get("document_id")) in allowed_ids]
        return filtered_results[: top_k or config.top_k]


def retrieve(
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> list[SearchResult]:
    return Retriever().retrieve(question, top_k=top_k, document_ids=document_ids)
