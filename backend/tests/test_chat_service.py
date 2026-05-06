from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.session import Base
from app.models.chunk import Chunk
from app.models.document import Document
from app.services.chat_service import generate_chat_response


def test_generate_chat_response_returns_sources() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        document = Document(file_name="hr_policy.pdf", page_count=3)
        db.add(document)
        db.flush()
        db.add(
            Chunk(
                document_id=document.id,
                page_number=3,
                content="입사 1년 미만 근로자는 월 1회 연차를 사용할 수 있습니다.",
            )
        )
        db.commit()

        response = generate_chat_response("회사 연차 정책은 어떻게 되나요?", db)

        assert response.sources
        assert response.sources[0].document == "hr_policy.pdf"
        assert response.sources[0].page == 3
        assert "mock RAG 응답" in response.answer
    finally:
        db.close()
