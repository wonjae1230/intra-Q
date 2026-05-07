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
        self._collection = self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": config.chroma_distance_metric},
        )

    def upsert_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> list[str]:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        if not chunks:
            return []

        seen: dict[str, tuple[Chunk, list[float]]] = {}
        for chunk, embedding in zip(chunks, embeddings):
            chunk_id = build_chunk_id(chunk)
            if chunk_id not in seen:
                seen[chunk_id] = (chunk, embedding)

        unique_ids = list(seen.keys())
        unique_chunks = [seen[i][0] for i in unique_ids]
        unique_embeddings = [seen[i][1] for i in unique_ids]

        self._collection.upsert(
            ids=unique_ids,
            embeddings=unique_embeddings,
            documents=[c["content"] for c in unique_chunks],
            metadatas=[_metadata_from_chunk(c) for c in unique_chunks],
        )
        return unique_ids

    def query_by_embedding(
        self,
        embedding: list[float],
        top_k: int = 4,
        distance_threshold: float | None = None,
        where: dict | None = None,
    ) -> list[SearchResult]:
        total = self._collection.count()
        if total == 0:
            return []
        n_results = min(top_k, total)

        query_kwargs: dict = {
            "query_embeddings": [embedding],
            "n_results": n_results,
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            query_kwargs["where"] = where

        raw = self._collection.query(**query_kwargs)

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

    def delete_by_document_id(self, document_id: int) -> int:
        if document_id <= 0:
            raise ValueError("document_id must be positive")

        existing = self._collection.get(where={"document_id": document_id})
        ids = existing.get("ids", [])
        if not ids:
            return 0

        self._collection.delete(ids=ids)
        return len(ids)
