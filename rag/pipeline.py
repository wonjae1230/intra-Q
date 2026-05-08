"""Public RAG entry points used by the backend API."""

from __future__ import annotations

from typing import Any

from rag.config import get_config
from rag.embeddings.embedder import OpenAITextEmbedder
from rag.generator.generator import AnswerGenerator
from rag.reranker.reranker import VertexAIReranker
from rag.retriever.retriever import Retriever
from rag.vectorstore.store import ChromaVectorStore


Chunk = dict[str, Any]


def embed_chunks(chunks: list[Chunk]) -> dict[str, Any]:
    """Embed and persist document chunks.

    Expected chunk format:
    {"content": "...", "document_id": 1, "file_name": "정책.pdf", "page": 3}
    """

    _validate_chunks(chunks)
    embedder = OpenAITextEmbedder()
    store = ChromaVectorStore()
    embeddings = embedder.embed_texts([chunk["content"] for chunk in chunks])
    ids = store.upsert_chunks(chunks, embeddings)
    return {"stored_count": len(ids), "ids": ids}


def query(
    question: str,
    top_k: int | None = None,
    document_ids: list[int] | None = None,
    history: list[dict] | None = None,
    approach_hint: str | None = None,
) -> dict[str, Any]:
    """Answer a question using retrieved chunks and return answer plus sources."""

    if not question or not question.strip():
        raise ValueError("question must not be empty")

    config = get_config()
    retriever = Retriever()
    generator = AnswerGenerator()

    # Rewrite follow-up questions into standalone search queries using conversation history.
    search_query = generator.rewrite_query(question, history or [])

    final_top_k = top_k or config.top_k
    if config.reranker_enabled:
        fetch_k = final_top_k * config.reranker_fetch_multiplier
        chunks = retriever.retrieve(search_query, top_k=fetch_k, document_ids=document_ids)
        reranker = VertexAIReranker()
        chunks = reranker.rerank(search_query, chunks, top_n=config.reranker_top_n)
    else:
        chunks = retriever.retrieve(search_query, top_k=final_top_k, document_ids=document_ids)

    return generator.generate(question, chunks, history=history, approach_hint=approach_hint)


def search_with_options(
    question: str,
    document_ids: list[int] | None = None,
) -> dict[str, Any]:
    """Search for relevant chunks, then ask LLM to generate answer approach options."""

    if not question or not question.strip():
        raise ValueError("question must not be empty")

    config = get_config()
    retriever = Retriever()
    generator = AnswerGenerator()

    fetch_k = config.top_k * config.reranker_fetch_multiplier
    chunks = retriever.retrieve(question, top_k=fetch_k, document_ids=document_ids)

    # Collect unique document_ids from retrieved chunks for the final chat call.
    seen_doc_ids: list[int] = []
    seen_set: set[int] = set()
    for chunk in chunks:
        doc_id = chunk.get("document_id")
        if doc_id is not None and int(doc_id) not in seen_set:
            seen_set.add(int(doc_id))
            seen_doc_ids.append(int(doc_id))

    result = generator.generate_clarify_options(question, chunks)
    rtype = result.get("type", "direct")

    if rtype == "context":
        return {
            "question": question,
            "options": [],
            "document_ids": seen_doc_ids,
            "context_question": result.get("question"),
        }
    if rtype == "options":
        return {
            "question": question,
            "options": result.get("items", []),
            "document_ids": seen_doc_ids,
            "context_question": None,
        }
    # direct
    return {"question": question, "options": [], "document_ids": seen_doc_ids, "context_question": None}


def delete_document_embeddings(document_id: int) -> dict[str, Any]:
    """Delete all stored embeddings for one document from the vector store."""

    if document_id <= 0:
        raise ValueError("document_id must be positive")

    store = ChromaVectorStore()
    deleted_count = store.delete_by_document_id(document_id)
    return {"deleted_count": deleted_count}


def _validate_chunks(chunks: list[Chunk]) -> None:
    if not isinstance(chunks, list):
        raise TypeError("chunks must be a list")

    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise TypeError(f"chunks[{index}] must be a dict")
        if not chunk.get("content") or not str(chunk["content"]).strip():
            raise ValueError(f"chunks[{index}].content must not be empty")
