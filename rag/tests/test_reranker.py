"""Reranker before/after 비교 테스트."""

from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from rag.config import get_config
from rag.retriever.retriever import Retriever
from rag.reranker.reranker import VertexAIReranker


TEST_QUESTIONS = [
    "소프트웨어융합학과의 졸업요건이 어떻게 돼?",
    "SK하이닉스의 2026년 매출은 얼마야?",
    "2025년 교육과정에서 달라진 점이 뭐야?",
]


def run_comparison(question: str, document_ids: list[int] | None = None) -> None:
    config = get_config()
    retriever = Retriever()
    final_top_k = config.reranker_top_n
    fetch_k = final_top_k * config.reranker_fetch_multiplier

    print(f"\n{'='*60}")
    print(f"질문: {question}")
    print(f"{'='*60}")

    # --- Before: 벡터 검색만 (top_k=5) ---
    t0 = time.perf_counter()
    before_chunks = retriever.retrieve(question, top_k=final_top_k, document_ids=document_ids)
    before_ms = int((time.perf_counter() - t0) * 1000)

    print(f"\n[Before] 벡터 검색만 (top_k={final_top_k}) — {before_ms}ms")
    for i, c in enumerate(before_chunks, 1):
        dist = c.get("distance", 0)
        score = round(1 - dist, 4) if dist is not None else "-"
        print(f"  {i}. [{c.get('file_name','?')[:30]} p.{c.get('page')}] cosine_score={score}")
        print(f"     {c.get('content','')[:80]}...")

    # --- After: 벡터 검색(top_k=15) → Reranker ---
    t1 = time.perf_counter()
    candidate_chunks = retriever.retrieve(question, top_k=fetch_k, document_ids=document_ids)
    reranker = VertexAIReranker()
    after_chunks = reranker.rerank(question, candidate_chunks, top_n=final_top_k)
    after_ms = int((time.perf_counter() - t1) * 1000)

    print(f"\n[After] 벡터({fetch_k}개) → Reranker(top {final_top_k}) — {after_ms}ms")
    for i, c in enumerate(after_chunks, 1):
        rerank_score = round(c.get("rerank_score", 0), 4)
        print(f"  {i}. [{c.get('file_name','?')[:30]} p.{c.get('page')}] rerank_score={rerank_score}")
        print(f"     {c.get('content','')[:80]}...")

    # --- 순위 변화 분석 ---
    before_keys = [(c.get("file_name"), c.get("page")) for c in before_chunks]
    after_keys  = [(c.get("file_name"), c.get("page")) for c in after_chunks]
    new_entries = [k for k in after_keys if k not in before_keys]
    dropped     = [k for k in before_keys if k not in after_keys]

    print(f"\n[변화 분석]")
    if new_entries:
        print(f"  Reranker로 새로 진입: {new_entries}")
    if dropped:
        print(f"  Reranker로 제외됨:    {dropped}")
    if not new_entries and not dropped:
        print("  순위 변화 없음 (같은 청크, 순서만 조정)")


if __name__ == "__main__":
    config = get_config()
    if not config.google_cloud_project:
        print("❌ GOOGLE_CLOUD_PROJECT가 .env에 설정되지 않았습니다.")
        sys.exit(1)

    print(f"프로젝트: {config.google_cloud_project}")
    print(f"Reranker: {config.reranker_model}")
    print(f"fetch_k={config.top_k * config.reranker_fetch_multiplier} → top_n={config.reranker_top_n}")

    for q in TEST_QUESTIONS:
        run_comparison(q)
