# 🏢 intra-Q — 기업 내부 문서 RAG 챗봇

> 사내 문서를 AI가 읽고, 출처를 명시하며 답변하는 엔터프라이즈 Q&A 시스템

---

## 📌 프로젝트 개요

| 항목 | 내용 |
|---|---|
| 프로젝트명 | intra-Q |
| 목적 | 기업 내부 문서(PDF) 기반 RAG 챗봇 |
| 주요 사용자 | 사내 직원 (HR, 재무, 정책, 업무 규정 등 문의) |
| 배포 형태 | 로컬 SQLite + ChromaDB MVP |

---

## 🗂 디렉터리 구조

```
intra-Q/
├── backend/              ← FastAPI 서버
│   ├── app/
│   │   ├── routers/      ← auth, chat, documents, chat_history
│   │   ├── models/       ← SQLAlchemy ORM 모델
│   │   ├── schemas/      ← Pydantic 요청/응답 스키마
│   │   ├── services/     ← 비즈니스 로직
│   │   ├── db/           ← DB 초기화 및 마이그레이션
│   │   └── main.py       ← FastAPI 진입점
│   └── requirements.txt
├── frontend/             ← React SPA
│   ├── src/
│   │   ├── pages/        ← ChatPage, DocumentUploadPage 등
│   │   ├── components/   ← UI 공통 컴포넌트
│   │   └── App.jsx
│   └── package.json
└── rag/                  ← RAG 파이프라인 모듈
    ├── embeddings/       ← OpenAI text-embedding-3-small
    ├── retriever/        ← ChromaDB 벡터 검색
    ├── reranker/         ← Vertex AI Semantic Ranker
    ├── generator/        ← Gemini 2.5 Flash 답변 생성
    ├── vectorstore/      ← ChromaDB 저장 레이어
    ├── pipeline.py       ← 공개 API 진입점
    └── config.py         ← 환경 설정
```

---

## ⚙️ 기술 스택

### Frontend

| 라이브러리 | 버전 | 역할 |
|---|---|---|
| React | 19.2.5 | UI 프레임워크 |
| React Router DOM | 7.15.0 | SPA 라우팅 |
| TailwindCSS | 4.2.4 | 스타일링 |
| React Markdown | 10.1.0 | AI 응답 마크다운 렌더링 |
| Vite | 8.0.10 | 번들러 |

### Backend

| 라이브러리 | 버전 | 역할 |
|---|---|---|
| FastAPI | ≥0.115.0 | REST API 서버 |
| SQLAlchemy | ≥2.0.30 | ORM (SQLite) |
| python-jose | - | JWT 인증 |
| passlib + bcrypt | - | 비밀번호 해싱 |
| PyMuPDF | ≥1.24.0 | PDF 텍스트 추출 |

### RAG 파이프라인

| 컴포넌트 | 기술 | 역할 |
|---|---|---|
| Embedding | OpenAI `text-embedding-3-small` | 텍스트 → 벡터 변환 |
| Vector DB | ChromaDB (HNSW) | 벡터 저장 및 유사도 검색 |
| Reranker | Vertex AI `semantic-ranker-default@latest` | 교차 인코더 재정렬 |
| Generator | Google Gemini 2.5 Flash | 최종 답변 생성 |
| Orchestration | LangChain | RAG 파이프라인 조율 |

---

## 🔄 RAG 파이프라인 아키텍처

```
사용자 질문
    ↓
[1단계: Clarify 분류]
    LLM이 질문 유형 분류
    - context  → 개인 맥락 확인 필요 (예: "어느 학과이신가요?")
    - options  → 다관점 질문 (예: "공식 규정 기준 / 실무 적용 기준")
    - direct   → 바로 답변 가능
    ↓
[2단계: 쿼리 확장]
    히스토리 없음 → 규칙 기반 3변형 (0ms, LLM 미사용)
    히스토리 있음 → LLM 단일 호출로 rewrite + 3변형 동시 생성
    ↓
[3단계: 벡터 검색 (Multi-Query RRF)]
    각 변형 쿼리로 ChromaDB 검색
    → Reciprocal Rank Fusion(RRF)으로 결과 합산
    → 문서당 최대 2청크 제한 (집중화 방지)
    ↓
[4단계: Reranking]
    Vertex AI Semantic Ranker로 교차 인코더 재정렬
    → Top-N 청크 선별
    ↓
[5단계: 답변 생성]
    Gemini 2.5 Flash가 청크만 근거로 답변
    → 각 사실마다 출처 번호 [1][2] 표기
    → 문서에 없는 내용은 명확히 고지
```

