# intra-Q
기업 내부 문서 Q&amp;A 챗봇 — RAG 기반 사내 지식베이스 검색 및 질의응답 시스템

## RAG 모듈

### 환경 설정

```bash
python3 -m venv rag/.venv
source rag/.venv/bin/activate
pip install -r rag/requirements.txt
cp rag/.env.example rag/.env
```

`.env`에 `OPENAI_API_KEY`를 설정합니다.

### 백엔드 연동 인터페이스

```python
from rag.pipeline import embed_chunks, query

chunks = [
    {"content": "...", "document_id": 1, "file_name": "정책.pdf", "page": 3},
]

embed_result = embed_chunks(chunks)
answer_result = query("연차 신청은 어떻게 하나요?")
```

`query()` 반환 형식:

```python
{
    "answer": "연차는 사내 시스템에서...",
    "sources": [
        {"file_name": "정책.pdf", "page": 3, "content": "..."},
    ],
}
```

### 구현 구조

- `rag/embeddings/embedder.py`: OpenAI `text-embedding-3-small` 임베딩
- `rag/vectorstore/store.py`: Chroma 영구 저장소에 벡터와 메타데이터 저장 및 검색
- `rag/retriever/retriever.py`: 질문 임베딩 후 Top-K 유사 청크 검색
- `rag/generator/generator.py`: 검색 청크 기반 `gpt-4o-mini` 답변 생성
- `rag/pipeline.py`: 백엔드 호출용 `embed_chunks()`, `query()` 진입점
