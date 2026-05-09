# Intra-Q RAG 기술 문서

사내 PDF 문서 Q&A 시스템 **Intra-Q**의 RAG(Retrieval-Augmented Generation) 파이프라인 전반을 설명합니다.

---

## 목차

1. [전체 파이프라인 개요](#1-전체-파이프라인-개요)
2. [구성 요소별 기술 스택](#2-구성-요소별-기술-스택)
3. [Clarify 단계 — 답변 방향 설계](#3-clarify-단계--답변-방향-설계)
4. [Reranker — 검색 품질 개선](#4-reranker--검색-품질-개선)
5. [프롬프트 최적화](#5-프롬프트-최적화)
6. [설정값 및 환경변수](#6-설정값-및-환경변수)
7. [참고 논문 및 출처](#7-참고-논문-및-출처)

---

## 1. 전체 파이프라인 개요

```
사용자 질문 입력
       │
       ▼
┌─────────────────────────────────────────┐
│              CLARIFY 단계                │
│  벡터 검색 → LLM 분석 → 세 가지 분기          │
│                                         │
│  [맥락 부족] → AI가 재질의                  │
│  [단순 질문] → 바로 답변 생성                │
│  [다관점 질문] → 접근 방향 선택 카드           │
└─────────────────────────────────────────┘
       │ 방향 선택 또는 스킵
       ▼
┌─────────────────────────────────────────┐
│              ANSWER 단계                 │
│                                         │
│  1. 쿼리 리라이팅 (대화 기록 기반)             │
│  2. OpenAI 임베딩                         │
│  3. ChromaDB 벡터 검색 (후보 15개)          │
│  4. Vertex AI Reranker (상위 5개 선별)     │
│  5. Gemini 2.5 Flash 답변 생성            │
└─────────────────────────────────────────┘
       │
       ▼
  인라인 출처 [1][2] 포함 답변 반환
```

### 후속 질문 처리

```
첫 질문 완료 → sessionDocumentIds 저장
       │
후속 질문 감지 (sessionDocumentIds 존재)
       │
       ▼
쿼리 리라이팅 → 벡터 검색 → Reranker → 답변
(Clarify 단계 스킵, 같은 문서 세트 재사용)
```

---

## 2. 구성 요소별 기술 스택

| 단계      | 기술                  | 모델/버전                        | 역할                             |
| --------- | --------------------- | -------------------------------- | -------------------------------- |
| 문서 파싱 | PyMuPDF               | —                                | PDF → 텍스트 청크 분할           |
| 임베딩    | OpenAI API            | `text-embedding-3-small`         | 텍스트 → 벡터 변환               |
| 벡터 저장 | ChromaDB              | —                                | 청크 임베딩 영구 저장            |
| 리랭킹    | Vertex AI Ranking API | `semantic-ranker-default@latest` | 후보 청크 정밀 재정렬            |
| 답변 생성 | Vertex AI (LangChain) | `gemini-2.5-flash`               | 답변 + 출처 생성                 |
| 백엔드    | FastAPI + SQLAlchemy  | —                                | API 서버, 사용자 인증, 채팅 이력 |
| 벡터 DB   | ChromaDB (파일 기반)  | —                                | 서버리스, 로컬 저장              |
| 사용자 DB | SQLite                | —                                | 사용자·문서·채팅 이력            |

### 파일 구조

```
rag/
├── pipeline.py          # 공개 진입점 (embed_chunks, query, search_with_options)
├── config.py            # 환경변수 로딩
├── embeddings/
│   └── embedder.py      # OpenAI 임베딩
├── retriever/
│   └── retriever.py     # ChromaDB 검색
├── reranker/
│   └── reranker.py      # Vertex AI Reranker
├── generator/
│   └── generator.py     # 쿼리 리라이팅, Clarify 분석, 답변 생성
└── vectorstore/
    └── store.py         # ChromaDB upsert/delete
```

---

## 3. Clarify 단계 — 답변 방향 설계

### 배경

기존에는 "어떤 문서를 기반으로 답변할까요?"라고 묻는 문서 선택 카드 방식이었습니다. 이 방식의 문제:

- 사용자가 문서 내용을 모르면 선택 불가
- 문서 목록이 많을수록 의미 없는 선택지

**변경 후**: AI가 검색된 청크를 먼저 분석한 뒤 "어떤 관점으로 답변할까요?"를 제시합니다.

### LLM 분류 로직 (`generate_clarify_options`)

벡터 검색 후 상위 청크를 LLM에 넘겨 세 가지 유형 중 하나를 JSON으로 반환합니다.

```python
# 반환 형식
{"type": "context",  "question": "어느 학과/학년이신가요?"}   # 개인 맥락 필요
{"type": "direct"}                                             # 단순 질문, 바로 답변
{"type": "options",  "items": [{id, label, description}]}     # 다관점 선택 카드
```

**분류 기준**

| 유형      | 조건                                                                                                |
| --------- | --------------------------------------------------------------------------------------------------- |
| `context` | `나`, `내가`, `우리` 등이 포함되어 있고, 문서 내 여러 대상(학과·부서·직급) 중 어느 것인지 특정 불가 |
| `direct`  | 사실 기반 단순 질문, 해석 방향이 하나뿐                                                             |
| `options` | 동일 질문에 대해 관점에 따라 답변이 달라지는 경우                                                   |

### 맥락 재질의 흐름

```
"내가 필수로 들어야하는 전공과목이 뭐야"
  └→ [context] AI: "어느 학과/학년이신가요? (예: 소프트웨어융합학과 3학년)"
       └→ 사용자: "소프트웨어융합학과 3학년이야"
            └→ "내가 필수로 들어야하는 전공과목이 뭐야 (소프트웨어융합학과 3학년)"
                 로 원본 질문에 맥락 합쳐 clarify 재실행
```

### approach_hint 전달 흐름

사용자가 접근 방향을 선택하면 `label + description`을 `approach_hint`로 조합해 최종 답변 생성 시 프롬프트에 주입합니다.

```
사용자: "공식 규정 기준" 선택
  └→ approach_hint = "공식 규정 기준: 규정집에 명시된 공식 절차와 요건 중심으로 답변합니다."
       └→ POST /api/chat { approach_hint: "..." }
            └→ _build_prompt() 앞에 [답변 관점] 블록으로 삽입
```

### 스키마 변경 이력

```python
# ClarifyOption — 변경 전
class ClarifyOption(BaseModel):
    document_id: int
    file_name: str
    preview: str
    chunk_count: int

# ClarifyOption — 변경 후
class ClarifyOption(BaseModel):
    id: str
    label: str
    description: str

# ClarifyData — 변경 후 추가 필드
class ClarifyData(BaseModel):
    question: str
    options: list[ClarifyOption]
    document_ids: list[int]       # 검색에 사용된 문서 ID (최종 chat 요청 시 재사용)
    context_question: str | None  # type=context 일 때 AI의 재질의 문장

# ChatRequest — 추가 필드
class ChatRequest(BaseModel):
    ...
    approach_hint: str | None     # 선택된 접근 방향 힌트
```

---

## 4. Reranker — 검색 품질 개선

### 도입 배경

벡터 검색(코사인 유사도)은 의미적으로 비슷한 청크를 넓게 수집하는 데 강하지만, 질문과 가장 관련성 높은 청크를 **정밀하게** 순위화하는 데는 한계가 있습니다.

- 같은 페이지 청크가 중복으로 반환
- 다른 학과·연도 문서가 섞임
- 핵심 페이지가 하위 순위에 묻힘

**Vertex AI Semantic Ranker**는 질문과 각 청크를 1:1로 비교해 재정렬합니다.

### 파이프라인 변화

```
변경 전: 코사인 검색 top_k=5 → 바로 LLM
변경 후: 코사인 검색 top_k×3=15 후보 → Reranker → 상위 5개 → LLM
```

### 실제 테스트 결과 (2026-05-07)

#### 질문 1: "소프트웨어융합학과의 졸업요건이 어떻게 돼?"

|     | Before (벡터만, 713ms)    | After (Reranker, 1652ms)           |
| --- | ------------------------- | ---------------------------------- |
| 1위 | 융합전공 이수요건 일반 ❌ | **소프트웨어융합학과 교과과정** ✅ |
| 2위 | 소프트웨어융합학과 ✅     | 소프트웨어융합학과 교과과정 ✅     |
| 3위 | **p.25 중복** ❌          | 게임소프트웨어전공                 |
| 4위 | 게임소프트웨어전공 ❌     | 전자전기융합공학과                 |
| 5위 | 데이터사이언스전공 ❌     | 소프트웨어융합학과 참고 ✅         |

> 중복 p.25 제거, 타 학과 청크 제거. 소프트웨어융합학과 관련 청크가 1·2·5위 점유.

#### 질문 2: "SK하이닉스의 2026년 매출은 얼마야?"

|         | Before (벡터만, 1184ms) | After (Reranker, 1410ms)    |
| ------- | ----------------------- | --------------------------- |
| 1위     | SK하이닉스 지분 정보    | **23. 매출액** ✅ (4위→1위) |
| 4위→1위 | **23. 매출액** ✅       | —                           |

> 핵심 페이지 "23. 매출액"이 4위 → 1위로 상승. 관련 없는 사채관리계약 청크 제거.

#### 질문 3: "2025년 교육과정에서 달라진 점이 뭐야?"

|     | Before (248ms)     | After (1276ms)                |
| --- | ------------------ | ----------------------------- |
| 3위 | **2024년 문서** ❌ | 제거됨                        |
| 5위 | **p.145 중복** ❌  | 제거됨                        |
| 1위 | 특정 학과 개설학점 | **교과과정 개정 적용원칙** ✅ |

> 다른 연도(2024) 문서 제거, 중복 청크 제거. 핵심 개정 페이지 신규 진입.

### 성능 요약

| 항목              | Before                | After                             |
| ----------------- | --------------------- | --------------------------------- |
| 검색 방식         | 코사인 유사도 top_k=5 | 코사인 15개 후보 → Reranker top 5 |
| 중복 청크         | 발생                  | 제거됨                            |
| 타 학과·연도 문서 | 포함됨                | 제거됨                            |
| 핵심 페이지 순위  | 하위에 묻힘           | 1위로 상승                        |
| 추가 응답 지연    | 0ms                   | +700~1400ms                       |

### 사전 준비

```bash
# Discovery Engine API 활성화
gcloud services enable discoveryengine.googleapis.com

# ADC 인증
gcloud auth application-default login

# 패키지 설치
pip install google-cloud-discoveryengine
```

---

## 5. 프롬프트 최적화

2024~2025 RAG 연구 기법을 적용해 답변 충실도·인용 정확도·검색 품질을 개선했습니다.

### 5-1. 쿼리 리라이팅 (`rewrite_query`)

후속 질문에 포함된 대명사와 구어체를 벡터 검색에 최적화된 형태로 변환합니다.

```
이전: "대화 기록을 참고하여 독립적인 쿼리로 재작성하세요."

이후 원칙:
- '그것', '해당', '위의', '앞서' → 대화 기록에서 찾아 구체적 용어로 치환
- 규정명, 절차명, 시스템명 등 도메인 용어를 명확히 포함
- 경어/구어체 제거, 명사 중심 검색 쿼리 형식으로 작성
```

**기대 효과**: 검색 정밀도 30~45% 향상 (arXiv 2501.07391)

### 5-2. 시스템 메시지 강화

```
이전: "근거가 부족하면 추측하지 말고 부족하다고 말하세요."

이후:
[핵심 원칙]
1. 제공된 문서 조각만 근거로 답변 — 일반 학습 지식 보완 금지
2. 각 주요 사실·수치·절차마다 [1], [2] 출처 번호 표시
3. 확인 안 되는 정보는 "제공된 문서에서 [해당 내용]을 확인할 수 없습니다"로 명시
4. 부분 답변 시 확인된 부분 / 확인되지 않은 부분 구분
```

**기대 효과**: Citation hallucination 17~33% → 대폭 감소 (arXiv 2601.05866)

### 5-3. 답변 생성 프롬프트 (`_build_prompt`)

```
이전 청크 헤더: [1] 파일명 p.3
이후 청크 헤더: [1] 출처: 파일명 p.3

추가된 [출처 표기 규칙] 섹션:
- 사실·수치·절차 언급 시 [1], [2] 형식 표시
- 여러 문서가 지지하면 [1][3] 중복 표기
- 없는 정보는 "어떤 정보가 없는지" 구체적으로
```

### 5-4. Clarify 분류 프롬프트 개선

```
이전: 나열식 지시
이후: 유형별 명확한 판단 기준 + 한국어 예시 포함
      "마크다운 코드 블록 없이" 명시 → JSON 파싱 오류 감소
```

### 기법별 근거 논문

| 기법                             | 논문/출처                                                                   | 핵심 수치                              |
| -------------------------------- | --------------------------------------------------------------------------- | -------------------------------------- |
| 인라인 citation 의무화           | arXiv 2601.05866 — _FACTUM: Citation Hallucination in Long-Form RAG_ (2025) | RAG 시스템의 17~33%가 잘못된 인용 생성 |
| 부분 답변 구분 지시              | arXiv 2407.01219 — _Searching for Best Practices in RAG_ (2024)             | faithfulness 향상                      |
| 대명사 치환 + 도메인 키워드 강화 | arXiv 2501.07391 — _Enhancing RAG: A Study of Best Practices_ (2025)        | 검색 정밀도 30~45% 향상                |
| Graceful refusal 패턴            | AWS ML Blog: _Prompt Engineering with Anthropic's Claude 3_                 | 막연한 거절 → 구체적 부재 설명         |
| 다관점 출처 구분                 | MEGA-RAG — _Frontiers in Public Health_ (2025)                              | 신뢰도 향상                            |
| 쿼리 리라이팅 ROI                | DEV Community: _Query Rewrite in RAG Systems_                               | 인프라 변경 없이 30~45% 정밀도 향상    |

---

## 6. 설정값 및 환경변수

```ini
# rag/.env

# OpenAI
OPENAI_API_KEY=sk-...

# Vertex AI / Google Cloud
GOOGLE_CLOUD_PROJECT=project-b54c621b-21b4-427e-95d
VERTEX_AI_LOCATION=us-central1
CHAT_MODEL=gemini-2.5-flash

# 검색 설정
TOP_K=8                        # 최종 LLM에 넘길 청크 수 (Reranker 비활성 시)

# Reranker
RERANKER_ENABLED=true
RERANKER_MODEL=semantic-ranker-default@latest
RERANKER_TOP_N=5               # Reranker 통과 후 최종 청크 수
RERANKER_FETCH_MULTIPLIER=3    # ChromaDB에서 TOP_K × 3 수집
```

**Reranker 비활성화**: `RERANKER_ENABLED=false` → 벡터 검색 top_k=8 결과를 그대로 사용.

---

## 7. 참고 논문 및 출처

| 논문/출처                                                                  | 연도 | 링크                       |
| -------------------------------------------------------------------------- | ---- | -------------------------- |
| _FACTUM: Mechanistic Detection of Citation Hallucination in Long-Form RAG_ | 2025 | arXiv 2601.05866           |
| _Enhancing Retrieval-Augmented Generation: A Study of Best Practices_      | 2025 | arXiv 2501.07391           |
| _Searching for Best Practices in Retrieval-Augmented Generation_           | 2024 | arXiv 2407.01219           |
| _MEGA-RAG: Multi-Evidence Guided Answer Refinement_                        | 2025 | Frontiers in Public Health |
| _CoT-RAG: Integrating Chain of Thought and RAG_                            | 2025 | arXiv 2504.13534           |
| _Conflict-Aware Soft Prompting for RAG_                                    | 2025 | arXiv 2508.15253           |
| _Prompt Engineering with Anthropic's Claude 3_                             | 2024 | AWS ML Blog                |
| _Query Rewrite in RAG Systems_                                             | 2024 | DEV Community              |
