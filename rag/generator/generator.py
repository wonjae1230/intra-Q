"""Answer generation from retrieved chunks."""

from __future__ import annotations

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
            thinking_budget=config.gemini_thinking_budget,
        )

    def generate(self, question: str, chunks: list[Source]) -> dict[str, Any]:
        if not chunks:
            return {
                "answer": "관련 문서를 찾지 못했습니다. 질문을 조금 더 구체적으로 입력해 주세요.",
                "sources": [],
            }

        prompt = self._build_prompt(question, chunks)
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

    def _build_prompt(self, question: str, chunks: list[Source]) -> str:
        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            source = f"{chunk.get('file_name', 'unknown')} p.{chunk.get('page', 'unknown')}"
            context_blocks.append(f"[{index}] {source}\n{chunk['content']}")

        return (
            "아래 문서 조각만 사용해서 질문에 답변하세요.\n\n"
            f"질문:\n{question}\n\n"
            "문서 조각:\n"
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
