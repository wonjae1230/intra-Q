"""Question-time retrieval over the Chroma vector store."""

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

        return self.store.query_by_embedding(query_embedding, top_k=k, where=where)


def retrieve(
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
) -> list[SearchResult]:
    return Retriever().retrieve(question, top_k=top_k, document_ids=document_ids)
