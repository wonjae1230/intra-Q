# intra-Q
사내 문서를 AI가 읽고, 출처를 명시하며 답변하는 기업 내부 문서 RAG 챗봇
> ---
> DevOps 과정 프로젝트 우수상🥈 수상
 <img width="1063" height="541" alt="image" src="https://github.com/user-attachments/assets/cae9b432-678d-4151-a380-e2e98cb3e089" />

---

## 목차

1. [프로젝트 소개](#1-프로젝트-소개)
2. [주요 기능](#2-주요-기능)
3. [기술 스택](#3-기술-스택)
4. [시스템 아키텍처](#4-시스템-아키텍처)
5. [RAG 파이프라인 상세](#5-rag-파이프라인-상세)
6. [설치 및 실행](#6-설치-및-실행)
7. [API 레퍼런스](#7-api-레퍼런스)
8. [데이터베이스 스키마](#8-데이터베이스-스키마)
9. [RAG 설정값](#9-rag-설정값)
10. [성능 테스트 결과](#10-성능-테스트-결과)
11. [기업 도입 효과](#11-기업-도입-효과)
12. [향후 개선 방향](#12-향후-개선-방향)
13. [참고 논문](#13-참고-논문)

---

## 1. 프로젝트 소개

**intra-Q**는 기업 내부 PDF 문서를 기반으로 직원들의 질문에 AI가 답변하는 RAG(Retrieval-Augmented Generation) 챗봇 시스템입니다.

- HR 정책, 사내 규정, SOP, 컴플라이언스 문서 등을 업로드하면 즉시 검색 가능
- 모든 답변에 출처 파일명·페이지 번호를 인라인 표기 (`[1]`, `[2]`)
- 질문 유형에 따라 맥락 확인 질문 또는 다관점 선택 옵션 제시
- 채팅 세션 관리 및 참조 근거 카드 영구 저장

---

## 2. 주요 기능

| 기능 | 설명 |
|---|---|
| PDF 문서 업로드 | PyMuPDF 기반 텍스트 추출 → 청킹 → OpenAI 임베딩 → ChromaDB 저장 |
| Clarify 단계 | 질문 유형을 `context` / `direct` / `options` 세 가지로 분류, 불필요한 답변 생략 |
| Multi-Query RRF | 3개 변형 쿼리로 검색 후 Reciprocal Rank Fusion 합산 — 키워드 매몰 방지 |
| Vertex AI Reranker | 코사인 검색 후보 15개를 교차 인코더로 재정렬, 상위 5개만 LLM에 전달 |
| 인라인 출처 표기 | 답변 내 모든 사실·수치·절차마다 `[1]`, `[2]` 번호 표시 |
| 출처 카드 영구 저장 | 채팅방 재진입 후에도 참조 근거 카드 유지 (DB JSON 저장) |
| 채팅 세션 관리 | 대화 목록, 제목 편집, 삭제 기능 |
| 임베딩 상태 표시 | 업로드 후 임베딩 성공 / 실패를 UI에서 즉시 확인 |

---

## 3. 기술 스택

### Frontend

| 라이브러리 | 버전 | 역할 |
|---|---|---|
| React | 19.2.5 | UI 프레임워크 |
| React Router DOM | 7.15.0 | SPA 라우팅 |
| TailwindCSS | 4.2.4 | 스타일링 |
| React Markdown | 10.1.0 | AI 응답 마크다운 렌더링 |
| Vite | 8.0.10 | 번들러 |

### Backend

| 라이브러리 | 역할 |
|---|---|
| FastAPI ≥ 0.115.0 | REST API 서버 |
| SQLAlchemy ≥ 2.0.30 | ORM (SQLite) |
| python-jose + bcrypt | JWT 인증 / 비밀번호 해싱 |
| PyMuPDF ≥ 1.24.0 | PDF 텍스트 추출 |

### RAG 파이프라인

| 컴포넌트 | 기술 | 역할 |
|---|---|---|
| 임베딩 | OpenAI `text-embedding-3-small` | 텍스트 → 벡터 변환 |
| 벡터 DB | ChromaDB (HNSW, ef=200) | 벡터 저장 및 유사도 검색 |
| 리랭킹 | Vertex AI `semantic-ranker-default@latest` | 교차 인코더 재정렬 |
| 답변 생성 | Google Gemini 2.5 Flash | 최종 답변 + 출처 생성 |
| 오케스트레이션 | LangChain | RAG 파이프라인 조율 |

---

## 4. 시스템 아키텍처

```
intra-Q/
├── backend/
│   ├── app/
│   │   ├── routers/      ← auth, chat, documents, chat_history
│   │   ├── models/       ← SQLAlchemy ORM 모델
│   │   ├── schemas/      ← Pydantic 요청/응답 스키마
│   │   ├── services/     ← 비즈니스 로직
│   │   ├── db/           ← DB 초기화 및 자동 마이그레이션
│   │   └── main.py       ← FastAPI 진입점 (port 8000)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/        ← ChatPage, DocumentUploadPage 등
│   │   ├── components/   ← UI 공통 컴포넌트
│   │   └── App.jsx
│   └── package.json
└── rag/
    ├── embeddings/       ← OpenAI 임베딩
    ├── retriever/        ← ChromaDB 벡터 검색
    ├── reranker/         ← Vertex AI Semantic Ranker
    ├── generator/        ← Gemini 2.5 Flash 답변 생성
    ├── vectorstore/      ← ChromaDB upsert/delete
    ├── pipeline.py       ← 공개 API 진입점
    └── config.py         ← 환경 설정
```

---

## 5. RAG 파이프라인 상세

### 전체 흐름

```
사용자 질문
    │
    ▼
┌─────────────────────────────────────────┐
│              CLARIFY 단계                │
│  벡터 검색 → LLM 분석 → 세 가지 분기     │
│                                         │
│  context  → AI가 맥락 재질의             │
│  direct   → 즉시 Answer 단계            │
│  options  → 답변 방향 선택 카드 제시     │
└─────────────────────────────────────────┘
    │ 방향 선택 또는 direct 스킵
    ▼
┌─────────────────────────────────────────┐
│              ANSWER 단계                 │
│                                         │
│  1. 쿼리 확장 (Multi-Query 3변형)         │
│     - 히스토리 없음: 규칙 기반 (0ms)     │
│     - 히스토리 있음: LLM 단일 호출        │
│  2. 각 변형 쿼리로 ChromaDB 검색         │
│  3. Reciprocal Rank Fusion (RRF) 합산   │
│  4. 문서당 최대 2청크 제한               │
│  5. Vertex AI Reranker (상위 5개 선별)  │
│  6. Gemini 2.5 Flash 답변 생성          │
└─────────────────────────────────────────┘
    │
    ▼
인라인 출처 [1][2] 포함 답변 + 참조 카드 반환
```

---

### Clarify 분류 기준

| 유형 | 조건 |
|---|---|
| `context` | `나`, `내가`, `우리` 등 1인칭 표현 + 문서 내 여러 대상 혼재 + 개인 기록 없음 (세 조건 모두 충족 시) |
| `direct` | 사실 기반 단순 질문 / 개인 기록이 문서에 명시된 경우 |
| `options` | 동일 질문에 대해 관점에 따라 답변이 달라지는 경우 |

```python
# 반환 형식
{"type": "context",  "question": "어느 학과/학년이신가요?"}
{"type": "direct"}
{"type": "options",  "items": [{"id": "1", "label": "공식 규정 기준", "description": "..."}]}
```

---

### Multi-Query + RRF

단일 쿼리의 키워드 매몰 문제를 해결하기 위해 3개 변형 쿼리로 검색 후 RRF로 합산합니다.

```python
# RRF 공식: score = Σ 1 / (60 + rank)
# 각 쿼리 결과 목록에서 동일 청크의 순위를 합산해 최종 정렬
_RRF_K = 60
scores[key] += 1.0 / (_RRF_K + rank)
```

**규칙 기반 쿼리 변형 (히스토리 없을 때, 0ms)**

| 변형 종류 | 예시 (원본: "과기대에 과가 뭐뭐있는지 알려줘") |
|---|---|
| 원본 | 과기대에 과가 뭐뭐있는지 알려줘 |
| 조사 제거 | 과기대 과 뭐뭐있는지 알려줘 |
| 핵심 명사만 | 과기대 과 |

히스토리가 있을 때는 LLM 단일 호출로 대화 맥락 반영 + 3변형 동시 생성합니다.

---

### 파일명 접두사 주입

청크 임베딩 시 파일명을 내용 앞에 주입해 파일명 기반 검색을 가능하게 합니다.

```python
stem = document_row.file_name.rsplit(".", 1)[0]  # "이체확인증"
chunk["content"] = f"[{stem}]\n{chunk['content']}"
```

> 문서 재업로드 시 자동 적용됩니다.

---

### 출처 카드 영구 저장

```
어시스턴트 답변 생성
    → sources JSON 직렬화
    → chat_messages.sources 컬럼에 저장
    → 세션 재진입 시 역직렬화
    → 프론트 참조 근거 카드 복원
```

---

## 6. 설치 및 실행

### 사전 준비

- Python 3.11+
- Node.js 20+
- Google Cloud 프로젝트 (Vertex AI API 활성화)
- OpenAI API 키

### Backend

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env   # OPENAI_API_KEY, GOOGLE_CLOUD_PROJECT 등 설정
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

### RAG 모듈

```bash
cd rag
pip install -r requirements.txt
cp .env.example .env
```

**`rag/.env` 필수 항목**

```ini
OPENAI_API_KEY=sk-...
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_AI_LOCATION=us-central1
CHAT_MODEL=gemini-2.5-flash
```

**Vertex AI Reranker 사전 설정**

```bash
gcloud services enable discoveryengine.googleapis.com
gcloud auth application-default login
```

### E2E 검증

```bash
cd rag
source .venv/bin/activate
python test_pipeline.py
```

### 백엔드 직접 연동 (Python import)

```python
from rag.pipeline import embed_chunks, query

chunks = [
    {"content": "...", "document_id": 1, "file_name": "정책.pdf", "page": 3},
]

embed_result = embed_chunks(chunks)
# {"stored_count": 1, "ids": [...]}

answer_result = query("연차 신청은 어떻게 하나요?")
# {"answer": "연차는...", "sources": [{"file_name": "정책.pdf", "page": 3, ...}]}
```

---

## 7. API 레퍼런스

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
| POST | `/clarify` | 질문 유형 분류 (context / options / direct) |
| POST | `/` | RAG 기반 답변 생성 |
| GET | `/sessions` | 세션 목록 조회 |
| POST | `/sessions` | 새 세션 생성 |
| GET | `/sessions/{id}/messages` | 세션 메시지 + 참조 카드 조회 |
| PATCH | `/sessions/{id}` | 세션 제목 수정 |
| DELETE | `/sessions/{id}` | 세션 삭제 |

---

## 8. 데이터베이스 스키마

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
| user_id | INTEGER FK | 업로드 사용자 |
| embedding_status | TEXT | `pending` / `done` / `failed` |
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
| user_id | INTEGER FK | 작성자 |
| role | TEXT | `user` / `assistant` |
| content | TEXT | 메시지 내용 |
| sources | TEXT | JSON 배열 (참조 청크) |
| latency_ms | INTEGER | 응답 시간(ms) |
| created_at | DATETIME | 생성일 |

> **자동 마이그레이션**: `init_db.py`의 `_add_column_if_missing()` 패턴으로 기존 DB도 서버 재시작 시 자동으로 새 컬럼이 추가됩니다.

---

## 9. RAG 설정값

| 파라미터 | 기본값 | 설명 |
|---|---|---|
| `embedding_model` | `text-embedding-3-small` | OpenAI 임베딩 모델 |
| `chat_model` | `gemini-2.5-flash` | 답변 생성 모델 |
| `top_k` | `8` | ChromaDB 후보 청크 수 |
| `distance_threshold` | `1.2` | 코사인 거리 컷오프 |
| `reranker_enabled` | `true` | Vertex AI 재정렬 사용 여부 |
| `reranker_top_n` | `5` | 재정렬 후 최종 청크 수 |
| `reranker_fetch_multiplier` | `3` | ChromaDB에서 top_k × 3 수집 |
| `max_chunks_per_doc` | `2` | 문서당 최대 청크 (다양성 확보) |
| `query_variants_count` | `3` | 쿼리 변형 개수 |
| `chroma_search_ef` | `200` | HNSW 탐색 폭 (높을수록 정확) |

---

## 10. 성능 테스트 결과

### Reranker 도입 효과 (2026-05-07)

#### 질문: "소프트웨어융합학과의 졸업요건이 어떻게 돼?"

| 순위 | 벡터만 (713ms) | Reranker (1,652ms) |
|---|---|---|
| 1 | 융합전공 이수요건 일반 ❌ | **소프트웨어융합학과 교과과정** ✅ |
| 2 | 소프트웨어융합학과 ✅ | 소프트웨어융합학과 교과과정 ✅ |
| 3 | p.25 **중복** ❌ | 게임소프트웨어전공 |
| 4 | 게임소프트웨어전공 ❌ | 전자전기융합공학과 |
| 5 | 데이터사이언스전공 ❌ | 소프트웨어융합학과 참고 ✅ |

> 중복 청크 제거, 타 학과 청크 제거, 관련 청크가 1·2·5위 점유.

### 프롬프트 최적화 후 종합 비교 (2026-05-09)

| 측정 항목 | Reranker 도입 | 프롬프트 최적화 후 | 변화 |
|---|---|---|---|
| 인라인 인용 (Q1 졸업요건) | 0개 | **35개** | +35 |
| 인라인 인용 (Q2 SK하이닉스 매출) | 0개 | **5개** | +5 |
| 인라인 인용 (Q3 교육과정 변경) | 0개 | **8개** | +8 |
| Clarify 분류 정확도 | 기능 없음 | **3/3 정확 (100%)** | 신규 |
| 핵심 청크 1위 유지 | 1위 | **1위 유지** | 유지 |
| Graceful refusal | 없음 | **3/3 구체 설명** | 신규 |

### 응답 속도 (2026-05 최적화 후)

| 조건 | 응답 시간 |
|---|---|
| 히스토리 없음 (규칙 기반 변형, LLM 0회) | ~2~3초 |
| 히스토리 있음 (LLM 단일 호출) | ~4~6초 |
| Reranker 비활성화 시 | ~1~2초 단축 |

---

## 11. 기업 도입 효과

### 유즈케이스 시뮬레이션

#### Case A. 대형 제조기업 — 현장 규정 조회

직원 2,400명 규모. 품질 관리 매뉴얼·ISO 절차서·설비 SOP 300건 이상 보유. 현장 반장들이 작업 중 규정을 찾는 데 평균 18분 소비.

```
작업자: "3호 프레스 설비 예방정비 주기가 어떻게 돼?"
intra-Q: [SOP_Press_Maintenance_v4.pdf, p.12] 기준
         "3호 프레스는 월 1회 유압 오일 교체, 분기 1회 전체 점검"
```

| 지표 | 도입 전 | 도입 후 (예상) |
|---|---|---|
| 규정 조회 평균 소요 시간 | 18분 | 2분 |
| 오규정 적용 사례 (월) | 7건 | 1건 이하 |
| 현장 작업 지연 건수 (월) | 23건 | 8건 |

#### Case B. 중견 IT 기업 — HR 정책 및 온보딩

직원 450명, 연간 신규 입사자 80명. HR 팀이 동일한 문의를 하루 평균 15건 처리.

```
신입 사원: "육아휴직 후 복직 절차가 어떻게 돼요?"
intra-Q: [HR_Policy_2025.pdf, p.34, p.41] 기준
         복직 신청 → 팀장 확인 → HR 최종 승인 (복직 30일 전 신청 필수)
         → "정규직인지 계약직인지에 따라 다릅니다. 어느 쪽인가요?"
```

| 지표 | 도입 전 | 도입 후 (예상) |
|---|---|---|
| HR 반복 문의 응대 시간 (주) | 12시간 | 3시간 |
| 온보딩 완료 기간 | 3주 | 1.5주 |
| 신입 만족도 (NPS) | 42점 | 68점 |

#### Case C. 금융 서비스사 — 컴플라이언스 감사 대응

직원 1,100명의 핀테크 기업. 금융감독원 가이드라인·AML 정책 수동 검색에 1건당 평균 4시간 소요.

```
담당자: "고객 실명 확인 의무 규정 근거는?"
intra-Q: [AML_Internal_Policy_v7.pdf, p.8] + [FSS_Guideline_2024.pdf, p.23] 기준
         특정금융정보법 제5조 2항 + 내부통제 지침 3.2절 병행 적용
```

| 지표 | 도입 전 | 도입 후 (예상) |
|---|---|---|
| 감사 대응 1건 소요 시간 | 4시간 | 45분 |
| 규정 불일치 리스크 (반기) | 4건 | 0~1건 |
| 컴플라이언스 팀 초과근무 (월) | 38시간 | 12시간 |

---

### 정량 효과 (중견기업 450명, 연간)

| 항목 | 추정치 | 산출 근거 |
|---|---|---|
| 문서 검색 시간 절감 | 연 4,320시간 | 1인 월 2회 × 18분 절감 × 12개월 |
| HR 반복 응대 비용 절감 | 약 1,800만원 | HR 담당자 시급 × 절감 시간 |
| 온보딩 기간 단축 효과 | 약 960만원 | 신규 80명 × 1.5주 단축 × 생산성 환산 |
| 오정보 기반 의사결정 감소 | 리스크 비용 30% 절감 | 내부 감사 비용 기준 |

---

### 기업 규모별 도입 가이드

| 항목 | 소기업 (50명 이하) | 중견기업 (50~500명) | 대기업 (500명 이상) |
|---|---|---|---|
| 권장 문서 수 | 20~80건 | 100~500건 | 500건 이상 |
| 예상 구축 기간 | 1~2주 | 2~4주 | 4~8주 |
| ROI 회수 기간 | 3~6개월 | 2~4개월 | 1~3개월 |
| DB 권장 | SQLite | SQLite / PostgreSQL | PostgreSQL + 관리형 Vector DB |
| 주요 주의사항 | 초기 문서 정리 선행 | 부서별 문서 권한 설계 | SSO(LDAP/AD) 연동, 스케일링 전략 |

---

## 12. 향후 개선 방향

### 검색 품질

- [ ] **하이브리드 검색** — BM25 키워드 검색 + 벡터 검색 결합 (희귀 단어 누락 방지)
- [ ] **청크 전략 개선** — 표(Table) 인식 후 별도 청킹, 슬라이딩 윈도우 오버랩
- [ ] **신뢰도 임계값** — Reranker 점수 0.6 미만 시 "관련 문서 없음" 명시적 거부

### 기능 확장

- [ ] **다중 파일 형식** — DOCX, HWP, XLSX 지원 (파서 팩토리 패턴)
- [ ] **Confluence / Notion 연동** — REST API 기반 주기적 청크 갱신 스케줄러
- [ ] **사용자별 문서 권한** — `PUBLIC` / `TEAM` / `PRIVATE` 가시성 레이어
- [ ] **응답 스트리밍** — SSE로 토큰 단위 실시간 출력

### 인프라

- [ ] **Vector DB 분리** — ChromaDB → Qdrant / Weaviate (대규모 확장)
- [ ] **관계형 DB 전환** — SQLite → PostgreSQL (동시 사용자 증가 대응)
- [ ] **관리자 대시보드** — 문서 관리 + 질문 로그 분석 + 👍 / 👎 피드백 수집
- [ ] **CI/CD** — GitHub Actions + Docker Compose 배포 자동화

---

## 13. 참고 논문

| 논문 / 출처 | 연도 | 핵심 내용 |
|---|---|---|
| _FACTUM: Citation Hallucination in Long-Form RAG_ (arXiv 2601.05866) | 2025 | RAG 시스템의 17~33%가 잘못된 인용 생성 → 인라인 citation 의무화 근거 |
| _Enhancing RAG: A Study of Best Practices_ (arXiv 2501.07391) | 2025 | 쿼리 리라이팅으로 검색 정밀도 30~45% 향상 |
| _Searching for Best Practices in RAG_ (arXiv 2407.01219) | 2024 | 부분 답변 구분 지시로 faithfulness 향상 |
| _MEGA-RAG: Multi-Evidence Guided Answer Refinement_ | 2025 | 다관점 출처 구분으로 신뢰도 향상 |
| _CoT-RAG: Integrating Chain of Thought and RAG_ (arXiv 2504.13534) | 2025 | 추론 체인 통합 |
| _Conflict-Aware Soft Prompting for RAG_ (arXiv 2508.15253) | 2025 | 문서 간 충돌 처리 |
| _Query Rewrite in RAG Systems_ (DEV Community) | 2024 | 인프라 변경 없이 정밀도 30~45% 향상 |
| _Prompt Engineering with Anthropic's Claude 3_ (AWS ML Blog) | 2024 | Graceful refusal 패턴 — 막연한 거절 → 구체적 부재 설명 |

---

*Last updated: 2026-05-11*
