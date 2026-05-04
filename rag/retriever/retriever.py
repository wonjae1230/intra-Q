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

    def retrieve(self, question: str, top_k: int | None = None) -> list[SearchResult]:
        if not question or not question.strip():
            raise ValueError("question must not be empty")

        config = get_config()
        query_embedding = self.embedder.embed_text(question)
        return self.store.query_by_embedding(query_embedding, top_k=top_k or config.top_k)


def retrieve(question: str, top_k: int | None = None) -> list[SearchResult]:
    return Retriever().retrieve(question, top_k=top_k)

