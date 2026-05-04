"""Public RAG entry points used by the backend API."""

from __future__ import annotations

from typing import Any

from rag.config import get_config
from rag.embeddings.embedder import GeminiTextEmbedder
from rag.generator.generator import AnswerGenerator
from rag.retriever.retriever import Retriever
from rag.vectorstore.store import ChromaVectorStore


Chunk = dict[str, Any]


def embed_chunks(chunks: list[Chunk]) -> dict[str, Any]:
    """Embed and persist document chunks.

    Expected chunk format:
    {"content": "...", "document_id": 1, "file_name": "정책.pdf", "page": 3}
    """

    _validate_chunks(chunks)
    embedder = GeminiTextEmbedder()
    store = ChromaVectorStore()
    embeddings = embedder.embed_texts([chunk["content"] for chunk in chunks])
    ids = store.upsert_chunks(chunks, embeddings)
    return {"stored_count": len(ids), "ids": ids}


def query(question: str, top_k: int | None = None) -> dict[str, Any]:
    """Answer a question using retrieved chunks and return answer plus sources."""

    if not question or not question.strip():
        raise ValueError("question must not be empty")

    config = get_config()
    retriever = Retriever()
    generator = AnswerGenerator()
    chunks = retriever.retrieve(question, top_k=top_k or config.top_k)
    return generator.generate(question, chunks)


def _validate_chunks(chunks: list[Chunk]) -> None:
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list")

    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise TypeError(f"chunks[{index}] must be a dict")
        if not chunk.get("content") or not str(chunk["content"]).strip():
            raise ValueError(f"chunks[{index}].content must not be empty")
