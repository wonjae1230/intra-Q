# Clarify 단계 재설계 — 변경사항 정리

## 개요

기존의 "어떤 문서를 기반으로 답변할까요?" 방식에서 **AI가 스스로 생각을 정리하고 답변 방향을 제시하는 구조**로 전면 개편했습니다.  
또한 질문에 사용자 맥락이 부족할 경우 AI가 역으로 질문하는 기능을 추가했습니다.

---

## 변경 전 vs 변경 후

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| Clarify 방식 | 문서 카드 선택 (다중 선택) | AI 생성 접근 방향 카드 (단일 선택) |
| 단순 질문 처리 | 항상 clarify 단계 거침 | LLM이 단순 질문 감지 시 바로 답변 |
| 맥락 부족 처리 | 오답 또는 "찾을 수 없음" 반환 | AI가 맥락 질문 재질의 |
| 답변 방향 반영 | 없음 | `approach_hint` 로 LLM 프롬프트에 주입 |

---

## 전체 흐름

```
사용자 질문 입력
  │
  ▼
POST /api/chat/clarify
  │
  ├─ 벡터 검색 (청크 retrieval)
  │
  └─ LLM 분석 → 세 가지 분기:
       │
       ├─ [맥락 부족] "어느 학과/학년이신가요?" 재질의
       │     → 사용자 답변 → 질문+맥락 합쳐서 clarify 재실행
       │
       ├─ [단순 질문] 바로 POST /api/chat 호출
       │
       └─ [복잡한 질문] 2-3개 접근 방향 카드 표시
               → 사용자 선택
               → POST /api/chat (approach_hint 포함)
                     → LLM이 선택된 방향에 맞게 답변 생성
```

---

## 수정 파일별 상세 내용

### 1. `rag/generator/generator.py`

#### `generate_clarify_options()` 추가 (신규)

LLM에게 질문과 청크를 넘겨 세 가지 중 하나를 JSON으로 반환하게 함.

```python
# 반환 형식
{"type": "context", "question": "어느 학과/학년이신가요?"}  # 맥락 부족
{"type": "direct"}                                          # 단순 질문
{"type": "options", "items": [{id, label, description}]}   # 접근 방향 제시
```

LLM 프롬프트 핵심 지시:
- `나`, `내가`, `우리` 등 개인 맥락이 필요한데 정보가 없으면 → `context` 반환
- 단순하거나 방향이 하나뿐이면 → `direct` 반환
- 여러 관점이 가능하면 2-3개 → `options` 반환

#### `generate()` 수정

`approach_hint` 파라미터 추가. 선택된 접근 방향을 프롬프트 앞에 삽입.

```python
def generate(self, question, chunks, history=None, approach_hint=None):
    ...

def _build_prompt(self, question, chunks, history=None, approach_hint=None):
    approach_block = f"다음 관점에서 답변하세요: {approach_hint}\n\n" if approach_hint else ""
    ...
```

---

### 2. `rag/pipeline.py`

#### `search_with_options()` 수정

기존: 문서별로 그룹핑해서 document 카드 반환  
변경: LLM `generate_clarify_options()` 호출 후 결과 타입에 따라 분기

- 검색된 청크의 고유 `document_ids` 수집 → 최종 chat 요청 시 재사용
- `context_question` 필드 포함하여 반환

```python
return {
    "question": question,
    "options": [...],           # type=options 일 때
    "document_ids": [...],      # 검색에 사용된 문서 ID
    "context_question": "...",  # type=context 일 때, 나머지는 None
}
```

#### `query()` 수정

`approach_hint` 파라미터 추가 → `generator.generate()` 로 전달

---

### 3. `backend/app/schemas/chat.py`

#### `ClarifyOption` 변경

```python
# 변경 전
class ClarifyOption(BaseModel):
    document_id: int
    file_name: str
    preview: str
    chunk_count: int

# 변경 후
class ClarifyOption(BaseModel):
    id: str
    label: str
    description: str
```

#### `ClarifyData` 변경

```python
class ClarifyData(BaseModel):
    question: str
    options: list[ClarifyOption]
    document_ids: list[int] = Field(default_factory=list)  # 신규
    context_question: str | None = None                     # 신규
```

#### `ChatRequest` 변경

```python
class ChatRequest(BaseModel):
    ...
    approach_hint: str | None = Field(default=None, ...)    # 신규
```

---

### 4. `backend/app/services/chat_service.py`

`generate_chat_response()` 에 `approach_hint` 파라미터 추가 → `rag_query()` 로 전달

```python
def generate_chat_response(question, ..., approach_hint=None):
    ...
    rag_result = rag_query(..., approach_hint=approach_hint)
```

---

### 5. `backend/app/routers/chat.py`

- `clarify` 엔드포인트: `context_question` 필드를 `ClarifyData` 에 포함
- `chat` 엔드포인트: `request.approach_hint` 를 `generate_chat_response()` 로 전달

---

### 6. `frontend/src/lib/api.js`

`askQuestion()` 에 `approachHint` 파라미터 추가

```js
export async function askQuestion(question, documentIds = [], approachHint = null) {
    body: JSON.stringify({
        question,
        document_ids: documentIds,
        ...(approachHint ? { approach_hint: approachHint } : {}),
    })
}
```

---

### 7. `frontend/src/pages/ChatPage.jsx`

#### 신규: `ContextRequestMessage` 컴포넌트

맥락 부족 시 AI 질문 + 텍스트 입력창 표시.  
사용자 입력 → 원본 질문과 합쳐서 clarify 재실행.

```
"내가 필수로 들어야하는 전공과목이 뭐야"
  + AI: "어느 학과/학년이신가요?"
  + 사용자: "소프트웨어융합학과 3학년"
  → "내가 필수로 들어야하는 전공과목이 뭐야 (소프트웨어융합학과 3학년)" 으로 재질의
```

#### 변경: `ClarifyMessage` 컴포넌트

- 다중 선택 → **단일 선택** (라디오 버튼 스타일)
- 문서 카드 → **접근 방향 카드** (`label` + `description`)
- 버튼 텍스트: "이 방향으로 답변받기"

#### 변경: `handleSendMessage()` 분기 추가

```
clarify 응답 수신
  ├─ context_question 있음 → context_request 메시지 추가
  ├─ options 없음 (direct) → 바로 _fetchAnswer()
  └─ options 있음 → clarify 메시지 추가
```

#### 변경: `handleSubmitClarify()`

선택된 옵션의 `label + description` 을 `approach_hint` 로 조합해서 `askQuestion()` 호출

#### 변경: 세션 표시

"문서 다시 선택" → "새 질문 시작"

---

## 메시지 타입 목록

| type | 설명 |
|---|---|
| `user` | 사용자 메시지 |
| `context_request` | AI가 맥락을 묻는 메시지 (텍스트 입력 포함) |
| `clarify` | AI가 접근 방향 선택지를 제시하는 메시지 |
| `ai` | AI 최종 답변 메시지 |