---

## 🧠 핵심 기술 상세

### ① Multi-Query + RRF (검색 다양성)

단일 쿼리의 키워드 집착 문제 해결을 위해 3가지 변형 쿼리로 검색 후 RRF 합산

```python
# RRF 공식: score = Σ 1/(60 + rank)
def _reciprocal_rank_fusion(result_lists):
    scores = {}
    for results in result_lists:
        for rank, chunk in enumerate(results, start=1):
            key = chunk.get("content", "")
            scores[key] = scores.get(key, 0.0) + 1.0 / (60 + rank)
    return sorted by score descending
```

### ② 규칙 기반 쿼리 변형 (0ms)

히스토리 없을 때 LLM 없이 즉시 생성하는 절충안

| 변형 종류 | 예시 (원본: "과기대에 과가 뭐뭐있는지 알려줘") |
|---|---|
| 원본 | 과기대에 과가 뭐뭐있는지 알려줘 |
| 조사 제거 | 과기대 과 뭐뭐있는지 알려줘 |
| 핵심 명사만 | 과기대 과 |

### ③ HNSW ef 버그 수정

ChromaDB `n_results=10` 요청 시 HNSW 인덱스가 실제 최근접 이웃을 놓치는 문제 수정

```python
# 수정 전: n_results=top_k → 가까운 벡터를 MISS
# 수정 후: n_results=total (전체 스캔) → 슬라이싱
query_kwargs = {"n_results": total, ...}
return filtered[:top_k]  # 이후 상위 K개만 반환
```

### ④ 파일명 접두사 삽입 (인식률 향상)

청크 임베딩 시 파일명을 내용 앞에 주입해 파일명 기반 검색 가능

```python
stem = document_row.file_name.rsplit(".", 1)[0]  # "이체확인증"
chunk["content"] = f"[{stem}]\n{chunk['content']}"
```

### ⑤ 출처 카드 영구 저장

채팅방 재진입 후에도 참조 근거 카드 유지

- `chat_messages.sources` 컬럼(TEXT/JSON) 추가
- 어시스턴트 메시지 저장 시 sources 직렬화
- 히스토리 조회 시 역직렬화 → 프론트 `evidence` 카드 복원

---

## 🗄 데이터베이스 스키마 (SQLite)

### users

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INTEGER PK | 사용자 ID |
| username | TEXT UNIQUE | 로그인 아이디 |
| hashed_password | TEXT | bcrypt 해시 |
| created_at | DATETIME | 가입일 |

### documents

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INTEGER PK | 문서 ID |
| file_name | TEXT | 원본 파일명 |
| user_id | INTEGER FK | 업로드한 사용자 |
| embedding_status | TEXT | pending / done / failed |
| created_at | DATETIME | 업로드일 |

### chat_sessions

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INTEGER PK | 세션 ID |
| user_id | INTEGER FK | 소유 사용자 |
| title | TEXT | 세션 제목 |
| created_at | DATETIME | 생성일 |
| updated_at | DATETIME | 최근 메시지 시각 |

### chat_messages

| 컬럼 | 타입 | 설명 |
|---|---|---|
| id | INTEGER PK | 메시지 ID |
| session_id | INTEGER FK | 소속 세션 |
| user_id | INTEGER FK | 메시지 작성자 |
| role | TEXT | user / assistant |
| content | TEXT | 메시지 내용 |
| sources | TEXT | JSON (참조 청크 배열) |
| latency_ms | INTEGER | 응답 시간(ms) |
| created_at | DATETIME | 생성일 |

---

## 🌐 API 엔드포인트

### 인증 (`/api/auth`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/register` | 회원가입 |
| POST | `/login` | 로그인 (JWT 발급) |
| GET | `/me` | 현재 사용자 정보 |

### 문서 (`/api/documents`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/upload` | PDF 업로드 + 청킹 + 임베딩 |
| GET | `/` | 문서 목록 조회 |
| DELETE | `/{document_id}` | 문서 삭제 + 벡터 제거 |

### 챗봇 (`/api/chat`)

| 메서드 | 경로 | 설명 |
|---|---|---|
| POST | `/clarify` | 질문 유형 분류 (context/options/direct) |
| POST | `/` | RAG 기반 답변 생성 |
| GET | `/sessions` | 세션 목록 |
| POST | `/sessions` | 새 세션 생성 |
| GET | `/sessions/{id}/messages` | 세션 메시지 조회 |
| PATCH | `/sessions/{id}` | 세션 제목 수정 |
| DELETE | `/sessions/{id}` | 세션 삭제 |

---

