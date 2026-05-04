"""Shared configuration for the RAG pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")


@dataclass(frozen=True)
class RagConfig:
    chroma_persist_dir: str = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "intra_q_documents")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    chat_model: str = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))


def get_config() -> RagConfig:
    return RagConfig()
