"""Answer generation from retrieved chunks."""

from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from rag.config import get_config


Source = dict[str, Any]


class AnswerGenerator:
    def __init__(self, model: str | None = None, temperature: float = 0.0) -> None:
        config = get_config()
        self.model = model or config.chat_model
        self._client = ChatGoogleGenerativeAI(
            model=self.model,
            temperature=temperature,
            vertexai=True,
            project=config.google_cloud_project,
            location=config.vertex_ai_location,
        )

    def rewrite_query(self, question: str, history: list[dict]) -> str:
        """Rewrite a follow-up question into a standalone search query using conversation history."""
        if not history:
            return question

        history_text = "\n".join(
            f"{'사용자' if msg['role'] == 'user' else 'AI'}: {msg['content'][:200]}"
            for msg in history
        )
        prompt = (
            "아래 대화 기록을 참고하여 새로운 질문을 문서 검색에 사용할 독립적인 쿼리로 재작성하세요.\n"
            "질문이 이미 독립적이면 그대로 반환하세요.\n"
            "검색 쿼리만 출력하세요. 설명이나 따옴표 없이.\n\n"
            f"대화 기록:\n{history_text}\n\n"
            f"새로운 질문: {question}\n\n"
            "독립적인 검색 쿼리:"
        )
        response = self._client.invoke([HumanMessage(content=prompt)])
        rewritten = str(response.content).strip().strip('"').strip("'")
        return rewritten if rewritten else question

    def generate_clarify_options(self, question: str, chunks: list[Source]) -> dict[str, Any]:
        """Analyze question and chunks; return options, direct-answer signal, or a context request.

        Returns one of:
          {"type": "options",  "items": [{id, label, description}, ...]}
          {"type": "direct"}                       # simple question, skip clarify
          {"type": "context", "question": "..."}  # missing user context, ask back
        """
        if not chunks:
            return {"type": "direct"}

        context_preview = "\n".join(
            f"[{i+1}] {c.get('file_name', 'unknown')} p.{c.get('page', '?')}: {c.get('content', '')[:200]}"
            for i, c in enumerate(chunks[:6])
        )
        prompt = (
            "아래 문서 조각들을 바탕으로 질문을 분석하세요.\n\n"
            f"질문: {question}\n\n"
            f"문서 조각:\n{context_preview}\n\n"
            "지시사항:\n"
            "1. 질문에 '나', '내가', '우리', '저의' 등 사용자 개인 맥락(학과, 학년, 부서, 직책 등)이 필요한데 "
            "   해당 정보가 없어서 정확히 답하기 어려우면 아래 형식으로 반환하세요:\n"
            '   {"type":"context","question":"어느 학과/학년이신가요?"}\n\n'
            "2. 질문이 단순하거나 해석 방향이 하나뿐이면:\n"
            '   {"type":"direct"}\n\n'
            "3. 여러 관점이 가능하면 2-3개의 접근 방향을 제시하세요:\n"
            '   {"type":"options","items":[{"id":"1","label":"공식 요건 기준","description":"..."},{"id":"2","label":"실무 처리 기준","description":"..."}]}\n\n'
            "반드시 JSON만 출력하세요. 설명 없이.\n\n"
            "JSON:"
        )
        try:
            response = self._client.invoke([HumanMessage(content=prompt)])
            raw = str(response.content).strip()
            raw = raw.strip("```json").strip("```").strip()
            result = json.loads(raw)
            if not isinstance(result, dict):
                return {"type": "direct"}

            rtype = result.get("type")
            if rtype == "context" and result.get("question"):
                return {"type": "context", "question": str(result["question"])}
            if rtype == "options":
                items = result.get("items", [])
                validated = [
                    {"id": str(o["id"]), "label": str(o["label"]), "description": str(o.get("description", ""))}
                    for o in items
                    if isinstance(o, dict) and o.get("id") and o.get("label")
                ]
                return {"type": "options", "items": validated} if validated else {"type": "direct"}
            return {"type": "direct"}
        except Exception:
            return {"type": "direct"}

    def generate(self, question: str, chunks: list[Source], history: list[dict] | None = None, approach_hint: str | None = None) -> dict[str, Any]:
        if not chunks:
            return {
                "answer": "관련 문서를 찾지 못했습니다. 질문을 조금 더 구체적으로 입력해 주세요.",
                "sources": [],
            }

        prompt = self._build_prompt(question, chunks, history, approach_hint)
        response = self._client.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 기업 내부 문서 Q&A 도우미입니다. "
                        "반드시 제공된 문서 조각에 근거해서 한국어로 답변하세요. "
                        "근거가 부족하면 추측하지 말고 부족하다고 말하세요."
                    )
                ),
                HumanMessage(content=prompt),
            ]
        )
        return {"answer": str(response.content), "sources": _dedupe_sources(chunks)}

    def _build_prompt(self, question: str, chunks: list[Source], history: list[dict] | None = None, approach_hint: str | None = None) -> str:
        history_block = ""
        if history:
            history_lines = "\n".join(
                f"{'사용자' if msg['role'] == 'user' else 'AI'}: {msg['content'][:300]}"
                for msg in history
            )
            history_block = f"이전 대화:\n{history_lines}\n\n"

        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            source = f"{chunk.get('file_name', 'unknown')} p.{chunk.get('page', 'unknown')}"
            context_blocks.append(f"[{index}] {source}\n{chunk['content']}")

        approach_block = f"다음 관점에서 답변하세요: {approach_hint}\n\n" if approach_hint else ""
        return (
            "아래 문서 조각만 사용해서 질문에 답변하세요.\n\n"
            + approach_block
            + history_block
            + f"질문:\n{question}\n\n"
            + "문서 조각:\n"
            + "\n\n".join(context_blocks)
            + "\n\n답변에는 핵심 절차나 조건을 명확히 정리하세요."
        )


def _dedupe_sources(chunks: list[Source]) -> list[dict[str, Any]]:
    seen: set[tuple[Any, Any, str]] = set()
    sources: list[dict[str, Any]] = []
    for chunk in chunks:
        key = (chunk.get("file_name"), chunk.get("page"), chunk.get("content", ""))
        if key in seen:
            continue
        seen.add(key)
        sources.append(
            {
                "document_id": chunk.get("document_id"),
                "file_name": chunk.get("file_name"),
                "document_name": chunk.get("file_name"),
                "page": chunk.get("page"),
                "content": chunk.get("content"),
                "chunk_text": chunk.get("content"),
                "distance": chunk.get("distance"),
            }
        )
    return sources


def generate_answer(question: str, chunks: list[Source]) -> dict[str, Any]:
    return AnswerGenerator().generate(question, chunks)
