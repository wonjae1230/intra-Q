"""Text embedding helpers backed by OpenAI embeddings."""

from __future__ import annotations

from functools import lru_cache
from typing import Iterable

from langchain_openai import OpenAIEmbeddings

from rag.config import get_config


class OpenAITextEmbedder:
    """Convert Korean or English text chunks into embedding vectors."""

    def __init__(self, model: str | None = None) -> None:
        config = get_config()
        self.model = model or config.embedding_model
        self._client = OpenAIEmbeddings(model=self.model)

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("text must not be empty")
        return self._client.embed_query(text)

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        text_list = [text for text in texts if text and text.strip()]
        if not text_list:
            return []
        return self._client.embed_documents(text_list)


@lru_cache(maxsize=1)
def _default_embedder() -> OpenAITextEmbedder:
    return OpenAITextEmbedder()


def embed_text(text: str) -> list[float]:
    return _default_embedder().embed_text(text)


def embed_texts(texts: Iterable[str]) -> list[list[float]]:
    return _default_embedder().embed_texts(texts)
