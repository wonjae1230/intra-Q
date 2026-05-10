# intra-Q

기업 내부 문서를 기반으로 답변하는 RAG Q&A 챗봇입니다. 사용자가 PDF 문서를 업로드하면 백엔드가 텍스트를 추출하고 청크로 분리한 뒤, RAG 파이프라인을 통해 관련 문서 근거를 찾아 답변을 생성합니다.

## 주요 기능

- 사용자 회원가입, 로그인, JWT 기반 인증
- PDF 문서 업로드 및 텍스트 추출
- 문서별 청크 생성 및 SQLite 저장
- ChromaDB 기반 벡터 저장 및 검색
- RAG 기반 질의응답
- 답변 출처 제공
- 문서 목록, 문서 상세, 채팅 이력 관리

## 기술 스택

### Frontend

- React
- Vite
- React Router
- Tailwind CSS

### Backend

- FastAPI
- SQLAlchemy
- SQLite
- JWT 인증
- PyMuPDF

### RAG

- LangChain
- ChromaDB
- Gemini Embedding
- Gemini 2.5 Flash

## 프로젝트 구조

```text
intra-Q/
├── backend/                 # FastAPI 백엔드
│   ├── app/
│   │   ├── core/            # 설정, 인증 의존성, 보안 유틸
│   │   ├── database/        # DB 세션 및 초기화
│   │   ├── models/          # SQLAlchemy 모델
│   │   ├── routers/         # API 라우터
│   │   ├── schemas/         # 요청/응답 스키마
│   │   ├── services/        # 비즈니스 로직
│   │   └── main.py          # FastAPI 앱 엔트리포인트
│   ├── tests/
│   └── requirements.txt
├── frontend/                # React 프론트엔드
│   ├── src/
│   │   ├── components/      # 공통 UI 컴포넌트
│   │   ├── lib/             # API, 인증 유틸
│   │   ├── pages/           # 화면 단위 컴포넌트
│   │   ├── router/          # 라우팅 및 가드
│   │   └── main.jsx
│   └── package.json
├── rag/                     # RAG 파이프라인
│   ├── embeddings/          # 임베딩 생성
│   ├── generator/           # 답변 생성
│   ├── reranker/            # 검색 결과 재정렬
│   ├── retriever/           # 유사 청크 검색
│   ├── vectorstore/         # ChromaDB 저장소
│   ├── pipeline.py          # 백엔드 연동 진입점
│   └── requirements.txt
├── INSIGHT.md
└── README.md
```

## 실행 준비

### 1. 환경 변수

루트 `.env`, `backend/.env`, `rag/.env` 중 하나에 필요한 값을 설정합니다. 백엔드는 루트 `.env`, `backend/.env`, `rag/.env` 순서로 환경 변수를 로드합니다.

```env
DATABASE_URL=sqlite:///./intra_q.db
GOOGLE_API_KEY=your-google-api-key
OPENAI_API_KEY=your-openai-api-key
JWT_SECRET_KEY=change-this-dev-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

현재 RAG 파이프라인은 `GOOGLE_API_KEY`가 필요합니다.

### 2. Backend 실행

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

기본 주소는 다음과 같습니다.

```text
http://localhost:8000
```

헬스 체크:

```text
GET /health
```

### 3. Frontend 실행

```bash
cd frontend
npm install
npm run dev
```

기본 주소는 다음과 같습니다.

```text
http://localhost:5173
```

### 4. RAG 단독 실행

루트 디렉터리 기준:

```bash
python -m rag.test_pipeline
```

또는 `rag/` 디렉터리에서:

```bash
cd rag
python test_pipeline.py
```

## API 개요

FastAPI 앱은 `backend/app/main.py`에서 라우터를 등록합니다.

### Auth

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/auth/register` | 회원가입 |
| POST | `/api/auth/login` | 로그인 및 JWT 발급 |
| GET | `/api/auth/me` | 현재 사용자 조회 |

### Documents

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/documents/upload` | PDF 업로드, 텍스트 추출, 청크 저장, 임베딩 생성 |
| GET | `/api/documents` | 로그인 사용자의 문서 목록 조회 |
| GET | `/api/documents/{document_id}` | 문서 상세 및 청크 미리보기 조회 |
| DELETE | `/api/documents/{document_id}` | 문서, 청크, 벡터 데이터 삭제 |

### Chat

| Method | Path | Description |
| --- | --- | --- |
| POST | `/api/chat` | 질문 답변 생성 및 채팅 이력 저장 |
| GET | `/api/chat/history` | 채팅 이력 조회 |
| DELETE | `/api/chat/history` | 채팅 이력 삭제 |

## RAG 처리 흐름

```text
PDF 업로드
→ PyMuPDF로 페이지별 텍스트 추출
→ 페이지 텍스트를 청크로 분리
→ SQLite에 문서 및 청크 저장
→ Gemini Embedding으로 청크 임베딩 생성
→ ChromaDB에 벡터와 메타데이터 저장
→ 사용자 질문 입력
→ 질문 임베딩 생성
→ 관련 청크 검색
→ 필요 시 검색 결과 재정렬
→ Gemini 2.5 Flash로 답변 생성
→ 답변과 출처 반환
```

백엔드에서 사용하는 RAG 진입점은 `rag/pipeline.py`입니다.

```python
from rag.pipeline import embed_chunks, query

chunks = [
    {
        "content": "문서 본문",
        "document_id": 1,
        "file_name": "policy.pdf",
        "page": 1,
    },
]

embed_result = embed_chunks(chunks)
answer_result = query("연차 신청은 어떻게 하나요?")
```

`query()`는 답변과 출처 정보를 포함한 결과를 반환합니다.

```python
{
    "answer": "연차 신청은 ...",
    "sources": [
        {
            "file_name": "policy.pdf",
            "page": 1,
            "content": "근거 문서 내용",
        },
    ],
}
```

자세한 RAG 설계는 `rag/RAG_ARCHITECTURE.md`를 참고합니다.

## Frontend 라우트

프론트엔드 라우팅은 `frontend/src/router/index.jsx`에서 관리합니다.

| Path | Page |
| --- | --- |
| `/` | 초기/빈 상태 화면 |
| `/login` | 로그인 |
| `/signup` | 회원가입 |
| `/upload` | 문서 업로드 |
| `/documents` | 문서 관리 |
| `/documents/detail` | 문서 상세 |
| `/chat` | 채팅 |
| `/error/not-found` | 답변 없음 |
| `/error/server` | 서버 오류 |

## 테스트 및 검증

### Backend

```bash
cd backend
pytest
```

### Frontend

```bash
cd frontend
npm run lint
npm run build
```

### RAG

```bash
python -m rag.test_pipeline
```

## 개발 참고

- 백엔드 앱 엔트리포인트는 `backend/app/main.py`입니다.
- 백엔드 설정 값은 `backend/app/core/settings.py`에서 로드합니다.
- 문서 업로드 로직은 `backend/app/routers/documents.py`에 있습니다.
- 채팅 응답 생성은 `backend/app/routers/chat.py`와 `backend/app/services/chat_service.py`에서 처리합니다.
- 프론트엔드 API 유틸은 `frontend/src/lib/api.js`에 있습니다.
- RAG 백엔드 연동 함수는 `rag/pipeline.py`의 `embed_chunks()`, `query()`, `delete_document_embeddings()`입니다.
