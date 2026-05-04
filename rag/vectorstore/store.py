"""Chroma persistence for document chunks and embeddings."""

from __future__ import annotations

import hashlib
from typing import Any

import chromadb

from rag.config import get_config


Chunk = dict[str, Any]
SearchResult = dict[str, Any]


def build_chunk_id(chunk: Chunk) -> str:
    """Build a stable Chroma id so repeated ingestion updates the same chunk."""

    document_id = chunk.get("document_id", "unknown")
    page = chunk.get("page", "unknown")
    content_hash = hashlib.sha1(chunk["content"].encode("utf-8")).hexdigest()[:16]
    return f"{document_id}:{page}:{content_hash}"


def _metadata_from_chunk(chunk: Chunk) -> dict[str, str | int | float | bool]:
    metadata: dict[str, str | int | float | bool] = {}
    for key in ("document_id", "file_name", "page"):
        value = chunk.get(key)
        if isinstance(value, (str, int, float, bool)):
            metadata[key] = value
        elif value is not None:
            metadata[key] = str(value)
    return metadata


class ChromaVectorStore:
    """Store and retrieve chunk embeddings from a persistent Chroma collection."""

    def __init__(
        self,
        persist_dir: str | None = None,
        collection_name: str | None = None,
    ) -> None:
        config = get_config()
        self.persist_dir = persist_dir or config.chroma_persist_dir
        self.collection_name = collection_name or config.chroma_collection_name
        self._client = chromadb.PersistentClient(path=self.persist_dir)
        self._collection = self._client.get_or_create_collection(name=self.collection_name)

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> list[str]:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return []

        ids = [build_chunk_id(chunk) for chunk in chunks]
        self._collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=[chunk["content"] for chunk in chunks],
            metadatas=[_metadata_from_chunk(chunk) for chunk in chunks],
        )
        return ids

    def query_by_embedding(
        self,
        embedding: list[float],
        top_k: int = 4,
        distance_threshold: float | None = None,
    ) -> list[SearchResult]:
        raw = self._collection.query(
            query_embeddings=[embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        results: list[SearchResult] = []
        for document, metadata, distance in zip(documents, metadatas, distances):
            metadata = metadata or {}
            results.append(
                {
                    "content": document,
                    "file_name": metadata.get("file_name"),
                    "page": metadata.get("page"),
                    "document_id": metadata.get("document_id"),
                    "distance": distance,
                }
            )

        threshold = get_config().distance_threshold if distance_threshold is None else distance_threshold
        return [result for result in results if result["distance"] < threshold]
