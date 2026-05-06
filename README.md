# intra-Q
기업 내부 문서 Q&amp;A 챗봇의 FastAPI 백엔드 MVP입니다.

이 저장소의 Day4 기준 백엔드는 다음 흐름을 제공합니다.

- PDF 업로드
- PDF 텍스트 추출
- 페이지별 청크 분할
- SQLite 저장
- 문서/청크 조회
- mock RAG 채팅 응답
- Swagger UI 기반 데모

실제 임베딩, 벡터 검색, LLM 호출은 나중에 AI/RAG 담당자가 교체할 수 있도록 구조를 분리해 두었습니다.

## 기술 스택

- Python 3.14
- FastAPI
- Uvicorn
- SQLAlchemy
- SQLite
- PyMuPDF
- python-dotenv

## 프로젝트 구조

```text
backend/
    app/
        core/
            settings.py
        database/
            init_db.py
            session.py
        db/
            init_db.py
            session.py
        models/
            chunk.py
            document.py
        routers/
            chat.py
            documents.py
        schemas/
            chat.py
            common.py
            documents.py
        services/
            chat_service.py
            chunk_service.py
        utils/
            logging.py
    tests/
        fixtures/
            hr_policy.pdf
        run_pdf_pipeline.py
    requirements.txt
    .env
```

`app/database/`는 Day4 정리용 구조이고, `app/db/`는 기존 호환성 레이어입니다.

## 설치 방법

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 환경 변수

`backend/.env` 파일을 사용합니다.

```env
DATABASE_URL=sqlite:///./intra_q.db
OPENAI_API_KEY=
```

- `DATABASE_URL`: SQLite 연결 문자열
- `OPENAI_API_KEY`: 추후 실제 LLM 연동 시 사용

## 실행 방법

```powershell
cd backend
uvicorn app.main:app --reload
```

브라우저에서 Swagger UI는 아래 주소로 열 수 있습니다.

```text
http://127.0.0.1:8000/docs
```

## API 목록

### GET /health

응답 예시:

```json
{
    "status": "ok"
}
```

### POST /api/documents/upload

PDF 업로드 후 텍스트 추출, 청크 분할, DB 저장까지 한 번에 처리합니다.

응답 예시:

```json
{
    "success": true,
    "message": "Document uploaded successfully",
    "data": {
        "document_id": 1,
        "file_name": "hr_policy.pdf",
        "page_count": 2,
        "chunk_count": 3
    }
}
```

### GET /api/documents/{document_id}

저장된 문서와 청크 미리보기를 조회합니다.

응답 예시:

```json
{
    "success": true,
    "message": "Document retrieved successfully",
    "data": {
        "document_id": 1,
        "file_name": "hr_policy.pdf",
        "page_count": 2,
        "chunks": [
            {
                "id": 1,
                "page_number": 1,
                "preview": "회사 연차 정책...",
                "len": 120,
                "created_at": "2026-05-06T12:34:56"
            }
        ]
    }
}
```

### POST /api/chat

mock RAG 기반 질문 응답 API입니다.

요청 예시:

```json
{
    "question": "회사 연차 정책은 어떻게 되나요?"
}
```

응답 예시:

```json
{
    "success": true,
    "message": "Chat response generated successfully",
    "data": {
        "answer": "근속 기간이 1년 미만인 직원은 매월 연차 1일을 사용할 수 있습니다. (참고문서: hr_policy.pdf 1페이지)",
        "sources": [
            {
                "document": "hr_policy.pdf",
                "page": 1,
                "preview": "회사 연차 정책..."
            }
        ]
    }
}
```

## Demo / 검증용 스크립트

샘플 PDF로 전체 흐름을 빠르게 확인할 수 있습니다.

```powershell
cd backend
python tests\run_pdf_pipeline.py
```

## 동작 원리

- 업로드된 PDF는 PyMuPDF로 페이지 단위 텍스트를 추출합니다.
- 페이지 텍스트는 문단 단위로 나뉘고, 300~500자 기준으로 청크가 생성됩니다.
- 청크는 `documents`와 `chunks` 테이블에 저장됩니다.
- `/api/chat`은 SQLite의 청크를 간단한 토큰 매칭으로 검색해 mock RAG 응답을 반환합니다.
- 추후 embedding/vector search로 교체할 수 있도록 `services/chat_service.py`에 검색/응답 생성 로직을 분리해 두었습니다.

## Swagger 문서

- `summary`
- `description`
- `response_model`

을 각 엔드포인트에 추가해 Swagger UI에서 바로 이해하기 쉽게 정리했습니다.

## 범위

이 MVP에는 다음은 포함하지 않았습니다.

- Celery
- Redis
- JWT 인증
- 백그라운드 잡 시스템
- 분산 벡터 데이터베이스

이후 Day5/확장 단계에서 필요해지면 추가하면 됩니다.
