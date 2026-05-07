"""Shared configuration for the RAG pipeline."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env", override=True)

_RAG_DIR = Path(__file__).resolve().parent


def _resolve_chroma_dir() -> str:
    raw = os.getenv("CHROMA_PERSIST_DIR", "chroma_db")
    p = Path(raw)
    return str(p if p.is_absolute() else _RAG_DIR / raw)


@dataclass(frozen=True)
class RagConfig:
    chroma_persist_dir: str = _resolve_chroma_dir()
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "intra_q_documents")
    chroma_distance_metric: str = os.getenv("CHROMA_DISTANCE_METRIC", "cosine")
    embedding_model: str = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
    chat_model: str = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
    gemini_thinking_budget: int = int(os.getenv("GEMINI_THINKING_BUDGET", "0"))
    top_k: int = int(os.getenv("RAG_TOP_K", "8"))
    distance_threshold: float = float(os.getenv("RAG_DISTANCE_THRESHOLD", "1.2"))
    # Vertex AI Reranker
    reranker_enabled: bool = os.getenv("RERANKER_ENABLED", "true").lower() == "true"
    google_cloud_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    reranker_model: str = os.getenv("RERANKER_MODEL", "semantic-ranker-default@latest")
    reranker_top_n: int = int(os.getenv("RERANKER_TOP_N", "5"))
    reranker_fetch_multiplier: int = int(os.getenv("RERANKER_FETCH_MULTIPLIER", "3"))


def get_config() -> RagConfig:
    return RagConfig()
