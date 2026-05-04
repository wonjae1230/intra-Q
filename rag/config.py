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
    embedding_model: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
    embedding_output_dimensionality: int = int(os.getenv("GEMINI_EMBEDDING_DIMENSIONS", "768"))
    chat_model: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    gemini_thinking_budget: int = int(os.getenv("GEMINI_THINKING_BUDGET", "0"))
    top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    distance_threshold: float = float(os.getenv("RAG_DISTANCE_THRESHOLD", "1.2"))


def get_config() -> RagConfig:
    return RagConfig()