## ⚡ RAG 설정값 (`rag/config.py`)

| 파라미터 | 값 | 설명 |
|---|---|---|
| `embedding_model` | `text-embedding-3-small` | OpenAI 임베딩 모델 |
| `chat_model` | `gemini-2.5-flash` | 답변 생성 모델 |
| `top_k` | `8` | ChromaDB 후보 청크 수 |
| `distance_threshold` | `1.2` | 코사인 거리 컷오프 |
| `reranker_enabled` | `true` | Vertex AI 재정렬 사용 여부 |
| `reranker_top_n` | `5` | 재정렬 후 최종 청크 수 |
| `max_chunks_per_doc` | `2` | 문서당 최대 청크 (다양성) |
| `query_variants_count` | `3` | 쿼리 변형 개수 |
| `chroma_search_ef` | `200` | HNSW 탐색 폭 |

---

## 🐛 해결한 주요 문제들

### 1. 키워드 매몰 문제

- **증상**: 동일 단어 포함 문서만 반복 검색, 다른 관련 문서 누락
- **원인**: 단일 쿼리 벡터 검색의 한계
- **해결**: Multi-Query 생성 + RRF 합산 + 문서당 청크 2개 제한

### 2. 이체확인증 / 특정 문서 미인식

- **증상**: 특정 PDF를 직접적으로 물어봐도 검색 미스
- **원인**: ChromaDB HNSW `n_results=10` 버그 — 실제 최근접 이웃을 건너뜀
- **해결**: `n_results=total` 전체 스캔 후 슬라이싱으로 변경

### 3. 파일명 기반 검색 불가 (인초강 9주차 등)

- **증상**: 파일명에 있는 키워드로 물어봐도 못 찾음
- **원인**: 파일명이 임베딩에 포함되지 않음
- **해결**: 청크 저장 시 `[파일명]\n내용` 형식으로 파일명 접두사 주입

### 4. 채팅방 재진입 시 출처 카드 소멸

- **증상**: 대화 중에는 참조 근거가 보이지만 나갔다 오면 사라짐
- **원인**: `sources` 데이터를 DB에 저장하지 않았음
- **해결**: `chat_messages.sources` JSON 컬럼 추가 + 저장/복원 로직 구현

### 5. PR 머지 후 팀원 DB 오류

- **증상**: `sources` 컬럼 없다는 에러 — 기존 SQLite 파일 사용 팀원
- **원인**: SQLAlchemy `create_all()`은 기존 테이블을 ALTER하지 않음
- **해결**: `init_db.py`에 `_add_column_if_missing()` 패턴으로 자동 마이그레이션

### 6. RAG 수정 후 응답 속도 저하

- **증상**: 질문당 6~10초 추가 지연
- **원인**: `generate_query_variants` LLM 호출이 clarify + chat 양쪽에서 발생
- **해결**:
  - clarify 단계에서 쿼리 변형 제거
  - 히스토리 없을 때 규칙 기반 변형으로 대체 (0ms)
  - 히스토리 있을 때 rewrite + variants를 단일 LLM 호출로 통합

---

## 📊 성능 지표 (2026-05 기준)

| 조건 | 응답 시간 |
|---|---|
| 히스토리 없음 (규칙 기반 변형) | ~2~3초 (임베딩 + 검색 + 생성) |
| 히스토리 있음 (LLM 변형 1회) | ~4~6초 |
| Reranker 미사용 시 | ~1~2초 단축 |

---

## 🔧 로컬 실행 방법

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev  # localhost:5173
```

### RAG 모듈 (독립 실행 시)

```bash
cd rag
pip install -r requirements.txt
python test_pipeline.py
```

### 환경변수 (`rag/.env`)

```
OPENAI_API_KEY=...
GOOGLE_CLOUD_PROJECT=...
VERTEX_AI_LOCATION=us-central1
```

---

## 🗺 향후 개선 방향

- [ ] **하이브리드 검색** — BM25 키워드 검색 + 벡터 검색 결합
- [ ] **청크 전략 개선** — 표(Table) 인식 후 별도 청킹
- [ ] **다중 파일 형식** — DOCX, HWP, XLSX 지원
- [ ] **사용자별 문서 권한** — 부서/역할별 접근 제어
- [ ] **응답 스트리밍** — SSE로 토큰 단위 실시간 출력
- [ ] **관리자 대시보드** — 문서 관리 + 질문 로그 분석
- [ ] **Vector DB 분리** — ChromaDB → Qdrant/Weaviate (확장성)
- [ ] **CI/CD** — GitHub Actions + Docker Compose 배포 자동화
