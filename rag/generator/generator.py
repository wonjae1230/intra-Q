"""응답파트"""

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

    def generate_query_variants(self, question: str, history: list[dict], n: int = 3) -> list[str]:
        """대화 기록 반영 + 다양한 관점 변형 쿼리를 단일 LLM 호출로 생성."""
        if n <= 1:
            return [question]

        # 히스토리 없으면 LLM 호출 없이 규칙 기반 변형으로 diversity 확보
        if not history:
            return _rule_based_variants(question, n)

        history_text = "\n".join(
            f"{'사용자' if msg['role'] == 'user' else 'AI'}: {msg['content'][:200]}"
            for msg in history
        )
        prompt = (
            "당신은 기업 내부 문서 검색 전문가입니다.\n"
            "아래 대화 기록과 새 질문을 보고 다음 두 가지를 동시에 수행하세요:\n"
            "1) 대명사('그것', '해당', '위의' 등)를 구체적 용어로 치환해 독립적인 쿼리로 재작성\n"
            f"2) 벡터 검색 다양화를 위해 서로 다른 표현·관점의 쿼리를 포함해 총 {n}개 생성\n\n"
            "출력 규칙: 쿼리만 새 줄에 하나씩. 번호나 설명 없이.\n\n"
            f"대화 기록:\n{history_text}\n\n"
            f"새 질문: {question}\n\n"
            "검색 쿼리들:"
        )
        response = self._client.invoke([HumanMessage(content=prompt)])
        lines = [l.strip().strip('"').strip("'") for l in str(response.content).strip().splitlines()]
        variants = [l for l in lines if l][:n]
        if not variants:
            return [question]
        return variants

    def rewrite_query(self, question: str, history: list[dict]) -> str:
        """generate_query_variants의 첫 번째 결과를 재사용 — 단독 호출 시 호환성 유지."""
        return self.generate_query_variants(question, history, n=1)[0]

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
        """프롬프트 리팩토링 파트"""
        prompt = (
            "당신은 질문 분석 전문가입니다. 아래 문서 조각들과 질문을 보고 세 가지 유형 중 하나로 분류하세요.\n\n"
            f"질문: {question}\n\n"
            f"문서 조각:\n{context_preview}\n\n"
            "분류 기준:\n\n"
            "유형 1 — 개인 맥락 필요 (context):\n"
            "  다음 조건을 모두 만족해야 합니다:\n"
            "  (a) 질문에 '나', '내가', '우리', '저의', '제' 등 1인칭 표현이 있다\n"
            "  (b) 문서에 학과·부서·직급·연도 등 여러 대상이 섞여 있어 어느 것을 검색해야 할지 알 수 없다\n"
            "  (c) 문서에 질문자의 이름·학번이 명시된 개인 기록(이체확인서, 영수증, 과제물 등)이 없다\n"
            "  → 조건을 모두 만족할 때만 맥락 확인 질문을 한국어로 작성하세요.\n"
            '  예: {"type":"context","question":"어느 학과/학년이신가요? (예: 소프트웨어융합학과 3학년)"}\n\n'
            "유형 2 — 단순 질문 (direct):\n"
            "  다음 중 하나라도 해당하면 direct로 분류하세요:\n"
            "  - 답변 방향이 명확하거나 문서에서 바로 찾을 수 있는 사실 기반 질문\n"
            "  - 문서에 질문자의 이름·학번이 명시된 개인 기록이 있어 바로 답변 가능한 경우\n"
            '  예: {"type":"direct"}\n\n'
            "유형 3 — 다관점 질문 (options):\n"
            "  동일 질문에 대해 해석 관점이 여러 개 존재하고, 사용자가 원하는 방향에 따라 답변이 달라지는 경우.\n"
            "  label은 5단어 이내, description은 한 문장으로 작성하세요.\n"
            '  예: {"type":"options","items":[{"id":"1","label":"공식 규정 기준","description":"규정집에 명시된 공식 절차와 요건 중심으로 답변합니다."},{"id":"2","label":"실무 적용 기준","description":"실제 업무에서 통용되는 실무 방식 중심으로 답변합니다."}]}\n\n'
            "반드시 JSON만 출력하세요. 마크다운 코드 블록 없이.\n\n"
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

        """최종 응답 파트 """
        prompt = self._build_prompt(question, chunks, history, approach_hint)
        response = self._client.invoke(
            [
                SystemMessage(
                    content=(
                        "당신은 기업 내부 문서 Q&A 전문 도우미입니다.\n\n"
                        "[핵심 원칙]\n"
                        "1. 반드시 제공된 문서 조각만을 근거로 답변하세요. "
                        "일반 학습 지식으로 보완하거나 추측하지 마세요.\n"
                        "2. 답변의 각 주요 사실·수치·절차를 언급할 때 반드시 해당 출처 번호([1], [2] 등)를 표시하세요.\n"
                        "3. 문서에서 확인되지 않는 정보는 '제공된 문서에서 [해당 내용]을 확인할 수 없습니다'라고 명확히 밝히세요.\n"
                        "4. 부분적으로만 답할 수 있다면 확인된 부분과 확인되지 않은 부분을 구분하여 설명하세요.\n"
                        "5. 답변은 한국어로 작성하세요."
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
            history_block = f"[이전 대화]\n{history_lines}\n\n"

        context_blocks = []
        for index, chunk in enumerate(chunks, start=1):
            source = f"{chunk.get('file_name', 'unknown')} p.{chunk.get('page', 'unknown')}"
            context_blocks.append(f"[{index}] 출처: {source}\n{chunk['content']}")

        approach_block = f"[답변 관점]\n{approach_hint}\n\n" if approach_hint else ""

        citation_guide = (
            "[출처 표기 규칙]\n"
            "- 사실·수치·절차를 언급할 때마다 [1], [2] 형식으로 출처 번호를 표시하세요.\n"
            "- 여러 문서가 같은 내용을 지지하면 [1][3]처럼 중복 표기하세요.\n"
            "- 문서에서 직접 확인되지 않는 내용은 절대 포함하지 마세요.\n"
            "- 질문에 답하기 위한 정보가 문서에 없다면 어떤 정보가 없는지 구체적으로 밝히세요.\n\n"
        )

        return (
            "아래 문서 조각만 사용해서 질문에 답변하세요.\n\n"
            + citation_guide
            + approach_block
            + history_block
            + f"[질문]\n{question}\n\n"
            + "[문서 조각]\n"
            + "\n\n".join(context_blocks)
            + "\n\n[답변] 핵심 절차·조건을 명확히 정리하고, 각 내용마다 출처 번호를 표시하세요."
        )


def _rule_based_variants(question: str, n: int) -> list[str]:
    """LLM 없이 한국어 조사 제거 + 키워드 조합으로 검색 쿼리 변형 생성 (0ms)."""
    import re

    variants: list[str] = [question]
    if n <= 1:
        return variants

    # 조사 제거 변형: 명사 + 조사 패턴에서 조사를 벗겨 키워드만 남김
    particles = r"(?:이|가|은|는|을|를|에서|에게|에|의|로부터|으로|로|과|와|도|만|까지|부터|이나|나|한테|께서)(?=\s|$)"
    stripped = re.sub(particles, " ", question).strip()
    stripped = re.sub(r"\s{2,}", " ", stripped)
    if stripped and stripped != question:
        variants.append(stripped)

    # 핵심 명사 키워드만 추출: 2글자 이상 한글 단어 중 의문사·조동사 제외
    stopwords = {"있나요", "있어요", "있어", "알려줘", "알려주세요", "무엇", "뭐야", "뭔가요",
                 "어떻게", "어떤", "언제", "어디", "누가", "왜", "어느", "어디서", "하나요",
                 "인가요", "인지", "해줘", "해주세요", "입니까", "입니다", "있습니다", "없나요"}
    tokens = re.findall(r"[가-힣]{2,}", question)
    keywords = [t for t in tokens if t not in stopwords]
    if keywords:
        keyword_query = " ".join(keywords)
        if keyword_query != question and keyword_query not in variants:
            variants.append(keyword_query)

    return variants[:n]


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
                # 교과과정 출처 강화 필드
                "curriculum_year": chunk.get("curriculum_year"),
                "college": chunk.get("college"),
                "department": chunk.get("department"),
                "subject_code": chunk.get("subject_code"),
                "subject_name": chunk.get("subject_name"),
                "category": chunk.get("category"),
                "credit": chunk.get("credit"),
                "semester": chunk.get("semester"),
            }
        )
    return sources


def generate_answer(question: str, chunks: list[Source]) -> dict[str, Any]:
    return AnswerGenerator().generate(question, chunks)
