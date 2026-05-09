"""구글 버텍스 AI 를 통한 reranker"""

from __future__ import annotations

import logging
from typing import Any

from rag.config import get_config

logger = logging.getLogger(__name__)

SearchResult = dict[str, Any]


class VertexAIReranker:
    """Rerank retrieved chunks using Vertex AI Ranking API."""

    def __init__(self) -> None:
        config = get_config()
        self._project_id = config.google_cloud_project
        self._model = config.reranker_model
        self._top_n = config.reranker_top_n
        self._client = self._build_client()

    def _build_client(self):
        try:
            from google.cloud import discoveryengine_v1 as discoveryengine
            return discoveryengine.RankServiceClient()
        except Exception as exc:
            logger.warning("Vertex AI Reranker 초기화 실패: %s", exc)
            return None

    def rerank(self, query: str, chunks: list[SearchResult], top_n: int | None = None) -> list[SearchResult]:
        if not self._client or not self._project_id:
            logger.warning("Reranker 비활성화 상태 — 원본 순서로 반환")
            return chunks[: top_n or self._top_n]

        if not chunks:
            return []

        try:
            from google.cloud import discoveryengine_v1 as discoveryengine

            ranking_config = self._client.ranking_config_path(
                project=self._project_id,
                location="global",
                ranking_config="default_ranking_config",
            )

            records = [
                discoveryengine.RankingRecord(
                    id=str(i),
                    title=f"{chunk.get('file_name', '')} p.{chunk.get('page', '')}",
                    content=chunk.get("content", ""),
                )
                for i, chunk in enumerate(chunks)
            ]

            request = discoveryengine.RankRequest(
                ranking_config=ranking_config,
                model=self._model,
                top_n=top_n or self._top_n,
                query=query,
                records=records,
            )

            response = self._client.rank(request=request)

            index_to_score: dict[int, float] = {
                int(r.id): r.score for r in response.records
            }

            reranked = sorted(
                [
                    {**chunks[idx], "rerank_score": score}
                    for idx, score in index_to_score.items()
                ],
                key=lambda x: x["rerank_score"],
                reverse=True,
            )

            logger.info(
                "Rerank 완료: 입력 %d개 → 출력 %d개 | top score=%.4f",
                len(chunks),
                len(reranked),
                reranked[0]["rerank_score"] if reranked else 0,
            )
            return reranked

        except Exception as exc:
            logger.error("Reranker 호출 실패 — 원본 순서 사용: %s", exc)
            return chunks[: top_n or self._top_n]


def rerank(query: str, chunks: list[SearchResult], top_n: int | None = None) -> list[SearchResult]:
    return VertexAIReranker().rerank(query, chunks, top_n=top_n)
