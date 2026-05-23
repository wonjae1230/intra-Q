"""형태소 분석 기반 BM25 희소 검색 — Dense 검색과 병행하여 하이브리드 검색에 사용."""

from __future__ import annotations

import re
from typing import Any

from kiwipiepy import Kiwi
from rank_bm25 import BM25Okapi

from rag.vectorstore.store import ChromaVectorStore, SearchResult

# BM25 검색에 활용할 품사 태그
_KEEP_POS = {"NNG", "NNP", "NNB", "NR", "SL", "SH", "XR"}

_kiwi: Kiwi | None = None

# 인덱스 캐시: curriculum_years 조합별로 (chunks, bm25) 보관
_index_cache: dict[str, tuple[list[dict], BM25Okapi]] = {}


def _get_kiwi() -> Kiwi:
    global _kiwi
    if _kiwi is None:
        _kiwi = Kiwi()
    return _kiwi


def _tokenize(text: str) -> list[str]:
    """형태소 분석으로 명사·고유명사·외래어 토큰 추출.

    외래어 복합어(캡스톤디자인 등) 분리 오류 보완:
    - Kiwi 분석 후 원문에서 2글자 이상 연속 외래어 덩어리를 별도로 추출해 추가.
    - 영문+숫자 과목 코드(SWE3001, CS101)와 숫자 단독(3학점)도 보존.
    """
    kiwi = _get_kiwi()
    tokens: list[str] = []

    for token in kiwi.tokenize(text):
        # 외래어(SL)는 1글자도 허용 — 분리된 외래어 조각 보존
        if token.tag in _KEEP_POS:
            if token.tag == "SL" or len(token.form) > 1:
                tokens.append(token.form)

    # 원문에서 한글+외래어 혼합 덩어리 추출 (캡스톤디자인, 소프트웨어공학 등)
    # Kiwi가 쪼갠 외래어 복합어를 원형 그대로 추가해 recall 보강
    for chunk in re.findall(r"[가-힣A-Za-z]{3,}", text):
        if chunk not in tokens:
            tokens.append(chunk)

    # 영문+숫자 과목 코드 (SWE3001, CS101)
    for code in re.findall(r"[A-Za-z]{2,}\d{2,}", text):
        upper = code.upper()
        if upper not in tokens:
            tokens.append(upper)

    # 숫자 단독 (학점·학기 값)
    for num in re.findall(r"\b\d+\b", text):
        tokens.append(num)

    return tokens if tokens else text.split()


def _cache_key(curriculum_years: list[int] | None) -> str:
    if not curriculum_years:
        return "__all__"
    return ",".join(str(y) for y in sorted(curriculum_years))


class BM25Retriever:
    """Chroma에 저장된 청크를 BM25로 색인하고 검색.

    인덱스는 curriculum_years 조합별로 모듈 수준에서 캐싱되어
    동일 필터 조건이면 재빌드 없이 재사용된다.
    """

    def __init__(self, store: ChromaVectorStore | None = None) -> None:
        self._store = store or ChromaVectorStore()

    def _get_or_build_index(
        self, curriculum_years: list[int] | None
    ) -> tuple[list[dict[str, Any]], BM25Okapi] | tuple[list, None]:
        key = _cache_key(curriculum_years)
        if key in _index_cache:
            return _index_cache[key]

        col = self._store._collection
        total = col.count()
        if total == 0:
            return [], None

        where: dict | None = None
        if curriculum_years:
            if len(curriculum_years) == 1:
                where = {"curriculum_year": curriculum_years[0]}
            else:
                where = {"curriculum_year": {"$in": curriculum_years}}

        raw = col.get(
            limit=total,
            include=["documents", "metadatas"],
            where=where,
        )

        chunks: list[dict[str, Any]] = [
            {
                "content": doc,
                "file_name": (meta or {}).get("file_name"),
                "page": (meta or {}).get("page"),
                "document_id": (meta or {}).get("document_id"),
                "curriculum_year": (meta or {}).get("curriculum_year"),
                "college": (meta or {}).get("college"),
                "department": (meta or {}).get("department"),
                "subject_code": (meta or {}).get("subject_code"),
                "subject_name": (meta or {}).get("subject_name"),
                "category": (meta or {}).get("category"),
                "credit": (meta or {}).get("credit"),
                "semester": (meta or {}).get("semester"),
                "distance": 0.0,
            }
            for doc, meta in zip(raw["documents"], raw["metadatas"])
        ]

        if not chunks:
            return [], None

        tokenized = [_tokenize(c["content"]) for c in chunks]
        bm25 = BM25Okapi(tokenized)
        _index_cache[key] = (chunks, bm25)
        return chunks, bm25

    def retrieve(
        self,
        question: str,
        top_k: int = 8,
        curriculum_years: list[int] | None = None,
    ) -> list[SearchResult]:
        """질문을 형태소 분석 후 BM25 검색. distance 필드에 역점수 저장."""
        chunks, bm25 = self._get_or_build_index(curriculum_years)

        if not chunks or bm25 is None:
            return []

        query_tokens = _tokenize(question)
        if not query_tokens:
            return []

        scores = bm25.get_scores(query_tokens)

        scored = sorted(
            ((score, chunk) for score, chunk in zip(scores, chunks) if score > 0),
            key=lambda x: x[0],
            reverse=True,
        )

        results: list[SearchResult] = []
        for score, chunk in scored[:top_k]:
            result = dict(chunk)
            result["distance"] = 1.0 / (1.0 + score)
            result["bm25_score"] = score
            results.append(result)

        return results


def invalidate_cache() -> None:
    """문서 추가/삭제 시 BM25 캐시를 무효화."""
    _index_cache.clear()
