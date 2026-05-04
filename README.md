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

`.env`에 `GOOGLE_API_KEY`를 설정합니다.

### 백엔드 연동 인터페이스

MVP에서는 백엔드가 같은 Python 환경에서 직접 import하는 Option A를 권장합니다.
RAG를 별도 FastAPI 서버로 분리하는 Option B는 배포 경계가 필요해질 때 검토합니다.

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

- `rag/embeddings/embedder.py`: Gemini embedding 기반 임베딩
- `rag/vectorstore/store.py`: Chroma 영구 저장소에 벡터와 메타데이터 저장 및 검색
- `rag/retriever/retriever.py`: 질문 임베딩 후 Top-K 유사 청크 검색
- `rag/generator/generator.py`: 검색 청크 기반 Gemini 2.5 Flash 답변 생성
- `rag/pipeline.py`: 백엔드 호출용 `embed_chunks()`, `query()` 진입점

### E2E 검증

`rag/.env`에 실제 `GOOGLE_API_KEY`를 설정한 뒤 실행합니다.

```bash
source rag/.venv/bin/activate
python -m rag.test_pipeline
```

또는 `rag/` 디렉터리 안에서 실행할 수 있습니다.

```bash
cd rag
source .venv/bin/activate
python test_pipeline.py
```
